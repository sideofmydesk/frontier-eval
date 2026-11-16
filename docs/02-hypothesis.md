# 02 Hypotheses

All hypotheses compare results on the same corpus with the same settings. "Plugin uplift" means the with-plugin result minus the without-plugin (baseline) result on the same model. Each threshold written as T-something below is a number that must be fixed before scored runs (see "Deciding what counts as meaningful").

## Main hypothesis (H1)

For a fixed plugin commit, the plugin uplift in detection recall is not the same across model releases: on at least one pair of tested releases, the uplift differs by more than T-recall.

The motivating expectation is that uplift shrinks on newer models, because instructions written for an older model become redundant. H1 is stated two-sided so that an increase is also reported.

- Rejects H1: for every pair of tested releases, the difference in uplift lies within plus or minus T-recall, with an interval estimate that excludes larger differences.
- Inconclusive: intervals are too wide to place the difference inside or outside the threshold. Report this as inconclusive, not as support for either side.

## Null hypothesis (H0)

Plugin uplift in detection recall is equal across the tested model releases, within plus or minus T-recall. H0 is rejected when at least one pairwise difference in uplift exceeds T-recall and the pre-registered statistical test excludes zero difference at the pre-registered error rate.

## Secondary hypotheses

| ID | Hypothesis | Result that rejects it |
|---|---|---|
| H2 Recall with plugin | With the plugin, recall on planted defects on a newer release is not lower than on the previous release by more than T-recall. | Recall drops by more than T-recall between consecutive releases. This is the regression signal used in the per-release report. |
| H3 False positives | With the plugin, the number of false-positive findings per case does not rise by more than T-fp between consecutive releases. | The rise exceeds T-fp. |
| H4 Harmful plugin | On every tested release, with-plugin recall is at least baseline recall minus T-recall. | On any release, the plugin lowers recall by more than T-recall relative to baseline. |
| H5 Token cost | With-plugin token usage per case (input and output counted separately) and cost per case change by less than T-cost between consecutive releases. | Change exceeds T-cost. Report tokens and dollars separately, because price changes move dollars without any behaviour change. |
| H6 Run time | With-plugin wall-clock time per case changes by less than T-time between consecutive releases. | Change exceeds T-time. |
| H7 Stability | Across repeated runs of the same cell, the spread of recall and of finding count on a newer release is no greater than on the previous release by more than T-var. | Spread grows by more than T-var. |
| H8 Threshold filtering | The share of planted defects that a review agent raised but the plugin's confidence threshold removed from the final output does not differ across releases by more than T-filter. | The share differs by more than T-filter. Testable only if transcripts expose pre-threshold findings; if they do not, record H8 as untestable. The plugin's use of parallel agents and a confidence threshold is from the project brief and unverified. |

Every hypothesis is evaluated only on requests answered by the requested model. Runs with a detected fallback are excluded from hypothesis tests and counted separately.

## Deciding what counts as meaningful

Thresholds must be fixed before any scored run, so that they cannot be tuned to the result.

1. Run a pilot on a small part of the corpus: repeated runs of identical cells. Pilot data is never used in hypothesis tests.
2. From the pilot, estimate the run-to-run noise floor for each metric.
3. Set each threshold to the larger of (a) a multiple of the noise floor chosen so that the planned number of repeats can detect it, and (b) the smallest change the project owner would act on. As a starting point for (b), ask the project owner: "How many additional missed defects per hundred would make you stop recommending the plugin on a new model?"
4. Choose the statistical test, the error rate, the correction for multiple comparisons, and the number of repeats per cell. Record the power calculation. "No meaningful change" claims must use an equivalence test (two one-sided tests, TOST) against the pre-set margin. A non-significant difference test alone is never reported as "no change."
5. Commit all of this in a pre-registration file with a timestamp before the first scored run. Any later change is a recorded deviation and is disclosed in the report.

## Measuring a result from repeated runs

- Each run is an independent session in a fresh environment. A run never reuses another run's state.
- For each planted defect, the detection rate is the share of that cell's runs that raised it. Cell-level recall is the mean of those rates across defects, reported with its spread.
- Findings are matched to planted defects by a deterministic rule first (defect identifier, file, and line range). Only findings the rule cannot place go to an LLM grader, and every such match is logged with the grader's rationale.
- A human audits a random sample of matches each campaign. The grader's error rate on that sample is reported. If it exceeds the pre-registered limit, the LLM-grading step is withdrawn for that campaign.
- Agreement among several agents is not evidence on its own. Agents from the same model share its errors, so their agreement measures variance, not correctness. Agreement can be used to flag cases for review, never to establish that a finding is correct.
- Intervals come from a mixed-effects model with corpus items as a random effect, or from a bootstrap over items where the model is not practical. Report intervals, not single scores.

## Cluster experiments

When several components change together (a release cluster), the factorial design in document 04 is used so that each factor's effect can be estimated separately. Its thresholds and repeat counts are pre-registered like any other hypothesis here. Single-factor comparisons are used for routine checks between clusters.

## What the hypotheses do not claim

They do not claim the plugin is good or bad at code review in general, only how its measured performance on this corpus moves across releases. They say nothing about defect types absent from the corpus.
