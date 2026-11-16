# Deep Dive: For Engineers

This track is for people who use Claude Code or similar agents day to day and want to know how the test works and what it found about the tools themselves.

## What you can use without running anything

**Read your plugins.** The code-review plugin is one Markdown file of instructions. Reading it took an hour and showed that it:

- names a model tier for every subagent ("haiku", "sonnet", "Opus"), so your `--model` choice mostly picks the orchestrator;
- tells its agents not to flag general security issues, or anything that depends on particular inputs or state;
- skips pull requests that are closed, drafts, "trivial", or already commented on;
- no longer uses the 0 to 100 confidence score its README still documents.

Details: [Early Findings](Early-Findings).

**Know how tier names resolve.** In a logged run, the plugin's "haiku", "sonnet", and "Opus" agents ran as `claude-haiku-5-5`, `claude-sonnet-5-5`, and `claude-opus-5-5`. Those aliases follow the newest model in each family and can change when you update Claude Code.

**Set effort explicitly.** Opus 5.5 defaults to `medium`. Fable 5.2 and Opus 5 default to `high`.

**Decide what you want on a flagged request.** By default Claude Code re-runs a request that a safety classifier declines on a different model, and keeps the session there. `CLAUDE_CODE_DISABLE_REFUSAL_FALLBACK=1` makes it stop instead.

## How the harness works

The harness runs the real `claude` binary non-interactively, one fresh session per run, and records every API request.

| Topic | Page |
|---|---|
| Components and the flow of one run | [Architecture](Architecture) |
| Capturing requested model, returned model, tokens, and fallback for every request | [Request Logging](Request-Logging) |
| Preparing pull requests as private two-commit copies | [Corpus](Corpus), "How cases are prepared" |

The logging uses only features Claude Code already has:

| Setting | What it does |
|---|---|
| `CLAUDE_CODE_ENABLE_TELEMETRY=1` | Turns on event export |
| `OTEL_LOGS_EXPORTER=otlp` with `OTEL_EXPORTER_OTLP_PROTOCOL=http/json` | Sends events to a local receiver |
| `OTEL_LOG_RAW_API_BODIES=file:<dir>` | Writes each request and response body to a file |
| `CLAUDE_CONFIG_DIR=<fresh dir>` | Isolates each run |
| `--plugin-dir <checked-out commit>` | Loads the plugin from an exact, hash-verified copy |
| `--max-budget-usd` | Caps each session |

## What a review costs

One pull request (15 files, 555 added lines), Opus 5.5, effort `high`:

| | Requests | Subagents | Time | Estimated cost |
|---|---|---|---|---|
| With plugin | 32 | 7 | 114 s | $0.78 |
| Plain prompt | 8 | 0 | 57 s | $0.30 |

Where the plugin's $0.78 went:

| Model | Requests | Estimated cost |
|---|---|---|
| Opus 5.5, subagents (bug review and validation) | 13 | $0.49 |
| Opus 5.5, main thread | 4 | $0.22 |
| Sonnet 5.5 (summary) | 3 | $0.06 |
| Haiku 5.5 (eligibility, file listing) | 12 | $0.01 |

Almost all input was cached. Each session and each subagent pays to write Claude Code's system prompt to the cache before doing anything: about $0.11 per session and $0.08 per subagent on Opus 5.5. The number of agents drives cost more than the size of the diff.

## Things that bit us

- **Windows line endings.** Git converted the plugin's files on checkout, changing their bytes. A checksum caught it. Export with `git archive` to get exact bytes.
- **Cloud-synced folders.** A sync client blocked a file deletion mid-run. Keep run directories out of synced folders.
- **Organisation-level API keys.** The API rejected a key that was not scoped to a workspace.
- **Unattended permission prompts.** In a non-interactive run, a tool call that would prompt a user is simply denied. Decide your permission rules up front.
- **Console telemetry.** The console exporter printed nothing in a non-interactive run. Exporting to a local receiver worked.
