# FrontierEval planning documents

## Summary

FrontierEval is an evaluation framework that tests Anthropic's official code-review Claude Code plugin against each Anthropic model release, to show whether the plugin still performs as well when the underlying model changes. The first and only feature in scope is the code-review test: a fixed corpus of code with planted defects is reviewed with and without the plugin (pinned by git commit SHA), on several models, with repeated runs, and the findings are graded against ground truth. These documents state the motivation, hypotheses, architecture, experimental design, and requirements. They deliberately leave six choices to Claude Code, listed in `07-open-decisions-for-claude-code.md`.

## Index

| File | Contents |
|---|---|
| `00-README.md` | This index, summary, reading order, conventions |
| `01-introduction.md` | What FrontierEval is, why it exists, scope, glossary |
| `02-hypothesis.md` | Main, null, and secondary hypotheses; what rejects each; how "meaningful change" is fixed in advance |
| `03-architecture.md` | Components, diagram, data flow, run identifiers, reproducibility |
| `04-design-approach.md` | Experimental design, baseline, repeats, blinding, release trigger, threats to validity |
| `05-business-requirements.md` | Owner requirements BR-1 onward, with priorities |
| `06-technical-requirements.md` | Technical requirements TR-1 onward, with priorities |
| `07-open-decisions-for-claude-code.md` | The handoff: six decisions with options, tradeoffs, evidence to gather, constraints |
| `08-risks-and-open-questions.md` | Risk register and open questions (owner field blank) |

## Reading order for Claude Code

1. `01-introduction.md` for scope and vocabulary.
2. `02-hypothesis.md` for what the test must be able to show.
3. `04-design-approach.md` and then `03-architecture.md` for how it is shown.
4. `05-business-requirements.md` and `06-technical-requirements.md` for the constraints every choice must satisfy.
5. `07-open-decisions-for-claude-code.md`. Work through these before writing any code.
6. `08-risks-and-open-questions.md` before the first paid run.

## What to do with these documents

1. Plan first. Resolve each open decision in document 07 by gathering the listed evidence. Record each decision, the evidence, and the date in a decision log.
2. Verify every item marked **Unverified** against Anthropic's official documentation before relying on it or publishing it.
3. Fix the thresholds for "meaningful change" (document 02) and commit them before any scored run.
4. Only then build the harness and run.

## Conventions

- **Unverified** marks a fact that came from secondary sources through the project brief and has not been checked against official Anthropic documentation. Nothing in these documents was checked against official sources at the time of writing, so treat every date, price, and behavioural claim about models or the plugin as unverified unless a later edit says otherwise.
- **Source: project brief** means the fact was supplied by the project owner in the brief for this project.
- "Must" marks a requirement. "Should" marks a strong preference that may be dropped with a recorded reason.
- These documents do not name the model versions, plugin commits, corpus, grading method, or implementation language to use. Where an example identifier appears, it illustrates a format only.
- The project owner is referred to as "the project owner". No personal or employer information belongs in this repository.

## Out of scope for this document set

Test code, other plugins, and any design for features after the code-review test.
