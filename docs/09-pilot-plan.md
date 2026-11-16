# 09 Pilot plan

Status: **owner decisions recorded 2026-11-15 (section 7). Sections 2, 4, and 6 are to be revised to match them.** Date: 2026-11-15. Supersedes the blocker placeholder in this file's earlier version.

Sections 1 to 6 predate the plugin review and the documentation check. Where they disagree with `docs/10-plugin-review.md` or `docs/11-verified-facts.md`, those documents are correct.

No paid model calls were made in writing this plan. Every cost figure below is an estimate built from stated assumptions, not a measurement. The pilot itself is what measures them.

## 1. Verified and unverified facts

### Verified (read from the public repository)

Source: a full clone of `anthropics/claude-plugins-official` (default branch at `b5b01ac`, 2026-11-13), read with `git log -- plugins/code-review`. The clone was made outside this repository and is not committed.

| Commit | Date (author) | Message | `plugin.json` version at commit |
|---|---|---|---|
| `4ca561fb8532594e7a5faef945e85096fcec0616` | 2025-11-20 | creating intital scaffolding for claude code plugins | 1.0.0 |
| `22d3def39e4a6ad96d4fffff7fce5fb28c8d6215` | 2025-12-01 | Merge pull request #2 from anthropics/noahz/official_language | not found |
| `19a119f97e361ebdec475cd2bf5667cc4e48e64b` | 2025-12-12 | Update plugins library to include authors (#6) | not found |
| `aecd4c852f10b466245f18383fa6aad8c0b10d57` | 2026-02-20 | Add Apache 2.0 LICENSE files to all internal plugins | not found |
| `c905cd8fec340e465dd66990b82b95b6e45db212` | 2026-10-26 | code-review: bring in the newer command from anthropics/claude-code | not found |
| `9780cf407f5593727b668bae95a0c4ae2e0de1ae` | 2026-10-26 | code-review: add version 1.0.1 | 1.0.1 |

Notes:
- Six commits touch the path. The version field is present only at the first and last. Where it is absent, the file may be missing or the version may live elsewhere; this is not yet checked (Q-10).
- `c905cd8` brings in a newer command from `anthropics/claude-code`. It is the most likely behaviour change in the history and should be a comparison point.
- **Provenance (TR-2) is not yet done.** The plugin's files have not been read or reviewed. That must happen before any commit is used.

### Unverified

- All model release dates and the Claude Code CLI release dates in documents 05 and 07 (Q-13).
- All prices in document 05. Only Fable 5.2 (about $8 in, $40 out per million tokens) and Opus 5 ($5 in, $25 out) were supplied, and neither has been checked against official pricing.
- Fable 5.2's thinking behaviour, default effort, fallback behaviour, and the 30-day retention requirement (BR-9, TR-5, TR-7).
- Whether the plugin names a model for its review agents (Q-11), and whether pre-threshold findings appear in transcripts (Q-12).

Because the plugin is versioned by commit rather than by release, the plugin axis is defined by commit SHA. A commit date is not a release date.

## 2. Pilot corpus (10 to 15 cases)

The pilot uses **12 cases**: 10 with planted defects and 2 clean cases with none. Clean cases measure false positives. Corpus source is still open (decision 4), so this section fixes only the shape.

| Planted defect category | Cases |
|---|---|
| Injection (SQL, command, or template) | 1 |
| Missing or broken authorisation check | 1 |
| Null or undefined dereference | 1 |
| Off-by-one or boundary error | 1 |
| Resource leak (file, connection, or lock not released) | 1 |
| Race condition or unsafe shared state | 1 |
| Unsafe deserialisation or path traversal | 1 |
| Incorrect error handling that hides failure | 1 |
| Wrong cryptographic or random-number use | 1 |
| Logic error in a business rule | 1 |
| Clean (no planted defect) | 2 |

Requirements for every case (from TR-10, TR-11, and BR-8):
- Recorded location (file and line range), category, and rationale for each planted defect.
- Per-case checksum, and a corpus-level checksum verified before each run.
- Ground truth stored outside the run environment, and not inferable from file names or comments.
- No sensitive, proprietary, personal, or employer-owned code and no real secrets. Licence recorded per case.
- Held-back cases and canary markers are reserved for the scored campaign, not the pilot.

Size check: 12 cases with about 10 planted defects gives roughly 100 defect-by-run observations per cell at 10 repeats, but only about 10 independent items. Interval width is dominated by the number of items, not the number of repeats. This is why the corpus can't be shrunk below 10 and why the campaign should grow it if the pilot's intervals are too wide.

## 3. Repeat counts

- **Pilot variance run:** 3 repeats per case, per condition, in one cell (see section 4). That gives 36 plugin runs and 36 baseline runs for the variance estimate.
- **Campaign repeats:** not fixed here. The campaign repeat count comes from the pilot's variance and the power calculation in document 02, using thresholds the project owner fixes beforehand (see section 7). As a planning value only, 5 repeats per case per cell is assumed for cost estimates below.
- Each repeat is a fresh environment (TR-12). Order is randomised across cells.

## 4. Cost estimate

### Assumptions (not measured)

| Quantity | Plugin run | Baseline run (no plugin) |
|---|---|---|
| Input tokens | 150,000 | 30,000 |
| Output tokens | 15,000 | 5,000 |

These figures are guesses for a multi-agent review of a small-to-medium diff. The pilot replaces them with measured values. Prices are the reported figures from document 05 and are **unverified**.

### Per-run cost

| Model | Plugin run | Baseline run |
|---|---|---|
| Fable 5.2 (about $8 in, $40 out) | about $1.80 | about $0.44 |
| Opus 5 ($5 in, $25 out) | about $1.13 | about $0.28 |

### Pilot total

Variance run in one cell: 12 cases × 3 repeats × (plugin + baseline).

| Model | Pilot estimate |
|---|---|
| Fable 5.2 | about $81 |
| Opus 5 | about $50 |

Plus a smoke test (not scored), the fallback check in section 5, and any re-runs. Plan on about $150 total for the pilot as a safety margin, with the cost ceiling (BR-4) set from the measured figures before the campaign.

### Campaign scale (for later)

The 2×2×2 cluster design in document 04 uses 8 cells. At 5 repeats per case on 12 cases, that is 480 plugin runs and 480 baselines. At the Fable estimate that is about $860 for plugin runs alone, before anchors and re-runs. That is why the campaign ceiling must come from measured pilot usage.

Report tokens as the primary cost metric and store the price table used, with its date (document 04).

## 5. Model and plugin pilot options

### Model options

1. **Opus 5.5 only.** Cheapest; checks the harness and gives a variance estimate. Does not test the hypothesis.
2. **Opus 5.5 and Fable 5.2 on one plugin commit.** Checks the harness on both families and measures Fable's fallback rate on code-review-style content. Comparison across families is confounded (see document 04).
3. **Opus 5 and Opus 5.5 on one commit.** Gives a within-family version comparison, which is the direct test of model drift. Adds one model's cost.

**Recommendation: option 2, with Opus 5.5 as the variance cell.** It tests the harness on both families, gives an early measure of Fable's fallback rate (TR-6), and uses the model the owner plans to compare against. Option 3 is the next step if option 2 shows the harness works.

Before any scored run, confirm each model's exact identifier, that it is callable, and its fallback and retention terms (BR-9, TR-5).

### Plugin commit options

1. **Head only (`9780cf4`).** Simplest. Cannot show whether the October change matters.
2. **Pair across the October change (`aecd4c8` and `9780cf4`).** Isolates the commit that brought in the newer command and the version bump.
3. **Earliest commit (`4ca561f`).** Shows total drift. It may not run on the pinned CLI, so it needs a smoke test first.

**Recommendation: option 2 for the pilot.** It is the smallest set that shows a real change in the plugin's history. Option 3 is added to the campaign only if its smoke test passes.

### Pilot cells

| Cell | Model | Plugin commit | Condition | Runs (12 cases × 3 repeats) |
|---|---|---|---|---|
| P1 | Opus 5.5 | `9780cf4` | with plugin | 36 |
| P2 | Opus 5.5 | `9780cf4` | baseline | 36 |
| P3 | Opus 5.5 | `aecd4c8` | with plugin | 36 (only if P1 and P2 pass the harness checks) |
| P4 | Fable 5.2 | `9780cf4` | with plugin | 12 (fallback and harness check, one repeat) |

P3 is held until the harness passes on P1 and P2. P4 is a single-repeat check, not a scored cell.

### Checks the pilot must pass before scored runs

- Requested and returned model match, or any mismatch is logged as a fallback (TR-6).
- Effort is set explicitly and recorded on every request (TR-7).
- Each run ends in one status (TR-15). Harness failures are reported separately from plugin failures.
- The corpus checksum verifies, and a deliberately corrupted case is rejected (TR-22).
- The plugin's files for each commit are read and recorded (TR-2).
- Retention terms are checked and recorded (BR-9).

## 6. Pre-registration template

Commit this file to the repository before the first scored run. Any later change is a recorded deviation and is reported with the results.

```
# Pre-registration: <campaign id>

Date committed (UTC): <timestamp>
Commit of this file: <SHA>

## Question
<one sentence, taken from document 02>

## Pinned identifiers (TR-1 to TR-4)
- Model(s), exact identifier: <...>
- Model(s), returned identifier observed in pilot: <...>
- Plugin commit SHA(s): <full SHA, one per row>
- Plugin file hash(es) verified (TR-2): <...>
- Claude Code CLI version and channel: <...>
- Corpus version and checksum: <...>
- Grader version and, if used, its judge model: <...>
- Prompt version (invocation prompt): <...>

## Fixed settings (document 04)
- Effort (explicit level): <...>
- Thinking configuration, as set or observed: <...>
- Subagent model forced or not: <...>
- Permission and tool settings: <...>
- Timeouts and retry policy: <...>
- Fallback handling (TR-5, TR-6): <...>

## Thresholds (set before the scored runs, document 02)
- T-recall: <value and basis>
- T-filter: <value and basis>
- T-var: <value and basis>
- T-cost: <value and basis>

## Statistics
- Primary test: TOST equivalence against the margins above, plus mixed-effects model with corpus items as random effect.
- Error rate: <alpha>
- Multiple-comparison correction: <method>
- Repeats per case per cell: <n>
- Power calculation: <attached or linked>

## Grading rules (document 02 and TR-9, TR-15)
- Deterministic match rule: <defect id, file, line range>
- Handling of partial matches, merged findings, and unplanted true defects: <rule>
- Human audit sample size and error limit: <n, limit>
- Rule for withdrawing LLM grading: <rule>

## Cost
- Cost ceiling (BR-4): <value, owner, date set>
- Price table used, with its date: <...>

## Data handling
- Retention terms checked on: <date, by whom>
- Account and organisation used: <identifier, no key>

## Deviations
<none, or each deviation with date and reason>
```

## 7. Owner decisions

These are the items that cannot be resolved from evidence and are not Claude Code's to decide. **The project owner answered all seven on 2026-11-15.** The answers are recorded below. Where an answer conflicts with an earlier section of this plan, the answer here wins, and the earlier section is to be revised.

| # | Question | Decision (2026-11-15) |
|---|---|---|
| 1 | Cost ceiling (Q-1, BR-4) | **$200 in total.** Set at $150 on 2026-11-15 and raised to $200 the same day, after one case measured about $4.00 per case per repeat (see `docs/12-request-logging.md`, section 6c). This covers the logging spike, the pilot, and any model-based checking. |
| 2 | Data retention (BR-9) | **Accepted.** The owner accepts 30-day retention of corpus content, and confirmed in the Claude Console on 2026-11-15 that 30-day retention is on. Which workspace the project's API key belongs to is not yet recorded. |
| 3 | Reading the plugin from `anthropics/claude-plugins-official` (TR-2) | **Accepted** as the source of plugin files for the campaign. |
| 4 | Corpus source (decision 4) | **Reuse an existing, established corpus and defect set where one fits, in preference to building one.** This replaces the "mix" assumed in section 2. **Chosen on 2026-11-15: the Martian Code Review Bench (offline), 50 pull requests with 173 golden comments.** See `docs/13-corpus-options.md`. |
| 5 | Unplanted true defects (decision 5) | **Recorded and reported as a separate measure.** They are not scored against planted ground truth. **An agent, not the owner, checks whether each is real.** |
| 6 | Thresholds | **No pass or fail thresholds are fixed in advance.** The evaluation produces results and the owner judges them afterwards. The first run is therefore **exploratory**, not a confirmatory test. |
| 7 | Older models | **Out of scope.** The pilot uses Claude Opus 5.5 (`claude-opus-5-5`) and Claude Fable 5.2 (`claude-fable-5-2`) only. |

### Further owner decisions (2026-11-15)

| Question | Decision |
|---|---|
| Q-17: plugin as shipped, or one model forced onto every subagent? | **As shipped.** Subagents run on the model tiers the plugin names. Which models actually ran is logged and reported. |
| Q-30: where do the pull request copies live? | **The `sideofmydesk` GitHub organisation, as private repositories.** |
| Q-32: is plugin commit `aecd4c8` in the pilot? | **No.** The pilot tests `9780cf4` against the no-plugin baseline. Section 5's cell P3 is dropped. |
| Workspace of the project's API key | The owner reports the key is scoped at the organisation level. The 30-day retention setting was confirmed on in the Console on 2026-11-15. The first API call in the spike confirms that Fable requests are accepted. |

### Pilot settings approved by the owner (2026-11-15, after the logging spike)

| Setting | Decision |
|---|---|
| Size (Q-33) | **15 cases, 3 from each of the 5 projects, taken in the fixed case order. 2 repeats.** Two models and two arms give 120 runs. |
| Effort (Q-24) | **`high` on every run**, set explicitly. |
| Tool permissions (Q-36) | **Read-only commands are allowed in both arms** (`git log`, `git diff`, file reads, and the `gh` read commands). Nothing that writes. |
| Baseline prompt (Q-37) | The wording used in the spike: "Review pull request #N in this repository. Use the gh CLI to read it. Report every bug or defect you find in the changed code, giving the file path and line for each. Do not post anything to GitHub." This is version 1 of the baseline prompt. |
| Judge (Q-31) | **Claude Sonnet 5.5**, with the Martian benchmark's judge prompts. Sonnet 5.5 is not a model under test as a session model, but the plugin does use it for one summary step. |

The spike measured one plugin run at about $0.78 and one baseline run at about $0.30 on Opus 5.5, on one case. See `docs/12-request-logging.md`, section 6b.

### What these decisions change

- **Section 2 (corpus).** The 12-case shape and the defect category table were written for a purpose-built corpus. They are placeholders until the corpus research is done. A reused public corpus raises the training-data leakage risk, so a small private held-back portion is still recommended.
- **Section 4 (cost).** The pilot must fit inside $150 in total. The estimates there are unreliable (see `docs/11-verified-facts.md`, section 2). The pilot is sized after the logging spike measures cost per run.
- **Section 5 (cells).** Decision 7 matches the recommended model option: Opus 5.5 and Fable 5.2.
- **Section 6 (pre-registration).** With no thresholds, the template's "Thresholds" block records "none fixed; exploratory". What is measured is still fixed in advance: recall on planted defects, false positives, unplanted true defects, cost, and run-to-run variance.
- **Document 02 (hypotheses).** Its equivalence test needs thresholds. It does not apply to an exploratory run and should say so.
- **Decision 5 adds a model-based checker.** Its calls count against the ceiling. Its choice of model must be justified against self-grading, and its error rate measured on a hand-checked sample, as document 07 requires for any model judge.

### Constraints noted with the decisions

- Part of the promotional API credit used for this work expires on 2026-11-23, and the rest on 2026-12-12. Paid work after the first date draws only on the second part.

## 8. What this plan does not decide

- The final model list, the final commit list, and the campaign repeat count. These wait for pilot results and owner decisions above.
- The harness language and invocation method (decision 6). The pilot needs an early spike on request logging and on installing a plugin from an exact commit.
- Any release date or price marked unverified above.

## Next steps, in order

1. Owner answers section 7.
2. Read the plugin files at `aecd4c8` and `9780cf4` and record the review (TR-2).
3. Verify model identifiers, fallback, retention, and prices against official documentation (Q-13).
4. Spike request logging and plugin install from a commit (decision 6).
5. Run the pilot cells P1, P2, and P4 under a pre-registration committed before the first scored run.
