# 08 Risks and open questions

## Risks

Likelihood and impact are initial estimates (L low, M medium, H high) to be revised after the pilot.

| ID | Risk | L | I | Mitigation | Related |
|---|---|---|---|---|---|
| R-1 | The plugin changes during a campaign (new commits upstream, or an auto-update inside the environment). | M | H | Install from a full commit SHA; disable marketplace auto-update in the run environment; verify the installed tree's checksum before every run. | TR-1 |
| R-2 | The plugin is not what it is assumed to be: wrong source, or a marketplace entry that is not first-party. | L | H | Provenance check and file review per pinned commit. | TR-2, BR-11 |
| R-3 | The corpus leaks into training data once published, inflating results on later models. | M | H | Held-back portion, canary markers, case rotation, separate reporting for held-back cases. | Decision 4 |
| R-4 | API cost overrun. Multi-agent review multiplies tokens; repeats multiply again. | M | M | Cost ceiling enforced by the harness; pilot-based projection before each campaign. | BR-4, TR-17 |
| R-5 | A fallback answer is attributed to the requested model. | M | H | Per-request logging including subagents; contaminated runs excluded; incomplete logs treated as harness failures. | TR-6, TR-16 |
| R-6 | Fallback is frequent enough on this corpus that too few clean runs remain. | M | M | Measure in the pilot; decide with the project owner whether to adjust the corpus or the repeat count. | Decision 2 |
| R-7 | The grader is wrong, or biased toward one model's phrasing. | M | H | Validate against a hand-labelled sample; publish the error rate; blind the grader; append-only regrading. | Decision 5, TR-20 |
| R-8 | The plugin selects its own model for some agents, so the "model under test" is not the model doing the review. | M | H | Read the plugin's agent definitions at each commit; confirm from request logs which models were called. | Decision 3 |
| R-9 | Settings are not equivalent across models (thinking always on for one model, defaults differ). | H | M | Explicit effort; record observed thinking behaviour; report the confound. | TR-7 |
| R-10 | A tested model is retired, so earlier results cannot be re-run after a corpus or grader change. | M | M | Check deprecation schedules; keep raw artifacts so regrading is still possible. | BR-13 |
| R-11 | Run-to-run variance is larger than any real difference, so every result is inconclusive. | M | M | Pilot and power calculation; accept "inconclusive" as a reportable outcome. | Document 02 |
| R-12 | Ceiling or floor effect: every model finds all, or none, of the planted defects. | M | M | Pilot the corpus for difficulty spread before the first campaign. | Decision 4 |
| R-13 | Harness failures are counted as plugin failures, or the reverse. | M | M | Written classification rules; separate reporting. | TR-15 |
| R-14 | A credential or sensitive content appears in a published transcript. | L | H | Secret scanning before publication; scoped keys; corpus content rules. | TR-18, BR-8 |
| R-15 | Unverified dates, prices, or behaviours are published as fact. | M | M | Pre-publication verification against official documentation. | BR-10 |
| R-16 | The Claude Code CLI changes behaviour between campaigns and is mistaken for a model effect. | M | M | Pin the CLI; anchor re-runs when it must change. | TR-4 |
| R-17 | Service-side behaviour of a fixed model identifier drifts over time. | L | M | Anchor re-runs; timestamps. | Document 04 |
| R-18 | Data-retention or usage terms change, or the account in use does not meet them. | L | H | Check the terms before each campaign and record the check. | BR-9 |
| R-19 | The public write-up is read as a ranking of models or as a statement by Anthropic. | M | M | Limit claims to what was measured; state independence and limitations. | BR-12 |

## Open questions

The owner field is intentionally blank.

| ID | Question | Owner | Needed by |
|---|---|---|---|
| Q-1 | What is the cost ceiling per campaign? | | Before the pilot |
| Q-2 | What is the smallest change in recall, false positives, or cost that would change a recommendation about the plugin? | | Before pre-registration |
| Q-3 | What is the target time from a model's release to a published report? | | Before the second campaign |
| Q-4 | Can automatic fallback be disabled, and how does a fallback appear in a response? | | Before decision 6 |
| Q-5 | Are Fable and Opus results compared with each other, or only within family? | | Before pre-registration |
| Q-6 | Does a new plugin commit trigger a campaign, or only a new model release? | | Before the second campaign |
| Q-7 | Where are results published, and under what licence for the corpus and data? | | Before publication |
| Q-8 | Is the whole corpus published, or is part held back permanently? | | Before decision 4 is final |
| Q-9 | Which account and terms will the runs use, and do they satisfy the reported 30-day retention requirement? | | Before any Fable run |
| Q-10 | Does the plugin's manifest carry any usable version field at the candidate commits? | | During decision 3 |
| Q-11 | Does the plugin pin or prefer a model for its review agents? | | During decision 3 |
| Q-12 | Are pre-threshold findings visible in transcripts? | | During decision 5 |
| Q-13 | Which of the reported release dates and prices are confirmed by official documentation, and what is Opus 4.5's exact date? | | Before publication |
| Q-14 | Is there prior published work testing this plugin across model versions? | | Before publication |
| Q-15 | Who reviews the hand-labelled sample used to validate the grader? | | Before the first scored run |
| Q-16 | When a campaign is inconclusive, is it re-run with more repeats or reported as is? | | Before pre-registration |
