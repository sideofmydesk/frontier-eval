# 11 Verified facts

Status: **checked against Anthropic's official documentation on 2026-11-15.** Covers Q-13 and the unverified items in BR-9, TR-5, and TR-7.

## How this was checked

- Every fact below was read from a page on `platform.claude.com/docs` or `code.claude.com/docs`. The pages were downloaded as Markdown on 2026-11-15, starting at about 19:40 UTC, and read directly, not summarised by a model.
- **No model or API call was made.** "Verified" here means "stated in official documentation on that date". It does not mean observed in a live response. Section 8 lists what still needs a live call.
- Documentation changes. Re-check before each campaign and record the date, as BR-9 already requires for retention.

Source pages, referred to by letter below:

| Ref | Page | URL |
|---|---|---|
| A | Models overview | `https://platform.claude.com/docs/en/about-claude/models/overview` |
| B | Pricing | `https://platform.claude.com/docs/en/about-claude/pricing` |
| C | Claude Fable 5.2 model page | `https://platform.claude.com/docs/en/models/fable-5-2/overview` |
| D | Claude Opus 5.5 model page | `https://platform.claude.com/docs/en/models/opus-5-5/overview` |
| E | Claude Opus 5 model page | `https://platform.claude.com/docs/en/models/opus-5/overview` |
| F | Model IDs and versioning | `https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions` |
| G | Model deprecations | `https://platform.claude.com/docs/en/about-claude/model-deprecations` |
| H | Refusals and fallback | `https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback` |
| I | Thinking | `https://platform.claude.com/docs/en/build-with-claude/thinking` |
| J | Effort | `https://platform.claude.com/docs/en/build-with-claude/effort` |
| K | API and data retention | `https://platform.claude.com/docs/en/manage-claude/api-and-data-retention` |
| L | Claude Code: Model configuration | `https://code.claude.com/docs/en/model-config` |
| M | Claude Code: Create custom subagents | `https://code.claude.com/docs/en/sub-agents` |
| N | Claude Code: Environment variables | `https://code.claude.com/docs/en/env-vars` |

## 1. Model identifiers

| Model | Claude API identifier | Status | Released | Retirement | Source |
|---|---|---|---|---|---|
| Claude Opus 5.5 | `claude-opus-5-5` | Active (latest) | 2026-09-22 | Not sooner than 2027-09-22 | A, D, G |
| Claude Opus 5 | `claude-opus-5` | Active (legacy) | 2026-07-24 | Not sooner than 2027-07-24 | A, E, G |
| Claude Fable 5.2 | `claude-fable-5-2` | Active (latest) | 2026-11-09 | Not sooner than 2027-11-09 | A, C, G |

Verified points about identifiers (source F):

- These identifiers have no date suffix, and that is the complete, pinned form. From the 4.6 generation on, "the dateless ID is the canonical model ID for that release. It maps to a single, fixed model snapshot."
- They are not moving aliases. The models overview lists the same string in both its "Claude API ID" and "Claude API alias" rows and states that every model ID is a pinned snapshot. This satisfies TR-3 as written.
- Weights are fixed per identifier, but serving infrastructure is not. Page F says the "request router, safety classifiers, and sampling logic" can change and may produce "minor differences in observable behavior even when the model ID and weights have not changed". A pinned identifier does not guarantee identical behaviour across a long campaign. This belongs in the threats to validity in document 04.
- Other platforms use different strings. Amazon Bedrock uses `anthropic.claude-opus-5-5` and `global.anthropic.claude-fable-5-2`. The pilot should record which platform it runs on.

## 2. Prices

US dollars per million tokens, Claude API first-party rates (source B, cross-checked against A).

| Model | Input | Output | Cache read | 5-minute cache write | 1-hour cache write | Batch input / output |
|---|---|---|---|---|---|---|
| Claude Opus 5.5 | $4 | $20 | $0.20 | $5 | $8 | $2 / $10 |
| Claude Opus 5 | $5 | $25 | $0.50 | $6.25 | $10 | $2.50 / $12.50 |
| Claude Fable 5.2 | $8 | $40 | $0.20 | $10 | $16 | $4 / $20 |

The plugin also directs work to Sonnet and Haiku (see `docs/10-plugin-review.md`), so their rates matter for cost:

| Model | Input | Output | Source |
|---|---|---|---|
| Claude Sonnet 5.5 | $2 | $10 | B |
| Claude Haiku 5.5, prompts up to 100,000 tokens | $0.10 | $0.50 | B |
| Claude Haiku 5.5, prompts over 100,000 tokens | $0.50 | $2.50 | B |
| Claude Opus 4.8 (a documented fallback target) | $5 | $25 | B |

Effect on the pilot plan (`docs/09-pilot-plan.md`, section 4):

