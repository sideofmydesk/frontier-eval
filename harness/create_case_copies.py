"""Create private pull request copies of benchmark cases.

For each selected case this makes a private repository holding two commits
(the tree at the pull request's merge base, then the tree at its head) and
opens a pull request between them. See docs/13-corpus-options.md, section 5.1a.

It creates repositories on GitHub. It does not call any model API.

Usage:
  python create_case_copies.py --ground-truth <dir> --org <github org>
      --work <local scratch dir> --per-project 3 [--gh <path to gh>]

<ground-truth dir> must hold selection-order.json; case-map.json is read and
updated there. Neither file belongs in this repository.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

FIXED_ENV = {
    "GIT_AUTHOR_NAME": "frontier-eval", "GIT_AUTHOR_EMAIL": "noreply@example.invalid",
    "GIT_COMMITTER_NAME": "frontier-eval", "GIT_COMMITTER_EMAIL": "noreply@example.invalid",
    "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
    "GIT_TERMINAL_PROMPT": "0",
}


def run(cmd, cwd=None, env=None, check=True, text=True):
    e = dict(os.environ)
    e.update(env or {})
    r = subprocess.run(cmd, cwd=cwd, env=e, capture_output=True, text=text, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(map(str, cmd[:6]))}...\n{r.stderr.strip()[-600:]}")
    return r.stdout.strip()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ground-truth", required=True)
    p.add_argument("--org", required=True)
    p.add_argument("--work", required=True)
    p.add_argument("--per-project", type=int, default=3)
    p.add_argument("--gh", default="gh")
    args = p.parse_args()

    gt = Path(args.ground_truth)
    order = json.load(open(gt / "selection-order.json", encoding="utf-8"))["order"]
    map_path = gt / "case-map.json"
    case_map = json.load(open(map_path, encoding="utf-8")) if map_path.exists() else {}
    by_source = {v["source_url"]: k for k, v in case_map.items()}
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    gh = args.gh
    cred = f"!'{gh}' auth git-credential".replace("\\", "/")

    selected = []
    for project in sorted(order):
        for entry in order[project][: args.per_project]:
            selected.append((project, entry))

    n = 0
    for project, entry in selected:
        n += 1
        name = f"fe-case-{n:03d}"
        url = entry["url"]
        if url in by_source:
            print(f"{by_source[url]}: exists, skipping ({project} rank {entry['rank']})", flush=True)
            continue
        if name in case_map:
            raise SystemExit(f"{name} is already mapped to a different source; refusing to continue")
        owner, repo, number = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url).groups()
        pr = json.loads(run([gh, "api", f"repos/{owner}/{repo}/pulls/{number}"]))
        base_sha, head_sha = pr["base"]["sha"], pr["head"]["sha"]
        mb = run([gh, "api", f"repos/{owner}/{repo}/compare/{base_sha}...{head_sha}", "--jq", ".merge_base_commit.sha"])

        local = work / f"{owner}__{repo}"
        if not (local / ".git").exists():
            run(["git", "init", "-q", str(local)])
            run(["git", "remote", "add", "up", f"https://github.com/{owner}/{repo}.git"], cwd=local)
        for sha in (mb, head_sha):
            run(["git", "-c", "credential.helper=", "fetch", "-q", "--depth", "1", "up", sha], cwd=local, env=FIXED_ENV)
        a = run(["git", "commit-tree", f"{mb}^{{tree}}", "-m", "Base state"], cwd=local, env=FIXED_ENV)
        b = run(["git", "commit-tree", f"{head_sha}^{{tree}}", "-p", a, "-m", "Change under review"], cwd=local, env=FIXED_ENV)

        full = f"{args.org}/{name}"
        run([gh, "repo", "create", full, "--private", "--disable-issues", "--disable-wiki"])
        run([gh, "api", "-X", "PUT", f"repos/{full}/actions/permissions", "-F", "enabled=false"], check=False)
        run(["git", "-c", "credential.helper=", "-c", f"credential.helper={cred}", "push", "-q",
             f"https://github.com/{full}.git", f"{a}:refs/heads/main", f"{b}:refs/heads/change"], cwd=local, env=FIXED_ENV)

        body = re.sub(r"@(?=[A-Za-z0-9])", "@​", pr["body"] or "")  # nobody gets notified from a copy
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8", newline="\n") as f:
            f.write(body)
            body_file = f.name
        try:
            pr_url = run([gh, "pr", "create", "--repo", full, "--base", "main", "--head", "change",
                          "--title", pr["title"], "--body-file", body_file]).splitlines()[-1]
        finally:
            os.unlink(body_file)

        got = json.loads(run([gh, "pr", "view", "1", "--repo", full, "--json", "changedFiles,additions,deletions,state,isDraft"]))
        private = run([gh, "api", f"repos/{full}", "--jq", ".private"])
        ok = (got["changedFiles"] == pr["changed_files"] and got["additions"] == pr["additions"]
              and got["deletions"] == pr["deletions"] and got["state"] == "OPEN" and private == "true")
        case_map[name] = {
            "copy": pr_url, "source_url": url, "original_url": entry.get("original_url"), "project": project,
            "rank": entry["rank"], "n_golden": entry["n_golden"], "merge_base_sha": mb, "head_sha": head_sha,
            "copy_base_commit": a, "copy_head_commit": b,
            "files": got["changedFiles"], "additions": got["additions"], "deletions": got["deletions"],
            "matches_source": ok, "method": "two-commit copy: merge-base tree then head tree; no upstream history",
        }
        json.dump(case_map, open(map_path, "w", encoding="utf-8"), indent=1)
        print(f"{name}: {project} rank {entry['rank']} files={got['changedFiles']} +{got['additions']} -{got['deletions']} "
              f"source=({pr['changed_files']},+{pr['additions']},-{pr['deletions']}) private={private} "
              f"{'OK' if ok else 'MISMATCH'}", flush=True)

    bad = [k for k, v in case_map.items() if v.get("matches_source") is False]
    print(f"done: {len(case_map)} cases mapped; mismatches: {bad or 'none'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
