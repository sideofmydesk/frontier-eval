# 15 Related work

Status: **literature search, 2026-11-16.** Three research passes searched for prior work. Summaries below are from abstracts, read through a fetch-and-summarise tool, so the one-line descriptions of findings still need checking against each paper before they are quoted.

**Existence check done.** All 63 arXiv identifiers cited here were looked up through arXiv's own API on 2026-11-16. Every one exists, and its title and first author match the entry below. The retrieved titles, author lists, and dates are saved in `paper/arxiv-metadata.json` and should be the source for the bibliography. Non-arXiv items (the METR note, blog posts, software, workshop posters) were not independently checked.

arXiv identifiers resolve at `https://arxiv.org/abs/<ID>`.

## Is this work novel?

**No prior work was found with this exact design:** a fixed, vendor-shipped prompt scaffold or plugin, run unchanged on successive model releases, against a plain-prompt baseline. Nothing was found on code-review plugins specifically.

The idea itself is not new. Several papers ask whether prompting techniques or scaffolds lose value on newer models, and the paper must cite them and say plainly how it differs.

### Closest prior work

| Work | What it did | How this study differs |
|---|---|---|
| Rudyk, Oertel, Hebig. *Aging of Prompt Engineering Techniques Across LLM Versions.* ICSME 2026. arXiv:2608.24641 | Five generic prompting techniques on three older and newer model pairs. Newer GPT models show diminishing or negative gains; Qwen still benefits. | Tests generic techniques, not a shipped artefact. Closest in framing to the hypothesis. |
| Salsabil, Saha, Dristi, Phair, Mozumder, Dwyer, Elbaum. *What Survives the Next Model? Benchmarking LLM-Based Techniques Against Single-Prompts.* arXiv:2609.00468 (2026) | For 37% to 63% of 35 ICSE 2026 tool papers, one auto-generated prompt on a newer model beat the tool. | Academic tools, not a vendor plugin; not the same tool on two generations. Closest in design. |
| Jurkovic. *Measuring Time Horizon using Claude Code and Codex.* METR research note, 13 February 2026 | Vendor scaffolds did not beat METR's default scaffolds for Opus 4.5 or GPT-5; neither difference was significant. | One model generation; not a plugin. |
| Gloaguen, Mündler-Sasahara, Müller, Raychev, Vechev. *Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?* arXiv:2602.11988 (2026) | Context files generally did not raise success and added over 20% cost. | Context files, not a multi-agent plugin. |
| Li et al. *SkillsBench: Benchmarking How Well Agent Skills Work Across Diverse Tasks.* arXiv:2602.12670 (2026) | Curated skills raise average pass rate from 33.9% to 50.5%. | Evidence that skills can help. Not across model generations. |
| Ying, Ai, Tang, Liu, Cao. *OpenSkillEval: Automatically Auditing the Open Skill Ecosystem for LLM Agents.* arXiv:2605.23657 (2026) | Many popular community skills fail to beat no-skill agents consistently. | Community skills, not a first-party plugin. |

### Evidence against the hypothesis, which the paper must report

- Cho. *It's Not the Capability: Harness Sensitivity Is Non-Monotone Across LLM Agent Tiers.* arXiv:2605.26731 (2026). Harness effects do not shrink steadily with capability.
- A Tessl blog post (grey literature) reports 21 agent skills gave about the same uplift on two successive Kimi models.
- SkillsBench, above, finds curated skills help.

## A. Prompts and scaffolds as models change

**Prompt sensitivity**

- Sclar, Choi, Tsvetkov, Suhr. *Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design or: How I learned to start worrying about prompt formatting.* ICLR 2024. arXiv:2310.11324.
- Mizrahi, Kaplan, Malkin, Dror, Shahaf, Stanovsky. *State of What Art? A Call for Multi-Prompt LLM Evaluation.* TACL 2024. arXiv:2401.00595.
- Meincke, E. Mollick, L. Mollick, Shapiro. *Prompting Science Report 1: Prompt Engineering is Complicated and Contingent.* arXiv:2503.04818 (2025).

