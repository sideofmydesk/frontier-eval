# Deep Dive: For AI Evaluators

This track is for people who build or read evaluations and want to judge whether this one deserves trust. It is candid about what the pilot cannot show.

## The claim under test

**Hypothesis.** Plugins age badly: instructions written for an older model add less value on a newer one.

**Prediction for this pilot.** The plugin's advantage over a plain review prompt is smaller on Claude Fable 5.2 than on Claude Opus 5.5. The plugin's current instructions were adopted in October 2026. Opus 5.5 was released in September 2026 and Fable 5.2 in November 2026.

**What would count against it.** An advantage on Fable 5.2 that is as large as, or larger than, the advantage on Opus 5.5.

**Status.** Exploratory. No thresholds were set in advance, the sample is 15 cases, and the result will be reported as an observation with intervals.

## The design in one table

| | |
|---|---|
| Unit | One review of one pull request |
| Factors | Model (2) × arm (plugin, baseline) × case (15) × repeat (2) = 120 runs |
| Ground truth | Human-curated issue descriptions from a public benchmark |
| Primary measures | Recall and precision against ground truth, by cell |
| Quantity of interest | The difference in (plugin minus baseline) between the two models |
| Grading | Model judge for matching, model checker for unmatched findings, hand-checked sample |

Full detail: [Experimental Design](Experimental-Design).

## The confound you should know about first

The plugin routes its own work. It names a model tier for each subagent, and the session model follows those instructions.

| Session model | Baseline reviewer | Plugin's bug reviewers |
|---|---|---|
| Opus 5.5 | Opus 5.5 | Opus 5.5 |
| Fable 5.2 | Fable 5.2 | Opus 5.5 (as the plugin instructs) |

On Opus 5.5 the arms differ in instructions only. On Fable 5.2 they differ in instructions and in reviewing model. So a smaller plugin advantage on Fable 5.2 has two candidate explanations: the instructions suit the newer model less well, or the plugin simply did not use the newer model.

For a user, those are the same outcome. For the hypothesis, they are different mechanisms. Separating them needs a third arm that forces one model onto every subagent. That arm is planned and is not in the pilot.

We test the plugin as shipped and log the model behind every request, so the routing is reported and not assumed.

## Ground truth and its weaknesses

The corpus is the offline set of the Martian Code Review Bench: 50 real pull requests, 173 golden comments. See [Corpus](Corpus) for the selection reasoning and the alternatives considered.

| Weakness | Consequence | Handling |
|---|---|---|
| Public pull requests and answers | Possible memorisation, likely stronger for newer models | Stated with results. It can bias *toward* the hypothesis: the Fable 5.2 baseline is reviewed by the newest model, which may recall more, while the plugin's bug reviewers are Opus 5.5 in both cells. |
| No clean cases | False-alarm rate on a correct change is unmeasured | Stated. A follow-up set addresses it. |
| Incomplete golden set | Precision is a lower bound | Unmatched findings go to a checker and are reported separately |
| No file or line in ground truth | Matching cannot be deterministic | Model judge with the benchmark's own prompts |
| Two-commit case copies | No repository history available to the reviewer | Departure from the published benchmark, stated in any comparison |

## Grading

- **Judge.** Claude Sonnet 5.5 decides whether a finding and a golden comment describe the same underlying issue, using the benchmark's published prompts so scores are comparable in kind with its leaderboard.
- **Self-grading.** Sonnet 5.5 is not a session model under test, but the plugin uses it for one summary step. That is a weaker independence than a judge from another provider would give.
- **Judge variance.** The benchmark's stored results show the same reviews scoring 0.46 precision under one judge and 0.41 under another. One judge is pinned for the whole pilot.
- **Checker.** A model assesses findings that match no golden comment. A sample of its verdicts is checked by hand and its error rate reported.

## Contamination control

Every run ends in exactly one status: completed, refused, contaminated by fallback, skipped by the plugin, or harness failure. Only completed runs are scored. All are counted.

A request can be answered by a different model than the one asked. We verified that the tool's own run summary does not reveal this, and that per-request body files do. Fallback is disabled for scored runs, so a declined request ends the run. See [Request Logging](Request-Logging).

## What would make this stronger

| Improvement | What it buys |
|---|---|
| Post-cutoff cases with injected bugs and clean controls | Removes leakage, measures false alarms |
| A forced-model arm | Separates instruction effects from routing effects |
| More model generations and the earlier plugin version | A trend, not a two-point comparison |
| Pre-registered thresholds and a power calculation from pilot variance | A confirmatory test |
| A judge from outside the model family | Stronger independence |
