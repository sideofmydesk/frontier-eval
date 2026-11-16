# 04 Design approach

## Controlled comparison

The core comparison varies two factors and holds everything else fixed.

| Factor | Levels |
|---|---|
| Model release | The set chosen under open decisions 1 and 2 |
| Plugin condition | Each chosen plugin commit SHA, plus a no-plugin baseline |

Held fixed across all cells: corpus version, case content, invocation prompt, effort setting, thinking configuration where it is configurable, Claude Code CLI version, environment image, permission and tool settings, timeouts, retry policy, and grader version.

Other factors are varied only in the experiments below, each with the rest held fixed.

| Experiment | Varied factor | Purpose |
|---|---|---|
| E1 Plugin value | Plugin condition, per model | Does the plugin still help on this model? |
| E2 Model effect | Model, with plugin commit fixed | How much of the difference comes from the model? |
| E3 Plugin change | Plugin commit, with model fixed | Does a plugin change alter behaviour? |
| E4 CLI effect | CLI version, with model and plugin fixed | Do CLI changes (prompts, permissions, tooling) alter results? |
| E5 Effort | Effort level, with everything else fixed | How sensitive are results to effort? |

## Release clusters: 2×2×2 factorial

When a cluster of releases lands together (for example, a model, a CLI version, and a plugin change on the same day), each combination of old and new is run: model, CLI, and plugin each at old or new, eight cells in total. Each cell is repeated under the same rules as every other cell. This estimates the main effect of each factor and the interactions between them, so a change can be attributed to the model, the CLI, the plugin, or a combination. If a cluster has only two known changes, use the matching 2×2 design and record the unknown factor as a limitation. A fractional design is used only if the cost ceiling forces it, and the lost interactions are recorded.

## Run manifest

Every run records the following fields, and a campaign is invalid if any are missing:

- Model: requested identifier, returned identifier, and any fallback event.
- Plugin: commit SHA and file hash of `plugins/code-review`.
- CLI: version and install channel (stable or latest), plus the bundled prompt version reported by the CLI.
- Effort: the explicit level set on the request.
- Subagent model: the forced model (`CLAUDE_CODE_SUBAGENT_MODEL_FORCE` or equivalent) and the model each subagent reported.
- Permission and auto-mode settings in effect.
- Enabled plugins and MCP servers, and the repository state hash.
- Output mode, timestamps, and token counts by type.

If a setting cannot be held equal across models, the difference is recorded as a known confound and reported next to every affected comparison. One is already expected: Fable 5.2 is documented to have thinking always on and an API default effort of high (source: project brief; unverified). Effort is therefore set explicitly on every request and never left to a default. Whether thinking can be made equivalent across the tested models is something Claude Code must establish from official documentation.

If the Claude Code CLI version must change between campaigns (for example, a new model requires a newer CLI), re-run at least one earlier model on the new CLI as an anchor, so a CLI effect is not mistaken for a model effect.

## Baseline: with and without the plugin

Every model is run on every case both with the plugin and without it. The baseline uses the same model, settings, and case, and a fixed plain review request with no plugin installed. The baseline prompt is written once, versioned, and never tuned per model. Its wording is part of open decision 6.

## Separating the plugin's contribution from the model's

With both conditions on every model, results form a model-by-condition grid:

- **Model effect**: the change in baseline results from one release to the next.
- **Plugin uplift**: with-plugin minus baseline on the same model.
- **Interaction**: the change in plugin uplift from one release to the next. This is what the main hypothesis tests.

A drop in with-plugin recall on a new model is attributed to the plugin only if the baseline did not drop by a similar amount. Where more than one plugin commit is tested, the same grid separates a plugin-change effect from a model-change effect.

## Repeated runs

Each cell is run several times, because both the model and the plugin's multi-agent process are nondeterministic. The number of repeats comes from the pilot and power calculation in document 02, bounded by the cost ceiling (BR-4). Each repeat is an independent session in a fresh environment, and execution order is randomised across cells. Report the spread for every metric, not only the mean. A single run is never evidence of a regression.

Repeated agents are a measurement tool, not a voting panel. Their outputs are scored against the planted-defect list (see the grading rules in document 02), and the result is the detection rate per defect across repeats. Agreement among agents is never treated as proof that a finding is correct.

## Blinding

- The grader receives findings stripped of model identifier, plugin condition, and run identifier, in shuffled order.
- Findings are normalised to one format first, because the plugin's output format would otherwise reveal the condition. Residual cues in wording cannot be fully removed; state this limitation in the report.
- If any human review of grades is done, the reviewer sees the same blinded view.
- Whoever sets thresholds does so before seeing scored results (document 02).

## How a new model release triggers a run

1. Detection: a scheduled check of Anthropic's official model listing, or a manual start. Which one is an implementation choice.
2. Verification: confirm the exact model identifier, that it is callable with the project's credentials, its effort and thinking behaviour, its fallback behaviour, its data-retention terms, and its price, from official documentation.
3. Smoke test: a small number of runs to confirm the harness works with the new model. Smoke results are not scored.
4. Campaign: run the new model in both conditions on the full corpus. Re-run at least one previously tested model as an anchor in the same campaign, so drift in the service, CLI, or harness is visible.
5. Report: compare with stored results and issue the per-release report.

Whether a new plugin commit also triggers a campaign is an open question (document 08).

## Threats to validity

| Threat | Why it matters | Mitigation |
|---|---|---|
| Self-grading | A Claude model grading Claude output may share blind spots or favour familiar phrasing. | Prefer deterministic matching where possible; fix one grader version for all cells; validate the grader against a hand-labelled sample and report its error rate. |
| Agreement mistaken for correctness | Agents from one model share errors, so consensus among them can look like confirmation. | Use agreement only to measure variance or flag cases; score against planted defects; audit a random sample by hand each campaign. |
| Unseparated release changes | A cluster of model, CLI, and plugin changes can look like a single effect. | 2×2×2 cluster design; anchor re-runs; report unknown factors as limitations. |
| Corpus leakage into training | Public corpus cases may enter training data of later models, inflating later results. | Constraints in open decision 4: a held-back portion, canary markers, and the ability to rotate cases. Report results on held-back cases separately. |
| Fallback contamination | A fallback answer credited to the requested model corrupts the comparison. | Disable fallback where possible, detect it always, exclude and count affected runs (TR-5, TR-6). |
| Plugin nondeterminism | Parallel agents and confidence scoring add variance beyond the model's own. (Plugin behaviour per project brief; unverified.) | Repeats; report spread; capture pre-threshold findings where transcripts allow. |
| Effort and thinking settings | Defaults differ by model and can change. | Explicit settings, recorded per request; confounds reported. |
| Price changes | Dollar cost can move with no behaviour change. | Report tokens as the primary cost metric; store the price table used, with date. |
| Planted defects are not natural defects | Results may not transfer to real reviews. | State as a limitation; see corpus constraints. |
| Service drift | The same model identifier may behave differently over time. | Anchor re-runs; timestamps on every request. |
| Small corpus | Wide intervals lead to over-reading noise. | Power calculation; "inconclusive" is a permitted outcome. |
