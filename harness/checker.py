"""Check a sample of unmatched findings: are they real defects the golden set missed?

THIS MAKES PAID API CALLS (Claude Sonnet 5.5 by default).

A finding that matches no golden comment is either wrong or a real issue the
human reviewers did not write down. This script takes a seeded random sample
of unmatched findings from completed pilot runs, stratified by model and arm,
and asks a checker model for a verdict on each, given the pull request's diff.

The checker is not told which model or arm produced a finding.

Limits, stated with any number this produces:
  - The checker sees the diff, not the whole repository. A finding that needs
    wider context gets "cannot_tell".
  - It is a model's opinion. A hand-checked subsample gives its error rate.

Usage:
  python checker.py --pilot <pilot out dir> --org <github org> --env-file <.env>
      --per-cell 25 [--gh <path>] [--model claude-sonnet-5-5]
Writes <pilot out dir>/checker/verdicts.jsonl and sample.json.
"""

import argparse
import json
import random
import subprocess
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2026-10-21"
CHECKER_VERSION = "1"
SEED = 20261115
MAX_DIFF_CHARS = 400_000

INSTRUCTIONS = """You are checking one finding from an automated code review of a pull request.

You are given the pull request's title and its full diff, then one finding. Decide whether the finding describes a real defect in the code this pull request adds or changes.

Verdicts:
- "real": the diff shows the defect exists. You can point to the lines.
- "not_real": the diff shows the finding is wrong, or it is not a defect (a style preference, a speculative concern with no concrete failure, or something the code already handles).
- "cannot_tell": deciding needs code that is not in the diff.

Be strict. Choose "real" only when the diff itself supports it. Do not give the finding the benefit of the doubt, and do not reject it merely because it is minor.

Also report:
- in_changed_code: whether the finding is about lines this pull request adds or changes.
- evidence: the file and lines that support your verdict, or what is missing."""

SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["real", "not_real", "cannot_tell"]},
        "in_changed_code": {"type": "boolean"},
        "evidence": {"type": "string"},
    },
    "required": ["verdict", "in_changed_code", "evidence"],
    "additionalProperties": False,
}


def read_key(env_file):
    for line in Path(env_file).read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("ANTHROPIC_API_KEY="):
            return line.strip().split("=", 1)[1].strip()
    raise SystemExit("ANTHROPIC_API_KEY not found in env file")


def call(key, model, title, diff, finding):
    body = {
        "model": model, "max_tokens": 4000,
        "system": [{"type": "text", "text": INSTRUCTIONS}],
        "messages": [{"role": "user", "content": [
            # The diff is the same for every finding on a case, so it is cached.
            {"type": "text", "text": f"Pull request title: {title}\n\nDiff:\n{diff}", "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": f"Finding to check:\n{finding}"},
        ]}],
        "output_config": {"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
    }
    data = json.dumps(body).encode("utf-8")
    last = None
    for attempt in range(5):
        req = urllib.request.Request(API_URL, data=data, method="POST", headers={
            "content-type": "application/json", "x-api-key": key, "anthropic-version": API_VERSION})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                resp = json.loads(r.read())
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}"
            if e.code in (429, 500, 502, 503, 529):
                time.sleep(min(60, 2 ** attempt * 3))
                continue
            raise RuntimeError(last)
        except (urllib.error.URLError, TimeoutError) as e:
            last = f"network: {e}"
            time.sleep(2 ** attempt)
            continue
        if resp.get("model") != model:
            raise RuntimeError(f"checker answered by {resp.get('model')}")
        if resp.get("stop_reason") in ("refusal", "max_tokens"):
            raise RuntimeError(f"checker stopped: {resp.get('stop_reason')}")
        text = next(b["text"] for b in resp.get("content", []) if b.get("type") == "text")
        return json.loads(text), resp.get("usage") or {}
    raise RuntimeError(f"checker call failed: {last}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pilot", required=True)
    p.add_argument("--org", required=True)
    p.add_argument("--env-file", required=True)
    p.add_argument("--per-cell", type=int, default=25)
    p.add_argument("--gh", default="gh")
    p.add_argument("--model", default="claude-sonnet-5-5")
    p.add_argument("--workers", type=int, default=4)
    args = p.parse_args()

    pilot = Path(args.pilot)
    out = pilot / "checker"
    out.mkdir(exist_ok=True)

    pool = {}
    for sp in sorted(pilot.glob("*/status.json")):
        s = json.load(open(sp, encoding="utf-8"))
        jp = sp.parent / "judgement.json"
        if s.get("status") != "completed" or not jp.exists():
            continue
        j = json.load(open(jp, encoding="utf-8"))
        for i, cand in enumerate(j["unmatched_candidates"]):
            pool.setdefault((s["model_key"], s["arm"]), []).append(
                {"id": f"{s['run_id']}#{i}", "run_id": s["run_id"], "case": s["case"], "model_key": s["model_key"],
                 "arm": s["arm"], "finding": cand})
    sample = []
    population = {}
    for cell in sorted(pool):
        items = sorted(pool[cell], key=lambda x: x["id"])
        population["/".join(cell)] = len(items)
        random.Random(f"{SEED}:{cell}").shuffle(items)
        sample += items[: args.per_cell]
    json.dump({"seed": SEED, "per_cell": args.per_cell, "population": population, "sampled": len(sample),
               "checker_version": CHECKER_VERSION, "model": args.model},
              open(out / "sample.json", "w", encoding="utf-8"), indent=1)
    print("unmatched findings per cell:", population, "| sampled:", len(sample), flush=True)

    done = set()
    vp = out / "verdicts.jsonl"
    if vp.exists():
        done = {json.loads(l)["id"] for l in open(vp, encoding="utf-8")}
    todo = [s for s in sample if s["id"] not in done]

    diffs = {}
    for case in sorted({s["case"] for s in todo}):
        title = subprocess.run([args.gh, "pr", "view", "1", "--repo", f"{args.org}/{case}", "--json", "title", "--jq", ".title"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
        diff = subprocess.run([args.gh, "pr", "diff", "1", "--repo", f"{args.org}/{case}"],
                              capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
        diffs[case] = (title, diff[:MAX_DIFF_CHARS], len(diff) > MAX_DIFF_CHARS)

    key = read_key(args.env_file)
    # Group by case so the cached diff is reused back to back.
    todo.sort(key=lambda s: (s["case"], s["id"]))

    def one(s):
        title, diff, truncated = diffs[s["case"]]
        try:
            v, u = call(key, args.model, title, diff, s["finding"])
            rec = {**s, **v, "diff_truncated": truncated, "error": None,
                   "input_tokens": u.get("input_tokens", 0), "output_tokens": u.get("output_tokens", 0),
                   "cache_read": u.get("cache_read_input_tokens", 0), "cache_write": u.get("cache_creation_input_tokens", 0)}
        except Exception as e:
            rec = {**s, "verdict": None, "error": str(e)}
        return rec

    with ThreadPoolExecutor(max_workers=args.workers) as ex, open(vp, "a", encoding="utf-8") as f:
        for rec in ex.map(one, todo):
            f.write(json.dumps(rec) + "\n")
            f.flush()
    recs = [json.loads(l) for l in open(vp, encoding="utf-8")]
    tally = {}
    for r in recs:
        k = (r["model_key"], r["arm"], r.get("verdict") or "error")
        tally[k] = tally.get(k, 0) + 1
    for k in sorted(tally):
        print("/".join(k[:2]), k[2], tally[k])


if __name__ == "__main__":
    main()