**Drift across model versions**

- Chen, Zaharia, Zou. *How is ChatGPT's behavior changing over time?* arXiv:2307.09009 (2023).
- Ma, Yang, Kästner. *(Why) Is My Prompt Getting Worse? Rethinking Regression Testing for Evolving LLM APIs.* arXiv:2311.11123 (2023).
- Tripathi, Nema, Halder, Qiao, Jindal. *Prompt Migration: Stabilizing GenAI Applications with Evolving Large Language Models.* arXiv:2507.05573 (2025).
- Wang, Liu, Wang, Li, Wei, Liu, Bao. *PromptBridge: Cross-Model Prompt Transfer for Large Language Models.* arXiv:2512.01420 (2025).

**Elaborate prompting helps less on stronger models**

- Meincke, E. Mollick, L. Mollick, Shapiro. *Prompting Science Report 2: The Decreasing Value of Chain of Thought in Prompting.* arXiv:2506.07142 (2025).
- Wang, Sun, Gong, Ye, Chen, Zhao, Liang, Hao. *Do Advanced Language Models Eliminate the Need for Prompt Engineering in Software Engineering?* arXiv:2411.02093 (2024).
- Khan. *You Don't Need Prompt Engineering Anymore: The Prompting Inversion.* arXiv:2510.22251 (2025). Single author, one benchmark.
- Nori, Usuyama, King, McKinney, Fernandes, Zhang, Horvitz. *From Medprompt to o1: Exploration of Run-Time Strategies for Medical Challenge Problems and Beyond.* arXiv:2411.03590 (2024).
- Zheng, Pei, Logeswaran, Lee, Jurgens. *When "A Helpful Assistant" Is Not Really Helpful: Personas in System Prompts Do Not Improve Performances of Large Language Models.* Findings of EMNLP 2024. arXiv:2311.10054.

**Scaffolding versus capability**

- mini-SWE-agent (software, SWE-agent team). `https://github.com/SWE-agent/mini-swe-agent`. Self-reported; cite as software.
- Vats, Golev. *The Scaffold Effect in Coding Agents: Harness Choice as a Hidden Variable in Coding-Agent Evaluation.* ICML 2026 workshop poster.
- Kapoor, Stroebl, Siegel, Nadgir, Narayanan. *AI Agents That Matter.* arXiv:2407.01502 (2024).

**Prompt optimisation**

- Khattab et al. *DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines.* arXiv:2310.03714 (2023).

## B. Method

**Multi-agent versus single agent**

- Cemri, Pan, Yang, et al. *Why Do Multi-Agent LLM Systems Fail?* arXiv:2503.13657 (2025).
- Li, Zhang, Yu, Fu, Ye. *More Agents Is All You Need.* TMLR 2024. arXiv:2402.05120.
- Smit, Duckworth, Grinsztajn, Barrett, Pretorius. *Should we be going MAD? A Look at Multi-Agent Debate Strategies for LLMs.* arXiv:2311.17371 (2023).
- Kim, Gu, Park, et al. *Towards a Science of Scaling Agent Systems.* arXiv:2512.08296 (2025). Author count needs checking.
- Tran, Kiela. *Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets.* arXiv:2604.02460 (2026).

**LLM as judge**

- Zheng, Chiang, Sheng, et al. *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.* NeurIPS 2023 Datasets and Benchmarks. arXiv:2306.05685.
- Panickssery, Bowman, Feng. *LLM Evaluators Recognize and Favor Their Own Generations.* arXiv:2404.13076 (2024).
- Gu, Jiang, Shi, et al. *A Survey on LLM-as-a-Judge.* arXiv:2411.15594 (2024).
- Spiliopoulou, Fogliato, Burnsky, et al. *Play Favorites: A Statistical Method to Measure Self-Bias in LLM-as-a-Judge.* arXiv:2508.06709 (2025).
- Pombal, Rei, Martins. *Self-Preference Bias in Rubric-Based Evaluation of Large Language Models.* arXiv:2604.06996 (2026).

