"""Grade one review run against the benchmark's golden comments.

THIS MAKES PAID API CALLS (to the judge model, Claude Sonnet 5.5 by default).

Method follows withmartian/code-review-benchmark at commit e616e84:
  1. Extract individual issues from the review text  (their EXTRACT_PROMPT, verbatim)
  2. Judge every (golden comment, candidate) pair     (their JUDGE_PROMPT, verbatim)
  3. A golden comment is found if any candidate matches it; a candidate that
     matches no golden comment is unmatched.

Differences from the benchmark, on purpose:
  - No dedup step. Our reviews are one message, not summary plus inline comments.
  - No temperature setting. Current Claude models reject it.
  - JSON is enforced with structured outputs instead of parsed from free text.
  - Raw HTTP is used because the Anthropic SDK's compiled dependency is blocked
    by this machine's application control policy.
  - No refusal fallback is requested: a refused judge call is recorded as an error.

The judge sees only the review text and the golden comment. It is not told the
model or the arm.

Usage:
  python judge.py --run <run dir> --golden <golden json> --source-url <pr url>
      --env-file <.env> [--model claude-sonnet-5-5] [--out <file>]
"""

import argparse
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2026-10-21"
JUDGE_VERSION = "1"

# --- Prompts copied verbatim from withmartian/code-review-benchmark @ e616e84 (MIT) ---
EXTRACT_PROMPT = """You are analyzing an AI code review comment to extract individual issues mentioned.

The comment may discuss multiple distinct problems. Extract each separate issue as a standalone item.

Code Review Comment:
{comment}

Instructions:
- Extract each distinct code issue, bug, or concern mentioned
- Each issue should be a single, specific problem (not a general observation)
- Ignore meta-commentary like "I found 2 issues" - extract the actual issues
- Ignore sign-offs, greetings, or formatting instructions
- If the comment contains no actionable code review issues, return an empty list

Example input:
"Found several problems: 1) The getUserById function doesn't handle null input, which will cause a crash.
2) The cache key uses user.name but should use user.id for uniqueness.
Also, consider adding retry logic for the API call."

Example output:
{{"issues": [
  "getUserById function doesn't handle null input, causing potential crash",
  "Cache key uses user.name instead of user.id, breaking uniqueness",
  "Missing retry logic for API call"
]}}

Respond with ONLY a JSON object:
{{"issues": ["issue 1", "issue 2", ...]}}"""

JUDGE_PROMPT = """You are evaluating AI code review tools.
Determine if the candidate issue matches the golden (expected) comment.

Golden Comment (the issue we're looking for):
{golden_comment}

Candidate Issue (from the tool's review):
{candidate}

Instructions:
- Determine if the candidate identifies the SAME underlying issue as the golden comment
- Accept semantic matches - different wording is fine if it's the same problem
- Focus on whether they point to the same bug, concern, or code issue

Respond with ONLY a JSON object:
{{"reasoning": "brief explanation", "match": true/false, "confidence": 0.0-1.0}}"""
# --- end of copied prompts ---

EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {"issues": {"type": "array", "items": {"type": "string"}}},
    "required": ["issues"],
    "additionalProperties": False,
}
JUDGE_SCHEMA = {
    "type": "object",
    "properties": {"reasoning": {"type": "string"}, "match": {"type": "boolean"}, "confidence": {"type": "number"}},
    "required": ["reasoning", "match", "confidence"],
    "additionalProperties": False,
}
STRICT = {"bug", "security", "concurrency", "data", "api"}
CORE = STRICT | {"perf", "test_gap", "doc_defect"}


def read_key(env_file):
    for line in Path(env_file).read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("ANTHROPIC_API_KEY="):
            return line.strip().split("=", 1)[1].strip()
    raise SystemExit("ANTHROPIC_API_KEY not found in env file")


class Judge:
    def __init__(self, key, model, effort="low"):
        self._key, self.model, self.effort = key, model, effort
        self.calls = []

    def call(self, prompt, schema, max_tokens):
        body = {
            "model": self.model, "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "output_config": {"effort": self.effort, "format": {"type": "json_schema", "schema": schema}},
        }
        data = json.dumps(body).encode("utf-8")
        last = None
        for attempt in range(5):
            req = urllib.request.Request(API_URL, data=data, method="POST", headers={
                "content-type": "application/json", "x-api-key": self._key, "anthropic-version": API_VERSION})
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    resp = json.loads(r.read())
                    rid = r.headers.get("request-id")
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", "replace")[:400]
                last = f"HTTP {e.code}: {detail}"
                if e.code in (429, 500, 502, 503, 529):
                    time.sleep(min(60, 2 ** attempt * 2))
                    continue
                raise RuntimeError(last)
            except (urllib.error.URLError, TimeoutError) as e:
                last = f"network: {e}"
                time.sleep(2 ** attempt)
                continue
            u = resp.get("usage") or {}
            rec = {"request_id": rid, "requested_model": self.model, "returned_model": resp.get("model"),
                   "stop_reason": resp.get("stop_reason"), "input_tokens": u.get("input_tokens", 0),
                   "output_tokens": u.get("output_tokens", 0),
                   "fallback_flag": resp.get("model") != self.model
                   or any(b.get("type") == "fallback" for b in resp.get("content", []))}
            self.calls.append(rec)
            if rec["fallback_flag"]:
                raise RuntimeError(f"judge answered by {resp.get('model')}, not {self.model}")
            if resp.get("stop_reason") == "refusal":
                raise RuntimeError("judge refused")
            if resp.get("stop_reason") == "max_tokens":
                raise RuntimeError("judge output truncated")
            text = next((b["text"] for b in resp.get("content", []) if b.get("type") == "text"), None)
            if text is None:
                raise RuntimeError("judge returned no text block")
            return json.loads(text)
        raise RuntimeError(f"judge call failed after retries: {last}")


