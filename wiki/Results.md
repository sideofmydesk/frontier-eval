# Results

> **Placeholder. The scored pilot has not run.** This page describes what will be reported, so the presentation is fixed before the numbers exist. Nothing below is a result.

## What will appear here

### 1. Run accounting

Before any score: how many of the 120 runs completed, and what happened to the rest.

| Model | Arm | Completed | Refused | Fallback | Skipped by plugin | Harness failure |
|---|---|---|---|---|---|---|
| Opus 5.5 | Plugin | | | | | |
| Opus 5.5 | Baseline | | | | | |
| Fable 5.2 | Plugin | | | | | |
| Fable 5.2 | Baseline | | | | | |

### 2. Recall and precision

**Planned chart:** a scatter plot with recall on one axis and precision on the other, one point per model and arm, with interval bars. This is the central picture: it shows the trade between catching more and saying less.

**Planned table:** recall, precision, and their intervals for each of the four cells, under the benchmark's Strict profile (bugs, security, concurrency, data, and API issues).

### 3. Per-case view

**Planned chart:** for each of the 15 pull requests, the number of ground-truth issues found by each arm, side by side. This shows whether a difference is broad or driven by a few cases.

### 4. Findings beyond the ground truth

How many findings matched no golden comment, and how many of those the checker judged real. Reported separately from precision.

### 5. Consistency

**Planned chart:** agreement between the two repeats of each case. A reviewer that finds different things each time is harder to rely on.

### 6. Cost

**Planned chart:** stacked bars of estimated cost per run by model tier (Haiku, Sonnet, Opus, Fable), for each cell. This shows where the plugin's cost goes.

**Planned table:** tokens and estimated dollars per run, and cost per ground-truth issue found.

### 7. Which models did the work

**Planned chart:** for plugin runs, the share of requests and tokens served by each model. This makes visible that a "Fable 5.2 with plugin" run is mostly not Fable.

### 8. Comparison with published numbers

The benchmark stores a prior run that appears to be this plugin (January 2026): precision 0.46, recall 0.38 under its Opus 4.5 judge. Our numbers will be set beside it with the caveats that apply: different date, unknown model and plugin commit, a different judge, and two-commit case copies.

## How to read the results when they arrive

- The run is **exploratory**. No thresholds were set in advance.
- Fifteen cases give wide intervals. A difference inside the intervals is not a finding.
- The cases and their answers are public. Scores may flatter every arm.
- Precision is a lower bound, because the ground truth is incomplete.
