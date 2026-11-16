# 12 Request logging design

Status: **design for review. Nothing here has been run.** Date: 2026-11-15. Covers decision 6 (where the request logger sits) and TR-6, with TR-3, TR-5, TR-7, and TR-16.

No model or API call was made. Every statement about Claude Code or the Claude API comes from official documentation read on 2026-11-15. Source pages are listed in section 9. Each such statement is a claim to test in the spike, not an observation.

## 1. Recommendation

1. **Test Claude Code's own OpenTelemetry export first, with raw API bodies written to files.** It is the only documented method that records, for every request, the model in the request body, the model in the response body, the full `usage` object, and any fallback marker, and that also labels subagent requests.
2. **Run a local logging proxy beside it during the spike, as an independent check.** The telemetry is the client reporting on itself. A proxy sees the traffic. If the two agree on request counts and models across the spike, the campaign can run on telemetry alone and keep the proxy out of the request path.
3. **Use the run's JSON output and session transcripts only as a third reconciliation of totals.** They do not record the requested model.

## 2. What must be recorded

TR-6 requires, for every request including subagent requests: requested model, returned model, and a fallback flag. TR-3 and TR-7 add the requested identifier and effort per request. The plugin review (`docs/10-plugin-review.md`) adds one more need: the plugin tells the session model which model tier each subagent should use, so the log must show which role made each request.

One record per API request:

| Field | Meaning | Needed for |
|---|---|---|
| `run_id` | Harness run identifier | Joining to the manifest |
| `session_id` | Claude Code session | Joining to the transcript |
| `request_id` | Server-assigned request ID | Joining across sources |
| `sequence` | Order within the run | Detecting a mid-run switch |
| `role` | Main thread, a subagent, or auxiliary | Attribution |
| `agent_id`, `parent_agent_id` | Which subagent, and what spawned it | Attribution |
| `agent_type` | Subagent type name | Attribution |
| `expected_model` | What the manifest says this role should run on | Off-target detection |
| `requested_model` | `model` in the request body | TR-3, TR-6 |
| `returned_model` | `model` in the response body | TR-6 |
| `effort` | Effort level sent | TR-7 |
| `thinking` | Thinking configuration sent | TR-7 |
| `stop_reason`, `refusal_category` | How the response ended | Refusal handling |
| `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_creation_tokens` | From `usage` | Cost |
| `usage_iterations` | Per-attempt usage, when present | Fallback, billing |
| `fallback_block` | Whether a `fallback` content block is present | TR-6 |
| `fallback_flag` | Derived. See section 3. | TR-6 |
| `off_target_flag` | Derived. See section 3. | TR-6 |
| `status` | Success, API error, or no response | TR-16 |

## 3. How the flags are defined

A comparison of requested and returned model is necessary but not enough. Two documented behaviours defeat it.

- **Session switch.** After a content-based fallback, Claude Code's documentation says "the session continues on the fallback model." Later requests then ask for the fallback model and receive it. Requested and returned match on every one of them.
- **Sticky routing.** After a server-side fallback, the API can send later turns of that conversation straight to the fallback model, with no `fallback` content block on those turns.

So the log carries two flags.

**`fallback_flag`** is set on a request when any of these is true:

1. `returned_model` differs from `requested_model`.
2. The response content contains a block of type `fallback`.
3. `usage.iterations` contains an entry of type `fallback_message`.
4. Telemetry reports a refusal event for the request with `server_fallback_hop` set to true.

**`off_target_flag`** is set when `requested_model` is not the model the manifest expects for that role. This catches a session that switched models earlier, a subagent that ran on a tier the plugin did not name, and an alias that resolved to an unexpected version.

A run is **contaminated** (TR-6) if any request has `fallback_flag` set, or if any main-thread request has `off_target_flag` set.

Off-target subagent requests need a separate rule, because they may not be faults. The plugin names tiers in prose, and the session model may not follow them. That is a behaviour of the model under test, not of the harness. The proposal is to record it as a measured outcome ("tier compliance") and not to mark the run contaminated. This depends on Q-17.

