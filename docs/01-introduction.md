# 01 Introduction

## What FrontierEval is

FrontierEval is an evaluation framework. It measures how a Claude Code plugin performs on a fixed task when the underlying Anthropic model changes. It produces a per-release report that says whether the plugin's performance held, improved, or regressed relative to earlier releases and relative to using the same model without the plugin.

## Why it exists

Three observations motivate the project. They are motivation, not established results about this plugin.

1. Plugins can encode workarounds for a specific model. A plugin's instructions may compensate for weaknesses of the model it was written against. A newer model may make some of those instructions redundant, or the instructions may now hold the model back. Research on agent harnesses and skills reports this pattern. No published study that the project owner is aware of tests Anthropic's code-review plugin across model versions. (Source: project brief. The absence of such a study is unverified; Claude Code should do a brief literature check before any public write-up claims novelty.)
2. The plugin cannot be pinned by manifest version. Anthropic's first-party plugins are not versioned in their manifests in a usable way, so the plugin must be pinned by git commit SHA from the `anthropics/claude-plugins-official` repository, where it lives under `plugins/code-review`. (Source: project brief. Unverified; confirm by reading the manifest at the chosen commits.)
3. The model that answers is not always the model requested. Some Fable requests can be answered by a fallback model when flagged. A result is only attributable to a model if the log shows that model actually answered. (Source: project brief. Unverified.)

## The first feature

The first feature is the code-review test. It runs the code-review plugin over a corpus of code containing planted defects, on a set of model releases, and grades the reported findings against ground truth. The same corpus is also reviewed without the plugin so that the plugin's contribution can be separated from the model's.

## Scope

In scope:
- The code-review plugin from `anthropics/claude-plugins-official`, pinned by commit SHA.
- Comparison across Anthropic model releases in the Opus and Fable families. Which versions is an open decision.
- A with-plugin and a without-plugin condition on each model.
- Metrics: detection recall, false positives, token usage and cost, run time, stability across repeated runs, and fallback incidence.
- A repeatable process triggered by each new model release, and a publishable, reproducible result format.

Out of scope:
- Other plugins, first-party or third-party. They may come later; do not design for them now beyond not blocking them.
- Evaluating models from other vendors.
- Modifying or improving the plugin. FrontierEval observes it.
- Judging code-review quality on real, private, or proprietary code.
- General model benchmarking unrelated to the plugin.

## Glossary

- **Plugin**: a Claude Code extension packaged for a marketplace, which can contain commands, agents, skills, and hooks. Here, the code-review plugin under `plugins/code-review`.
- **Harness**: the FrontierEval software that sets up an environment, invokes Claude Code, and collects the output. Distinct from the plugin under test. In the motivating research, "harness" also means the scaffolding around a model in general; these documents use it only for FrontierEval's own runner unless stated.
- **Model release**: a distinct, publicly callable model version identified by a specific model identifier, not a moving alias.
- **Pinning by SHA**: fixing the plugin to the exact contents of one git commit, identified by its full commit hash, so that every run uses byte-identical plugin files.
- **Fallback**: the service answering a request with a model other than the one requested. A fallback is detected by comparing the requested model with the model reported in the response.
- **Planted defect**: a defect deliberately introduced into corpus code, with a recorded location, type, and description.
- **Ground truth**: the authoritative record of planted defects for each corpus case, against which findings are graded. It also records which cases have no planted defect.
- **Finding**: one issue reported by a review run.
- **Cell**: one combination of model, plugin condition, and corpus case. A cell is run several times.
- **Baseline**: the without-plugin condition on the same model and corpus.
