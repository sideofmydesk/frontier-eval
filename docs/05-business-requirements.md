# 05 Business requirements

Requirements from the project owner's point of view. Priority: **P0** must be met before the first published result; **P1** must be met before the process is called repeatable; **P2** is desirable.

| ID | Requirement | Priority | How it is checked |
|---|---|---|---|
| BR-1 | A repeatable process is run for each new Anthropic model release in the tested families. Starting a campaign for a new model requires changing only the run manifest, not the harness code. | P0 | A second campaign is completed with manifest changes only. |
| BR-2 | A documented target exists for the time from a model's general availability to a published report. The target value is set by the project owner (open question in document 08). | P1 | Elapsed time is recorded per campaign and compared with the target. |
| BR-3 | Each campaign produces a per-release report that states, for each primary metric, one of: pass, regression, or inconclusive, using the thresholds fixed in advance (document 02). The report states the overall outcome on its first page in one sentence. | P0 | Report exists; every status traces to a pre-registered threshold. |
| BR-4 | A cost ceiling per campaign is set by the project owner before the campaign starts. The harness stops starting new runs when projected spend reaches the ceiling, and reports what was left incomplete. | P0 | A test with an artificially low ceiling halts as specified. |
| BR-5 | Cost is a required reported metric: input tokens, output tokens, and dollars, per run, per cell, per model, and per campaign, with the price table and its date. | P0 | Report contains all four levels; totals reconcile with the provider's usage records within a stated tolerance. |
| BR-6 | Results are published in a documented, reproducible format suitable for a public write-up: the run manifest, pre-registration, result schema, aggregated results, and enough raw data for a third party to recompute every reported number. | P0 | A person outside the project recomputes the headline numbers from the bundle. |
| BR-7 | The report states which model actually answered. Runs affected by fallback are counted and shown separately and are never included in a model's results. | P0 | Report has a fallback table per model; spot check of raw logs agrees. |
| BR-8 | Data handling: the corpus contains no sensitive, proprietary, employer-owned, or personal code or data, and no real secrets. All corpus content is either written for this project or used under a licence that permits publication. | P0 | Corpus review checklist signed off before the first run; licence recorded per case. |
| BR-9 | Data handling: Fable requires 30-day data retention and is not available under zero data retention (source: project brief; unverified). The project must run under an account and terms that permit this, and nothing sent to the API may be content that cannot be retained for 30 days. Confirm the current terms before each campaign. | P0 | Retention terms checked and recorded in the campaign log. |
| BR-10 | Unverified facts are not published as fact. Every model date, price, and behavioural claim in a public write-up is checked against Anthropic's official documentation and cited, or is labelled as reported by secondary sources. | P0 | Pre-publication checklist. |
| BR-11 | The plugin's provenance is verified before use. The marketplace also contains plugins not made by Anthropic; the code-review plugin is reported to be first-party (source: project brief), and this must be confirmed for each pinned commit. | P0 | Provenance record per pinned SHA (see TR-2). |
| BR-12 | Public claims are limited to what was measured: this plugin, these commits, these models, this corpus. The write-up describes limitations and does not present results as a general ranking of models. | P1 | Write-up review against the limitations in document 04. |
| BR-13 | Results from earlier campaigns remain comparable. If the corpus, grader, or schema changes, either earlier models are re-run or the report states that comparison across the change is not valid. | P1 | Every cross-campaign comparison names the corpus and grader versions on both sides. |
| BR-14 | The design does not prevent later addition of other first-party plugins, but nothing is built for them now. | P2 | Design review: no component assumes code review except the corpus, grader, and invocation. |
| BR-15 | The repository and all published material contain no personal contact details and no employer-confidential information. | P0 | Pre-publication scan. |

## Reported pricing (unverified)

Source: project brief, from secondary sources. Verify before budgeting.

| Model | Input, per million tokens | Output, per million tokens |
|---|---|---|
| Fable 5.2 | about $8 | about $40 |
| Opus 5 | $5 | $25 |

Prices for other candidate models were not supplied and must be looked up. A multi-agent plugin can use many times the tokens of a single review, so the cost ceiling should be set from pilot measurements, not from these list prices alone.

## Definition of done for the first feature

One campaign completed on the chosen models with both conditions; a per-release report meeting BR-3, BR-5, and BR-7; a public bundle meeting BR-6; and the process documented well enough that BR-1 can be tested on the next release.