A run where telemetry is missing or request counts do not reconcile is a **harness failure** (TR-16), not a contaminated run.

## 4. Candidate methods

### Method A: Claude Code OpenTelemetry with raw API bodies

Claude Code can export OpenTelemetry events for its own API requests. The documentation describes these pieces:

- `CLAUDE_CODE_ENABLE_TELEMETRY=1` turns export on. `OTEL_LOGS_EXPORTER` selects `otlp`, `console`, or `none`.
- `OTEL_LOG_RAW_API_BODIES=file:<dir>` writes the untruncated request body and response body of each request to files, and appends one line per successful response to `<dir>/index.jsonl` with `timestamp`, `session_id`, `query_source`, `model`, `request_id`, `message_id`, `message_uuid`, `request_file`, and `response_file`. The index requires Claude Code v2.1.274 or later.
- A `claude_code.api_request` event per request carries `model`, token counts, cache token counts, `cost_usd`, `request_id`, `query_source`, `effort`, and agent and plugin attribution.
- A `claude_code.api_refusal` event fires when a response has `stop_reason: "refusal"`. It carries `model` ("Model identifier from the request"), `server_fallback_hop`, and the category when tool-detail logging is on.
- A `claude_code.api_error` event fires for failed requests.
- A `claude_code.subagent_completed` event carries `model` ("the model the subagent was resolved to run"), `final_model` ("which differs from `model` after a mid-run switch such as a fallback"), and `model_swapped`.
- Events from a subagent carry `agent_id`. `parent_agent_id` requires v2.1.310 or later.

How each required field would be filled:

| Field | Source under method A |
|---|---|
| `requested_model` | `model` in the request body file |
| `returned_model` | `model` in the response body file |
| Token counts, `usage_iterations` | `usage` in the response body file |
| `fallback_block` | Content blocks in the response body file |
| `effort`, `thinking` | Request body file. `effort` is also on the `api_request` event. |
| `role`, `agent_id`, `agent_type` | `query_source`, `agent_id`, and `agent.name` on events, joined by `request_id` |
| Refusals | `api_refusal` event, and `stop_reason` in the response body |
| Failed requests | `api_error` event. The response body event fires only for successful responses. |

Strengths:

- Nothing is added to the request path, so the logger cannot change behaviour or timing.
- It is the only method with documented subagent attribution.
- Bodies also contain each subagent's returned findings before filtering, which may answer Q-12.

Weaknesses and unknowns:

- It is the client's own report. A bug or gap in Claude Code's telemetry would be invisible without a second source.
- The `model` attribute on the `api_request` event is a single field. The documentation does not say whether it is the requested or the returned model. That is why the body files are needed, and why the events alone do not satisfy TR-6.
- The response body file is described as the "Messages API response, including the id, content blocks, usage, and stop reason". Whether this holds for streamed responses, and whether `usage.iterations` is kept, is untested.
- Whether a short non-interactive run flushes all telemetry before the process exits is not stated.
- Body files contain the full conversation, which includes corpus code. They must be stored outside this repository, apart from ground truth (TR-11), and kept out of any published artefact until reviewed.
- Version floor: v2.1.274 for the index file and `effort`, v2.1.310 for `parent_agent_id`, v2.1.318 for the documented subagent fallback behaviour. The pinned CLI must be at least v2.1.318.

### Method B: local logging proxy

Set `ANTHROPIC_BASE_URL` to a proxy on the same machine that forwards to the Claude API and writes each request and response to disk. Claude Code documents the requests it sends through a gateway: inference posts to `/v1/messages?beta=true`.

Strengths:

- Independent of Claude Code's telemetry. It records what was sent and received.
- Sees every request to the API host, whether or not Claude Code logs it.
- Does not depend on Claude Code's telemetry format, which can change between versions.

Weaknesses and unknowns:

