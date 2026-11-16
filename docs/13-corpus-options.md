# 13 Corpus options

Status: **corpus chosen by the project owner on 2026-11-15: the Martian Code Review Bench (offline).** This document records the research behind the choice, what a direct read of that repository found, and what has to be settled before it is used. Covers decision 4 and Q-18.

No model or API call was made. No repository was created or forked. Nothing from the benchmark was executed.

## 1. Decision and summary

1. **The pilot corpus is the offline benchmark in `withmartian/code-review-benchmark`**: 50 real pull requests from five open-source projects, with 173 human-curated "golden comments" as ground truth.
2. **It is the nearest thing to a shared standard.** The same 50 pull requests are scored by several organisations. No benchmark found meets every requirement in document 07.
3. **Its "claude" leaderboard entry appears to be this plugin.** The repository's helper script tells the operator to run `/code-review:code-review --comment`. A reference run of the plugin under test already exists in the benchmark's published results.
4. **Ground truth is a text description with a severity and a category. There is no file or line.** Matching findings to ground truth therefore needs a model-based judge. Deterministic matching on location (decision 5) is not possible with this corpus.
5. **There are no clean cases, and the answers are public.** False positives can only be measured against an incomplete golden set, and training-data leakage cannot be ruled out. Both limits are accepted for an exploratory first run and must be reported with the results.
6. **Using it needs pull requests re-created under a GitHub organisation the owner controls.** That is an outward-facing step and has not been taken. See section 5.

## 2. How the options were researched

Two research passes ran on 2026-11-15: one on benchmarks built for automated code review, one on general defect datasets and bug-injection methods. Both used web search and page fetches.

Reliability of what follows:

- **Section 3 was read directly** from a clone of the Martian repository. Those facts are verified at the commit given.
- **Section 6 comes from the research passes.** Pages were read through a fetch-and-summarise tool, so figures there are **unverified** until checked at the source. They were used to choose between options, not as facts to publish.

## 3. The Martian benchmark, as read

Source: `https://github.com/withmartian/code-review-benchmark`, cloned anonymously on 2026-11-15 at commit `e616e849755441da38f18bf3adba2c9583b03803` (2026-08-30). The clone was made outside this repository and deleted afterwards. Licence of the benchmark's own code and data files: MIT, copyright 2025 Martian.

### 3.1 Contents

| Item | Finding |
|---|---|
| Cases | 50 pull requests, 10 from each of 5 projects |
| Projects | Sentry, Grafana, Cal.com, Discourse, Keycloak |
| Ground truth | 173 golden comments in `offline/golden_comments/*.json` |
| Fields per golden comment | `comment` (text), `severity`, `category`. **No file path, no line number.** |
| Golden comments per pull request | Minimum 1, median 3, maximum 9. Two pull requests have exactly 1. |
| Clean cases | None. Every pull request has at least one golden comment. |
| Severity | Critical 12, High 54, Medium 61, Low 46 |

Categories:

| Category | Count | In the benchmark's "Strict" profile |
|---|---|---|
| `bug` | 94 | Yes |
| `concurrency` | 14 | Yes |
| `api` | 13 | Yes |
| `security` | 11 | Yes |
| `data` | 7 | Yes |
| `style` | 10 | No |
| `doc_defect` | 9 | No |
| `perf` | 6 | No |
| `speculative` | 5 | No |
| `test_gap` | 4 | No |

The benchmark defines three scoring profiles: Strict (139 golden comments), Core (158), and All (173). A match on a category outside the active profile is neither rewarded nor penalised.

### 3.2 Where the pull requests live

Each golden entry has a `url`. They point to different places:

| Location of `url` | Count |
|---|---|
| The upstream project (`calcom/cal.com`, `grafana/grafana`, `keycloak/keycloak`, `getsentry/sentry`) | 35 |
| A third-party organisation, `ai-code-review-evaluation` (`discourse-graphite`, `sentry-greptile`, `keycloak-greptile`) | 15 |

Five entries carry a maintainer note (`az_comment`) flagging a problem:

- Four say "reviewed commit is not in the repo": `keycloak-greptile/pull/1`, and `sentry-greptile/pull/1`, `/2`, and `/3`.
- One says "there is no such PR, it is a mix of many PRs": `sentry-greptile/pull/5`.

These five should be excluded from the pilot unless the notes are understood.

### 3.3 How the benchmark scores a tool

