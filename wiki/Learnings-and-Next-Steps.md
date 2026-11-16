# Learnings and Next Steps

## Was the hypothesis right?

The hypothesis is that **plugins age badly**: instructions written for an older model add less on a newer one.

**Partly.** The first study gives it some support. It does not prove it.

- **What supports it.** The plugin's one advantage is that more of its findings match a known issue. That advantage was +31.9 points on Opus 5.5 and +16.6 points on Fable 5.2. The difference, −15.4 points (−30.1 to −3.2), is clear of zero.
- **What does not.** On known issues found, the plugin did worse than a simple request on both models: −34.9 points on Opus 5.5 and −41.0 on Fable 5.2. The difference between models, −6.1 points (−14.5 to +3.7), could be chance.
- **What we did not expect.** The bigger result is not about ageing. On both models, the plugin found about half as many known issues as just asking, and cost about 1.5 times as much. That was already true on the model the plugin's instructions were written beside.

The question also turned out to be less simple than it looked. "Does the plugin still help on the new model?" assumes the plugin's work is done by the new model. For this plugin, much of it is not. The plugin picks its own models, so one way a plugin can age is by never using the model you upgraded to. On Fable 5.2 reviews, 43% of the plugin's cost went to helpers running on Opus 5.5.

Two models are two points. They cannot show a trend. See [Results](Results) for the numbers and the limits.

## Learnings

The first eight are about method. The last three came from the results.

**1. Read the plugin before designing the test.**
An hour of reading changed the design more than anything else. The plugin names its own models, has a narrower scope than its description suggests, and ships a README that describes a previous version.

**2. "Which model ran?" needs evidence.**
The tool's own summary credited the wrong model when another one answered. If results are attributed to a model, something has to record the model on every request.

**3. Check the defaults.**
Two models in the same family, released two months apart, have different default effort levels. An evaluation that leaves defaults alone is comparing settings.

**4. Test the measuring equipment for free first.**
A scripted stand-in for the API exercised fallback, refusal, and error handling without spending anything, and without having to provoke a real refusal.

**5. Cost models built from list prices are wrong for agents.**
Nearly all input in these runs was cached. Cost was driven by how many sessions and subagents start, not by how much they read.

**6. There is no clean public benchmark for AI code review.**
The best available one has public answers, no clean cases, and no line-level ground truth. Reusing it is still better than inventing one, as long as the limits travel with the numbers.

**7. The baseline is a design decision.**
"Without the plugin" still needs a prompt, and its wording moves the result. It should be fixed, versioned, and published.

**8. Small frictions are real.**
Line-ending conversion on Windows changed the plugin's bytes until it was caught by a checksum. A cloud-synced folder blocked a file deletion mid-run. An organisation-level API key was rejected for lacking a workspace. None is interesting, and each would have cost time later.

**9. A model may not follow the plugin.**
Opus 5.5 skipped the plugin's helper process in 13 of 30 reviews. Those reviews cost a third as much and found about as many known issues.

**10. The test set is missing most of the issues.**
A checker judged 285 findings outside the test set to be real: 123 separate issues, against 53 listed. A second review agreed with 24 of 30 sampled verdicts. Any score built on "matched a known issue" undercounts a thorough reviewer.

**11. Leave the machine awake.**
The run stopped at 113 of 120 when the computer slept. The harness can now pick up where it left off and grade saved reviews without paying for them again.

## Next steps

### Done

The first study is finished and published: 120 reviews, graded, with a check of findings outside the test set and a second review of a sample of that check. One step is still open: comparing the estimated cost (about $136) with the billed amount.

### Next

| Step | Why |
|---|---|
| **People checking a sample of the grading** | Every verdict so far came from an AI model |
| **A leak-free case set**: recent pull requests from after the models' training cutoff, some left clean, some with one injected bug | The current corpus cannot measure false alarms on clean changes or rule out memorisation |
| **A second arm that forces one model onto every subagent** | Separates "the plugin's instructions" from "the plugin's choice of models" |
| **The older plugin version** | Tests whether the October rewrite helped |
| **More models, including earlier ones** | Turns two data points into a trend, which is the original question |
| **Pre-registered thresholds** | Moves from exploratory to confirmatory |
| **Run on every new model release** | The reason the harness exists |
| **Other plugins** | Nothing in the harness is specific to code review except the corpus, the grader, and the prompt |