- It sits in the request path. The gateway documentation warns that features break when a gateway strips headers or body fields, and that the non-streaming fallback can cause duplicate tool execution behind some proxies. A proxy can change the behaviour being measured.
- Responses are streamed. The proxy must parse server-sent events to recover `model`, `usage`, and content block types.
- It cannot tell which subagent made a request, except by inference from request content.
- The API key passes through it. It must bind to localhost only and must never write headers to disk.
- Some traffic bypasses it. The documentation says the fast-mode availability check "calls `api.anthropic.com` directly rather than following `ANTHROPIC_BASE_URL`". This is not inference traffic, but request counts must allow for it.
- Claude Code may behave differently when `ANTHROPIC_BASE_URL` points away from Anthropic. The documentation notes Remote Control is disabled in that case. Other differences are not ruled out.

### Method C: run output and transcripts

`claude -p --output-format json` returns a result with `total_cost_usd` and a per-model cost breakdown. `--output-format stream-json --verbose` emits one event per message. `--forward-subagent-text` adds subagent messages with a parent tool-use ID. Session transcripts under the configuration directory persist `requestId` on assistant entries.

Strengths: no setup, and it is needed anyway to capture the review output.

Weaknesses: it records the model that answered, not the model requested, so it cannot detect a fallback on its own. The documentation calls the transcript format "internal to Claude Code" and says it "changes between versions". Subagent coverage depends on a flag.

Use: reconcile token totals per model against method A. A mismatch is a harness failure.

### Method D: Usage and Cost Analytics API

Anthropic's Admin API reports usage by model after the fact. It needs an admin credential, is not per request, and lags. It could serve as an after-campaign check of billed totals if the pilot runs in a dedicated workspace. It is not a logging method.

### Not a logging method, but relevant: `claude plugin eval`

Claude Code has a built-in command that runs a plugin against test cases, repeats each case, and compares against a no-plugin baseline. It accepts `--model` and writes a JSON result. This overlaps with the harness the project plans to build. Whether it exposes per-request model logging, supports pinning a plugin by commit, or meets the isolation and blinding requirements is not known. It should be assessed under decision 6 before the harness is built. See Q-26.

### Comparison

| Requirement | A: telemetry with bodies | B: proxy | C: output and transcripts |
|---|---|---|---|
| Requested model per request | Yes, documented | Yes | No |
| Returned model per request | Yes, documented | Yes, by parsing the stream | Yes |
| Token counts per request | Yes | Yes, by parsing the stream | Partly |
| Fallback markers | Yes: body, plus refusal and subagent events | Yes, by parsing the stream | No |
| Subagent requests included | Yes, documented | Yes | With a flag |
| Subagent attribution | Yes, documented | No | Partly |
| Effort per request | Yes | Yes | No |
| Adds a component to the request path | No | Yes | No |
| Independent of Claude Code's self-report | No | Yes | No |
| Stable across CLI versions | Version floors apply | Yes | No |

## 5. Run settings the logger depends on

These make the log interpretable. Each is recorded in the run manifest. All are from documentation and untested.

| Setting | Value | Why |
|---|---|---|
| `--model` | Exact identifier, for example `claude-opus-5-5` | TR-3. Verified identifiers are in `docs/11-verified-facts.md`. |
| `CLAUDE_CODE_EFFORT_LEVEL` | One explicit level for every cell | TR-7. It takes precedence over `--effort` and settings. Opus 5.5 defaults to `medium`, the others to `high`. |
| `CLAUDE_CODE_DISABLE_REFUSAL_FALLBACK=1`, or `switchModelsOnFlag: false` | Set | TR-5. A flagged request then ends the turn with a refusal in non-interactive mode. |
| `--fallback-model` and `fallbackModel` | Not set | Avoids availability-based switching. |
| `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL` | Exact identifiers, if Q-23 is answered yes | Stops the plugin's tier names resolving differently after a CLI update. |
| `CLAUDE_CONFIG_DIR` | A fresh directory per run | TR-12. Keeps settings, transcripts, and plugins per run. |
| Claude Code version | Pinned, at least v2.1.318 | Version floors in section 4. |
| Plugin | Loaded from a checked-out commit with `--plugin-dir`, after its tree hash is verified | TR-1, TR-2. Hashes are in `docs/10-plugin-review.md`. |

