# 06 Technical requirements

Priority: **P0** required before any scored run; **P1** required before the first published result; **P2** desirable. These are constraints on the harness, not a design. The implementation is an open decision (document 07).

## Pinning and provenance

| ID | Requirement | Priority |
|---|---|---|
| TR-1 | The plugin is installed from an exact full-length git commit SHA of `anthropics/claude-plugins-official`, path `plugins/code-review`. Branch names, tags, and "latest" are not accepted. The SHA and a checksum of the installed plugin file tree are recorded per run, and the checksum is verified before each invocation. | P0 |
| TR-2 | Before a commit is used, its source is verified: the repository owner, the plugin's path, its manifest author fields, and the files' contents are reviewed, and the review is recorded. The plugin's files are read before first use, since plugin content runs with the session's permissions. | P0 |
| TR-3 | The model is requested by an exact versioned identifier, not an alias that can move. The requested identifier is recorded per run and per request. | P0 |
| TR-4 | The Claude Code CLI version and the environment image digest are pinned and recorded per run. | P0 |

## Fallback and settings

| ID | Requirement | Priority |
|---|---|---|
| TR-5 | Automatic model fallback is disabled where the platform provides a way to do so. Whether and how it can be disabled is unverified and must be established from official documentation. | P0 |
| TR-6 | Regardless of TR-5, every request logs: requested model, returned model, and a fallback flag set when they differ or when the response otherwise signals a fallback. This covers subagent requests. A run with any fallback request is marked contaminated, excluded from model results, and counted. | P0 |
| TR-7 | Effort is set explicitly on every run and recorded. API or CLI defaults are never relied on. Thinking configuration is set explicitly where configurable and recorded as observed where not. (Fable 5.2 is documented to have thinking always on and default effort high; source: project brief; unverified.) | P0 |

## Capture

| ID | Requirement | Priority |
|---|---|---|
| TR-8 | The full transcript of every run is captured: all messages, all tool calls with inputs and outputs, all subagent sessions, and the final review output, plus token usage, latency per request, wall-clock time per run, and exit status. Raw artifacts are stored unmodified. | P0 |
| TR-9 | Where the transcript exposes findings before the plugin's confidence threshold is applied, they are captured separately from the final findings. If it does not, that is recorded once per plugin commit. | P1 |

## Corpus and isolation

| ID | Requirement | Priority |
|---|---|---|
| TR-10 | The corpus is deterministic: versioned, with a checksum per case and for the whole corpus, verified before each run. The same corpus version yields byte-identical inputs. | P0 |
| TR-11 | Ground truth is never present in the run environment, in file names, in comments, or in git history visible to the review. | P0 |
| TR-12 | Each run executes in a fresh environment created from the pinned image and destroyed afterwards. No state, cache, memory file, user configuration, or other plugin carries between runs. Baseline runs have no plugin installed. | P0 |
| TR-13 | The run environment's network access is limited to the endpoints the run needs. The review cannot reach the ground truth, the results store, or earlier transcripts. | P1 |

## Reliability

| ID | Requirement | Priority |
|---|---|---|
| TR-14 | Retry policy: only harness and infrastructure failures are retried (for example rate limits, timeouts before any output, environment creation errors), with a fixed maximum number of attempts and backoff, both defined in the run manifest. A retry is a new attempt with a new attempt index; the failed attempt's artifacts are kept. A completed run is never retried because of its content. | P0 |
| TR-15 | Every run ends in exactly one status: `completed`, `plugin_failure`, `harness_failure`, `contaminated_fallback`, or `budget_stopped`. `harness_failure` means FrontierEval or its infrastructure failed (setup, checksum mismatch, API unavailable, logging gap, crash of the runner). `plugin_failure` means the environment and API were sound but the review errored, hung past the timeout, or produced no parseable output. Plugin failures count against the plugin in the results; harness failures do not, and are reported separately with their rate. The classification rules are written before scored runs. | P0 |
| TR-16 | A run whose request log is incomplete is a `harness_failure`, because the answering model cannot be confirmed. | P0 |
| TR-17 | The harness enforces the campaign cost ceiling (BR-4) using measured usage and a dated price table. | P0 |

## Secrets and schema

| ID | Requirement | Priority |
|---|---|---|
| TR-18 | API keys and other credentials are supplied at run time from a secret store or environment, never committed, never written to transcripts, logs, run identifiers, or the public bundle. Captured artifacts are scanned for credential patterns before storage in any shared location and before publication. Keys are scoped to this project. | P0 |
| TR-19 | Results conform to a versioned, documented schema. At minimum it has: run record (identifier, all pinned identifiers from TR-1 to TR-4, settings, timestamps, status); request record (TR-6 fields, tokens, latency); finding record (run, location, category, description, severity or confidence if given, pre- or post-threshold); grade record (finding or defect, outcome, grader version); and cost record (tokens, price table reference, dollars). Field names and the storage format are part of open decision 6. | P0 |
| TR-20 | The results store is append-only. Regrading adds grade records under a new grader version and never alters raw artifacts or old grades. | P1 |
| TR-21 | Every number in a report can be regenerated from the results store by a single documented command. | P1 |
| TR-22 | The harness has its own tests, including a check that a deliberately mismatched returned model is flagged as a fallback and that a deliberately corrupted corpus case is rejected. | P1 |