1. Step 0 re-creates each pull request in a GitHub organisation where the tool is installed.
2. Step 1 downloads the tool's review comments with `gh`.
3. Step 2 turns comments into candidate issues. Line-specific comments become candidates directly. General comments go to a model that extracts distinct issues.
4. Step 2.5 groups duplicate candidates, so a tool is not penalised for stating an issue twice.
5. Step 3 asks a model judge, for each candidate and golden comment, whether they describe the same underlying issue. Semantic matches count.
6. Precision, recall, and F-beta are computed per profile.

The repository stores results under three judge models: `anthropic_claude-opus-4-5-20251101`, `anthropic_claude-sonnet-4-5-20250929`, and `openai_gpt-5.2`. The pipeline calls an OpenAI-compatible endpoint configured through `MARTIAN_API_KEY`, `MARTIAN_BASE_URL`, and `MARTIAN_MODEL`.

The README lists its own limitations: the dataset is static and "tools may have seen them during training"; golden comments "may miss edge cases"; style coverage is sparse (about 10 items), so correct style findings can count as false positives; and the judge "introduces model-dependent variance".

### 3.4 The existing Claude entries

The stored results include two Claude-related tools. Totals across all 50 pull requests, computed from `evaluations.json`:

| Tool name | Reviews posted | Judge: Opus 4.5 | Judge: GPT-5.2 |
|---|---|---|---|
| `claude` | 2026-01-27 | Precision 0.46, recall 0.38 (TP 66, FP 79, FN 107) | Precision 0.41, recall 0.38 |
| `claude-code` | 2026-03-11 | Precision 0.49, recall 0.49 (TP 84, FP 88, FN 89) | Precision 0.42, recall 0.41 |

What can be said about them:

- **`claude` appears to be the code-review plugin.** `offline/scripts/claude_clone_and_review.clj` clones a benchmark pull request, opens Claude Code, and prints "Run: /code-review:code-review --comment". Its example repository name contains `__claude__` and the date `20260127`. The stored `claude` reviews are single summary comments starting "### Code review" and "Found N issues", with no inline comments. That is the output format of the plugin's older command (see `docs/10-plugin-review.md`, section 4.1).
- **This is an inference.** The repository does not state which plugin commit, Claude Code version, or model produced the entry.
- **`claude-code` is a different configuration.** Its reviews have inline comments and an "Extended reasoning" section. What produced it is not recorded in the files read.
- The same reviews score differently under different judges. Precision for `claude` moves from 0.46 to 0.41 with the judge alone. Any comparison with these numbers must use the same judge and prompts.

## 4. Fit with the plugin and the requirements

| Requirement | Fit | Note |
|---|---|---|
| Input is a GitHub pull request | Good | Cases are pull requests. A script re-creates them. |
| Ground truth has location, category, rationale (document 07) | Partial | Category and description, no location. |
| Includes cases with no planted defect | **No** | No clean cases. |
| Ground truth held outside the run environment (TR-11) | Risk | Golden comments are public on GitHub. A reviewing agent with web access could find them. |
| Deterministic, checksummed (TR-10) | Achievable | Pin the benchmark commit and record each case's base and head SHA. |
| No leakage | **No** | Pull requests and golden comments were public before the models' knowledge cutoffs. |
| Licence | Mixed | Benchmark is MIT. The five projects carry their own licences, which the research pass reported as including AGPL-3.0 and GPL-2.0. **Unverified.** |
| No real secrets (BR-8) | To check | The fork script disables GitHub push protection "to allow pushing test fixtures with token-like strings". |
| Within the plugin's stated scope | Mostly | 94 of 173 golden comments are `bug`. `security` (11) and `concurrency` (14) fall partly outside what the plugin tells its agents to flag. Label each for Q-19. |
| Comparable published results | Yes | Section 3.4, with the caveats there. |

Consequences for earlier decisions:

- **Grading (decision 5) becomes model-based.** A judge decides whether a finding matches a golden comment. Document 07 requires the judge to be pinned, its fallback logged, its choice justified against self-grading, and its error rate measured on a hand-labelled sample. Reusing Martian's judge prompts would keep results comparable with the published ones.
- **Owner decision 5 fits this corpus.** The golden set is known to be incomplete. Findings that match no golden comment go to the checking agent, and those it confirms are reported separately.
- **"Planted defect" no longer describes the ground truth.** These are real issues found by human reviewers in real changes. Documents 02 and 04 use the planted-defect wording and need adjusting.
- **False positives are an upper bound.** An unmatched finding is either wrong or a real issue missing from the golden set.

## 5. What using it requires

### 5.1 Re-creating the pull requests

The benchmark's `step0_fork_prs.py`, as read:

- Needs a GitHub **organisation** and a token that can create repositories in it. It calls the organisation endpoint, so a personal account will not work without changing the script.
- Creates **one new repository per pull request**, named from the project, tool name, pull request number, and date.
- Clones the full upstream repository, pushes the base commit and the pull request head, then opens the pull request.
- Creates each repository private, then **makes it public** after pushing.
- Disables GitHub Actions and secret-scanning push protection on each new repository.

For this project:

- **Private repositories are enough.** The plugin reads pull requests through an authenticated `gh`. Skipping the "make public" step avoids publishing copies of five projects and keeps the forks out of search. This needs a small change to the script or a short script of our own.
- **The upstream pull requests cannot be reviewed in place.** They are closed or merged, and the plugin skips closed pull requests. The existing public benchmark copies already carry review comments, which also triggers the plugin's skip rule.
- **At `9780cf4` one copy per case can serve every run.** Without `--comment` the plugin posts nothing, so repeats do not contaminate each other.
- **At `aecd4c8` each run needs a fresh copy**, or its comment must be deleted afterwards, because that commit always posts and then skips pull requests that already have a review.
- Sentry and Grafana are large repositories. Cloning and pushing them takes time and disk, not API spend.

### 5.1a What has been created (2026-11-15)

The owner approved the `sideofmydesk` organisation for private copies and dropped `aecd4c8` from the pilot, so one copy per case serves every run.

**One copy exists so far**, as a proof of the process: a private repository in `sideofmydesk` holding one open pull request. Checked after creation: the repository is private (an anonymous request returns 404); the pull request shows the same 15 files and 555 added lines as its source; GitHub Actions is disabled and no workflow ran.

The copies are made differently from the benchmark's own script, on purpose:

| Aspect | Benchmark's script | This project |
|---|---|---|
| History | Full upstream history | **Two commits**: the tree at the merge base, then the tree at the pull request head. The diff is identical. |
| Visibility | Made public after pushing | Private |
| Repository name | Project, tool, pull request number, date | Neutral (`fe-case-NNN`), so the name does not point to the source |
| Commit author | Upstream authors | A neutral placeholder |
| Description | Copied as is | Copied, with `@` mentions neutralised so nobody is notified |

Consequences of the two-commit method: `git blame` and `git log` on a copy show nothing useful. The plugin at `9780cf4` has no history-reading agents, so it is not affected. A reviewer that wanted history would be. This is a deviation from the published benchmark and must be stated with any comparison to its numbers.

Ground truth, the case order, and the map from copy to source are kept outside this repository. The case order was fixed before any run: entries carrying a maintainer note are excluded, leaving 45; each project's entries are sorted by URL and shuffled with Python's `random.Random` seeded with `20261115:<project>`. The pilot takes the first k cases from each project.

SHA-256 of the golden files at benchmark commit `e616e84`:

| File | SHA-256 |
|---|---|
| `cal_dot_com.json` | `57db13d7b226a502c113782956c6f00ed23c5ae074e8552fb2eb0e36b1aeb691` |
| `discourse.json` | `e74f032c1f92182a4eed7f7b1636cd838ef145494c236cac29c42e55d15e949a` |
| `grafana.json` | `41a1d1eabae61d03d5f4b16c6546dd8b51bfd65d1c91d99d65819ea8b3ae05b4` |
| `keycloak.json` | `a3d210731f1d9019b24206722ab02d9fcf1d7773562c134926d0b830d2921dfc` |
| `sentry.json` | `2084e31da3c96b4e352a79a74a5dcb001d2b6c693e8efe7d22e26ad51de2ec1b` |

### 5.2 Sizing against the $150 ceiling

Runs = pull requests × models × arms × repeats. Two models and two arms (with plugin, without) give 4 runs per pull request per repeat. All 50 pull requests at one repeat is 200 runs, before judge and checker calls.

Cost per run is not known. The pilot plan's estimates are unreliable (see `docs/11-verified-facts.md`, section 2). The subset is sized after the logging spike measures a real run. As an illustration only: if a plugin run and a baseline run averaged $1.50 between them per model, 10 pull requests with 2 repeats would cost about $60 for runs, leaving room for the spike, the judge, and the checker.

Proposed selection rule, fixed before any run:

1. Exclude the five entries flagged in section 3.2.
2. Stratify by project, so all five projects and their languages are represented.
3. Pick within each project with a seeded random draw, and record the seed.

### 5.3 The baseline arm

The no-plugin arm reviews the same pull request with a plain prompt asking for a code review. The prompt is fixed and versioned (TR-4). Its wording is not yet written.

## 6. Options considered

Figures in this section are from the research passes and are **unverified**.

