# 10 Plugin file review

Status: **complete for commits `aecd4c8` and `9780cf4`.** Date of review: 2026-11-15. Covers TR-2, BR-11, Q-10, Q-11, and part of Q-12.

No model or API calls were made. Every file under `plugins/code-review` at both commits was read in full. Nothing from the plugin was installed or executed.

## 1. Summary

1. **`9780cf4` changed no review logic and no documentation.** Its only difference from its parent `c905cd8` is one added line in the manifest: `"version": "1.0.1"`.
2. **All the behaviour change is in `c905cd8`**, which rewrote the command file. `c905cd8` and `9780cf4` carry a byte-identical command file and README. Testing both would test the same plugin twice.
3. **The pair `aecd4c8` and `9780cf4` is still a valid comparison**, because `c905cd8` sits between them. The pilot plan should attribute the change to `c905cd8`, not to the version bump.
4. **The plugin names a model tier for every subagent at both commits (Q-11: yes).** The names are family words in prose ("Haiku agent", "Sonnet agents", "Opus bug agent"), not versioned identifiers. The session model mostly orchestrates. This changes what "the model under test" means. See section 6.
5. **A version field exists only at `9780cf4` (Q-10).** It is absent at `aecd4c8`. The commit SHA stays the only reliable identifier.
6. **The README at `9780cf4` does not describe the command it ships with.** It still documents the 0 to 100 confidence score and the threshold of 80, which the command no longer uses.
7. **The plugin contains no executable code.** It is a manifest, a licence, a README, and one Markdown command file. There are no hooks, scripts, MCP server definitions, or agent definition files.

## 2. Provenance (TR-2, BR-11)

| Item | Value |
|---|---|
| Repository | `https://github.com/anthropics/claude-plugins-official` |
| How obtained | Anonymous HTTPS clone, no credentials, into a scratch directory outside this repository. Deleted after the review. |
| Date cloned | 2026-11-15 |
| Default branch head at clone | `b5b01ac4f889fec0c4c6bb89f27ca7c8574473f6` (2026-11-13) |
| Plugin path | `plugins/code-review` |
| Marketplace entry (`.claude-plugin/marketplace.json`, same at `aecd4c8` and `9780cf4`) | name `code-review`; author `Anthropic`, `support@anthropic.com`; source `./plugins/code-review`; category `productivity` |

Commits reviewed:

| Commit | Author and committer | Author date (UTC) | Parent | Signature |
|---|---|---|---|---|
| `aecd4c852f10b466245f18383fa6aad8c0b10d57` | `Claude <noreply@anthropic.com>` | 2026-02-20T01:06:49Z | `8deab8460a9d4df5a01315ef722a5ca6b061c074` | none found |
| `c905cd8fec340e465dd66990b82b95b6e45db212` | `Claude <noreply@anthropic.com>` | 2026-10-26T22:29:58Z | `58267944f92187b7d6a1c822165c96c81c864806` | none found |
| `9780cf407f5593727b668bae95a0c4ae2e0de1ae` | `Claude <noreply@anthropic.com>` | 2026-10-26T22:42:44Z | `c905cd8fec340e465dd66990b82b95b6e45db212` | none found |

Limits of this provenance check:

- The evidence that the plugin is first-party is that it sits in a repository under the `anthropics` GitHub organisation and that its manifest and marketplace entry name Anthropic as author. Ownership of that organisation was not checked by any means other than the URL.
- Git reported no signature on any of the three commits. Commit author fields are not proof of authorship.
- The marketplace entry's `homepage` points to `anthropics/claude-plugins-public`, a different repository name from the one cloned. This was not investigated.

### File hashes

The file set is the same four paths at all three commits. There is no `agents/`, `hooks/`, `skills/`, `scripts/`, or `.mcp.json`.