With fallback disabled, a refused request gives the run a distinct status, **refused**. It is counted and reported per cell, and excluded from model results, like a contaminated run. Too many refused runs in a cell is the situation decision 2 says to raise with the owner.

Do not set `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` or `DISABLE_TELEMETRY` without checking their effect. Both are documented as turning telemetry off, and whether that includes the OpenTelemetry export is not confirmed.

## 6. What the spike must prove

The spike has a free stage and a paid stage. **The paid stage cannot start until the owner decisions in section 7 of `docs/09-pilot-plan.md` are recorded.**

### Stage 0: no model calls

Point Claude Code at a local stand-in for the API that returns canned streamed responses. No request reaches Anthropic and nothing is billed. This tests the logging pipeline, not the model.

The stand-in returns, in turn: a normal response; a response whose `model` differs from the request; a response with a `fallback` content block and `usage.iterations`; a response with `stop_reason: "refusal"`; and an HTTP error.

Stage 0 passes when:

1. Telemetry export works in a non-interactive run, and every event is on disk when the process exits.
2. Each request the stand-in received has a request body file, and each successful response has a response body file and an index line. Counts match exactly.
3. The response body file for a streamed response contains `model`, `usage`, `stop_reason`, and all content blocks, including `fallback`.
4. The harness derives `fallback_flag` correctly for each canned case.
5. With fallback disabled, the refusal case ends the run with the refused status, and Claude Code sends no retry to another model.
6. A run with telemetry deliberately broken is classed as a harness failure, not a clean run.
7. The proxy's record and the telemetry record agree request for request.

Stage 0 may fail for a reason unrelated to logging: Claude Code may not complete a session against a stand-in. If so, record that and move the checks to stage 1.

### Stage 1: a few paid calls

One small run per model, with a prompt that makes the session start at least one subagent on a different tier. Then one run of the plugin command at each commit against a throwaway pull request. Estimated cost is a few dollars. It must be within the pilot ceiling the owner sets.

Stage 1 passes when:

1. `requested_model` in every main-thread request equals the exact identifier passed to `--model`.
2. `returned_model` is present on every response and equals the requested identifier on a clean run.
3. Subagent requests appear in the log, carry `agent_id`, and join to body files by `request_id`.
4. The request body of a subagent started with a tier name shows which identifier that tier resolved to. This settles how the plugin's "Haiku", "Sonnet", and "Opus" resolve, including the same-family rule for Opus.
5. `effort` is present on every request, including subagent requests, and the spike records what level subagents run at when the session level is set explicitly.
6. Per-model token totals from the log match the per-model breakdown in the run's JSON output.
7. Auxiliary requests that are neither main thread nor subagent are identified and counted separately.
8. The plugin command loads from a checked-out commit in a non-interactive run, and the session's init event lists the plugin with no load errors.
9. The spike records how often the session model followed the plugin's tier instructions.
10. The spike records whether subagent outputs before filtering can be read from the body files (Q-12).

### What the spike cannot prove

- That a real refusal from Anthropic's classifiers appears as documented. A refusal cannot be produced on demand, and the project should not try to provoke one. Stage 0 tests the handling with canned responses. A real one may first be seen in pilot cell P4.
- The fallback rate on corpus content. That is the pilot's job.

## 6a. Stage 0 results (2026-11-15)

Stage 0 was run on 2026-11-15. **No request reached Anthropic and nothing was billed.** Code is in `spikes/request-logging/`. Claude Code v2.1.325 (Windows, SHA-256 of the binary `87e0cb6ae0f4775da388cd3043f4d8097ef961dcddbf55fe90bc61ffc3f57a30`) ran one non-interactive session per scenario against a local stand-in, with a dummy key, a fresh configuration directory, `--model claude-opus-5-5`, `CLAUDE_CODE_EFFORT_LEVEL=high`, and `CLAUDE_CODE_DISABLE_REFUSAL_FALLBACK=1`.

