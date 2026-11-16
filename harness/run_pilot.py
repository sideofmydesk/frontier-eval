"""Run the pilot: every case x model x arm x repeat, then grade each review.

THIS MAKES PAID API CALLS. It stops starting new runs once estimated spend
reaches --max-spend. It is resumable: a run with a status.json is skipped.

Order: all of repeat 1 (shuffled with a fixed seed), then all of repeat 2, so
that every case has one run per cell before any case gets a second.

Each run ends in exactly one status:
  completed        review finished, logs complete, right model throughout
  refused          a request was declined by a safety classifier (fallback is off)
  fallback         a request was answered by another model, or the main thread
                   asked for the wrong model
  budget_exceeded  the per-run budget cap stopped the session
  review_error     Claude Code reported an error result
  harness_failure  logs missing or incomplete, timeout, or no result

Only completed runs are judged.

Usage:
  python run_pilot.py --ground-truth <dir> --cases <dir> --out <dir> --claude <binary>
      --plugin-dir <dir> --env-file <.env> --org <github org> --max-spend 170
      [--workers 3] [--gh <path>] [--dry-run] [--repeats 2]
"""

import argparse
import json
import os
import random
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPIKE = HERE.parent / "spikes" / "request-logging"
SEED = 20261115
MODELS = {"opus55": "claude-opus-5-5", "fable52": "claude-fable-5-2"}
EFFORT = "high"
PLUGIN_PROMPT = "/code-review:code-review 1"
BASELINE_PROMPT_VERSION = "1"
BASELINE_PROMPT = ("Review pull request #1 in this repository. Use the gh CLI to read it. Report every bug or defect "
                   "you find in the changed code, giving the file path and line for each. Do not post anything to GitHub.")
# Read-only commands, allowed in both arms. `gh search` is left out on purpose:
# it could surface the benchmark's public answers.
READ_ONLY = [
    "Bash(gh pr view:*)", "Bash(gh pr diff:*)", "Bash(gh pr list:*)", "Bash(gh issue view:*)", "Bash(gh issue list:*)",
    "Bash(git log:*)", "Bash(git diff:*)", "Bash(git show:*)", "Bash(git blame:*)", "Bash(git ls-tree:*)",
    "Bash(git ls-files:*)", "Bash(git status:*)", "Bash(git grep:*)", "Bash(git rev-parse:*)",
    "Bash(ls:*)", "Bash(cat:*)", "Bash(grep:*)",
]
BUDGET = {("fable52", "plugin"): 6.0, ("fable52", "baseline"): 4.0, ("opus55", "plugin"): 4.0, ("opus55", "baseline"): 3.0}
LEAK_MARKERS = [b"code-review-benchmark", b"withmartian", b"golden_comments", b"ai-code-review-evaluation"]
JUDGE_PRICE = (2.0, 10.0)  # Sonnet 5.5, dollars per million input and output tokens

_lock = threading.Lock()
_spent = 0.0
_stop = False