**Contamination and refreshed benchmarks**

- Aleithan, Xue, Mohajer, Nnorom, Uddin, Wang. *SWE-Bench+: Enhanced Coding Benchmark for LLMs.* arXiv:2410.06992 (2024).
- Liang, Garg, Zilouchian Moghaddam. *The SWE-Bench Illusion: When State-of-the-Art LLMs Remember Instead of Reason.* arXiv:2506.12286 (2025).
- Ramos, Mamede, Jain, Canelas, Gamboa, Le Goues. *Are Large Language Models Memorizing Bug Benchmarks?* arXiv:2411.13323 (2024).
- Zhang, He, Zhang, et al. *SWE-bench Goes Live!* arXiv:2505.23419 (2025).
- Badertdinov, Golubev, Nekrashevich, et al. *SWE-rebench: An Automated Pipeline for Task Collection and Decontaminated Evaluation of Software Engineering Agents.* NeurIPS 2025. arXiv:2505.20411.
- Jain, Han, Gu, et al. *LiveCodeBench: Holistic and Contamination Free Evaluation of Large Language Models for Code.* arXiv:2403.07974 (2024).

**Statistics for small evaluations**

- Miller. *Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations.* arXiv:2411.00640 (2024).
- Bjarnason, Silva, Monperrus. *On Randomness in Agentic Evals.* arXiv:2602.07150 (2026).

**Incomplete ground truth**

- Zhang, Yu, Yu, et al. *AACR-Bench: Evaluating Automatic Code Review with Holistic Repository-Level Context.* arXiv:2601.19494 (2026). Expert re-annotation raised defect coverage by 285%.
- Zeng, Shi, Han, et al. *SWR-Bench: Assessing LLM Performance in Real-World Code Review Comment Generation.* arXiv:2509.01494 (2025).
- Wang, Pradel, Liu. *Are "Solved Issues" in SWE-bench Really Solved Correctly? An Empirical Study.* arXiv:2503.15223 (2025).

**Model substitution and drift behind an API**

- Gao, Liang, Guestrin. *Model Equality Testing: Which Model Is This API Serving?* ICLR 2025. arXiv:2410.20247.
- Cai, Shi, Zhao, Song. *Are You Getting What You Pay For? Auditing Model Substitution in LLM APIs.* arXiv:2504.04715 (2025).

**Over-refusal on benign content**

- Bhatt, Chennabasappa, Li, et al. *CyberSecEval 2: A Wide-Ranging Cybersecurity Evaluation Suite for Large Language Models.* arXiv:2404.13161 (2024).
- Cui, Chiang, Stoica, Hsieh. *OR-Bench: An Over-Refusal Benchmark for Large Language Models.* ICML 2025. arXiv:2405.20947.

## Gaps the searches reported

- No paper was found that directly measures precision being understated because valid findings sit outside the ground truth. AACR-Bench is the nearest.
- No study was found of safety-classifier false positives on code-review content specifically.

## C. Automated code review with LLMs

**No prior work was found that compares a vendor's official agent plugin or skill against a plain prompt on the same model.**

**Benchmarks and datasets**