These are observations of one CLI version against canned responses. They show how Claude Code records what it receives. They do not show how the real API behaves.

### Pass criteria

| # | Criterion | Result |
|---|---|---|
| 1 | Telemetry export works in a non-interactive run and is on disk at exit | **Pass, with a change.** The `console` exporter produced no output. Export over OTLP (`http/json`) to a local receiver delivered every event, in runs lasting about one second. |
| 2 | Every request has a request body file; every successful response has a response file and an index line | **Pass.** Counts matched the stand-in's own log in all scenarios. |
| 3 | The response file for a streamed response keeps `model`, `usage`, `stop_reason`, and all content blocks | **Pass.** The `fallback` block and `usage.iterations` were preserved. |
| 4 | `fallback_flag` can be derived for each canned case | **Pass.** See the table below. |
| 5 | With fallback disabled, a refusal ends the run and no other model is contacted | **Pass.** Exit code 1, `is_error: true`, `stop_reason: "refusal"`. Claude Code retried once on the same model and sent nothing to another model. |
| 6 | A run with telemetry off is detectable | **Pass.** It produced no body files and no events while the session itself succeeded. A run with zero body files is a harness failure. |
| 7 | Telemetry and an independent record agree request for request | **Pass** for these scenarios, with the stand-in as the independent record. |

### What each source recorded

| Scenario | Request body `model` | Response body `model` | `api_request` event `model` | Other events | Run result `modelUsage` |
|---|---|---|---|---|---|
| Normal | `claude-opus-5-5` | `claude-opus-5-5` | `claude-opus-5-5` | none | `claude-opus-5-5` |
| Response from another model | `claude-opus-5-5` | `claude-opus-4-8` | `claude-opus-4-8` | none | **`claude-opus-5-5`** |
| Fallback block and iterations | `claude-opus-5-5` | `claude-opus-4-8` | `claude-opus-4-8` | `api_refusal` with `server_fallback_hop: true` | **`claude-opus-5-5`** |
| Refusal | `claude-opus-5-5` (2 requests) | no response file | `claude-opus-5-5` | `api_refusal` with `category: cyber`, `server_fallback_hop: false` | `claude-opus-5-5` |
| HTTP 400 | `claude-opus-5-5` (6 requests) | no response file | none | one `api_error` | empty |

### Findings

1. **The run's own summary hides a fallback.** When the response came from another model, the JSON result still attributed all usage to the requested model. Method C cannot detect a fallback. This is risk R-5 observed.
2. **The `model` attribute on the `api_request` event is the returned model.** The documentation left this open. The requested model is in the request body file and on the `api_request_body` event. Both sources are needed to compare the two.
3. **A refused response gets no response body file and no index line.** Refusals must be read from the `api_refusal` event and the run result, not from the body files.
4. **Failed attempts are under-counted by events.** Six requests were sent in the error scenario, although retries were set to zero. All six have request body files. Only one `api_error` event was emitted. Request counts must come from request body files.
5. **`effort` was `high` on every request and event**, matching `CLAUDE_CODE_EFFORT_LEVEL`. Thinking was sent as `{"type": "adaptive", "display": "omitted"}`.
6. **No `fallbacks` parameter was sent** with refusal fallback disabled. Whether Claude Code sends it when fallback is enabled was not tested.
7. **A fresh configuration directory still loads four bundled plugins** (`cc-plugin-agents-md`, `cc-plugin-telemetry`, `cc-plugin-privacy`, `cc-plugin-plugin-authoring`). They load in both arms. The "no plugin" baseline means "no code-review plugin", not "no plugins".
8. **Main-thread requests are labelled `query_source: "sdk"`** in a non-interactive run, not `repl_main_thread`.
9. Claude Code sends a `HEAD /api/hello` probe to the base URL before the first request. It is not an inference request.

### Changes to the design

