**Six slides, two minutes.** Each slide is a 1600×900 image you can save and drop into your own deck. The bullets beneath each one are the talking points. Click a slide to open the detail behind it.

> **Status (15 November 2026): pilot in preparation.** The method is built and proven on real runs. The scored pilot has not run, so slide 6 is still a question.

---

[![Do your AI plugins age badly? FrontierEval is a repeatable test of whether an AI coding plugin still earns its place each time a new model ships.](images/slide-1-title.png)](Deep-Dive)

- **Coding agents are extended with plugins**, and a plugin is a set of written instructions.
- **Those instructions are written for the models of the day.** Then a new model ships.
- **FrontierEval checks whether the plugin still helps.** Its first subject is the official code-review plugin for Claude Code.

---

[![The problem: the plugin was written for yesterday's model. Timeline: Claude Opus 5.5 released September 2026, the plugin's current instructions adopted October 2026, Claude Fable 5.2 released November 2026. Hypothesis: plugins age badly.](images/slide-2-problem.png)](Experimental-Design)

- **Hypothesis: plugins age badly.** Instructions written for an older model help less on a newer one, and may hold it back.
- **Teams rarely re-check.** A plugin gets installed, seems to work, and stays through several model generations.
- **We have a natural test.** One of our two models was released after the plugin's current instructions were adopted.

*Detail: [Experimental Design](Experimental-Design)*

---

[![What this gives a team: a decision before you upgrade, proof of which model did the work, and a small bill.](images/slide-3-value.png)](Learnings-and-Next-Steps)

- **A decision before you upgrade.** When a model ships, know whether to keep, retune, or drop a plugin.
- **Proof of which model did the work.** Quality and cost are attributed to the model that actually answered.
- **A small bill.** The whole pilot runs under a $150 ceiling. One plugin review cost about 78 cents.

*Detail: [Learnings and Next Steps](Learnings-and-Next-Steps)*

---

[![How to use it: four steps repeated on every model release. Pin, run twice, record, compare.](images/slide-4-how.png)](Architecture)

- **Pin.** Fix the exact model, the plugin version, and the tool version.
- **Run twice.** The same real pull requests, once with the plugin and once with a plain request to review.
- **Record.** Log every request: which model answered, how many tokens, any switch to another model.
- **Compare.** Score both against issues that human reviewers already found.

*Detail: [Architecture](Architecture)*

---

[![What we have found so far: 3 models did the work in one single-model review; 1 versus 12 issues reported by plugin and plain prompt; 0 warnings when a different model answered; a plugin review cost 2.6 times a plain one.](images/slide-5-findings.png)](Early-Findings)

- **The plugin picks its own models.** We chose one model for a review. The plugin sent the work to three.
- **The plugin is selective; a plain prompt is thorough.** On one pull request with 6 known issues, the plugin reported 1 and the plain prompt reported 12.
- **The tool did not flag a model switch.** In testing, its own summary credited the model we asked for when a different one answered.
- **The plugin costs more.** About 2.6 times a plain review on the same pull request.

These are early observations from set-up runs on one pull request. They are not pilot results.

*Detail: [Early Findings](Early-Findings)*

---

[![The result we are waiting for: does the plugin help less on the newer model? Claude Opus 5.5 versus Claude Fable 5.2. Results pending.](images/slide-6-result.png)](Results)

- **The measure:** how much better review is with the plugin than without it, on each model.
- **The prediction:** if plugins age badly, the plugin helps less on the newer model.
- **The test:** 120 reviews of 15 real pull requests, across both models.
- **Not yet run.** This slide will be replaced with the answer.

*Detail: [Results](Results)*

---

## Questions to take to your own team

1. Which plugins or custom instructions do our engineers rely on, and when were they last checked against the model we use now?
2. When we upgrade a model, do our plugins use it, or do they name their own?
3. If a request were answered by a different model than the one we selected, would we know?
4. Do we want an AI reviewer that says little and is usually right, or one that says a lot and needs filtering?
5. What would it cost us to answer these with a measurement? Here it was under $150.

## Go deeper

| If you are | Start at | You will find |
|---|---|---|
| **An engineer using AI coding tools** | [Deep Dive: For Engineers](For-Engineers) | How the harness drives Claude Code, how every request is logged, what the plugin does, where the cost goes |
| **An AI evaluation practitioner** | [Deep Dive: For AI Evaluators](For-AI-Evaluators) | The experimental design, the benchmark and its limits, grading, threats to validity |

All pages: [Deep Dive index](Deep-Dive).