- Li, Lu, Guo, Duan, et al. *Automating Code Review Activities by Large-Scale Pre-training* (CodeReviewer). ESEC/FSE 2022. arXiv:2203.09095.
- Lin, Liu, Gao, Thongtanunam, Treude. *CodeReviewQA: The Code Review Comprehension Assessment for Large Language Models.* Findings of ACL 2025. arXiv:2503.16167.
- Zeng, Shi, Han, et al. *SWR-Bench.* arXiv:2509.01494 (2025). 1,000 verified pull requests; LLM judge agrees with humans about 90% of the time; best F1 19.4%, with low precision the limit.
- Guo, Zheng, Liao, Yu, Di, Zhang, Dai. *CodeFuse-CR-Bench: A Comprehensiveness-aware Benchmark for End-to-End Code Review Evaluation in Python Projects.* arXiv:2509.14856 (2025).
- Hu, Wang, Wen, et al. *Benchmarking LLMs for Fine-Grained Code Review with Enriched Context in Practice.* arXiv:2511.07017 (2025).
- Zhang, Yu, Yu, et al. *AACR-Bench.* arXiv:2601.19494 (2026).
- Pereira, Sinha, Ghosh, Dutta. *CR-Bench: Evaluating the Real-World Utility of AI Code Review Agents.* arXiv:2603.11078 (2026). A reflection step raised recall from 27.0% to 32.8% but cut signal-to-noise from 5.11 to 1.95.
- Zhang, Pan, Yusuf, Ruan, Shariffdeen, Roychoudhury. *Code Review Agent Benchmark* (c-CRAB). arXiv:2603.23448 (2026). In a manual check of 92 agent comments, 77 were useful although most failed the human-derived tests.
- Kumar. *SWE-PRBench: Benchmarking AI Code Review Quality Against Pull Request Feedback.* arXiv:2603.26130 (2026).
- Zheng, Wang, Wang, et al. *From Static to Dynamic: Benchmarking Real-World Code Review with MCR-Bench.* ISSTA 2026. arXiv:2608.27442.
- Industry, not peer reviewed: the Martian Code Review Bench (`https://github.com/withmartian/code-review-benchmark`); Greptile, "AI Code Review Benchmarks", July 2025; Qodo, "Qodo Outperforms Claude in Code Review Benchmark", 12 March 2026.

**Studies of tools in practice**

- Cihan, Haratian, İçöz, et al. *Automated Code Review In Practice.* ICSE-SEIP 2025. arXiv:2412.18531.
- Sun, Xu, Li, et al. *BitsAI-CR: Automated Code Review via LLM in Practice.* arXiv:2501.15134 (2025). A generate-then-filter pipeline at ByteDance.
- Vijayvergiya et al. *AI-Assisted Assessment of Coding Practices in Modern Code Review.* AIware 2024. arXiv:2405.13565.
- Aðalsteinsson et al. *Rethinking Code Review Workflows with LLM Assistance: An Empirical Study.* arXiv:2505.16339 (2025).
- Sun, Kuang, Baltes, et al. *Does AI Code Review Lead to Code Changes? A Case Study of GitHub Actions.* arXiv:2508.18771 (2025).
- Zhong, Noei, Adams, Zou. *From Human-Centric to Agentic Code Review: The Impact of Different Generations of Generative AI Technology on Review Quality.* arXiv:2607.13196 (2026).

**Multi-agent or scaffolded review against a simpler baseline**

- CR-Bench (above): single-shot against a reflection loop on the same models. The closest academic analogue.
- SWR-Bench (above): aggregating ten runs raises F1 by 43.67%, mostly through recall.
- Li, Zhang, Wu, et al. *OpenCodeReview: Determinism over Non-Determinism for Cost-Effective Agent-Based Code Review.* arXiv:2608.09290 (2026).
- Li, Wang, Thongtanunam, et al. *Issue-Oriented Agent-Based Framework for Automated Review Comment Generation.* arXiv:2511.00517 (2025).
- Tang, Kim, Song, et al. *CodeAgent: Autonomous Communicative Agents for Code Review.* arXiv:2402.02172 (2024).
- Han, Zhang, Song, et al. *SWE-Skills-Bench: Do Agent Skills Actually Help in Real-World Software Engineering?* arXiv:2603.15401 (2026). 92 of 98 skills show no significant effect.

**Nearest non-academic comparisons**

- A Tessl blog post (10 April 2026) compares the author's own review plugin with a generic prompt on 43 self-built scenarios (97.7% against 66.6%). Not a vendor's official plugin, and it points the other way.
- Qodo's post benchmarks Anthropic's Claude Code Review against other tools, with no plain-prompt arm.

**Searches reported no paper that audits unmatched findings after the fact**, as this study's checker pass does.