- Section 5 gains three settings: `OTEL_LOGS_EXPORTER=otlp`, `OTEL_EXPORTER_OTLP_PROTOCOL=http/json`, and `OTEL_EXPORTER_OTLP_ENDPOINT` pointing at a local receiver. The harness runs that receiver.
- `returned_model` comes from the response body file when one exists, and otherwise from events. `requested_model` always comes from the request body file.
- Run output directories must not sit in a folder synced by a cloud drive. A deletion failed on such a folder during this stage.

### Not covered by stage 0

Subagent requests, alias resolution, the plugin command, and anything about the real API. Those are stage 1.

## 6b. Stage 1 results (2026-11-15)

Stage 1 made the project's first paid calls, on Claude Opus 5.5 only, with Claude Code v2.1.325, effort `high`, and refusal fallback disabled. Runner: `spikes/request-logging/run_real.py`. Per-request log builder: `analyze_run.py`.

Costs below are Claude Code's client-side estimates. They have not been reconciled against the Console's billed usage.

| Run | What | Requests | Time | Estimated cost |
|---|---|---|---|---|
| Smoke (first attempt) | One-word reply | 1, rejected | 1 s | $0.00 |
| Smoke | One-word reply | 1 | 3 s | $0.11 |
| Subagents | Launch a haiku, a sonnet, and an Opus agent | 5 | 9 s | $0.18 |
| Plugin | `/code-review:code-review 1` at `9780cf4` on one corpus case | 32 | 114 s | $0.78 |
| Baseline | Plain review prompt on the same case, no code-review plugin | 8 | 57 s | $0.30 |
| **Total** | | | | **$1.37** |

The first smoke attempt was rejected with HTTP 400 because the API key was not scoped to a workspace. A key scoped to a dedicated workspace fixed it. No tokens were used by the rejected request.

### Pass criteria

| # | Criterion | Result |
|---|---|---|
| 1 | Main-thread requests ask for the exact identifier passed to `--model` | **Pass.** `claude-opus-5-5` on every main-thread request. |
| 2 | The returned model is present and matches on a clean run | **Pass.** A live response reported `claude-opus-5-5`. No fallback, refusal, or error in any run. |
| 3 | Subagent requests are logged, attributed, and joined to body files | **Pass.** Every request had a request and a response body file. Subagent requests carry an agent ID and agent type. |
| 4 | A tier name resolves to a visible identifier | **Pass.** See below. |
| 5 | Effort is on every request, including subagents | **Pass.** `high` on all requests, including Haiku and Sonnet subagents. The session-level setting applies to subagents. |
| 6 | Per-model token totals match the run's own summary | **Pass.** Cost by model from the per-request log equals `modelUsage` in the result, to four decimal places, in all four runs. |
| 7 | Auxiliary requests are identified | **Pass, none seen.** Every request was main thread or subagent. |
| 8 | The plugin loads from a checked-out commit in a non-interactive run | **Pass.** The init event lists `code-review` with no load errors. Files matched the reviewed SHA-256 values. |
| 9 | Tier compliance is recorded | **Pass.** See below. |
| 10 | Pre-filter findings are recoverable (Q-12) | **Yes in principle.** Subagent outputs are in the response body files, and the plugin's final message named a finding it dropped. Extraction is not built. |

### How the plugin's tier names resolved

Asked in the plugin's own wording to launch "a haiku agent", "a sonnet agent", and "an Opus agent", the session model passed the Agent tool's `model` parameter as `haiku`, `sonnet`, and `opus`. The request bodies show:

| Tier named | Identifier requested and returned |
|---|---|
| haiku | `claude-haiku-5-5` |
| sonnet | `claude-sonnet-5-5` |
| opus | `claude-opus-5-5` |

The session was on Opus 5.5, so this does not test the same-family rule for a session on another Opus version, or what "Opus" resolves to in a Fable session.

In the plugin run the session model followed the plugin's instructions exactly:

| Step in the command | Agents launched | Model |
|---|---|---|
| 1. Eligibility check | 1 | `claude-haiku-5-5` |
| 2. Find `CLAUDE.md` files | 1 | `claude-haiku-5-5` |
| 3. Summarise the pull request | 1 | `claude-sonnet-5-5` |
| 4. `CLAUDE.md` compliance (agents 1 and 2) | **0** | not launched |
| 4. Bug review (agents 3 and 4) | 2 | `claude-opus-5-5` |
| 5. Validation | 2 | `claude-opus-5-5` |

The two compliance agents were skipped because the repository has no `CLAUDE.md`, as `docs/10-plugin-review.md` predicted. On a session running Opus 5.5, every review and validation request therefore ran on the session's own model. The plugin and baseline arms differed in instructions, not in reviewing model. That will not hold for a Fable 5.2 session.

### Where the cost goes

| Run | Model | Requests | Cache read | Cache write | Output | Estimated cost |
|---|---|---|---|---|---|---|
| Plugin | Opus 5.5, main thread | 4 | 103,047 | 19,451 | 5,243 | $0.22 |
| Plugin | Opus 5.5, subagents | 13 | 250,641 | 59,675 | 7,143 | $0.49 |
| Plugin | Sonnet 5.5, subagent | 3 | 47,406 | 16,814 | 1,581 | $0.06 |
| Plugin | Haiku 5.5, subagents | 12 | 214,118 | 15,636 | 4,866 | $0.01 |
| Baseline | Opus 5.5, main thread | 8 | 237,355 | 31,810 | 4,903 | $0.30 |

- Uncached input tokens were negligible (2 per request). Almost all input is cache reads and cache writes. The pilot plan's cost model, which used plain input and output prices, does not describe this.
- Each session and each subagent starts by writing Claude Code's own system prompt to the cache: about 22,000 tokens for a session and about 16,000 for a subagent. On Opus 5.5 that is about $0.11 per session and $0.08 per subagent before any work.
- **Runs close together share a cache.** The subagent test started within five minutes of the smoke test and read 38,968 tokens from cache on its first request. Cost per run therefore depends on how runs are spaced. This affects cost measurement, not review quality.

### Other observations

- **Nothing was posted to GitHub.** After both runs the pull request had no comments and no reviews.
- **Permission denials occurred in both arms.** In the plugin run, five `git` commands from a subagent were denied, because the command pre-approves only `gh`. In the baseline, two tool calls were denied. A non-interactive run cannot prompt, so denied calls fail. An interactive user would be asked. The permission policy for scored runs is not yet decided (Q-36).
- **The baseline prompt shapes the baseline.** With the prompt used here the baseline listed 12 issues and the plugin reported 1. The golden set for this case has 6. This is one case and one run per arm, read by hand, and is not a result. It shows that the baseline prompt is a design choice that needs fixing and versioning before scored runs.
- **Effort `high` was my choice for the spike.** Q-24 is still open.

### Sizing implication

On this one case, one plugin run plus one baseline run on Opus 5.5 cost about $1.08. Fable 5.2 sessions will cost more for the main thread and the baseline (list prices are double), while the plugin's subagents stay on the tiers it names. Other cases have larger diffs. A working figure of $3 per case per repeat for both models and both arms, before the judge, is a guess to be replaced by measurement on the first few cases.

## 6c. Fable 5.2 measurement and judge check (2026-11-15)