- The reported prices for Fable 5.2 ($8 in, $40 out) and Opus 5 ($5 in, $25 out) are **confirmed**.
- Opus 5.5 was not priced in the plan. At $4 in and $20 out, the plan's token assumptions give about $0.90 per plugin run and about $0.22 per baseline run on Opus 5.5.
- Those per-run figures assume every token is billed at the session model's rate. That assumption is wrong for plugin runs, because the plugin sends most work to other models. The estimate cannot be fixed without measured token counts per model.
- Claude Code relies on prompt caching, so cache read and cache write rates will apply to a large share of input tokens. The plan's estimate ignores caching.
- Some refusals are billed. See section 3.

## 3. Fallback behaviour and whether it can be disabled

The project documents treat "fallback" as one thing. The official documentation describes it at two levels, and they behave differently.

### 3.1 At the Claude API (source H)

- **Refusals are always on.** Fable 5.2, Opus 5.5, and Opus 5 all run safety classifiers that can decline a request. A decline is an HTTP 200 response with `stop_reason: "refusal"` and a `stop_details.category` of `cyber`, `bio`, `frontier_llm`, `reasoning_extraction`, `general_harms`, or `null`. This is not specific to Fable.
- **Fallback is opt-in at the API.** A refused request is retried on another model only if the caller asks for it: the `fallbacks` request parameter (server-side fallback, in beta), the SDK's client-side middleware, or a manual retry. A plain request with none of these is not silently answered by another model. It returns the refusal.
- **A fallback is visible in the response in three places:**
  - The top-level `model` field "reports the model that produced the returned message, whether that is the requested model or a fallback."
  - A `fallback` content block marks the handover: `{"type": "fallback", "from": {"model": ...}, "to": {"model": ...}, "trigger": {"type": "refusal", "category": ...}}`.
  - `usage.iterations` lists every attempt. The model that served the turn appears as a `fallback_message` entry.
- **Sticky routing.** After a conversation falls back, later requests in it that include `fallbacks` can go straight to the fallback model for about an hour. Such a turn has no `fallback` block. It is identified by the `fallback_message` entry and the `model` field.
- **`fallbacks` does not carry over to subagent calls.** Page H says: "The `fallbacks` parameter does not carry over to model calls made from inside tool execution."
- **Billing.** A refusal before any output is billed when its category is `bio`, `frontier_llm`, or `reasoning_extraction`, and not billed for `cyber`, `general_harms`, or `null`. A mid-stream refusal bills input tokens and the output already streamed. The page says the billed categories may change.
- The page notes that "benign cybersecurity work can also trigger" the `cyber` category. A corpus of planted security defects is exactly that kind of content.

### 3.2 In Claude Code (source L)

Claude Code adds its own behaviour on top. It has **two separate fallback mechanisms**.

**Content-based ("automatic model fallback").** Applies to Fable models, Opus 5.5, Sonnet 5.5, and Opus 5.

| Session or subagent model | Cybersecurity flag re-runs on | Biology flag re-runs on |
|---|---|---|
| Fable models, Opus 5.5 | Opus 4.8 | Opus 5 |
| Opus 5 | Opus 4.8 | No fallback. Ends in a refusal. |
| Sonnet 5.5 | Sonnet 5 | No fallback. Ends in a refusal. |

- "After a fallback, the session continues on the fallback model." The switch is not limited to the flagged request.
- Fallback "can trigger on the first request of a session", because that request carries workspace context such as `CLAUDE.md` content and git status.
- **It can be disabled.** Set `switchModelsOnFlag` to `false` in settings, or set the environment variable `CLAUDE_CODE_DISABLE_REFUSAL_FALLBACK=1` (source N). With switching off, "in non-interactive mode and SDK integrations that can't show the prompt, a flagged request ends the turn with a refusal instead."
- **Subagents.** With automatic switching on, or with no choice saved, a flagged subagent request re-runs on the fallback model and the session's model is unchanged. With switching off, the subagent fails with `Agent terminated early due to an API error`. This behaviour is documented for Claude Code v2.1.318 or later. Earlier versions re-ran the subagent request on a fallback whichever setting was chosen.
- Category-based targets require Claude Code v2.1.219 or later.

**Availability-based ("fallback model chains").** When the primary model is overloaded or unavailable, Claude Code switches to a configured fallback model for the current turn. The page describes this as something the user configures, with `--fallback-model` or the `fallbackModel` setting. It does not state a built-in default chain, and that absence is not confirmed. The chain also applies to subagents.

### 3.3 Answers for the requirements