def sh(cmd, cwd=None, timeout=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def last_result(stream_path):
    result = None
    if stream_path.exists():
        for line in open(stream_path, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line.startswith("{"):
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                if o.get("type") == "result":
                    result = o
    return result


def classify(out, manifest):
    result = last_result(out / "stream.jsonl")
    rows = []
    rp = out / "requests.jsonl"
    if rp.exists():
        rows = [json.loads(l) for l in open(rp, encoding="utf-8")]
    n_req_bodies = len(list((out / "bodies").glob("*.request.json")))
    info = {
        "requests": len(rows), "request_body_files": n_req_bodies,
        "cost_usd": (result or {}).get("total_cost_usd") or 0.0,
        "models": sorted({r["returned_model"] for r in rows if r.get("returned_model")}),
        "subagent_models": sorted({r["requested_model"] for r in rows if r["role"] == "subagent" and r.get("requested_model")}),
        "refused": sum(1 for r in rows if r.get("refused")),
        "fallback": sum(1 for r in rows if r.get("fallback_flag")),
        "off_target_main": sum(1 for r in rows if r.get("off_target_flag")),
        "missing_body": sum(1 for r in rows if not r.get("refused") and not (r["has_request_body"] and r["has_response_body"])),
        "result_subtype": (result or {}).get("subtype"), "stop_reason": (result or {}).get("stop_reason"),
        "num_turns": (result or {}).get("num_turns"),
        "permission_denials": len((result or {}).get("permission_denials") or []),
    }
    if manifest.get("timed_out") or result is None or n_req_bodies == 0 or not rows:
        status = "harness_failure"
    elif info["refused"] or info["stop_reason"] == "refusal":
        status = "refused"
    elif info["fallback"] or info["off_target_main"]:
        status = "fallback"
    elif info["missing_body"]:
        status = "harness_failure"
    elif "budget" in str(info["result_subtype"] or ""):
        status = "budget_exceeded"
    elif result.get("is_error"):
        status = "review_error"
    else:
        status = "completed"
    return status, info


def leak_scan(out):
    hits = set()
    for f in (out / "bodies").glob("*.json"):
        data = f.read_bytes()
        for m in LEAK_MARKERS:
            if m in data:
                hits.add(m.decode())
    return sorted(hits)


def do_run(job, args):
    global _spent, _stop
    out = Path(args.out) / job["run_id"]
    if (out / "status.json").exists():
        return json.load(open(out / "status.json", encoding="utf-8"))
    with _lock:
        if _stop or _spent + BUDGET[(job["model_key"], job["arm"])] > args.max_spend:
            _stop = True
            return None
    # A review that already finished (manifest and result on disk) is not run or paid for
    # again: only the grading is redone. Anything less complete is set aside and re-run.
    review_done = (out / "manifest.json").exists() and last_result(out / "stream.jsonl") is not None
    if out.exists() and not review_done:
        out.rename(out.with_name(out.name + f".partial-{int(time.time())}"))
    cwd = Path(args.cases) / job["case"]
    cmd = [sys.executable, "-I", str(SPIKE / "run_real.py"), "--claude", args.claude, "--env-file", args.env_file,
           "--out", str(out), "--cwd", str(cwd), "--model", MODELS[job["model_key"]], "--effort", EFFORT,
           "--budget", str(BUDGET[(job["model_key"], job["arm"])]), "--prepend-path", str(Path(args.gh).parent),
           "--prompt", PLUGIN_PROMPT if job["arm"] == "plugin" else BASELINE_PROMPT, "--timeout", "2400"]
    if job["arm"] == "plugin":
        cmd += ["--plugin-dir", args.plugin_dir]
    for rule in READ_ONLY:
        cmd += ["--allowed-tools", rule]
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if review_done:
        r = subprocess.CompletedProcess(cmd, 0, "", "")
    else:
        try:
            r = sh(cmd, timeout=2700)
        except subprocess.TimeoutExpired:
            r = subprocess.CompletedProcess(cmd, 1, "", "runner timed out")
    manifest = json.load(open(out / "manifest.json", encoding="utf-8")) if (out / "manifest.json").exists() else {"timed_out": True}
    a = sh([sys.executable, "-I", str(SPIKE / "analyze_run.py"), str(out)]) if (out / "manifest.json").exists() else None
    if a is not None:
        (out / "analyze.txt").write_text(a.stdout + a.stderr, encoding="utf-8")
    status, info = classify(out, manifest) if out.exists() else ("harness_failure", {"cost_usd": 0.0})
    rec = {"run_id": job["run_id"], **job, "model": MODELS[job["model_key"]], "effort": EFFORT, "status": status,
           "started_utc": started, "elapsed_s": manifest.get("elapsed_s"), **info,
           "baseline_prompt_version": BASELINE_PROMPT_VERSION if job["arm"] == "baseline" else None,
           "runner_stderr": (r.stderr or "")[-300:] if r.returncode else "", "graded_from_saved_review": review_done}
    rec["leak_markers"] = leak_scan(out) if out.exists() else []
    # Did the run post anything to the pull request? It must not.
    g = sh([args.gh, "pr", "view", "1", "--repo", f"{args.org}/{job['case']}", "--json", "comments,reviews",
            "--jq", "(.comments|length)+(.reviews|length)"])
    rec["pr_comments_after"] = int(g.stdout.strip()) if g.stdout.strip().isdigit() else None
    dirty = sh(["git", "status", "--porcelain"], cwd=cwd).stdout.strip()
    rec["checkout_dirty"] = bool(dirty)

    judge_cost = 0.0
    if status == "completed":
        jp = out / "judgement.json"
        if jp.exists():
            jp.unlink()  # never reuse a judgement from an interrupted attempt
        try:
            j = sh([sys.executable, "-I", str(HERE / "judge.py"), "--run", str(out), "--golden",
                    str(Path(args.ground_truth) / f"{job['project']}.json"), "--source-url", job["source_url"],
                    "--env-file", args.env_file], timeout=3600)
        except subprocess.TimeoutExpired:
            j = subprocess.CompletedProcess([], 1, "", "judge timed out")
        if jp.exists():
            jd = json.load(open(jp, encoding="utf-8"))
            judge_cost = jd["judge_input_tokens"] * JUDGE_PRICE[0] / 1e6 + jd["judge_output_tokens"] * JUDGE_PRICE[1] / 1e6
            rec.update({"judged": True, "n_candidates": jd["n_candidates"], "judge_errors": len(jd["errors"]),
                        "scores": jd["scores"]})
        else:
            rec.update({"judged": False, "judge_stderr": (j.stderr or j.stdout or "")[-300:]})
    rec["judge_cost_usd_estimate"] = round(judge_cost, 4)
    (out / "status.json").write_text(json.dumps(rec, indent=1), encoding="utf-8") if out.exists() else None
    with _lock:
        _spent += (rec.get("cost_usd") or 0.0) + judge_cost
        if rec.get("pr_comments_after"):
            _stop = True  # a posted comment would make the plugin skip this case from now on
        line = (f"{time.strftime('%H:%M:%S')} {job['run_id']:34s} {status:15s} ${rec.get('cost_usd') or 0:.2f} "
                f"judge ${judge_cost:.2f} cand={rec.get('n_candidates')} spent=${_spent:.2f}"
                f"{' LEAK ' + ','.join(rec['leak_markers']) if rec['leak_markers'] else ''}"
                f"{' PR-COMMENT' if rec.get('pr_comments_after') else ''}{' DIRTY' if rec['checkout_dirty'] else ''}")
        print(line, flush=True)
        with open(Path(args.out) / "progress.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")
    return rec


def main():
    global _spent
    p = argparse.ArgumentParser()
    p.add_argument("--ground-truth", required=True)
    p.add_argument("--cases", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--claude", required=True)
    p.add_argument("--plugin-dir", required=True)
    p.add_argument("--env-file", required=True)
    p.add_argument("--org", required=True)
    p.add_argument("--max-spend", type=float, required=True)
    p.add_argument("--workers", type=int, default=3)
    p.add_argument("--gh", default="gh")
    p.add_argument("--repeats", type=int, default=2)
    p.add_argument("--only-repeat", type=int)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    case_map = json.load(open(Path(args.ground_truth) / "case-map.json", encoding="utf-8"))
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    jobs = []
    for rep in range(1, args.repeats + 1):
        block = [{"run_id": f"r{rep}-{case}-{mk}-{arm}", "repeat": rep, "case": case, "project": c["project"],
                  "source_url": c["source_url"], "model_key": mk, "arm": arm}
                 for case, c in sorted(case_map.items()) for mk in MODELS for arm in ("plugin", "baseline")]
        random.Random(f"{SEED}:{rep}").shuffle(block)
        jobs += block
    if args.only_repeat:
        jobs = [j for j in jobs if j["repeat"] == args.only_repeat]

    # Spend already recorded by earlier invocations counts toward the cap.
    for sp in out_root.glob("*/status.json"):
        s = json.load(open(sp, encoding="utf-8"))
        _spent += (s.get("cost_usd") or 0.0) + (s.get("judge_cost_usd_estimate") or 0.0)
    todo = [j for j in jobs if not (out_root / j["run_id"] / "status.json").exists()]
    print(f"jobs: {len(jobs)} total, {len(todo)} to run; already spent in this campaign: ${_spent:.2f}; cap ${args.max_spend:.2f}", flush=True)
    if args.dry_run:
        for j in todo[:8]:
            print("  ", j["run_id"])
        return

    # Local checkouts, without line-ending conversion.
    cred = f"!'{args.gh}' auth git-credential".replace("\\", "/")
    for case in sorted(case_map):
        d = Path(args.cases) / case
        if not (d / ".git").exists():
            r = sh(["git", "-c", "core.autocrlf=false", "-c", "core.longpaths=true", "-c", "credential.helper=",
                    "-c", f"credential.helper={cred}", "clone", "-q", "--branch", "change",
                    "-c", "core.autocrlf=false", "-c", "core.longpaths=true",
                    f"https://github.com/{args.org}/{case}.git", str(d)], timeout=1800)
            if r.returncode:
                raise SystemExit(f"clone of {case} failed: {r.stderr[-300:]}")
            print("cloned", case, flush=True)

    json.dump({"seed": SEED, "models": MODELS, "effort": EFFORT, "plugin_prompt": PLUGIN_PROMPT,
               "baseline_prompt": BASELINE_PROMPT, "baseline_prompt_version": BASELINE_PROMPT_VERSION,
               "read_only_rules": READ_ONLY, "budgets": {f"{k[0]}/{k[1]}": v for k, v in BUDGET.items()},
               "order": [j["run_id"] for j in jobs]}, open(out_root / "campaign.json", "w", encoding="utf-8"), indent=1)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(lambda j: do_run(j, args), todo))
    done = [r for r in results if r]
    counts = {}
    for r in done:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(f"finished this invocation: {len(done)} runs {counts}; not started: {len(results) - len(done)}; "
          f"campaign spend estimate ${_spent:.2f}", flush=True)


if __name__ == "__main__":
    main()
