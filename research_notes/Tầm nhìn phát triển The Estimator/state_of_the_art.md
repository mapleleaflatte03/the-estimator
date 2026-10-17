# State of the Art in Software Effort Estimation from Text (AI/LLMs), 2024–2026, and What The Estimator Could Adopt

How these notes were made: web search did not work in this session, so sources were found through the arXiv API, Crossref and direct page fetches (arXiv HTML full texts, Springer open-access chapters, Derek Jones' blog, GitHub). Every number below was copied from the cited source. Where a source only gave a number in its abstract, these notes say so. Product context (from the brief): rule-based clause extraction plus the Jev AI decision model, Beta-PERT Monte Carlo with an empirical shared shock, bias correction learned from actual hours, and a temporal-holdout benchmark on the SiP dataset (MAE 10.34 → 9.26 h, P10–P90 coverage 82%).

---

## 1. LLM-based and deep-learning effort / story-point estimation (methods, datasets, numbers, pitfalls)

### Takeaway
On the standard JIRA story-point benchmarks, deep models were long reported as SOTA (Deep-SE, then GPT2SP). Independent replications later found that they rarely beat a simple Median baseline, and one of them (GPT2SP) had a bug in its MAE calculation. From 2024 to 2026 the field moved to LLMs: zero-shot and few-shot prompting, search-optimised few-shot examples, RAG, fine-tuned small LLM agents, and comparative (pairwise) judgements. LLMs rank items reasonably well even with no project data, but their absolute calibration is weak, and gains over baselines are often small or not statistically significant. Almost all of this work predicts unitless story points from issue title and description, not hours from client briefs.

### Cited Findings
**Datasets**
- Choetkiertikul et al. dataset: 23,313 issues from 16 open-source JIRA projects, collected up to 8 Aug 2016. It is the most-used benchmark — [Maha, Rahman, Roy 2026, arXiv:2604.03443](https://arxiv.org/abs/2604.03443); [Tawosi et al. 2022, arXiv:2209.00437](https://arxiv.org/abs/2209.00437)
- TAWOS dataset (Tawosi et al. 2022): 31,960 issues from 26 open-source agile projects, filtered more strictly (following Porru et al.). 3 projects were later removed from the public replication package, leaving 23 — [Maha et al. 2026](https://arxiv.org/html/2604.03443v1)
- SiP dataset: more than ten years of commercial Agile development, with 10,100 unique task estimates made by 22 developers under 20 project codes. Factors that influenced estimation accuracy: the person estimating, the project, and the tendency to use round numbers. Any improvement from practice "did not noticeably improve regression models fitted" — [Jones & Cullum 2019, arXiv:1901.01621](https://arxiv.org/abs/1901.01621); data at [github.com/Derek-Jones/SiP_dataset](https://github.com/Derek-Jones/SiP_dataset)
- Until April 2026 the only two non-trivial public datasets with human-effort project data were SiP and CESAW. The SEA Data Warehouse (released 2026) covers 679,904 tasks across 1,211 Team Software Process (TSP) projects, with estimates, actuals, phases, people and dates. CESAW is roughly a 10% subset of it — [Derek Jones, "Detailed management data on 1,211 software projects", 5 Jul 2026](https://shape-of-code.com/?s=SiP)

**Deep-learning generation (pre-LLM SOTA) and replications**
- Deep-SE (LSTM plus Recurrent Highway Network, trained on issue text) — [Choetkiertikul, Dam, Tran, Pham, IEEE TSE 2019, doi:10.1109/TSE.2018.2792473](https://doi.org/10.1109/TSE.2018.2792473)
- **Deep-SE replication:** Deep-SE beat the Median baseline with statistical significance in only 8 of 42 cases, and beat TF/IDF-SVM in only 9 of 32. Adding more training data or pre-training did not improve it. The authors conclude that "using semantic similarity is not enough to differentiate user stories with respect to their story points" — [Tawosi, Moussa, Sarro 2022, arXiv:2201.05401](https://arxiv.org/abs/2201.05401)
- GPT2SP (GPT-2-based Transformer) originally claimed 6–47% MAE improvement over Deep-SE within-project and 3–46% cross-project — [Fu & Tantithamthavorn, IEEE TSE 2023, doi:10.1109/TSE.2022.3158252](https://doi.org/10.1109/TSE.2022.3158252)
- **GPT2SP replication:** a bug in the MAE calculation of the released code "may have inflated the GPT2SP's accuracy". The fix was merged upstream ([PR #2](https://github.com/awsm-research/gpt2sp/pull/2)), and the replication also reports MdAE and SA — [Tawosi, Moussa, Sarro 2022, arXiv:2209.00437](https://arxiv.org/abs/2209.00437). A 2026 paper declined to compare against GPT2SP because the replication "found a bug that made their results unreliable" — [Maha et al. 2026](https://arxiv.org/html/2604.03443v1)
- Fine-SE combines semantic text features with expert features. It was evaluated on 17 industrial projects and 4 open-source projects — [Li, Ren, Wang et al., ICSE 2024, doi:10.1145/3597503.3623349](https://doi.org/10.1145/3597503.3623349); dataset described in [Bui, Dam, Hoda 2025](https://arxiv.org/html/2509.14483v1)
- HeteroSP, a heterogeneous graph neural network over issue text, used GPT2SP and Deep-SE as baselines — [arXiv:2206.11023 (2022)](https://arxiv.org/abs/2206.11023)

**LLM generation (2024–2026)**
- **Search-optimised few-shot examples (Tawosi, Alamir, Liu — J.P. Morgan AI Research, 2024):** using search-based SE to choose the number and mix of few-shot examples improved LLM story-point MAE "by 59.34% on average … over three datasets against a zero-shot setting". The authors call the results preliminary — [arXiv:2403.08430](https://arxiv.org/abs/2403.08430). A later paper says this line of work used GPT-4 — [Maha et al. 2026](https://arxiv.org/html/2604.03443v1)
- **Zero-shot and few-shot LLMs (Shetty, Balakrishnan, Xu, Xi, Yu, 2026):** DeepSeek-V3.2, Kimi K2, Gemini 2.5 Flash-Lite and GPT-5 Nano were tested on the 16 Choetkiertikul projects.
  - "Without any training data (zero-shot prompting), LLMs can predict story points better than supervised deep learning models trained on 80% of the data". The metrics are Pearson ρ and Spearman r_s, not MAE.
  - Kimi and DeepSeek beat the best supervised baseline on both metrics zero-shot.
  - Few-shot raised DeepSeek's mean Pearson from about 0.3816 to 0.4532, and Gemini/OpenAI ρ from 0.2363/0.2519 to 0.3204/0.3220.
  - Kimi zero-shot: Spearman 0.411 vs Pearson 0.373. Spearman ≥ Pearson throughout, so LLMs rank better than they calibrate absolute values.
  - Few-shot examples chosen to cover the story-point scale ("Prompt 2-Scale") beat examples chosen by count.
  - Pairwise accuracy implied by direct zero-shot estimates (DeepSeek 0.743, OpenAI 0.658, Kimi 0.649, Gemini 0.587) was higher than asking the LLM directly which item is bigger (0.631/0.606/0.582/0.556).
  - Pairwise comparisons used as few-shot examples still improved all four models
  - [arXiv:2603.06276](https://arxiv.org/abs/2603.06276), [HTML](https://arxiv.org/html/2603.06276v2)
- **Comparative learning (Khan, Xi, Meneely, Tang, Yu, 2025):** a model trained only on pairwise "which is more effort" judgements reached an average Spearman of 0.34 against true story points across 16 projects (23,313 estimates). That is "similar to, if not better than" a SOTA regression model. In a human study, pairwise judgements gave higher confidence, lower annotation time and comparable agreement versus direct ratings — [arXiv:2507.14642](https://arxiv.org/abs/2507.14642)
- **RAG (Maha, Rahman, Roy, 2026):** bge-large-en-v1.5 or all-mpnet-base-v2 retrieval plus a Llama-3.2-3B-Instruct generator on 23 TAWOS projects (80/20 split).
  - Mean MAE by project-size group: small 1.99 / mid 1.67 / large 1.90 (BAAI) and 1.90 / 1.61 / 1.86 (SBERT).
  - Per-project MAE ranged from 0.85 (SERVER) to 4.98 (APSTUD).
  - Best settings: top_k = 2 with temperature 0.1 for small and mid projects; top_k = 4 with temperature 0 for large projects.
  - RAG "outperformed the baseline models in several occasions" (vs Deep-SE, LHC-SE, LHCtc-SE, TF-IDF), but differences were not statistically significant
  - [arXiv:2604.03443](https://arxiv.org/html/2604.03443v1)
- **Multi-agent LLM, SEEAgent (Bui, Dam, Hoda, 2025):** Llama-3.1-8B-Instruct, fine-tuned per project (so within-project), with agents that discuss estimates with humans.
  - Fine-SE open-source subset: DM 4,320 issues, ME 414, TD 73, US 100.
  - ME: MAE 1.217, MMRE 0.414, PRED(50) 0.747, vs Deep-SE (1.382, 0.489, 0.687), GPT2SP (1.583, 0.629, 0.578) and Fine-SE (1.395, 0.449, 0.723).
  - US: MAE 0.350.
  - TD: worse than Deep-SE (MAE 5.133 vs 4.108).
  - Base model vs fine-tuned on DM: MAE 17.053 vs 4.251.
  - Tested with Wilcoxon and Vargha–Delaney Â12. TD comparisons were not significant (p = 0.095–0.524).
  - [arXiv:2509.14483](https://arxiv.org/html/2509.14483v1)
- **Multimodal (BERT + CNN + XGBoost on text, image and categorical data):** good accuracy for small story points, weak for large ones because of class imbalance. Severity has a strong influence — [arXiv:2505.16290 (2025)](https://arxiv.org/abs/2505.16290)
- **Effort when AI agents do the work:** ACEM proposes splitting cost into LLM tokens, human-in-the-loop oversight and infrastructure, with a Revision Factor, a Context Factor and a HITL Intensity Score. Its constants are "left symbolic pending empirical grounding" (conceptual only) — [El-Ramly 2026, arXiv:2608.02582](https://arxiv.org/abs/2608.02582). Similar conceptual "LLM-aware SEE" frameworks: [Frontiers in AI 2026, doi:10.3389/frai.2026.1772418](https://doi.org/10.3389/frai.2026.1772418); [Discover Computing 2026, doi:10.1007/s10791-026-10331-6](https://doi.org/10.1007/s10791-026-10331-6)

**Known pitfalls**
- **Cross-project vs within-project:** story points are project-specific, and deep models drop "notably" in cross-project settings — [Shetty et al. 2026](https://arxiv.org/html/2603.06276v2). GPT2SP and FastText-SVM "only make accurate (within-project) predictions when they are trained on data from the same project" — [Khan et al. 2025](https://arxiv.org/abs/2507.14642)
- **Implementation bugs and weak baselines** (GPT2SP MAE bug; Deep-SE rarely beating Median) — [arXiv:2209.00437](https://arxiv.org/abs/2209.00437), [arXiv:2201.05401](https://arxiv.org/abs/2201.05401)
- **Ignoring time order:** SEE research "generally ignores" the rule that models for future projects should be built only from completed projects, preferring recent ones. Time-aware models are feasible and pick different parameters and weights than models that ignore time — [Bosu, MacDonell, Whigham 2020, arXiv:2012.01596](https://arxiv.org/abs/2012.01596). A "Bellwether moving window" of recent exemplary projects with Gaussian weighting "significantly improve[s] the prediction accuracy" — [Mensah et al. 2021, arXiv:2105.14179](https://arxiv.org/abs/2105.14179)
- **Small test sets:** the SEEAgent comparisons include projects with 73 and 100 items — [arXiv:2509.14483](https://arxiv.org/html/2509.14483v1)

### Inferences
- The product works in hours rather than story points, uses commercial briefs and evaluates on a temporal holdout. That puts it outside most of the 2024–2026 literature, which uses random 80/20 splits on open-source JIRA story points. Its results can't be compared head-to-head with published MAEs. Its edge is realism, and it should claim that explicitly.
- LLMs rank well and calibrate poorly (Spearman ≥ Pearson; few-shot "scale anchors" help most). This supports the product's design: use Jev for qualitative judgements per clause (kind of work, tentativeness, "longer than it looks"), and let a statistical layer trained on actuals set the absolute hours.
- Leakage risk for The Estimator: the public datasets (Choetkiertikul 2016, TAWOS, SiP on GitHub since 2019) may be in LLM pretraining data. If Jev uses an LLM, SiP results could be slightly optimistic. A private, post-cutoff holdout from the company's own actuals would be more credible.
- Search-optimised example selection (59.34%) and scale-covering examples both suggest that which past examples Jev sees matters a lot. RAG over the company's own actuals, with examples stratified by size, is a cheap next step. Plain RAG with a small model was not significantly better in the 2026 study.

### Gaps
- No peer-reviewed study was found that estimates **hours from client briefs or RFP/contract text** with LLMs and reports MAE against actuals. The literature is almost entirely issue-level story points.
- No verified per-project MAE/MdAE/SA tables were obtained for the fixed GPT2SP replication, the TAWOS baselines, or the GPT-4 numbers in the Tawosi SBSE work. Only the abstract-level figures above were verified.
- No study was found that measures LLM training-data contamination specifically for effort datasets.

---

## 2. Expert judgement research (Jørgensen et al.): anchoring, optimism, reference class, interval overconfidence, what works

### Takeaway
Human estimates are strongly pulled by anchors (including the client's stated expectations), and warnings don't remove the effect. Min–max intervals usually capture only 50–70% of actuals when people believe they are 90% sure. The interventions with the best evidence are: use close analogies (reference class or outside view), checklists, careful decomposition that includes allowances for unknown work, and uncertainty derived from the distribution of past estimation errors rather than gut-feel intervals.

### Cited Findings
- **Anchoring:** "The anchoring effect may be said to be the king of human biases". In an experiment with software professionals, the "customer expected" figure changed the estimates even though participants were told to ignore it:

  | Customer anchor | Median estimate |
  |---|---|
  | 800 h | 300 h |
  | 40 h | 100 h |
  | 4 h (implausibly low) | 60 h (lowest of all) |

  Professionals denied being affected, or said they were affected "only a little". "Anchoring effects are fairly robust to all kinds of warnings and there is so far no efficient strategy to remove the effect" — [Halkjelsvik & Jørgensen 2018, *Time Predictions*, Ch. 5 (open access)](https://link.springer.com/chapter/10.1007/978-3-319-74953-2_5)
- **Team size and coordination:** actual time ran 55% over prediction for two-person teams and 75% over for four-person teams. Judges predicted four-person teams would be faster overall, which implied about 140% overrun for them vs 45% for two-person teams — [Ch. 5](https://link.springer.com/chapter/10.1007/978-3-319-74953-2_5)
- **Overconfident intervals:**
  - Students' 98% min–max intervals missed the actual time 43% of the time.
  - Software professionals' individual 90% intervals contained only 10% of actuals. Team-discussed intervals contained 40%.
  - Groups asked for 50%, 75%, 90% and 99% intervals gave about the same width, which the authors call "ignorance of confidence levels".
  - Rule of thumb for software work: min–max intervals correspond to a hit rate of **50–70%**.
  - Managers preferred narrow intervals and judged the developer who gave them as more skilled
  - [Ch. 6](https://link.springer.com/chapter/10.1007/978-3-319-74953-2_6). See also [Jørgensen, Teigen, Moløkken 2004, JSS, doi:10.1016/S0164-1212(02)00160-7](https://doi.org/10.1016/S0164-1212(02)00160-7)
- **Interventions that work for intervals:**
  - Turn the question around: give the person a fixed range (e.g. 50–200% of the best guess) and ask how likely the actual is to fall inside it. This produces a "remarkable reduction in overconfidence".
  - Combine that with the distribution of past prediction accuracy. Assuming lognormal times, derive p5/p95 and any pX value; the book's worked example is a 90% interval of 7–19 h.
  - Use **pX estimates** (e.g. p80 = 80% chance of not exceeding) to give estimates a precise meaning.
  - [Ch. 6](https://link.springer.com/chapter/10.1007/978-3-319-74953-2_6); [Ch. 8](https://link.springer.com/chapter/10.1007/978-3-319-74953-2_8). Related: [Jørgensen 2015, "The Use of Precision of Software Development Effort Estimates to Communicate Uncertainty", doi:10.1007/978-3-319-27033-3_11](https://doi.org/10.1007/978-3-319-27033-3_11)
- **Decomposition vs analogy, and checklists:**
  - Projects that used checklists underestimated by 10% on average, vs 38% for projects that did not.
  - Decomposed estimates come out higher. That helps when tasks are usually underestimated and hurts when they are usually overestimated. One software study found decomposed estimates higher but less accurate.
  - Close analogies "inherently" include unknown components and unexpected events. Decomposition has to add explicit allowances for them.
  - "The more you unpack … the higher the time prediction will be, unless you forget components"
  - [Ch. 7](https://link.springer.com/chapter/10.1007/978-3-319-74953-2_7)
- **Reference class forecasting:** Ch. 8 recommends analogy-based prediction from similar completed tasks when data exists. Countering a misleading anchor with a realistic one "may help but [is] usually not sufficient" — [Ch. 8](https://link.springer.com/chapter/10.1007/978-3-319-74953-2_8). The method has three steps: pick a reference class, build its outcome distribution, place the project within it. It comes from Kahneman and Tversky's "outside view" and was put into practice by Flyvbjerg and COWI (UK DfT guidance, 2004) — [Wikipedia: Reference class forecasting](https://en.wikipedia.org/wiki/Reference_class_forecasting)
- **Unit effect:** asking for estimates in work-hours gives lower estimates than asking in workdays — [Jørgensen 2016, JSS, doi:10.1016/j.jss.2016.03.048](https://doi.org/10.1016/j.jss.2016.03.048) (title-level finding only)
- **Patterns in real task data (Derek Jones, 2024 synthesis):**
  - Round-number heaping, with the ratios between common round numbers close to Fibonacci ratios.
  - Short tasks tend to be underestimated and long tasks overestimated.
  - Individuals are consistently over- or under-estimators.
  - About 30% of estimates are accurate, 68% within a factor of two, and 95% within a factor of four.
  - "developer estimation accuracy does not change with practice".
  - Jones calls most academic SEE research on tiny datasets "essentially fake research" and names Jørgensen as the one person doing good work
  - [Shape of Code, "What is known about software effort estimation in 2024", 10 Mar 2024](https://shape-of-code.com/2024/03/10/what-is-known-about-software-effort-estimation-in-2024/)

### Inferences
- **Hide anchors from estimators, human or AI.** Briefs often contain budgets, deadlines or "this should be quick" language. Jørgensen's results suggest stripping or masking client-stated hours or budgets before Jev makes its judgement. A/B testing Jev with and without the anchor present would quantify its susceptibility. That is a novel, publishable test.
- The product's empirical shared shock plus bias correction is essentially a statistical version of Jørgensen's "past accuracy distribution → pX" method. Presenting outputs as P50/P80/P90 matches the evidence better than a single number.
- Jones' finding that short tasks are underestimated and long ones overestimated, plus per-person bias, suggests the bias correction should depend on size and estimator (and on client or project), not be one global factor.
- The checklist effect (10% vs 38% underestimation) supports turning clause extraction into an explicit omitted-work checklist (testing, deployment, PM, meetings, data migration, rework) that flags what the brief doesn't mention.

### Gaps
- Jørgensen's 2020–2026 papers could not be listed: Simula moved its publication list to NVA, and Crossref was rate-limited. Specific recent findings (e.g. on sequence effects, or on LLMs as estimators) are not verified here.
- No primary source was found on whether LLMs show human-like anchoring in effort estimation.

---

## 3. Probabilistic forecasting practice (Monte Carlo, #NoEstimates, interval calibration, conformal prediction)

### Takeaway
Practitioners commonly run Monte Carlo simulations on historical throughput or cycle time (Magennis/Focused Objective tools, the #NoEstimates movement). Peer-reviewed evidence on how accurate these forecasts are is thin. Conformal prediction gives distribution-free, finite-sample coverage guarantees and has variants for drift over time, but **no software-effort-estimation paper using conformal prediction was found**. This looks like an open niche.

### Cited Findings
- Throughput, cycle-time and WIP forecasting tools exist as free spreadsheets: "take start date and complete date data and see the top 15 charts" — [FocusedObjective.Resources (Troy Magennis), GitHub](https://github.com/FocusedObjective/FocusedObjective.Resources)
- #NoEstimates appears in Jones' 2024 talk summary as a movement, but he gives no accuracy data for it — [Shape of Code 2024](https://shape-of-code.com/2024/03/10/what-is-known-about-software-effort-estimation-in-2024/)
- Prediction intervals for effort from Random Forest can be tuned for interval quality with meta-validation — [Bayley & Falessi 2018, arXiv:1801.07194](https://arxiv.org/abs/1801.07194)
- **Conformal prediction background:**
  - Split conformal gives distribution-free prediction bands around any regression model — [Lei, G'Sell, Rinaldo 2016/2018, arXiv:1604.04173](https://arxiv.org/abs/1604.04173)
  - Conformalized Quantile Regression (CQR) avoids "unnecessarily conservative" constant-width intervals by adapting width to the input — [Romano, Patterson, Candès 2019, arXiv:1905.03222](https://arxiv.org/abs/1905.03222)
  - Adaptive Conformal Inference keeps coverage online when "the data generating distribution is allowed to vary over time in an unknown fashion" — [Gibbs & Candès 2021, arXiv:2106.00170](https://arxiv.org/abs/2106.00170)
  - Tutorial: [Angelopoulos & Bates 2021, arXiv:2107.07511](https://arxiv.org/abs/2107.07511)
- arXiv searches for "conformal" with "effort" or "software engineering … estimation", and for "story point" with "uncertainty", returned no relevant SEE papers (searched Oct 2026 via the arXiv API) — [arXiv query](http://export.arxiv.org/api/query?search_query=all:conformal%20AND%20all:effort)

### Inferences
- The product's P10–P90 coverage of 82% against a nominal 80% is already well calibrated *marginally*. The next credibility step is **conditional calibration**: coverage and interval width split by work kind, client, task size and "tentative" flag. Mondrian (group-wise) conformal or CQR on top of the Monte Carlo quantiles would guarantee per-group coverage.
- Adaptive Conformal Inference fits the product's learning-from-actuals loop: after each closed task, update the interval multiplier so coverage stays near target as team, tools and AI-assisted development change.
- Monte Carlo on throughput (the #NoEstimates style) complements per-clause estimation at portfolio or schedule level. Calendar-time forecasting can be offered alongside hours.

### Gaps
- No peer-reviewed accuracy comparison was found between throughput-based Monte Carlo/#NoEstimates and effort-based estimation.
- No conformal-prediction SEE study was found. The absence may partly reflect limited search (arXiv only; web search failed).

---

## 4. Evaluation standards reviewers expect

### Takeaway
Reviewers expect absolute-error metrics (MAE/MAR, MdAE), Standard Accuracy (SA) against random guessing, and comparisons with simple baselines (Mean, Median, Random, plus stronger ones such as linear programming (LP4EE) and the automatically transformed linear model (ATLM)). They also expect non-parametric significance tests with effect sizes (Wilcoxon, Vargha–Delaney Â12), per-project reporting, and time-aware splits. MMRE is discouraged but still common (SEEAgent reports MMRE and PRED(50)). For intervals, report coverage alongside width.

### Cited Findings
- Shepperd & MacDonell propose evaluating prediction systems against a random-guessing baseline (Standard Accuracy) and argue against biased relative-error measures such as MMRE — [IST 2012, doi:10.1016/j.infsof.2011.12.008](https://doi.org/10.1016/j.infsof.2011.12.008)
- Linear programming (LP4EE) as a baseline — [Sarro & Petrozziello, TOSEM 2018, doi:10.1145/3234940](https://doi.org/10.1145/3234940). ATLM baseline — [Whigham, Owen, MacDonell, TOSEM 2015, doi:10.1145/2738037](https://doi.org/10.1145/2738037)
- Replications compare against Random, Mean and Median estimators and report MAE, MdAE and SA. Significance is counted per project (e.g. "8/42 cases") — [arXiv:2201.05401](https://arxiv.org/abs/2201.05401); [arXiv:2209.00437](https://arxiv.org/abs/2209.00437)
- Wilcoxon signed-rank with Â12 effect size per project — [Bui et al. 2025](https://arxiv.org/html/2509.14483v1). Wilcoxon and Kruskal–Wallis tests on per-project MAE — [Maha et al. 2026](https://arxiv.org/html/2604.03443v1)
- MdAE can hide differences: "MdAE values are almost the same for most of the projects, but the MAE values differ" — [Maha et al. 2026](https://arxiv.org/html/2604.03443v1)
- Time-aware evaluation (train only on completed, earlier work) — [Bosu et al. 2020](https://arxiv.org/abs/2012.01596)
- An everyday reference point: on real task datasets, about 30% of estimates are accurate, 68% within a factor of 2 and 95% within a factor of 4 — [Jones 2024](https://shape-of-code.com/2024/03/10/what-is-known-about-software-effort-estimation-in-2024/)

### Inferences
- **A credible benchmark report for The Estimator on SiP should include:**
  1. MAE, MdAE and SA versus a random-guessing baseline (MAR_P0)
  2. Baselines: Median, the **developer's own SiP estimate** (the strongest and most meaningful human baseline, since SiP contains estimates and actuals), the developer estimate × a global correction factor, and LP4EE/ATLM if features allow
  3. Percentage within a factor of 2 and PRED(25), so results can be compared with Jones' 68% figure
  4. Coverage *and* mean or median relative width of P10–P90 and P5–P95. Optionally the interval score or CRPS (proper scoring rules; no SEE source found).
  5. Wilcoxon signed-rank on per-task absolute errors with Â12 and bootstrap confidence intervals for the MAE difference
  6. Results by project and developer, plus a rolling-origin temporal evaluation rather than a single split
- The current headline (MAE 10.34 → 9.26 h) is a 10.4% reduction. It's unclear from the brief what the 10.34 baseline is. If it is the raw human estimate, say so. Beating the developers' own estimates on a temporal holdout is a strong claim that most papers do not make.

### Gaps
- No formal "reporting checklist" document specific to SEE from 2020–2026 was retrieved. The recommendations above are pieced together from the cited papers.

---

## 5. High-impact ideas for The Estimator to move past the state of the art

### Takeaway
The literature's weak points are: story points instead of hours, random splits, no calibrated uncertainty, susceptibility to anchoring, and no handling of requirement ambiguity. The product already covers several of these (hours, temporal holdout, Monte Carlo, bias learning). The most clearly differentiating next steps are calibrated, group-conditional intervals that adapt online; retrieval of the company's own similar past tasks as the outside view; anchor masking; and ambiguity detection linked to the value of asking clarifying questions.

### Cited Findings (evidence behind each idea)
- **Retrieval and examples:** search-optimised few-shot examples gave 59.34% lower MAE than zero-shot ([arXiv:2403.08430](https://arxiv.org/abs/2403.08430)). Scale-covering examples beat count-based ones ([arXiv:2603.06276](https://arxiv.org/html/2603.06276v2)). Plain RAG with a 3B model was not significantly better than baselines ([arXiv:2604.03443](https://arxiv.org/html/2604.03443v1)). Analogies naturally include unknown work ([Ch. 7](https://link.springer.com/chapter/10.1007/978-3-319-74953-2_7)).
- **Comparative judgements** need less annotation effort, give higher confidence and work as few-shot signals ([arXiv:2507.14642](https://arxiv.org/abs/2507.14642); [arXiv:2603.06276](https://arxiv.org/html/2603.06276v2)).
- **Anchoring** effects are large and resist warnings ([Ch. 5](https://link.springer.com/chapter/10.1007/978-3-319-74953-2_5)).
- **Uncertainty formats:** pX values and past-error-based intervals beat gut-feel intervals ([Ch. 6](https://link.springer.com/chapter/10.1007/978-3-319-74953-2_6)).
- **Checklists:** 10% vs 38% underestimation ([Ch. 7](https://link.springer.com/chapter/10.1007/978-3-319-74953-2_7)).
- **Recency weighting:** time-aware and moving-window models improve accuracy ([arXiv:2105.14179](https://arxiv.org/abs/2105.14179); [arXiv:2012.01596](https://arxiv.org/abs/2012.01596)).
- **Ambiguous requirements** degrade LLM code generation. There are 2026 benchmarks of whether LLMs ask clarifying questions ([arXiv:2604.21505](https://arxiv.org/abs/2604.21505); [ClarifyCodeBench, arXiv:2607.00711](https://arxiv.org/abs/2607.00711)), but none target estimation.
- **AI-agent development** changes cost structure, but models such as ACEM are uncalibrated ([arXiv:2608.02582](https://arxiv.org/abs/2608.02582)).
- **Interactive agents:** practitioners responded positively to LLM agents that discuss estimates ([arXiv:2509.14483](https://arxiv.org/abs/2509.14483)).

### Inferences (ranked proposals)
1. **Conformal layer on top of the Monte Carlo output**
   - Use split or Mondrian CQR per work kind, client and tentative flag, plus Adaptive Conformal Inference updated on each new actual.
   - Report group-wise coverage. Aim for "every subgroup within ±5 points of nominal coverage" as a headline no SEE paper reports.
2. **Outside-view retrieval**
   - Embed clauses and retrieve the k most similar *completed* tasks with their actual hours and estimate errors.
   - Use them (a) as scale-covering few-shot anchors for Jev and (b) as an empirical reference-class distribution blended with the PERT distribution.
   - Add recency weighting (Gaussian moving window).
3. **Anchor firewall**
   - Detect and mask client-stated budgets, hours and deadlines before Jev reasons, then show them after the estimate as a "client expectation gap" signal.
   - Run an ablation: Jev with vs without anchors on historical briefs.
4. **Ambiguity and omission detection, plus value-of-information clarification**
   - Score each clause for vagueness, tentativeness, missing acceptance criteria and missing non-functional requirements.
   - For each candidate question, estimate how much it would narrow the P10–P90 width, using the Monte Carlo variance contribution of that clause (a sensitivity or Sobol-style decomposition).
   - Ask only the top 3 questions. This turns "tentative" flags into the measurable outcome of hours of uncertainty removed per question.
5. **Omitted-work checklist** (PM, QA, deployment, meetings, migration, rework, client review cycles), each with a learned share of total hours. The evidence is the 10% vs 38% checklist result.
6. **Structured bias correction:** separate correction factors by task size (short tasks under, long tasks over), by estimator or team, and by client, with hierarchical shrinkage so sparse groups borrow from the global factor.
7. **pX-first output:** present P50/P80/P90 and the probability of meeting a given budget, using Jørgensen's "turn the question around" format. Example: "70% chance the job fits within 50–200% of the point estimate".
8. **Pairwise calibration from staff:** collect cheap "A is bigger than B" judgements on new briefs to calibrate Jev's scale when actuals are scarce (for new clients or new kinds of work).
9. **AI-assisted development factor:** track actuals by whether coding agents were used, and learn a multiplier rather than assume one. ACEM-style dimensions are an uncalibrated template.
10. **Publishable benchmark:**
    - SiP plus a private post-LLM-cutoff holdout from the company's own data.
    - Rolling-origin evaluation reporting MAE, MdAE, SA, within-2×, PRED(25), coverage, width and interval score.
    - Baselines: developer estimate, Median, LP4EE and a zero-shot LLM.
    - Wilcoxon with Â12 for significance.

### Gaps
- None of the proposals above has been evaluated in the published SEE literature (no conformal-SEE, VOI-clarification-SEE or anchor-masking-LLM-SEE papers were found). Their expected impact is inferred, not measured.
- No source quantified how much LLM-based ambiguity detection improves estimation accuracy.