def review_text(run):
    result = None
    for line in open(run / "stream.jsonl", encoding="utf-8", errors="replace"):
        line = line.strip()
        if line.startswith("{"):
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if o.get("type") == "result":
                result = o
    if result is None:
        raise SystemExit("no result in stream.jsonl")
    return result.get("result") or "", result


def score(found, n_candidates_unmatched, golden, profile):
    cats = {"strict": STRICT, "core": CORE, "all": None}[profile]
    inc = [g for g in golden if cats is None or g["category"] in cats]
    tp = sum(1 for g in inc if found[g["comment"]])
    fn = len(inc) - tp
    fp = n_candidates_unmatched
    return {"golden": len(inc), "tp": tp, "fn": fn, "fp": fp,
            "recall": tp / len(inc) if inc else None,
            "precision": tp / (tp + fp) if (tp + fp) else None}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True)
    p.add_argument("--golden", required=True)
    p.add_argument("--source-url", required=True)
    p.add_argument("--env-file", required=True)
    p.add_argument("--model", default="claude-sonnet-5-5")
    p.add_argument("--out")
    p.add_argument("--workers", type=int, default=8)
    args = p.parse_args()

    run = Path(args.run)
    golden = next(it["comments"] for it in json.load(open(args.golden, encoding="utf-8")) if it["url"] == args.source_url)
    text, result = review_text(run)
    judge = Judge(read_key(args.env_file), args.model)

    candidates = judge.call(EXTRACT_PROMPT.format(comment=text), EXTRACT_SCHEMA, 8000)["issues"] if text.strip() else []
    pairs = [(g, c) for g in golden for c in candidates]
    errors = []

    def one(pair):
        g, c = pair
        try:
            return judge.call(JUDGE_PROMPT.format(golden_comment=g["comment"], candidate=c), JUDGE_SCHEMA, 2000)
        except Exception as e:  # recorded, never silently dropped
            errors.append({"golden": g["comment"], "candidate": c, "error": str(e)})
            return None

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        verdicts = list(ex.map(one, pairs))

    found = {g["comment"]: False for g in golden}
    best = {g["comment"]: None for g in golden}
    matched_cand = {c: [] for c in candidates}
    for (g, c), v in zip(pairs, verdicts):
        if v and v["match"]:
            found[g["comment"]] = True
            if best[g["comment"]] is None or v["confidence"] > best[g["comment"]]["confidence"]:
                best[g["comment"]] = {"candidate": c, "confidence": v["confidence"], "reasoning": v["reasoning"]}
            matched_cand[c].append(g["category"])
    unmatched = [c for c in candidates if not matched_cand[c]]

    out = {
        "judge_version": JUDGE_VERSION, "judge_model": args.model, "judge_effort": judge.effort,
        "run": run.name, "source_url": args.source_url,
        "review_is_error": bool(result.get("is_error")), "review_chars": len(text),
        "candidates": candidates, "n_candidates": len(candidates),
        "golden": [{"comment": g["comment"], "severity": g["severity"], "category": g["category"],
                    "found": found[g["comment"]], "match": best[g["comment"]]} for g in golden],
        "unmatched_candidates": unmatched,
        "scores": {prof: score(found, len(unmatched), golden, prof) for prof in ("strict", "core", "all")},
        "errors": errors,
        "judge_calls": len(judge.calls),
        "judge_input_tokens": sum(c["input_tokens"] for c in judge.calls),
        "judge_output_tokens": sum(c["output_tokens"] for c in judge.calls),
        "judge_fallbacks": sum(c["fallback_flag"] for c in judge.calls),
    }
    out_path = Path(args.out) if args.out else run / "judgement.json"
    out_path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    s = out["scores"]["all"]
    print(json.dumps({"run": run.name, "candidates": len(candidates), "golden": s["golden"], "found": s["tp"],
                      "unmatched": s["fp"], "recall": s["recall"], "precision": s["precision"],
                      "errors": len(errors), "judge_calls": out["judge_calls"],
                      "judge_tokens_in": out["judge_input_tokens"], "judge_tokens_out": out["judge_output_tokens"]}))


if __name__ == "__main__":
    main()