| Question | Answer | Status |
|---|---|---|
| Does Fable 5.2 fall back automatically? | Not at the bare API. In Claude Code, yes by default, for flagged requests. | Verified from documentation |
| Is this specific to Fable? | No. Opus 5.5 and Opus 5 also refuse and, in Claude Code, also fall back. | Verified from documentation |
| Can it be disabled (TR-5)? | Yes in Claude Code: `switchModelsOnFlag: false` or `CLAUDE_CODE_DISABLE_REFUSAL_FALLBACK=1`. Do not configure a fallback chain. The refusal itself cannot be disabled. | Verified from documentation. **Not tested.** |
| How does a fallback appear (TR-6)? | Returned `model` differs from requested; a `fallback` content block; a `fallback_message` entry in `usage.iterations`. | Verified from documentation. **Not observed.** |
| How often will corpus content be flagged? | Unknown. | **Unverified.** Needs the pilot. |

One consequence for TR-6: comparing requested and returned model on each request is not enough inside Claude Code. After a content-based fallback the session continues on the fallback model, so later requests ask for the fallback model and get it. Requested and returned match, yet the run is off-target. The log must also compare each requested model against the model the manifest expects. See `docs/12-request-logging.md`.

## 4. Thinking behaviour and default effort

| Model | Thinking | Can thinking be turned off? | Default effort (Claude API) | Effort levels | Source |
|---|---|---|---|---|---|
| Claude Fable 5.2 | Adaptive, always on | No. `thinking: {type: "disabled"}` is rejected. | `high` | `low`, `medium`, `high`, `xhigh`, `max` | C, I, J |
| Claude Opus 5.5 | Adaptive, always on | No. `thinking: {type: "disabled"}` is rejected. | **`medium`** | all five | D, I, J |
| Claude Opus 5 | Adaptive, on by default | Yes at effort `high` or below. Rejected at `xhigh` or `max`. | `high` | all five | E, I, J |

Verified points:

- The project brief's claim about Fable 5.2 is **confirmed**: thinking is always on and default effort is `high`. Page C: "Adaptive thinking is always on and can't be turned off. Control thinking depth with the effort parameter."
- **Opus 5.5 defaults to `medium`, one level below Opus 5 and Fable 5.2.** Page J: "Claude Opus 5 and earlier Opus models default to `high`, so a request that omits `effort` runs one level lower on Claude Opus 5.5." A comparison of Opus 5 with Opus 5.5 on defaults would confound model with effort. TR-7 already requires explicit effort. This shows why.
- Opus 5.5 also cannot run without thinking. So among the three models, only Opus 5 has thinking as a configurable setting. Any cell that includes Fable 5.2 or Opus 5.5 must run with thinking on, and Opus 5 should be left on to match.
- Thinking text is hidden by default (`display: "omitted"`) on all three. Thinking is still performed and billed. Transcripts will not contain reasoning unless `display: "summarized"` is requested, and that returns a summary, never the raw reasoning (source I).
- Non-default `temperature`, `top_p`, or `top_k` returns a 400 error on all three (source I). Sampling cannot be fixed or varied by the harness.
- The effort defaults above are the Claude API's. Claude Code applies its own effort resolution. The environment variable `CLAUDE_CODE_EFFORT_LEVEL` "takes precedence over `--effort`, `/effort`", and the settings (source N). After a fallback, Claude Code keeps the effort level of the flagged request (source L).

## 5. Data retention

| Fact | Status | Source |
|---|---|---|
| Claude Fable 5.2 requires 30-day data retention. | **Confirmed** | C, K |
| It is not available under zero data retention "unless expressly authorized by Anthropic". | **Confirmed** | C, K |
| The same applies to Fable 5.1, Fable 5, and the Mythos counterparts ("Covered Models"). | Confirmed | K |
| Opus 5.5 and Opus 5 are not listed as Covered Models. | Confirmed by absence from the list | K |
| A request from an organisation whose retention setting does not meet the requirement returns `400 invalid_request_error`. | Confirmed for the Claude API. The page's example names Claude Fable 5. | K |
| An organisation with a zero-data-retention arrangement can enable 30-day retention for one workspace only, leaving others unchanged. The Default Workspace always follows the organisation setting. | Confirmed | K |

Page K, quoted: "Claude Fable 5.2, Claude Mythos 5.2, Claude Fable 5.1, Claude Mythos 5.1, Claude Fable 5, and Claude Mythos 5 are designated Covered Models... They require 30-day data retention. ZDR is therefore not available for any of them unless expressly authorized by Anthropic."

For other models, the same page says conversation content "is not retained by default", with Covered Models as the exception.

What this does not settle: whether the account the project will use has retention enabled, and whether the owner accepts 30-day retention of corpus content. That is owner decision 2 in section 7 of the pilot plan. It cannot be answered from documentation.

## 6. How Claude Code resolves the model names the plugin uses

The plugin names model tiers in prose (see `docs/10-plugin-review.md`). These facts decide which models actually run.