Before committing to the pilot, the same case was run once per arm on Claude Fable 5.2, and the judge (`harness/judge.py`, Claude Sonnet 5.5, effort `low`, the benchmark's prompts) was run on all four reviews. Read-only tool permissions were allowed in both arms.

| Model | Arm | Requests | Time | Estimated cost | Issues reported | Golden found (of 6) | Unmatched | Judge cost (approx.) |
|---|---|---|---|---|---|---|---|---|
| Opus 5.5 | Plugin | 32 | 114 s | $0.78 | 1 | 1 | 0 | $0.02 |
| Opus 5.5 | Baseline | 8 | 57 s | $0.30 | 12 | 4 | 8 | $0.18 |
| Fable 5.2 | Plugin | 32 | 193 s | $1.80 | 4 | 3 | 1 | $0.06 |
| Fable 5.2 | Baseline | 6 | 63 s | $0.68 | 15 | 4 | 11 | $0.21 |

**This is one case with one run per cell. It is a cost measurement and a check that the pipeline works end to end. It is not a result.**

What it established:

- **Fable 5.2 requests are accepted** on the project's workspace, so the retention requirement is met. Requested and returned model were `claude-fable-5-2` on every main-thread request.
- **In a Fable 5.2 session the plugin's "Opus" agents ran on `claude-opus-5-5`**, as the documentation implied. Of the plugin run's $1.80, $0.91 was Fable 5.2 orchestration and $0.76 was Opus 5.5 subagents.
- **The judge agreed with a hand reading** of the two Opus 5.5 reviews on every golden comment.
- **Judge cost scales with the number of reported issues**, because every issue is compared with every golden comment. A baseline review with 15 issues needed 91 judge calls.
- **Nothing was posted to GitHub**, and the local case checkout was unchanged after all runs.

**Cost per case per repeat, on this case: about $4.00** ($1.08 for Opus 5.5 both arms, $2.48 for Fable 5.2 both arms, about $0.47 for judging). The earlier working figure of $3 was too low. At $4.00, 15 cases with 2 repeats is about $120 before the checker for unmatched findings, against a $150 ceiling of which about $4.30 is spent.

All 15 private pull request copies now exist and match their sources on file count and line counts (`harness/create_case_copies.py`).

## 7. Risks

| Risk | Mitigation |
|---|---|
| Telemetry silently drops requests | Proxy cross-check in the spike. Count reconciliation against run output on every run. |
| Telemetry format changes between CLI versions | Pin the CLI. Re-run stage 0 on any version change. |
| Body files leak corpus content or ground truth | Store outside the repository. Ground truth never enters the run environment. |
| The API key is written to a log | The proxy never writes headers. Check stored files for key patterns before archiving. |
| The proxy changes behaviour | Proxy is used in the spike only, unless telemetry proves unreliable. |
| Session switches model mid-run and per-request comparison misses it | `off_target_flag` against the manifest. |
| Disabling fallback makes too many runs end refused | Measured in pilot cell P4. Raised with the owner per decision 2. |

## 8. Open questions

Numbering continues from Q-25 in `docs/11-verified-facts.md`.

| ID | Question |
|---|---|
| Q-26 | Should `claude plugin eval` be assessed as the basis for the harness before a custom one is built? |
| Q-27 | When the session model does not follow the plugin's tier instruction for a subagent, is the run contaminated, or is this recorded as an outcome? This document proposes an outcome. Depends on Q-17. |
| Q-28 | Where are raw body files stored, for how long, and may any part be published? They contain corpus code. |
| Q-29 | Is a refused run excluded from model results, as proposed here, or scored as a failure to review? |
| Q-36 | Which tool permissions do scored runs grant? In a non-interactive run, calls the plugin does not pre-approve are denied, where an interactive user would be prompted. Numbering here follows Q-35 in `docs/13-corpus-options.md`. |
| Q-37 | What is the fixed wording of the baseline prompt? |

## 9. Sources

All read on 2026-11-15.

| Topic | URL |
|---|---|
| Claude Code monitoring and OpenTelemetry | `https://code.claude.com/docs/en/monitoring-usage` |
| Claude Code model configuration and fallback | `https://code.claude.com/docs/en/model-config` |
| Claude Code subagents | `https://code.claude.com/docs/en/sub-agents` |
| Claude Code non-interactive use | `https://code.claude.com/docs/en/headless` |
| Claude Code CLI reference | `https://code.claude.com/docs/en/cli-reference` |
| Claude Code environment variables | `https://code.claude.com/docs/en/env-vars` |
| Claude Code gateway compatibility | `https://code.claude.com/docs/en/llm-gateway-protocol` |
| Claude Code plugin evals | `https://code.claude.com/docs/en/plugin-evals` |
| Claude API refusals and fallback | `https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback` |