| File | Commit | Git blob | SHA-256 of contents |
|---|---|---|---|
| `.claude-plugin/plugin.json` | `aecd4c8`, `c905cd8` | `c48abfeb` | `61af303bf05e05338c82910405292059c932e51567d8cf368c40e77519d1c742` |
| `.claude-plugin/plugin.json` | `9780cf4` | `85fbd7c6` | `0c5d2784bc1ab85b14e578132c141e9e0bb52dbc041f8a9094f8564cd370ffce` |
| `LICENSE` | all three | `d6456956` | `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |
| `README.md` | `aecd4c8` | `b0962f09` | `1fca74bab6969b609519927ae49112760e15d8113eef6bbcf9b9a96c49d73c89` |
| `README.md` | `c905cd8`, `9780cf4` | `42cc8095` | `8ba1b98f4537d70347ec982691a8fc8a1ee4153189877d028375fb644ddc3071` |
| `commands/code-review.md` | `aecd4c8` | `c46e327f` | `7d5a0bc9a41babad32a387152f9680316997bc4ad376928827d670b1760cc890` |
| `commands/code-review.md` | `c905cd8`, `9780cf4` | `8d1533fa` | `3f02ea6eed996590348264777b2e324859a6e2c0c5f7dd298617ea21deb3b1b2` |

Git tree hashes for `plugins/code-review`: `67f860bfae9ae06a0dba9edffcbb6d811a43f83b` at `aecd4c8`, `0579b877e50f5fb3e8974722eed853e5aa904d36` at `c905cd8`, `0a12e55fc6b4966832674e01354591e051b7a78d` at `9780cf4`. The harness can check an installed copy against these.

## 3. Manifest (Q-10)

| Field | `aecd4c8` | `9780cf4` |
|---|---|---|
| `name` | `code-review` | `code-review` |
| `description` | Automated code review for pull requests using multiple specialized agents with confidence-based scoring | same |
| `version` | **absent** | `1.0.1` |
| `author.name` | `Anthropic` | `Anthropic` |
| `author.email` | `support@anthropic.com` | `support@anthropic.com` |

The manifest has no other fields at either commit. It declares no model, agents, hooks, or MCP servers.

Version history across all six commits that touch the path, for the record:

| Commit | `version` | `author` |
|---|---|---|
| `4ca561f` (2025-11-20) | `1.0.0` | Boris Cherny, `boris@anthropic.com` |
| `22d3def` (2025-12-01) | absent | Boris Cherny, `boris@anthropic.com` |
| `19a119f` (2025-12-12) | absent | Anthropic, `support@anthropic.com` |
| `aecd4c8` (2026-02-20) | absent | Anthropic, `support@anthropic.com` |
| `c905cd8` (2026-10-26) | absent | Anthropic, `support@anthropic.com` |
| `9780cf4` (2026-10-26) | `1.0.1` | Anthropic, `support@anthropic.com` |

Answer to Q-10: a version field is usable at the first and last commits only. It was removed in `22d3def` and re-added in `9780cf4`. The pilot plan's "not found" entries mean the field was absent, not that the file was missing. `1.0.1` labels a commit whose behaviour change arrived one commit earlier under no version at all, so the version cannot stand in for the SHA.

The README at both reviewed commits ends with "Author: Boris Cherny (boris@anthropic.com)" and "Version: 1.0.0". Both statements disagree with the manifest at `9780cf4`.

## 4. Commands and agents

There is one command, `/code-review`, defined in `commands/code-review.md`. There are no agent definition files. Every "agent" is a subagent that the command's prose tells the session model to launch.

### 4.1 Command at `aecd4c8`

Front matter: `allowed-tools` lists seven `gh` subcommands (`issue view`, `search`, `issue list`, `pr comment`, `pr diff`, `pr view`, `pr list`). `description: Code review a pull request`. `disable-model-invocation: false`. No `model` key.

| Step | What the command instructs | Model named |
|---|---|---|
| 1 | Check whether the pull request is closed, a draft, does not need review (automated, or "very simple and obviously ok"), or already has a review from an earlier run. Stop if so. | Haiku |
| 2 | List the paths of relevant `CLAUDE.md` files: the root one and any in directories the pull request touches. | Haiku |
| 3 | View the pull request and return a summary. | Haiku |
| 4 | Launch **5 parallel review agents**. Each returns issues with a reason. (1) `CLAUDE.md` compliance. (2) Shallow scan of the changes for obvious, large bugs. (3) Bugs in light of git blame and history. (4) Comments on previous pull requests touching the same files. (5) Compliance with guidance in code comments. | Sonnet (all five) |
| 5 | For each issue, launch a scoring agent that returns a confidence score from 0 to 100 against a five-point rubric (0, 25, 50, 75, 100) given verbatim. | Haiku |
| 6 | **Drop every issue scoring below 80.** If none remain, stop. | session model |
| 7 | Repeat the eligibility check from step 1. | Haiku |
| 8 | Post the result as a pull request comment with `gh pr comment`, in a fixed format with full-SHA links. | session model |

Output: a comment on the pull request. There is no terminal-only mode. When no issue reaches 80, step 6 stops the run before anything is posted, although the notes also give a "No issues found" comment format.

### 4.2 Command at `9780cf4` (identical at `c905cd8`)

Front matter: the same seven `gh` subcommands plus `mcp__github_inline_comment__create_inline_comment`. Otherwise unchanged. No `model` key.

A new preamble tells all agents and subagents to assume tools work, to make no exploratory calls, and to call a tool only when needed.

| Step | What the command instructs | Model named |
|---|---|---|
| 1 | Eligibility check: closed, draft, does not need review (automated, or trivial and obviously correct), or Claude has already commented (checked with `gh pr view <PR> --comments`). Stop if any is true. A note says pull requests generated by Claude are still reviewed. | haiku |
| 2 | List paths of relevant `CLAUDE.md` files. | haiku |
| 3 | View the pull request and return a summary. | sonnet |
| 4 | Launch **4 parallel review agents**. Agents 1 and 2: `CLAUDE.md` compliance. Agent 3: scan the diff alone for obvious, significant bugs, flagging nothing that needs context outside the diff. Agent 4: problems in the introduced code, such as security issues and incorrect logic. Each agent is given the pull request title and description. | sonnet (agents 1, 2); Opus (agents 3, 4) |
| 5 | For each issue, launch a validation subagent that confirms with high confidence that the issue is real. | Opus for bugs and logic; sonnet for `CLAUDE.md` violations |
| 6 | Drop every issue that was not validated. | session model |
| 7 | Print a summary to the terminal. Without `--comment`, stop here. With `--comment` and no issues, post a summary comment and stop. | session model |
| 8 | With `--comment` and issues: prepare the list of comments. | session model |
| 9 | Post one inline comment per issue through `mcp__github_inline_comment__create_inline_comment`, with a committable suggestion for small self-contained fixes. | session model |

Step 4 adds a "high signal" rule. Agents flag only: code that will fail to compile or parse; code that "will definitely produce wrong results regardless of inputs"; and `CLAUDE.md` violations where the exact rule can be quoted. Agents do not flag style or quality concerns, "potential issues that depend on specific inputs or state", or subjective suggestions.

There is **no numeric confidence score and no threshold** at this commit. Filtering is validated or not validated.

### 4.3 Models named by the plugin (Q-11)

| Role | `aecd4c8` | `9780cf4` |
|---|---|---|
| Eligibility check | Haiku | haiku |
| `CLAUDE.md` path listing | Haiku | haiku |
| Pull request summary | Haiku | sonnet |
| `CLAUDE.md` compliance review | Sonnet (1 agent) | sonnet (2 agents) |
| Bug review | Sonnet (1 shallow-scan agent) | Opus (2 agents) |
| History, previous pull requests, code comments | Sonnet (3 agents) | removed |
| Filtering | Haiku confidence scorer, one per issue | Opus validator for bugs; sonnet validator for `CLAUDE.md` issues |
| Eligibility re-check | Haiku | removed |
| Orchestration, final filter, output | session model | session model |

Answer to Q-11: **yes, at both commits.** Points that matter for the design:

- The names are family words. No versioned identifier appears anywhere in the plugin. Which exact model runs depends on how Claude Code resolves the alias at run time.
- The names appear in prose, not in a configuration field. The session model decides whether to pass a model when it launches each subagent. Compliance is a behaviour of the model under test, so it can vary by model and by run. It must be measured, not assumed.
- At `aecd4c8` no review or scoring step is assigned to the session model. If the instructions are followed, changing the session model changes orchestration only.
- At `9780cf4` bug review and bug validation run on "Opus". Official Claude Code documentation (checked 2026-11-15, see `docs/11-verified-facts.md`) says the `opus` alias resolves to Opus 5.5 on the Anthropic API, except that a subagent given a family alias runs on its parent's model when the parent is in the same family. If that holds, a session on `claude-opus-5` gets bug agents on `claude-opus-5`, while a session on `claude-fable-5-2` gets bug agents on Opus 5.5. This is from documentation and has not been tested.

## 5. Did `9780cf4` alter review logic?

No. The full diff from `c905cd8` to `9780cf4` is:

```diff
--- a/plugins/code-review/.claude-plugin/plugin.json
+++ b/plugins/code-review/.claude-plugin/plugin.json
@@ -1,6 +1,7 @@
 {
   "name": "code-review",
   "description": "Automated code review for pull requests using multiple specialized agents with confidence-based scoring",
+  "version": "1.0.1",
   "author": {
     "name": "Anthropic",
     "email": "support@anthropic.com"
```

One file changed, one line added. The command file and the README are the same git blobs at both commits. `9780cf4` is a version label only. It changed neither logic nor documentation.

## 6. The diff from `c905cd8` (the newer command)

`c905cd8` changes two files against `aecd4c8`: `commands/code-review.md` (126 lines changed) and `README.md` (24 lines changed). The manifest and licence are untouched. The full diff is in the appendix.

### Changes to review logic (`commands/code-review.md`)

| Area | `aecd4c8` | `c905cd8` and later |
|---|---|---|
| Review agents | 5, all Sonnet | 4: two sonnet, two Opus |
| Bug review scope | One shallow scan of the changes | Two agents: one diff-only scan, one covering security and logic in introduced code |
| Context agents | Git blame and history; previous pull request comments; code comments | All three removed |
| Flagging bar | "Large bugs", avoid nitpicks | Compile or parse failure, definite wrong results regardless of inputs, or a quotable `CLAUDE.md` violation |
| Filtering | Haiku scores each issue 0 to 100; drop below 80 | Opus or sonnet validates each issue; drop unvalidated |
| Confidence threshold | 80 | none |
| Summary agent | Haiku | sonnet |
| Second eligibility check | Yes, before posting | Removed |
| Default output | Pull request comment, always | Terminal. Comment only with `--comment` |
| Comment style | One summary comment listing issues with links | Inline comments per issue through an MCP tool, with optional committable suggestions |
| Context given to agents | Not specified | Pull request title and description |
| Tool-use preamble | None | Assume tools work; no exploratory calls |
| False-positive list | 8 items | 6 items. Removed: "changes in functionality that are likely intentional" and "real issues, but on lines that the user did not modify" |
| Allowed tools | 7 `gh` subcommands | The same, plus `mcp__github_inline_comment__create_inline_comment` |
| Example link repository | `anthropics/claude-cli-internal` | `anthropics/claude-code` |

### Changes to documentation (`README.md`)

The README gained the `--comment` flag: a usage line, an options section, and updated workflow examples. Nothing else changed.

The README was not updated for the new logic. At `9780cf4` it still says the plugin scores each issue 0 to 100, filters below 80, and runs an agent on git blame and history. It tells users to change the threshold by editing a line, "Filter out any issues with a score less than 80", that is no longer in the command file. Anyone describing the plugin from its README at `9780cf4` will describe the old design.

The README was already inaccurate at `aecd4c8`: it says 4 parallel agents, and the command launches 5.

## 7. What this means for the pilot

These follow from the files. Each needs a decision before the design is fixed.

1. **The plugin pins model tiers, so the model axis is weaker than planned.** With the plugin, most or all review work runs on models the plugin names, not on the session model. The baseline has no such instruction and runs on the session model. A with-plugin against baseline comparison on one "model" therefore compares different models as well as different instructions. Options: test the plugin as shipped and report which models actually ran; or force one model onto every subagent (Claude Code documents `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`), which tests a configuration users do not get. The first matches the hypothesis about what users experience. The second isolates the model. This is a design question for the owner. See Q-17 in section 10.
2. **Cost estimates by session model are wrong.** Subagent requests are billed at the subagent's model rate. A Fable 5.2 session at `9780cf4` would pay Haiku, Sonnet, and Opus rates for most of its tokens.
3. **Per-request model logging is not optional.** Whether the session model obeys "launch a haiku agent" is itself an outcome. TR-6 logging must attribute each request to a subagent role.
4. **The input is a GitHub pull request, and the command needs `gh`.** Corpus cases must be real pull requests on a GitHub repository, or `gh` must be replaced by a stand-in that serves canned responses. This shapes decision 4 and the isolation design.
5. **Eligibility rules can skip a case.** A draft, closed, or "trivial and obviously correct" pull request is not reviewed. A small clean case may be skipped as trivial. A skip must be a distinct run status, not a "no findings" result.
6. **Repeats can contaminate each other.** Both commits skip a pull request that already has a review comment. At `aecd4c8` every run with findings posts one. A second repeat on the same pull request would be skipped. Each repeat needs a fresh pull request, or comments must be removed between runs.
7. **Capturing output differs by commit.** At `aecd4c8` the findings exist only as a pull request comment, so the harness must let the comment be posted, or intercept it. At `9780cf4` findings print to the terminal and nothing is written unless `--comment` is passed. The two commits cannot be run with one invocation and one capture method.
8. **Several pilot defect categories are outside the plugin's stated scope.** Both commits list "general security issues" as false positives unless `CLAUDE.md` requires them. `9780cf4` also excludes "potential issues that depend on specific inputs or state". Injection, path traversal, null dereference, race conditions, and resource leaks usually depend on inputs or state. A miss on those may be the plugin doing what it was told. Agent 4 at `9780cf4` is also told to look for "security issues", so the instructions conflict. Each planted defect should be labelled in or out of the plugin's stated scope at each commit, and the hypotheses should say which set is scored.
9. **Half the review agents check `CLAUDE.md` compliance.** A corpus repository with no `CLAUDE.md` leaves them with nothing to find. Decision 4 should say whether cases include `CLAUDE.md` files and planted violations.
10. **The filter metric needs redefining (Q-12, T-filter).** At `aecd4c8` a filtered finding has a score below 80. At `9780cf4` there is no score, only validated or not. Pre-filter findings exist only as subagent outputs returned to the session model. They would be visible in subagent transcripts or raw request logs if those are captured. This is not yet tested.
11. **Step 5 at `9780cf4` is ambiguous.** It says to validate issues found "by agents 3 and 4", then describes validating `CLAUDE.md` issues, which come from agents 1 and 2. Step 6 drops anything not validated. Whether `CLAUDE.md` findings survive depends on how the session model reads this. Expect variance here.
12. **The inline comment tool is not supplied by the plugin.** `mcp__github_inline_comment__create_inline_comment` is pre-approved but no MCP server is defined in the plugin. It matters only with `--comment`. The pilot should not use `--comment` at `9780cf4`.

## 8. Safety notes from the read (TR-2)

- The plugin ships no code that runs on install or on load. Its effect is the prompt text in one command file.
- That prompt directs the session to run `gh` commands. `gh pr comment` writes to GitHub, and `gh search` and `gh pr list` can read beyond the target pull request. Runs should use a GitHub credential scoped to the corpus repository only.
- The old output template includes a "Generated with Claude Code" footer and a request to react with a thumbs-up or thumbs-down. These would appear in posted comments.
- Nothing in the files asks the model to read credentials, contact other hosts, or change the repository under review.

## 9. Still unverified

- That Claude Code resolves "Haiku", "Sonnet", and "Opus" in command prose to the models described in section 4.3. This comes from documentation about aliases, and the plugin uses prose, not an alias field.
- That the session model follows the tier instructions, and how often.
- That either commit installs and runs on the Claude Code version the pilot will pin.
- Whether pre-filter findings can be recovered from transcripts or logs.
- The `anthropics/claude-plugins-public` homepage reference.

## 10. New open questions

Numbering continues from Q-16 in `docs/08-risks-and-open-questions.md`.

| ID | Question | Raised by |
|---|---|---|
| Q-17 | Is the plugin tested as shipped, with the subagent models it names, or with one model forced onto every subagent? | Section 7, item 1 |
| Q-18 | How do corpus cases become GitHub pull requests: a real repository, or a stand-in for `gh`? How is output captured at `aecd4c8`, which only posts comments? | Items 4, 6, 7 |
| Q-19 | Which planted defect categories are inside the plugin's stated scope at each commit, and are out-of-scope defects scored? | Item 8 |
| Q-20 | Do corpus cases include `CLAUDE.md` files and planted violations of them? | Item 9 |
| Q-21 | How is the filter threshold (T-filter) defined at `9780cf4`, which has no numeric score? | Item 10 |

## Appendix: full diff, `aecd4c8` to `c905cd8`

The plugin is licensed under Apache 2.0. The text below is quoted from `anthropics/claude-plugins-official` for review purposes.

````diff
diff --git a/plugins/code-review/README.md b/plugins/code-review/README.md
index b0962f09..42cc8095 100644
--- a/plugins/code-review/README.md
+++ b/plugins/code-review/README.md
@@ -22,23 +22,29 @@ Performs automated code review on a pull request using multiple specialized agen
    - **Agent #4**: Analyze git blame/history for context-based issues
 5. Scores each issue 0-100 for confidence level
 6. Filters out issues below 80 confidence threshold
-7. Posts review comment with high-confidence issues only
+7. Outputs review (to terminal by default, or as PR comment with `--comment` flag)
 
 **Usage:**
 ```bash
-/code-review
+/code-review [--comment]
 ```
 
+**Options:**
+- `--comment`: Post the review as a comment on the pull request (default: outputs to terminal only)
+
 **Example workflow:**
 ```bash
-# On a PR branch, run:
+# On a PR branch, run locally (outputs to terminal):
 /code-review
 
+# Post review as PR comment:
+/code-review --comment
+
 # Claude will:
 # - Launch 4 review agents in parallel
 # - Score each issue for confidence
-# - Post comment with issues ≥80 confidence
-# - Skip posting if no high-confidence issues found
+# - Output issues ≥80 confidence (to terminal or PR depending on flag)
+# - Skip if no high-confidence issues found
 ```
 
 **Features:**
@@ -114,17 +120,23 @@ This plugin is included in the Claude Code repository. The command is automatica
 ### Standard PR review workflow:
 ```bash
 # Create PR with changes
+# Run local review (outputs to terminal)
 /code-review
 
 # Review the automated feedback
 # Make any necessary fixes
+
+# Optionally post as PR comment
+/code-review --comment
+
 # Merge when ready
 ```
 
 ### As part of CI/CD:
 ```bash
 # Trigger on PR creation or update
-# Automatically posts review comments
+# Use --comment flag to post review comments
+/code-review --comment
 # Skip if review already exists
 ```
 
diff --git a/plugins/code-review/commands/code-review.md b/plugins/code-review/commands/code-review.md
index c46e327f..8d1533fa 100644
--- a/plugins/code-review/commands/code-review.md
+++ b/plugins/code-review/commands/code-review.md
@@ -1,89 +1,107 @@
 ---
-allowed-tools: Bash(gh issue view:*), Bash(gh search:*), Bash(gh issue list:*), Bash(gh pr comment:*), Bash(gh pr diff:*), Bash(gh pr view:*), Bash(gh pr list:*)
+allowed-tools: Bash(gh issue view:*), Bash(gh search:*), Bash(gh issue list:*), Bash(gh pr comment:*), Bash(gh pr diff:*), Bash(gh pr view:*), Bash(gh pr list:*), mcp__github_inline_comment__create_inline_comment
 description: Code review a pull request
 disable-model-invocation: false
 ---
 
 Provide a code review for the given pull request.
 
+**Agent assumptions (applies to all agents and subagents):**
+- All tools are functional and will work without error. Do not test tools or make exploratory calls. Make sure this is clear to every subagent that is launched.
+- Only call a tool if it is required to complete the task. Every tool call should have a clear purpose.
+
 To do this, follow these steps precisely:
 
-1. Use a Haiku agent to check if the pull request (a) is closed, (b) is a draft, (c) does not need a code review (eg. because it is an automated pull request, or is very simple and obviously ok), or (d) already has a code review from you from earlier. If so, do not proceed.
-2. Use another Haiku agent to give you a list of file paths to (but not the contents of) any relevant CLAUDE.md files from the codebase: the root CLAUDE.md file (if one exists), as well as any CLAUDE.md files in the directories whose files the pull request modified
-3. Use a Haiku agent to view the pull request, and ask the agent to return a summary of the change
-4. Then, launch 5 parallel Sonnet agents to independently code review the change. The agents should do the following, then return a list of issues and the reason each issue was flagged (eg. CLAUDE.md adherence, bug, historical git context, etc.):
-   a. Agent #1: Audit the changes to make sure they compily with the CLAUDE.md. Note that CLAUDE.md is guidance for Claude as it writes code, so not all instructions will be applicable during code review.
-   b. Agent #2: Read the file changes in the pull request, then do a shallow scan for obvious bugs. Avoid reading extra context beyond the changes, focusing just on the changes themselves. Focus on large bugs, and avoid small issues and nitpicks. Ignore likely false positives.
-   c. Agent #3: Read the git blame and history of the code modified, to identify any bugs in light of that historical context
-   d. Agent #4: Read previous pull requests that touched these files, and check for any comments on those pull requests that may also apply to the current pull request.
-   e. Agent #5: Read code comments in the modified files, and make sure the changes in the pull request comply with any guidance in the comments.
-5. For each issue found in #4, launch a parallel Haiku agent that takes the PR, issue description, and list of CLAUDE.md files (from step 2), and returns a score to indicate the agent's level of confidence for whether the issue is real or false positive. To do that, the agent should score each issue on a scale from 0-100, indicating its level of confidence. For issues that were flagged due to CLAUDE.md instructions, the agent should double check that the CLAUDE.md actually calls out that issue specifically. The scale is (give this rubric to the agent verbatim):
-   a. 0: Not confident at all. This is a false positive that doesn't stand up to light scrutiny, or is a pre-existing issue.
-   b. 25: Somewhat confident. This might be a real issue, but may also be a false positive. The agent wasn't able to verify that it's a real issue. If the issue is stylistic, it is one that was not explicitly called out in the relevant CLAUDE.md.
-   c. 50: Moderately confident. The agent was able to verify this is a real issue, but it might be a nitpick or not happen very often in practice. Relative to the rest of the PR, it's not very important.
-   d. 75: Highly confident. The agent double checked the issue, and verified that it is very likely it is a real issue that will be hit in practice. The existing approach in the PR is insufficient. The issue is very important and will directly impact the code's functionality, or it is an issue that is directly mentioned in the relevant CLAUDE.md.
-   e. 100: Absolutely certain. The agent double checked the issue, and confirmed that it is definitely a real issue, that will happen frequently in practice. The evidence directly confirms this.
-6. Filter out any issues with a score less than 80. If there are no issues that meet this criteria, do not proceed.
-7. Use a Haiku agent to repeat the eligibility check from #1, to make sure that the pull request is still eligible for code review.
-8. Finally, use the gh bash command to comment back on the pull request with the result. When writing your comment, keep in mind to:
-   a. Keep your output brief
-   b. Avoid emojis
-   c. Link and cite relevant code, files, and URLs
-
-Examples of false positives, for steps 4 and 5:
+1. Launch a haiku agent to check if any of the following are true:
+   - The pull request is closed
+   - The pull request is a draft
+   - The pull request does not need code review (e.g. automated PR, trivial change that is obviously correct)
+   - Claude has already commented on this PR (check `gh pr view <PR> --comments` for comments left by claude)
 
-- Pre-existing issues
-- Something that looks like a bug but is not actually a bug
-- Pedantic nitpicks that a senior engineer wouldn't call out
-- Issues that a linter, typechecker, or compiler would catch (eg. missing or incorrect imports, type errors, broken tests, formatting issues, pedantic style issues like newlines). No need to run these build steps yourself -- it is safe to assume that they will be run separately as part of CI.
-- General code quality issues (eg. lack of test coverage, general security issues, poor documentation), unless explicitly required in CLAUDE.md
-- Issues that are called out in CLAUDE.md, but explicitly silenced in the code (eg. due to a lint ignore comment)
-- Changes in functionality that are likely intentional or are directly related to the broader change
-- Real issues, but on lines that the user did not modify in their pull request
+   If any condition is true, stop and do not proceed.
 
-Notes:
+Note: Still review Claude generated PR's.
 
-- Do not check build signal or attempt to build or typecheck the app. These will run separately, and are not relevant to your code review.
-- Use `gh` to interact with Github (eg. to fetch a pull request, or to create inline comments), rather than web fetch
-- Make a todo list first
-- You must cite and link each bug (eg. if referring to a CLAUDE.md, you must link it)
-- For your final comment, follow the following format precisely (assuming for this example that you found 3 issues):
+2. Launch a haiku agent to return a list of file paths (not their contents) for all relevant CLAUDE.md files including:
+   - The root CLAUDE.md file, if it exists
+   - Any CLAUDE.md files in directories containing files modified by the pull request
 
----
+3. Launch a sonnet agent to view the pull request and return a summary of the changes
 
-### Code review
+4. Launch 4 agents in parallel to independently review the changes. Each agent should return the list of issues, where each issue includes a description and the reason it was flagged (e.g. "CLAUDE.md adherence", "bug"). The agents should do the following:
 
-Found 3 issues:
+   Agents 1 + 2: CLAUDE.md compliance sonnet agents
+   Audit changes for CLAUDE.md compliance in parallel. Note: When evaluating CLAUDE.md compliance for a file, you should only consider CLAUDE.md files that share a file path with the file or parents.
 
-1. <brief description of bug> (CLAUDE.md says "<...>")
+   Agent 3: Opus bug agent (parallel subagent with agent 4)
+   Scan for obvious bugs. Focus only on the diff itself without reading extra context. Flag only significant bugs; ignore nitpicks and likely false positives. Do not flag issues that you cannot validate without looking at context outside of the git diff.
 
-<link to file and line with full sha1 + line range for context, note that you MUST provide the full sha and not use bash here, eg. https://github.com/anthropics/claude-code/blob/1d54823877c4de72b2316a64032a54afc404e619/README.md#L13-L17>
+   Agent 4: Opus bug agent (parallel subagent with agent 3)
+   Look for problems that exist in the introduced code. This could be security issues, incorrect logic, etc. Only look for issues that fall within the changed code.
 
-2. <brief description of bug> (some/other/CLAUDE.md says "<...>")
+   **CRITICAL: We only want HIGH SIGNAL issues.** Flag issues where:
+   - The code will fail to compile or parse (syntax errors, type errors, missing imports, unresolved references)
+   - The code will definitely produce wrong results regardless of inputs (clear logic errors)
+   - Clear, unambiguous CLAUDE.md violations where you can quote the exact rule being broken
 
-<link to file and line with full sha1 + line range for context>
+   Do NOT flag:
+   - Code style or quality concerns
+   - Potential issues that depend on specific inputs or state
+   - Subjective suggestions or improvements
 
-3. <brief description of bug> (bug due to <file and code snippet>)
+   If you are not certain an issue is real, do not flag it. False positives erode trust and waste reviewer time.
 
-<link to file and line with full sha1 + line range for context>
+   In addition to the above, each subagent should be told the PR title and description. This will help provide context regarding the author's intent.
 
-🤖 Generated with [Claude Code](https://claude.ai/code)
+5. For each issue found in the previous step by agents 3 and 4, launch parallel subagents to validate the issue. These subagents should get the PR title and description along with a description of the issue. The agent's job is to review the issue to validate that the stated issue is truly an issue with high confidence. For example, if an issue such as "variable is not defined" was flagged, the subagent's job would be to validate that is actually true in the code. Another example would be CLAUDE.md issues. The agent should validate that the CLAUDE.md rule that was violated is scoped for this file and is actually violated. Use Opus subagents for bugs and logic issues, and sonnet agents for CLAUDE.md violations.
 
-<sub>- If this code review was useful, please react with 👍. Otherwise, react with 👎.</sub>
+6. Filter out any issues that were not validated in step 5. This step will give us our list of high signal issues for our review.
 
----
+7. Output a summary of the review findings to the terminal:
+   - If issues were found, list each issue with a brief description.
+   - If no issues were found, state: "No issues found. Checked for bugs and CLAUDE.md compliance."
+
+   If `--comment` argument was NOT provided, stop here. Do not post any GitHub comments.
+
+   If `--comment` argument IS provided and NO issues were found, post a summary comment using `gh pr comment` and stop.
+
+   If `--comment` argument IS provided and issues were found, continue to step 8.
+
+8. Create a list of all comments that you plan on leaving. This is only for you to make sure you are comfortable with the comments. Do not post this list anywhere.
 
-- Or, if you found no issues:
+9. Post inline comments for each issue using `mcp__github_inline_comment__create_inline_comment` with `confirmed: true`. For each comment:
+   - Provide a brief description of the issue
+   - For small, self-contained fixes, include a committable suggestion block
+   - For larger fixes (6+ lines, structural changes, or changes spanning multiple locations), describe the issue and suggested fix without a suggestion block
+   - Never post a committable suggestion UNLESS committing the suggestion fixes the issue entirely. If follow up steps are required, do not leave a committable suggestion.
+
+   **IMPORTANT: Only post ONE comment per unique issue. Do not post duplicate comments.**
+
+Use this list when evaluating issues in Steps 4 and 5 (these are false positives, do NOT flag):
+
+- Pre-existing issues
+- Something that appears to be a bug but is actually correct
+- Pedantic nitpicks that a senior engineer would not flag
+- Issues that a linter will catch (do not run the linter to verify)
+- General code quality concerns (e.g., lack of test coverage, general security issues) unless explicitly required in CLAUDE.md
+- Issues mentioned in CLAUDE.md but explicitly silenced in the code (e.g., via a lint ignore comment)
+
+Notes:
+
+- Use gh CLI to interact with GitHub (e.g., fetch pull requests, create comments). Do not use web fetch.
+- Create a todo list before starting.
+- You must cite and link each issue in inline comments (e.g., if referring to a CLAUDE.md, include a link to it).
+- If no issues are found and `--comment` argument is provided, post a comment with the following format:
 
 ---
 
-### Code review
+## Code review
 
 No issues found. Checked for bugs and CLAUDE.md compliance.
 
-🤖 Generated with [Claude Code](https://claude.ai/code)
+---
 
-- When linking to code, follow the following format precisely, otherwise the Markdown preview won't render correctly: https://github.com/anthropics/claude-cli-internal/blob/c21d3c10bc8e898b7ac1a2d745bdc9bc4e423afe/package.json#L10-L15
+- When linking to code in inline comments, follow the following format precisely, otherwise the Markdown preview won't render correctly: https://github.com/anthropics/claude-code/blob/c21d3c10bc8e898b7ac1a2d745bdc9bc4e423afe/package.json#L10-L15
   - Requires full git sha
   - You must provide the full sha. Commands like `https://github.com/owner/repo/blob/$(git rev-parse HEAD)/foo/bar` will not work, since your comment will be directly rendered in Markdown.
   - Repo name must match the repo you're code reviewing
````
