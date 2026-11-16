# Learnings and Next Steps

## Was the hypothesis right?

The hypothesis is that **plugins age badly**: instructions written for an older model add less on a newer one.

**Not yet known.** The pilot that tests it has not run. This section will be rewritten when it has, and it will say plainly whether the prediction held, failed, or could not be told apart from noise.

What can be said today is that the question turned out to be less simple than it looked. "Does the plugin still help on the new model?" assumes the plugin's work is done by the new model. For this plugin, most of it is not. The plugin picks its own models, so one way a plugin can age is by never using the model you upgraded to.

## Learnings so far

These are about method. They hold whatever the results turn out to be.

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

## Next steps

### To finish the pilot

1. Create the remaining 14 private pull request copies.
2. Build the judge and the checker, and hand-check a sample of their verdicts.
3. Run one case on Fable 5.2 to measure its cost before committing to all 120 runs.
4. Run the pilot inside a short window, so both models see the same serving conditions.
5. Reconcile estimated cost against billed usage.
6. Publish results on the [Results](Results) page, limits included.

### After the pilot

| Step | Why |
|---|---|
| **A leak-free case set**: recent pull requests from after the models' training cutoff, some left clean, some with one injected bug | The current corpus cannot measure false alarms on clean changes or rule out memorisation |
| **A second arm that forces one model onto every subagent** | Separates "the plugin's instructions" from "the plugin's choice of models" |
| **The older plugin version** | Tests whether the October rewrite helped |
| **More models, including earlier ones** | Turns two data points into a trend, which is the original question |
| **Pre-registered thresholds** | Moves from exploratory to confirmatory |
| **Run on every new model release** | The reason the harness exists |
| **Other plugins** | Nothing in the harness is specific to code review except the corpus, the grader, and the prompt |
