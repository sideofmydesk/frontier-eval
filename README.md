# FrontierEval

**Do the AI plugins your team relies on get worse as the models get better?**

FrontierEval is a small, repeatable test of that question. Its first subject is Anthropic's official code-review plugin for Claude Code, compared with a simple one-paragraph request to review the same pull request, on two current models.

This repository holds the testing programs, the results for every review, and the files that build the paper.

## The first study

**Research Edition 1: Does the Official Code-Review Plugin Still Help?** (Ian J Michel, Side of My Desk LLC, November 2026)

- Summary and charts: https://research.sideofmydesk.com/edition-1/
- Paper: [`paper/paper.pdf`](paper/paper.pdf)
- Video walkthrough: https://youtu.be/nSp_vWTHrMI

Fifteen real pull requests were each reviewed with and without the plugin, on Claude Opus 5.5 and Claude Fable 5.2, twice each: 120 reviews.

| Model | Setup | Known issues found | Findings that matched a known issue | Findings per review | Cost per review |
|---|---|---|---|---|---|
| Opus 5.5 | With the plugin | 31% | 53% | 2.1 | $0.60 |
| Opus 5.5 | Without it | 66% | 21% | 11.3 | $0.41 |
| Fable 5.2 | With the plugin | 32% | 43% | 2.5 | $1.75 |
| Fable 5.2 | Without it | 73% | 26% | 10.1 | $1.14 |

**Read this as a first look.** The study is small, the test set is public, an AI did the grading, and no pass marks were set ahead of time. No person checked the grading. The paper's section "What this study cannot show" lists the limits.

## What is here

| Folder | Contents |
|---|---|
| [`paper/`](paper/) | The paper's LaTeX source, figures, and PDF. `make_generated.py` builds every table from the result files and the bibliography from arXiv's records. |
| [`results/pilot-1/`](results/pilot-1/) | `runs.csv` (one row per review), `summary.json` (scores with ranges, cost by model, and more), the checker's results on findings outside the test set, and the second review of a sample of those. |
| [`harness/`](harness/) | The programs that make the pull request copies, run the reviews, grade them, check unmatched findings, and add up the results. |
| [`spikes/request-logging/`](spikes/request-logging/) | The record-keeping that shows which model answered each request, with a stand-in for the API used to test it at no cost. |
| [`wiki/`](wiki/) | Source for the [wiki](https://github.com/sideofmydesk/frontier-eval/wiki) and the programs that draw the charts. |
| [`docs/`](docs/) | The planning notes written along the way: requirements, the review of the plugin's files, facts checked against Anthropic's documentation, the record-keeping design, the choice of test set, and the survey of earlier work. They are a working record and some early ones are out of date. |

## What is not here

- **The pull request copies.** They are private, because they hold other projects' code. `harness/create_case_copies.py` makes them again from the [Martian Code Review Bench](https://github.com/withmartian/code-review-benchmark) at commit `e616e84`.
- **The test set's answers.** Get them from the benchmark's repository.
- **Raw request and response logs.** They contain the reviewed projects' code.

## Running it yourself

These programs make paid API calls. You need Claude Code, the GitHub CLI, an Anthropic API key, and a GitHub organisation to hold private copies of the pull requests.

1. `harness/create_case_copies.py` makes the pull request copies.
2. `harness/run_pilot.py` runs the reviews, with a spending cap, and grades each one.
3. `harness/checker.py` and `harness/new_issues.py` check the findings that matched no known issue.
4. `harness/aggregate.py` builds the summary.
5. `paper/make_generated.py`, then LaTeX, builds the paper.

What was fixed in place for the first study: Claude Code 2.1.325; plugin commit `9780cf4`; models `claude-opus-5-5` and `claude-fable-5-2`; judge and checker `claude-sonnet-5-5`; effort `high`. The whole study cost about $136.

The programs were written for one study on one Windows machine. Expect to adjust paths.

## How AI was used

This work was done with a great deal of help from Claude Code, Anthropic's AI coding tool. Under the author's direction it wrote these programs, ran the reviews, did the analysis, and drafted the paper and these notes. The tool tested, the models that graded it, and the assistant that helped are all Claude models from one company.

## Licence and contact

The paper, figures, and results are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The code is licensed under the [MIT License](LICENSE), so you are free to use and change it.

Questions and corrections: research@sideofmydesk.com

*FrontierEval is a project of Side of My Desk LLC.*
