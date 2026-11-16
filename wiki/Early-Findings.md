# Early Findings

These came out of preparation: reading the plugin, checking claims against Anthropic's documentation, and testing the logging. None of them is a pilot result. Several changed the design.

## From reading the plugin

The plugin was read in full at two commits before anything was run.

**It is a prompt, not a program.** The whole plugin is a manifest, a licence, a README, and one Markdown file of instructions. There are no scripts, hooks, or agent definition files.

**It names a model tier for every subagent.** The instructions say things like "launch a haiku agent" and "Opus bug agent". The model you choose for your session orchestrates. This was the single most consequential finding for the design.

**The version number does not track behaviour.** The October 2026 rewrite of the review logic landed in one commit with no version field. The next commit added `"version": "1.0.1"` and changed nothing else.

**The October rewrite was substantial:**

| | Before | After |
|---|---|---|
| Review agents | 5, all Sonnet | 4: two Sonnet for guideline compliance, two Opus for bugs |
| History and prior-review agents | 3 | Removed |
| Filtering | Haiku scores each issue 0 to 100; drop below 80 | A validator confirms each issue or it is dropped |
| Flagging bar | "Large bugs" | Will not compile, or "definitely" wrong regardless of inputs |
| Output | Always posts a pull request comment | Prints to the terminal unless `--comment` is passed |

**The README describes the old design.** At the current commit it still documents the 0 to 100 score and the threshold of 80, and tells users to tune a line that is no longer in the command file.

**The plugin's scope is narrower than "find bugs".** It tells its agents not to flag general security issues, or problems that depend on particular inputs or state. A missed injection flaw may be the plugin doing as instructed.

## From checking the documentation

Every claim the project started with was checked against Anthropic's official documentation on 15 November 2026.

| Claim | Finding |
|---|---|
| Model identifiers are stable | Confirmed. `claude-opus-5-5` and `claude-fable-5-2` are pinned snapshots, not moving aliases. |
| Prices per million tokens | Confirmed: Opus 5.5 $4 in and $20 out, Fable 5.2 $8 in and $40 out |
| Fable 5.2 thinking is always on | Confirmed. The same is true of Opus 5.5. |
| Fable 5.2 needs 30-day data retention | Confirmed |
| Fallback is a Fable behaviour | **Wrong.** Opus 5.5 and Opus 5 also decline flagged requests, and Claude Code re-runs those on another model too. |
| Fallback cannot be controlled | **Wrong.** Claude Code has a setting and an environment variable that disable it. |
| Default effort is the same across models | **Wrong.** Opus 5.5 defaults to `medium`; Fable 5.2 and Opus 5 default to `high`. |

Two of those corrections would have distorted results if missed. Leaving effort at its default would have compared a `medium` model with a `high` one. Assuming fallback was a Fable-only concern would have left Opus runs unchecked.

One more caution from the documentation: a pinned identifier fixes the model's weights, not the serving infrastructure around it. Anthropic notes that routers and classifiers can change and produce small differences in behaviour. Comparisons should be run close together in time.

## From testing the logging

Covered in detail on the [Request Logging](Request-Logging) page. The headline:

> When a different model answered a request, Claude Code's own run summary still credited the model that was asked.

## From one case

One pull request was reviewed once with the plugin and once without, on Opus 5.5. It adds a feature to Cal.com and has six issues in the benchmark's ground truth.

| | With plugin | Baseline |
|---|---|---|
| Issues reported | 1 | 12 |
| Of those, in the ground truth (read by hand) | 1 | about 4 |
| Candidates dropped after validation | 1 | not applicable |
| Estimated cost | $0.78 | $0.30 |

**This is an anecdote.** One case, one run per arm, matched by hand rather than by the judge. It is here because it shows the shape of the question. The plugin was more selective and missed more. The baseline caught more and said much more. Which of those is better depends on what a team wants from a reviewer, and that trade-off is what the pilot will put numbers on.