### 6.1 Benchmarks built for code review

| Benchmark | Cases | Ground truth | Clean cases | Why not chosen |
|---|---|---|---|---|
| Martian offline (chosen) | 50 pull requests, 5 projects | Text, severity, category | No | Chosen. See above. |
| GitHub ReviewBench | 219 pull requests, 187 repositories, 19 languages | Validated golden findings | Not stated | Could not confirm the dataset is downloadable, its licence, or its fields. The official route is submitting a container. |
| AACR-Bench (Alibaba) | 200 pull requests, 10 languages | File and line ranges, category | Not stated | Best ground-truth shape, Apache-2.0. No published Claude scores. Each pull request must be re-created. Some ground truth is AI-generated. |
| SWR-Bench | 1,000 pull requests, Python | Structured change points, no line | **Yes, 500** | Only confirmed source of clean cases. Python only. Data link is an anonymised URL. |
| Qodo Benchmark 1.0 | 100 pull requests, 580 injected issues | File and line | Not scored | Injected-bug ground truth reportedly not published. |
| SWE-PRBench | 350 pull requests | Human review comments with file and line | No | Ground truth is whatever reviewers commented on, not verified defects. |
| SWE-CARE, c-CRAB | 671 and 184 | Human comments; executable tests | Not stated | Pull requests date from 2015 to mid-2025. High leakage risk. |

### 6.2 General defect datasets

None is ready-made. Each records a bug by its fix, so every case needs the fix reversed to make a pull request that introduces the bug.

| Group | Examples | Assessment |
|---|---|---|
| Real-bug collections | Defects4J, BugsInPy, GitBug-Java, GHRB, ManySStuBs4J | Good scope fit. Mostly public before the cutoff. Defects4J was reported as the most memorised of the bug benchmarks one study tested. |
| SWE-bench family | SWE-bench Verified, SWE-bench-Live, SWE-rebench | Reversal is mechanical. Many cases are features, not defects. Only refreshed variants limit leakage. |
| Security suites | NIST Juliet, OWASP Benchmark, CVEfixes, PrimeVul | Poor fit. The plugin tells its agents not to flag general security issues. |
| Injection | Mutation operators (PIT, mutmut), SWE-smith | Exact-line ground truth, no leakage of the defect, closest match to the plugin's "definitely wrong regardless of inputs" rule. Less realistic. Not a recognised benchmark. |

Reversing or replaying a known fix is an established method. The research found it described by SWE-smith, Greptile, Qodo, and bugbench.

### 6.3 Recommended follow-up

The Martian corpus cannot answer two questions: how often the plugin raises findings on a clean change, and how much of any score is recall from training data. A small second set would address both: recent merged pull requests from after the models' cutoff, some left clean and some with one bug injected by a standard mutation operator. This is not part of the pilot. It is a candidate for the next round.

## 7. Risks

| Risk | Mitigation |
|---|---|
| Models or agents have seen the pull requests or the golden comments | Report as a limitation. Deny web access to reviewing agents where possible. Use the follow-up set in section 6.3 later. |
| A reviewing agent finds the golden comments online during a run | Keep forks private and renamed. Restrict tools to `gh` on the fork. Check transcripts for fetches of the benchmark repository. |
| Judge variance changes scores | Pin one judge. Report the judge. Hand-check a sample. |
| Small sample: a subset of 50 swings easily | Report intervals. Treat the run as exploratory, per owner decision 6. |
| Golden set incomplete, so precision is understated | Owner decision 5: check unmatched findings and report confirmed ones separately. |
| Token-like strings in project fixtures | Keep forks private. Do not copy fixture content into logs that are published. |
| Benchmark repository changes | Pin commit `e616e84`. Record a checksum of each golden file. |

## 8. Open questions

Numbering continues from Q-29 in `docs/12-request-logging.md`.

| ID | Question |
|---|---|
| Q-30 | Which GitHub organisation hosts the re-created pull requests, and are they private? This document recommends private. Creating them needs the owner's approval. |
| Q-31 | Which model judges matches, and are Martian's judge prompts reused for comparability? The judge must not be a model under test if self-grading is to be avoided. |
| Q-32 | Does the pilot include plugin commit `aecd4c8`? It needs a fresh pull request per run and posts comments. Dropping it from the pilot halves the plugin runs. |
| Q-33 | How many pull requests and repeats, once the spike has measured cost per run? |
| Q-34 | Is the follow-up set in section 6.3 built for the next round? |
| Q-35 | Which scoring profile is primary: Strict (139), Core (158), or All (173)? |
