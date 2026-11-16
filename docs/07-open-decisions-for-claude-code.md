# 07 Open decisions for Claude Code

This is the handoff document. The project owner has explicitly left the six decisions below to Claude Code. These documents do not make them. For each one: gather the evidence, choose, and write the choice, the evidence, and the date in a decision log before building on it. Stop and ask the project owner only where a decision would breach a constraint or the cost ceiling.

## Open decisions for Claude Code

### Decision 1: Which Opus model version(s) to test against

Reported release dates (source: project brief, from secondary sources; **unverified**; verify against Anthropic's official documentation before publishing):

| Model | Reported release |
|---|---|
| Opus 4.5 | November 2025 (sources disagree on the exact date) |
| Opus 4.6 | February 5, 2026 |
| Opus 4.7 | April 16, 2026 |
| Opus 4.8 | May 28, 2026 |
| Opus 5 | July 24, 2026 |
| Opus 5.5 | September 22, 2026 |

Opus 4 and Opus 4.1 are reported retired and not callable. Do not plan to use them unless a live call proves they are reachable.

Options and tradeoffs:
- **Latest only.** Cheapest; gives a current baseline but no cross-version comparison within Opus, so it cannot test the main hypothesis alone.
- **Latest plus one older anchor.** Modest cost; one comparison; sensitive to the choice of anchor.
- **Every callable version.** Best view of trend; highest cost; older models may be retired mid-project.
- **Versions bracketing plugin commits** (the model current when each chosen commit was written, plus later ones). Most directly tests "instructions written for an older model"; depends on decision 3.

Evidence to gather: the official model list and deprecation schedule; a live call per candidate confirming the exact identifier and that the response reports that identifier; price per candidate; which effort and thinking settings each supports; which Claude Code CLI versions support each.

Constraints: at least two releases in total across decisions 1 and 2, or no comparison exists; exact versioned identifiers only (TR-3); effort settable explicitly (TR-7); projected cost within the ceiling (BR-4); no model with a scheduled retirement before the campaign can finish.

### Decision 2: Which Fable model version(s) to test against

Reported release dates (same source and status, **unverified**): Fable 5 on June 9, 2026; Fable 5.1 on September 1, 2026; Fable 5.2 on November 9, 2026.

Options: the same four as decision 1. An additional question is whether Fable and Opus results are compared with each other or only within family. Cross-family comparison is of interest but carries more confounds (thinking behaviour, effort defaults, price).

Evidence to gather: everything in decision 1, plus: the documented fallback behaviour, whether fallback can be disabled, and how a fallback appears in a response; whether thinking can be configured or is always on (reported always on for Fable 5.2, with default effort high; unverified); the current data-retention terms (reported: 30-day retention required, not available under zero data retention; unverified); the measured fallback rate on a pilot using corpus-like content, since code containing security defects might be flagged more often.

Constraints: BR-9 retention terms satisfied by the account in use; fallback logged per request (TR-6); if the pilot fallback rate would leave too few clean runs per cell, raise it with the project owner before proceeding.

### Decision 3: Which plugin commit SHA(s) to test, and how to choose them

Options and tradeoffs:
- **Current head only, pinned at campaign start.** Simplest; tests what users get today; cannot show whether plugin changes tracked model changes.
- **Head plus the earliest usable commit.** Shows total drift; the earliest commit may not run on the pinned CLI.
- **Commits where the plugin's prompts, agents, or thresholds changed materially.** Most informative; needs a reading of the history; cost grows with each commit.
- **The commit current at each tested model's release date.** Reconstructs what users had at the time; adds a full grid of model by commit.

Evidence to gather: the commit history restricted to `plugins/code-review` (dates, authors, diffs); which commits change instructions, agent definitions, model selection, or the confidence threshold rather than documentation; whether the plugin itself names a model for its agents, which would override the model under test and must be understood before any run; whether each candidate installs and runs on the pinned CLI; provenance for each (TR-2).

Constraints: full SHA (TR-1); provenance verified and files read before use (TR-2, BR-11); the commit set is frozen for the campaign; cost within the ceiling.

### Decision 4: Design of the test corpus

To decide: what code, which languages, which planted defects, how many cases, how many clean cases, and the form the review target takes (for example a diff or pull request versus whole files), which depends on what the plugin expects as input.

Options and tradeoffs:
- **Purpose-written synthetic code.** Full control and clean licensing; may be unrealistically easy.
- **Open-source code with defects injected.** Realistic context; the base code is probably in training data; licence checks needed.
- **Historical real defects re-introduced.** Most realistic; highest leakage risk, since fixes are public.
- **A mix, with a held-back private portion.** Balances realism and leakage; more work.

Evidence to gather: the plugin's expected input and the defect categories it claims to cover; a pilot showing cases are neither all found nor all missed (ceiling or floor effects make every comparison uninformative); pilot variance, to size the corpus with the power calculation in document 02.

Constraints: no sensitive, proprietary, personal, or employer-owned code and no real secrets (BR-8); publishable licence per case; deterministic and checksummed (TR-10); ground truth held outside the run environment and not inferable from file names or comments (TR-11); includes cases with no planted defect so false positives are measurable; each planted defect has a recorded location, category, and rationale; a held-back portion and canary markers for leakage; nothing that must not be retained for 30 days (BR-9); the corpus may contain real defects that were not planted, and the grading design must say how those are treated.

### Decision 5: How findings are graded and matched against ground truth

Options and tradeoffs:
- **Deterministic matching on location and category.** Reproducible and free of self-grading; brittle when a finding describes the right defect at a nearby line.
- **Model-based judging.** Flexible; introduces self-grading bias and its own variance and cost.
- **Human grading.** Most trusted; slow and does not scale to every release.
- **Hybrid** (deterministic first, a judge or human for the remainder). Often the practical choice; more moving parts.

Evidence to gather: a hand-labelled sample of real pilot findings to measure any grader's agreement with a human; the plugin's actual output format; whether pre-threshold findings are visible in transcripts.

Constraints: the plugin reportedly uses multiple parallel agents and a confidence threshold that may filter findings (unverified). Grading must therefore distinguish, where transcripts allow, a defect never raised from one raised and then filtered, and must handle duplicate findings of one defect from several agents without double counting. The same grader version scores every cell in a comparison. The grader is blind to model and condition. Rules exist for partial matches, for one finding covering two defects, and for true defects that were not planted. The grader's measured error rate is published. If a model judge is used, it is pinned, its fallback is logged like any other request, and the choice of judge model is justified against self-grading.

### Decision 6: Harness implementation, language, and repository layout

To decide: the language; how Claude Code is invoked non-interactively; how the plugin is installed from a commit; where the request logger sits; the isolation mechanism; the results store format; the baseline prompt; the repository layout for code.

Options and tradeoffs (examples, not a complete list): driving the CLI in headless mode versus using an agent SDK; a logging proxy versus Claude Code's own telemetry versus transcript parsing for the request log; containers versus virtual machines versus hosted CI runners for isolation; flat files versus a database for results.

Evidence to gather: current official Claude Code documentation for non-interactive use, plugin and marketplace installation from a git reference, model and effort selection, and telemetry; a spike proving that requested and returned models can be captured for subagent requests; a spike proving that a plugin can be installed from an exact commit and its checksum verified.

Constraints: all of document 06; document 03's component contracts; campaigns startable from a manifest change alone (BR-1); nothing specific to code review outside the corpus, grader, and invocation (BR-14); these planning documents stay in `docs/` under their current names.

## Suggested order

Decisions 3 and 6 need early spikes, because the plugin's input format and the logging mechanism shape decisions 4 and 5. Decisions 1 and 2 can be finalised last, once pilot costs are known.
