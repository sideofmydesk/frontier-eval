"""Aggregate a finished pilot into summary numbers with uncertainty intervals.

No API calls. Reads each run's status.json, judgement.json, and requests.jsonl.

Scores are pooled within a cell: recall = golden comments found / golden
comments, summed over that cell's completed runs. Intervals are 95% percentile
intervals from a cluster bootstrap that resamples the 15 cases (10,000
resamples, fixed seed), because runs on the same case are not independent.

Usage: python aggregate.py --pilot <pilot out dir> --out <dir for summary files>
"""

import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

SEED = 20261116
B = 10000
CELLS = [("opus55", "plugin"), ("opus55", "baseline"), ("fable52", "plugin"), ("fable52", "baseline")]
PROFILES = ("strict", "core", "all")
PRICE_TIER = {"claude-fable-5-2": "Fable 5.2", "claude-opus-5-5": "Opus 5.5", "claude-sonnet-5-5": "Sonnet 5.5", "claude-haiku-5-5": "Haiku 5.5"}


def pct(xs, q):
    xs = sorted(xs)
    i = q * (len(xs) - 1)
    lo, hi = int(i), min(int(i) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def ratio(n, d):
    return n / d if d else None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pilot", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    pilot, out = Path(args.pilot), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    runs = []
    for sp in sorted(pilot.glob("*/status.json")):
        s = json.load(open(sp, encoding="utf-8"))
        d = sp.parent
        s["_judgement"] = json.load(open(d / "judgement.json", encoding="utf-8")) if (d / "judgement.json").exists() else None
        s["_requests"] = [json.loads(l) for l in open(d / "requests.jsonl", encoding="utf-8")] if (d / "requests.jsonl").exists() else []
        runs.append(s)
    cases = sorted({r["case"] for r in runs})
    done = [r for r in runs if r["status"] == "completed" and r.get("judged")]

    # ---- run accounting
    accounting = {f"{m}/{a}": dict(Counter(r["status"] for r in runs if (r["model_key"], r["arm"]) == (m, a))) for m, a in CELLS}

    # ---- per (cell, case) counts for the bootstrap
    cnt = defaultdict(lambda: defaultdict(lambda: Counter()))  # cnt[cell][case] -> counters
    for r in done:
        c = cnt[(r["model_key"], r["arm"])][r["case"]]
        for prof in PROFILES:
            sc = r["scores"][prof]
            c[f"golden_{prof}"] += sc["golden"]
            c[f"tp_{prof}"] += sc["tp"]
        c["fp"] += r["scores"]["all"]["fp"]
        c["cand"] += r["n_candidates"]
        c["runs"] += 1
        c["cost"] += r["cost_usd"]

    def stats(case_list):
        o = {}
        for cell in CELLS:
            t = Counter()
            for case in case_list:
                t.update(cnt[cell].get(case, {}))
            key = "/".join(cell)
            for prof in PROFILES:
                o[f"{key}:recall_{prof}"] = ratio(t[f"tp_{prof}"], t[f"golden_{prof}"])
                o[f"{key}:precision_{prof}"] = ratio(t[f"tp_{prof}"], t[f"tp_{prof}"] + t["fp"])
            o[f"{key}:findings_per_run"] = ratio(t["cand"], t["runs"])
            o[f"{key}:unmatched_per_run"] = ratio(t["fp"], t["runs"])
            o[f"{key}:cost_per_run"] = ratio(t["cost"], t["runs"])
        for m in ("opus55", "fable52"):
            for metric in [f"recall_{p}" for p in PROFILES] + [f"precision_{p}" for p in PROFILES] + ["findings_per_run", "unmatched_per_run", "cost_per_run"]:
                a, b = o[f"{m}/plugin:{metric}"], o[f"{m}/baseline:{metric}"]
                o[f"{m}:plugin_minus_baseline:{metric}"] = None if a is None or b is None else a - b
        for metric in [f"recall_{p}" for p in PROFILES] + [f"precision_{p}" for p in PROFILES]:
            a, b = o[f"fable52:plugin_minus_baseline:{metric}"], o[f"opus55:plugin_minus_baseline:{metric}"]
            o[f"fable_minus_opus:plugin_advantage:{metric}"] = None if a is None or b is None else a - b
        return o

    point = stats(cases)
    rng = random.Random(SEED)
    boot = defaultdict(list)
    for _ in range(B):
        sample = [rng.choice(cases) for _ in cases]
        for k, v in stats(sample).items():
            if v is not None:
                boot[k].append(v)
    estimates = {k: {"value": v, "lo": pct(boot[k], 0.025) if boot[k] else None, "hi": pct(boot[k], 0.975) if boot[k] else None,
                     "share_above_zero": (sum(1 for x in boot[k] if x > 0) / len(boot[k])) if boot[k] and "minus" in k else None}
                 for k, v in point.items()}

    # ---- totals per cell
    totals = {}
    for cell in CELLS:
        t = Counter()
        for case in cases:
            t.update(cnt[cell].get(case, {}))
        totals["/".join(cell)] = dict(t)

    # ---- per case table (all profile)
    per_case = []
    cm = {r["case"]: r["project"] for r in runs}
    for case in cases:
        row = {"case": case, "project": cm[case]}
        for cell in CELLS:
            c = cnt[cell].get(case, Counter())
            row["/".join(cell)] = {"runs": c["runs"], "golden_per_run": ratio(c["golden_all"], c["runs"]), "found": c["tp_all"],
                                   "golden": c["golden_all"], "unmatched": c["fp"], "findings": c["cand"]}
        per_case.append(row)

    # ---- consistency between the two repeats: per golden comment, found in 0, 1 or 2 runs
    consistency = {}
    for cell in CELLS:
        by = defaultdict(lambda: defaultdict(dict))  # case -> golden -> repeat -> found
        for r in done:
            if (r["model_key"], r["arm"]) != cell:
                continue
            for g in r["_judgement"]["golden"]:
                by[r["case"]][g["comment"]][r["repeat"]] = g["found"]
        c = Counter()
        for case in by:
            for g, reps in by[case].items():
                if len(reps) == 2:
                    c[sum(1 for v in reps.values() if v)] += 1
        n = sum(c.values())
        consistency["/".join(cell)] = {"golden_with_two_runs": n, "found_in_both": c[2], "found_in_one": c[1], "found_in_neither": c[0],
                                       "agreement": ratio(c[2] + c[0], n),
                                       "found_both_given_found_any": ratio(c[2], c[2] + c[1])}

    # ---- recall by severity (all profile)
    severity = {}
    for cell in CELLS:
        c = defaultdict(Counter)
        for r in done:
            if (r["model_key"], r["arm"]) != cell:
                continue
            for g in r["_judgement"]["golden"]:
                c[g["severity"]]["n"] += 1
                c[g["severity"]]["found"] += bool(g["found"])
        severity["/".join(cell)] = {s: {"golden": v["n"], "found": v["found"], "recall": ratio(v["found"], v["n"])} for s, v in c.items()}

    # ---- cost and requests by model tier, per cell (completed runs)
    tiers = {}
    for cell in CELLS:
        c = defaultdict(Counter)
        n = 0
        for r in runs:
            # Completed runs only, so these totals match the per-cell cost figures.
            if (r["model_key"], r["arm"]) != cell or not r["_requests"] or r["status"] != "completed":
                continue
            n += 1
            for q in r["_requests"]:
                t = PRICE_TIER.get(q.get("returned_model"), str(q.get("returned_model")))
                c[t]["requests"] += 1
                c[t]["cost"] += q.get("cost_usd_estimate") or 0
                c[t]["output_tokens"] += q.get("output_tokens") or 0
        tiers["/".join(cell)] = {t: {"requests_per_run": v["requests"] / n, "cost_per_run": v["cost"] / n,
                                    "output_tokens_per_run": v["output_tokens"] / n} for t, v in c.items()}

    # ---- did the session follow the plugin's instruction to delegate?
    delegation = {}
    for m in ("opus55", "fable52"):
        pr = [r for r in runs if r["model_key"] == m and r["arm"] == "plugin" and r["_requests"]]
        pat = Counter()
        for r in pr:
            sub = sorted({PRICE_TIER.get(x, x) for x in r.get("subagent_models", [])})
            pat[" + ".join(sub) if sub else "no subagents"] += 1
        none = [r for r in pr if not r.get("subagent_models")]
        some = [r for r in pr if r.get("subagent_models")]

        def pooled(rs):
            rs = [r for r in rs if r["status"] == "completed" and r.get("judged")]
            g = sum(r["scores"]["all"]["golden"] for r in rs)
            tp = sum(r["scores"]["all"]["tp"] for r in rs)
            fp = sum(r["scores"]["all"]["fp"] for r in rs)
            return {"runs": len(rs), "recall": ratio(tp, g), "precision": ratio(tp, tp + fp),
                    "cost_per_run": ratio(sum(r["cost_usd"] for r in rs), len(rs))}
        delegation[m] = {"plugin_runs": len(pr), "patterns": dict(pat), "runs_with_no_subagents": len(none),
                         "no_subagents": pooled(none), "with_subagents": pooled(some)}

    safety = {"refused_runs": [r["run_id"] for r in runs if r["status"] == "refused"],
              "fallback_runs": [r["run_id"] for r in runs if r["status"] == "fallback"],
              "runs_with_leak_markers": [r["run_id"] for r in runs if r.get("leak_markers")],
              "runs_that_posted_to_pr": [r["run_id"] for r in runs if r.get("pr_comments_after")],
              "runs_with_dirty_checkout": [r["run_id"] for r in runs if r.get("checkout_dirty")],
              "judge_errors": sum(r.get("judge_errors") or 0 for r in runs),
              "permission_denials_per_run": {"/".join(c): ratio(sum(r.get("permission_denials") or 0 for r in runs if (r["model_key"], r["arm"]) == c),
                                                                sum(1 for r in runs if (r["model_key"], r["arm"]) == c)) for c in CELLS}}
    spend = {"review_cost_estimate": sum(r.get("cost_usd") or 0 for r in runs),
             "judge_cost_estimate": sum(r.get("judge_cost_usd_estimate") or 0 for r in runs)}

    summary = {"runs_total": len(runs), "runs_scored": len(done), "cases": len(cases), "bootstrap": {"resamples": B, "seed": SEED, "unit": "case"},
               "accounting": accounting, "totals": totals, "estimates": estimates, "per_case": per_case, "consistency": consistency,
               "severity": severity, "tiers": tiers, "delegation": delegation, "safety": safety, "spend": spend}
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")

    with open(out / "runs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["run_id", "repeat", "case", "project", "model", "arm", "status", "requests", "elapsed_s", "cost_usd_estimate",
                    "subagent_models", "findings", "golden_all", "found_all", "unmatched", "golden_strict", "found_strict", "permission_denials"])
        for r in runs:
            sc = r.get("scores") or {}
            a, st = sc.get("all") or {}, sc.get("strict") or {}
            w.writerow([r["run_id"], r["repeat"], r["case"], r["project"], r["model"], r["arm"], r["status"], r.get("requests"),
                        r.get("elapsed_s"), round(r.get("cost_usd") or 0, 4), "+".join(x.replace("claude-", "") for x in r.get("subagent_models", [])),
                        r.get("n_candidates"), a.get("golden"), a.get("tp"), a.get("fp"), st.get("golden"), st.get("tp"), r.get("permission_denials")])

    def show(k, pc=True):
        e = estimates[k]
        f = (lambda x: f"{100 * x:5.1f}%") if pc else (lambda x: f"{x:6.2f}")
        tail = f"  P(>0)={e['share_above_zero']:.2f}" if e["share_above_zero"] is not None else ""
        return f"{f(e['value'])} [{f(e['lo'])}, {f(e['hi'])}]{tail}"

    print(f"runs {len(runs)}, scored {len(done)}, cases {len(cases)}; accounting {accounting}")
    for prof in PROFILES:
        print(f"\n== profile: {prof}")
        for cell in CELLS:
            k = "/".join(cell)
            print(f"  {k:17s} recall {show(k + ':recall_' + prof)}   precision {show(k + ':precision_' + prof)}")
        for m in ("opus55", "fable52"):
            print(f"  {m} plugin - baseline: recall {show(m + ':plugin_minus_baseline:recall_' + prof)}   precision {show(m + ':plugin_minus_baseline:precision_' + prof)}")
        print(f"  Fable advantage - Opus advantage: recall {show('fable_minus_opus:plugin_advantage:recall_' + prof)}   precision {show('fable_minus_opus:plugin_advantage:precision_' + prof)}")
    print("\nfindings per run / unmatched per run / cost per run")
    for cell in CELLS:
        k = "/".join(cell)
        print(f"  {k:17s} {show(k + ':findings_per_run', False)}  {show(k + ':unmatched_per_run', False)}  ${show(k + ':cost_per_run', False)}")
    print("\nconsistency:", json.dumps(consistency, indent=0)[:900])
    print("\ndelegation:", json.dumps(delegation, indent=0)[:1400])
    print("\nseverity:", json.dumps(severity)[:900])
    print("\ntiers:", json.dumps({k: {t: round(v["cost_per_run"], 3) for t, v in d.items()} for k, d in tiers.items()}))
    print("\nsafety:", json.dumps(safety)[:700])
    print("spend:", spend)


if __name__ == "__main__":
    main()