| Fact | Source |
|---|---|
| On the Anthropic API, the aliases `opus`, `sonnet`, and `haiku` resolve to Opus 5.5, Sonnet 5.5, and Haiku 5.5. Other providers resolve them to older models. | L |
| Aliases "point to the recommended version for your provider and update over time." | L |
| `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, and `ANTHROPIC_DEFAULT_HAIKU_MODEL` set what each alias resolves to. | L |
| When the session model starts a subagent through the Agent tool, the `model` parameter "takes a model alias, not a full model ID". | M |
| Subagent model order: the per-invocation `model` parameter; then the subagent definition's `model` field; then `CLAUDE_CODE_SUBAGENT_MODEL`; then the parent's model. | M |
| Same-family rule: a subagent given a family alias runs on its parent's model when the parent is in that family. A session on an Opus model with a subagent asked for `opus` gets the session's Opus version. | M |
| `CLAUDE_CODE_SUBAGENT_MODEL` with `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` forces one model onto every subagent and stops the session model passing its own choice. Requires v2.1.257 or later. | M |

Consequences, from documentation only:

- Alias resolution depends on the Claude Code version and the provider. A campaign that leaves aliases unpinned can change subagent models by updating the CLI. Pinning the three `ANTHROPIC_DEFAULT_*_MODEL` variables to exact identifiers removes that. See Q-23.
- Under the same-family rule, the plugin's "Opus" agents would run on `claude-opus-5` in an Opus 5 session and on `claude-opus-5-5` in an Opus 5.5 session, but on Opus 5.5 in a Fable 5.2 session.

## 7. Other reported facts from documents 05 and 07

| Claim in the project documents | Finding | Status |
|---|---|---|
| Opus 5.5 released September 22, 2026 | Stated on the model page | **Confirmed** (D) |
| Opus 5 released July 24, 2026 | Stated on the model page | **Confirmed** (E) |
| Fable 5.2 released November 9, 2026 | Stated on the model page | **Confirmed** (C) |
| Opus 4.6 on February 5, 2026; Opus 4.7 on April 16, 2026; Opus 4.8 on May 28, 2026; Fable 5 on June 9, 2026; Fable 5.1 on September 1, 2026 | The deprecations table gives each a "not sooner than" retirement date exactly one year after the reported date. Their model pages were not read. | Consistent, **not directly verified** (G) |
| Opus 4.5 released November 2025, exact date disputed | Identifier is `claude-opus-4-5-20251101`. Retirement is "not sooner than November 24, 2026", which fits a release on 2025-11-24. Its model page was not read. | **Unverified** |
| Opus 4 and Opus 4.1 are retired | `claude-opus-4-20250514` retired 2026-06-15. `claude-opus-4-1-20250805` retired 2026-08-05. | **Confirmed** (G) |
| Claude Code CLI release dates | Not checked | **Unverified** |

Opus 4.5 can be retired from 2026-11-24, nine days after this check. It should not be planned into a campaign. This bears on owner decision 7.

## 8. Still unverified

| Item | Why | What would settle it |
|---|---|---|
| That a live response reports the identifiers in section 1 | No API call was made | One request per model in the pilot smoke test |
| That disabling fallback in Claude Code behaves as documented in non-interactive runs and in subagents | Documentation only | The logging spike |
| That the fallback markers in section 3.1 appear in responses Claude Code receives | Documentation only | The logging spike, with a stand-in upstream |
| Whether Claude Code implements content-based fallback with the server-side `fallbacks` parameter or with its own retry | Not stated on the pages read. A telemetry attribute named `server_fallback_hop` suggests server-side. | The logging spike |
| How often corpus-like content is refused or flagged | Depends on content | Pilot cell P4 |
| Whether the project's account has 30-day retention enabled, and what its terms are | Account-specific | The owner checks the Console |
| Whether the model words in the plugin's prose resolve like aliases, and whether the session model passes them | The documentation covers alias fields, not prose | The logging spike |
| What effort level subagents run at when the session effort is set explicitly | Not confirmed on the pages read | The logging spike |
| Release dates for Opus 4.5 to 4.8 and Fable 5 and 5.1 | Model pages not read | Read each model page |
| Claude Code CLI release dates and the version to pin | Not checked | Claude Code changelog |

## 9. New open questions

Numbering continues from Q-21 in `docs/10-plugin-review.md`.

| ID | Question |
|---|---|
| Q-22 | Should content-based fallback be disabled for scored runs, so a flagged request ends the run with a "refused" status, or left on and flagged as contaminated? Disabling is the stricter reading of TR-5. |
| Q-23 | Should the `opus`, `sonnet`, and `haiku` aliases be pinned to exact identifiers with the `ANTHROPIC_DEFAULT_*_MODEL` variables for the whole campaign? |
| Q-24 | Which explicit effort level do all cells use, given that Opus 5.5 defaults to `medium` and the other two to `high`? |
| Q-25 | Is Opus 4.5 excluded, given retirement can begin on 2026-11-24? |
