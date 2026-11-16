"""Build the per-request log for one run directory made by run_real.py.

Joins three sources by request ID:
  - request body files   -> requested model, effort, thinking
  - response body files  -> returned model, usage, fallback markers
  - telemetry events     -> role, agent IDs, refusals, errors, cost estimate

Prints a summary and writes requests.jsonl into the run directory.
Usage: python analyze_run.py <run dir> [--expected-main <model id>]
"""

import argparse
import glob
import json
import os
from collections import Counter, defaultdict
from pathlib import Path


def attrs(rec):
    out = {}
    for a in rec.get("attributes", []):
        v = a.get("value", {})
        out[a["key"]] = next(iter(v.values())) if v else None
    return out


def load_events(run):
    events = []
    path = run / "receiver.jsonl.otel.jsonl"
    if not path.exists():
        return events
    for line in open(path, encoding="utf-8"):
        o = json.loads(line)
        if o.get("signal") != "logs":
            continue
        for rl in o["body"].get("resourceLogs", []):
            for sl in rl.get("scopeLogs", []):
                for lr in sl.get("logRecords", []):
                    events.append(attrs(lr))
    return events


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("run")
    p.add_argument("--expected-main")
    args = p.parse_args()
    run = Path(args.run)
    manifest = json.load(open(run / "manifest.json", encoding="utf-8"))
    expected_main = args.expected_main or manifest["model"]
    events = load_events(run)
    by_name = defaultdict(list)
    for e in events:
        by_name[e.get("event.name")].append(e)

    # request bodies, keyed by request_body_id (file stem)
    req_bodies = {}
    for f in glob.glob(str(run / "bodies" / "*.request.json")):
        b = json.load(open(f, encoding="utf-8"))
        req_bodies[Path(f).name.split(".")[0]] = b
    # response bodies keyed by request_id
    resp_bodies = {}
    for f in glob.glob(str(run / "bodies" / "*.response.json")):
        resp_bodies[Path(f).name.split(".")[0]] = json.load(open(f, encoding="utf-8"))
    index = []
    ip = run / "bodies" / "index.jsonl"
    if ip.exists():
        index = [json.loads(l) for l in open(ip, encoding="utf-8")]
    # map request_id -> request_body_id via api_response_body events / index
    rid_to_rbid = {}
    for e in by_name["api_response_body"]:
        if e.get("request_id") and e.get("request_body_id"):
            rid_to_rbid[e["request_id"]] = e["request_body_id"]
    for i in index:
        rf = i.get("request_file")
        if i.get("request_id") and rf:
            rid_to_rbid.setdefault(i["request_id"], Path(rf).name.split(".")[0])
    refusals = {e.get("request_id"): e for e in by_name["api_refusal"]}

    rows = []
    for e in sorted(by_name["api_request"], key=lambda e: num(e.get("event.sequence"))):
        rid = e.get("request_id")
        rb = req_bodies.get(rid_to_rbid.get(rid, ""), None)
        resp = resp_bodies.get(rid)
        usage = (resp or {}).get("usage") or {}
        requested = (rb or {}).get("model")
        returned = (resp or {}).get("model") or e.get("model")
        blocks = [c.get("type") for c in (resp or {}).get("content", [])]
        iters = usage.get("iterations") or []
        is_sub = bool(e.get("agent_id")) or str(e.get("query_source", "")).startswith("agent")
        role = "subagent" if is_sub else ("main" if e.get("query_source") in ("sdk", "repl_main_thread") else "auxiliary")
        fallback = bool(
            (requested and returned and requested != returned)
            or "fallback" in blocks
            or any(i.get("type") == "fallback_message" for i in iters)
            or (rid in refusals and str(refusals[rid].get("server_fallback_hop")).lower() == "true")
        )
        rows.append({
            "sequence": e.get("event.sequence"), "request_id": rid, "role": role,
            "query_source": e.get("query_source"), "agent_id": e.get("agent_id"),
            "parent_agent_id": e.get("parent_agent_id"), "agent_name": e.get("agent.name"),
            "skill_name": e.get("skill.name"), "plugin_name": e.get("plugin.name"),
            "requested_model": requested, "returned_model": returned, "effort": e.get("effort"),
            "request_effort": ((rb or {}).get("output_config") or {}).get("effort"),
            "thinking": (rb or {}).get("thinking"),
            "has_request_body": rb is not None, "has_response_body": resp is not None,
            "stop_reason": (resp or {}).get("stop_reason"),
            "input_tokens": num(e.get("input_tokens")), "output_tokens": num(e.get("output_tokens")),
            "cache_read_tokens": num(e.get("cache_read_tokens")),
            "cache_creation_tokens": num(e.get("cache_creation_tokens")),
            "cost_usd_estimate": num(e.get("cost_usd")),
            "refused": rid in refusals, "fallback_flag": fallback,
            "off_target_flag": bool(role == "main" and requested and requested != expected_main),
        })
    with open(run / "requests.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    # final result from the stream
    result = None
    init = None
    sp = run / "stream.jsonl"
    if sp.exists():
        for line in open(sp, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if o.get("type") == "result":
                result = o
            if o.get("type") == "system" and o.get("subtype") == "init":
                init = o

    print(f"run: {run.name}  exit={manifest.get('exit_code')}  elapsed={manifest.get('elapsed_s')}s  model={manifest['model']}  effort={manifest['effort']}")
    if init:
        print("init: model=", init.get("model"), "| plugins=", [pl.get("name") if isinstance(pl, dict) else pl for pl in init.get("plugins", [])],
              "| plugin_errors=", init.get("plugin_errors"))
    print(f"events: {dict(Counter(e.get('event.name') for e in events))}")
    print(f"request body files={len(req_bodies)}  response body files={len(resp_bodies)}  api_request events={len(rows)}  "
          f"api_error={len(by_name['api_error'])}  api_refusal={len(by_name['api_refusal'])}")
    missing = [r["request_id"] for r in rows if not r["has_request_body"] or not r["has_response_body"]]
    print(f"requests missing a body file: {len(missing)}")
    groups = defaultdict(lambda: Counter())
    for r in rows:
        k = (r["role"], r["agent_name"] or r["query_source"], r["requested_model"], r["returned_model"], r["effort"])
        g = groups[k]
        g["n"] += 1
        for t in ("input_tokens", "output_tokens", "cache_read_tokens", "cache_creation_tokens", "cost_usd_estimate"):
            g[t] += r[t]
    print("\nrole | source/agent | requested -> returned | effort | requests | in | out | cache_read | cache_write | est. cost")
    for k, g in sorted(groups.items(), key=lambda kv: str(kv[0])):
        print(f"{k[0]} | {k[1]} | {k[2]} -> {k[3]} | {k[4]} | {g['n']} | {int(g['input_tokens'])} | {int(g['output_tokens'])} | "
              f"{int(g['cache_read_tokens'])} | {int(g['cache_creation_tokens'])} | ${g['cost_usd_estimate']:.4f}")
    total = sum(r["cost_usd_estimate"] for r in rows)
    print(f"\nflags: fallback={sum(r['fallback_flag'] for r in rows)}  off_target_main={sum(r['off_target_flag'] for r in rows)}  refused={sum(r['refused'] for r in rows)}")
    print(f"estimated cost from events: ${total:.4f}")
    subs = by_name["subagent_completed"]
    for s in subs:
        print("subagent_completed:", {k: s.get(k) for k in ("agent_type", "model", "final_model", "model_swapped", "total_tool_uses", "duration_ms")})
    if result:
        mu = result.get("modelUsage") or {}
        print(f"result: is_error={result.get('is_error')} subtype={result.get('subtype')} turns={result.get('num_turns')} "
              f"total_cost_usd={result.get('total_cost_usd')}")
        for m, u in mu.items():
            print(f"  modelUsage {m}: in={u.get('inputTokens')} out={u.get('outputTokens')} cache_read={u.get('cacheReadInputTokens')} "
                  f"cache_write={u.get('cacheCreationInputTokens')} cost=${u.get('costUSD'):.4f}")
        by_model = defaultdict(float)
        for r in rows:
            by_model[r["returned_model"]] += r["cost_usd_estimate"]
        print("  cost by returned model from events:", {m: round(c, 4) for m, c in by_model.items()})
    else:
        print("result: none found in stream")


if __name__ == "__main__":
    main()
