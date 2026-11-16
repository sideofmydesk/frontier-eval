"""Group checker-confirmed findings into distinct new issues, and label them.

THIS MAKES PAID API CALLS (Claude Sonnet 5.5, one call per case).

Input: <pilot>/checker/verdicts.jsonl (every unmatched finding with a verdict).
For each case, the findings judged "real" are grouped into distinct issues
(the same bug reported by several runs becomes one issue) and each issue gets
a category from the benchmark's list and a severity.

These are issues the benchmark's golden comments do not list. "Real" is the
checker model's verdict from the diff alone; it has not been confirmed by hand.

Usage: python new_issues.py --pilot <dir> --env-file <.env> --out <summary dir>
"""

import argparse
import json
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2026-10-21"
MODEL = "claude-sonnet-5-5"
CATEGORIES = ["bug", "security", "concurrency", "data", "api", "perf", "test_gap", "doc_defect", "style", "speculative"]

PROMPT = """Below is a numbered list of code review findings about one pull request. Each was produced by a different review run, so the same underlying problem often appears several times in different words.

Group the findings into distinct issues. Two findings belong to the same issue only if a single code change would fix both. Findings about the same kind of problem in different places are separate issues. When in doubt, keep them separate.

For each distinct issue give:
- title: one plain sentence naming the problem and where it is
- category: one of bug, security, concurrency, data, api, perf, test_gap, doc_defect, style, speculative
- severity: Critical, High, Medium, or Low
- members: the numbers of the findings that describe it

Every finding number must appear in exactly one issue.

Findings:
{findings}"""

SCHEMA = {
    "type": "object",
    "properties": {"issues": {"type": "array", "items": {
        "type": "object",
        "properties": {"title": {"type": "string"}, "category": {"type": "string", "enum": CATEGORIES},
                       "severity": {"type": "string", "enum": ["Critical", "High", "Medium", "Low"]},
                       "members": {"type": "array", "items": {"type": "integer"}}},
        "required": ["title", "category", "severity", "members"], "additionalProperties": False}}},
    "required": ["issues"], "additionalProperties": False,
}


def read_key(env_file):
    for line in Path(env_file).read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("ANTHROPIC_API_KEY="):
            return line.strip().split("=", 1)[1].strip()
    raise SystemExit("ANTHROPIC_API_KEY not found in env file")


def call(key, prompt):
    body = {"model": MODEL, "max_tokens": 16000, "messages": [{"role": "user", "content": prompt}],
            "output_config": {"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}}}
    data = json.dumps(body).encode("utf-8")
    last = None
    for attempt in range(5):
        req = urllib.request.Request(API_URL, data=data, method="POST", headers={
            "content-type": "application/json", "x-api-key": key, "anthropic-version": API_VERSION})
        try:
            with urllib.request.urlopen(req, timeout=900) as r:
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
        if resp.get("model") != MODEL or resp.get("stop_reason") in ("refusal", "max_tokens"):
            raise RuntimeError(f"unexpected response: model={resp.get('model')} stop={resp.get('stop_reason')}")
        return json.loads(next(b["text"] for b in resp["content"] if b.get("type") == "text"))
    raise RuntimeError(f"call failed: {last}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pilot", required=True)
    p.add_argument("--env-file", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    pilot = Path(args.pilot)
    V = [json.loads(l) for l in open(pilot / "checker" / "verdicts.jsonl", encoding="utf-8")]
    real = defaultdict(list)
    for v in V:
        if v.get("verdict") == "real":
            real[v["case"]].append(v)
    key = read_key(args.env_file)
    cache = pilot / "checker" / "new-issues.json"
    grouped = json.load(open(cache, encoding="utf-8")) if cache.exists() else {}
    for case in sorted(real):
        if case in grouped:
            continue
        items = sorted(real[case], key=lambda v: v["id"])
        listing = "\n".join(f"{i}. {v['finding']}" for i, v in enumerate(items))
        res = call(key, PROMPT.format(findings=listing))
        seen = Counter(m for g in res["issues"] for m in g["members"])
        bad = [m for m in seen if m < 0 or m >= len(items) or seen[m] > 1]
        missing = [i for i in range(len(items)) if i not in seen]
        issues = [g for g in res["issues"] if g["members"]]
        for i in missing:  # anything the grouping dropped stays as its own issue
            issues.append({"title": items[i]["finding"][:200], "category": "bug", "severity": "Medium", "members": [i], "ungrouped": True})
        grouped[case] = {"n_findings": len(items), "grouping_problems": {"duplicated_or_out_of_range": bad, "missing": missing},
                         "issues": [{**g, "found_by": sorted({f"{items[m]['model_key']}/{items[m]['arm']}" for m in g["members"] if 0 <= m < len(items)}),
                                     "runs": sorted({items[m]["run_id"] for m in g["members"] if 0 <= m < len(items)})} for g in issues]}
        json.dump(grouped, open(cache, "w", encoding="utf-8"), indent=1)
        print(case, "real findings", len(items), "-> distinct issues", len(issues), "| problems", len(bad), len(missing), flush=True)

    # ---- summary
    cells = ["opus55/plugin", "opus55/baseline", "fable52/plugin", "fable52/baseline"]
    verdicts = {c: Counter() for c in cells}
    for v in V:
        verdicts[f"{v['model_key']}/{v['arm']}"][v.get("verdict") or "error"] += 1
    all_issues = [(case, g) for case in sorted(grouped) for g in grouped[case]["issues"]]
    by_cell = {c: sum(1 for _, g in all_issues if c in g["found_by"]) for c in cells}
    by_arm = {a: sum(1 for _, g in all_issues if any(x.endswith("/" + a) for x in g["found_by"])) for a in ("plugin", "baseline")}
    only = {"plugin_only": sum(1 for _, g in all_issues if all(x.endswith("/plugin") for x in g["found_by"])),
            "baseline_only": sum(1 for _, g in all_issues if all(x.endswith("/baseline") for x in g["found_by"])),
            "both": sum(1 for _, g in all_issues if {x.split("/")[1] for x in g["found_by"]} == {"plugin", "baseline"})}
    summary = {
        "note": "Issues not in the benchmark's golden comments. 'Real' is a checker model's verdict from the diff alone; not confirmed by hand.",
        "verdicts_by_cell": {c: dict(verdicts[c]) for c in cells},
        "verdict_totals": dict(sum((verdicts[c] for c in cells), Counter())),
        "distinct_new_issues": len(all_issues),
        "per_case": {case: len(grouped[case]["issues"]) for case in sorted(grouped)},
        "by_category": dict(Counter(g["category"] for _, g in all_issues).most_common()),
        "by_severity": dict(Counter(g["severity"] for _, g in all_issues)),
        "distinct_found_by_cell": by_cell, "distinct_found_by_arm": by_arm, "overlap": only,
        "found_in_runs_distribution": dict(sorted(Counter(len(g["runs"]) for _, g in all_issues).items())),
        "by_arm_and_category": {a: dict(Counter(g["category"] for _, g in all_issues if any(x.endswith("/" + a) for x in g["found_by"])).most_common())
                                for a in ("plugin", "baseline")},
        "by_arm_and_severity": {a: dict(Counter(g["severity"] for _, g in all_issues if any(x.endswith("/" + a) for x in g["found_by"])))
                                for a in ("plugin", "baseline")},
        "grouping_problems": sum(len(grouped[c]["grouping_problems"]["missing"]) + len(grouped[c]["grouping_problems"]["duplicated_or_out_of_range"]) for c in grouped),
    }
    Path(args.out).mkdir(parents=True, exist_ok=True)
    (Path(args.out) / "new-issues-summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
