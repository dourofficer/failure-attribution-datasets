# Literature search A: error-targeted / failure-driven RL for LLM agents

- Search date: 2026-10-28
- Anchor: MiRL, arXiv:2610.35697 (Tian, Khan, Wang, Chen, Bansal; submitted 26 Oct 2026). Not re-summarized here.
- Verification: **VERIFIED** means I opened the arxiv.org abstract page, and for most entries the arxiv.org HTML full text too. **UNVERIFIED** means the item came only from search snippets or from memory.
- Model names such as "Qwen3.8-27B", "Qwen3.6-27B", "GPT-6.1 Sol" and "Claude Opus 5" are copied as the papers write them.
- Numbers come from the papers' own tables as read through a summarizing fetch. Where a paper's text and tables disagree, I say so. Check any figure against the PDF before quoting it in the report.

## 0. What MiRL itself says about this family (from its arXiv HTML)

- MiRL's Related Work cites, in this family, only R3, PivotRL, Lightman et al. (PRM800K), GiGPO and RaR. Its failure-analysis section cites MAST, AgentDebug, Who&When, AgenTracer and TermiGen.
- MiRL contrasts those failure-analysis papers ("used to evaluate, diagnose, or debug") with its own use of failure analysis "to choose training data". It runs no experimental comparison against any of them.
- MiRL does **not** cite the closest 2026 RL work found below:
  - R3L (2601.03715)
  - ELPO (2602.09598)
  - PivoARL (2607.03702)
  - SPROUT (2610.14405)
  - RTI (2610.13438)
  - SENTINEL (2606.12908)
  - Agent-World's diagnosis loop (2604.18292)
- MiRL details relevant to comparisons:
  - Localizer and teacher: Qwen3.8-27B. Annotator: Claude Opus 5. Training-time behavior judge: Gemini 3.8 Flash.
  - "Verified prefix" means **deterministic replay**: every command must reproduce its recorded output in a fresh container. 219 of 640 prefixes (34%) survived, from 189 environments.
  - That verifies the replay, not the error label. Whether the localized step is really where success drops is never checked counterfactually (contrast with ELPO and 2610.17633 below).
- Follow-ups to MiRL: none found. It was posted two days before this search.

## 1. Summary table (15 core entries)

| # | Paper | arXiv | Date / venue | Domain | Error localized by | Localization used for | Algo | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | PivoARL | 2607.03702 | Jul 2026, preprint | ALFWorld/WebShop/Minesweeper/SciWorld, search-QA | policy self-reflection (pivot turn index) | restart from pivot + prefix-only cross-episode credit | GiGPO | VERIFIED |
| 2 | R³L | 2601.03715 | Jan 2026 (v2 May), preprint | ALFWorld/WebShop/ScienceWorld, math | policy self-reflection (pivot turn index) | restart from pivot; gradient mask before pivot | GRPO variant | VERIFIED |
| 3 | ELPO | 2602.09598 | Feb 2026, preprint | tool-integrated math/sci/code | counterfactual rollouts, binary search for first irrecoverable step | branch tree at that step; hierarchical advantage; error-localized clipping | GRPO-family | VERIFIED |
| 4 | SPROUT | 2610.14405 | Oct 2026, preprint | SWE + terminal | actor in analyst/reviewer roles + verifier test feedback | resume from per-turn FS+context checkpoint; prefix-masked GRPO | GRPO-style | VERIFIED |
| 5 | RTI | 2610.13438 | Oct 2026, preprint | tool-use (τ²), navigation, Claw-Eval | policy as rubric-evidence validator (privileged) | rewrite flagged step, continue, swap into all-fail group | GRPO-modified | VERIFIED |
| 6 | PivotRL | 2603.21383 | Mar 2026, preprint | τ², SWE-V, Terminal-Bench, BrowseComp | none (outcome-variance filter on expert turns) | start-state selection at "pivot" turns | GRPO-style | VERIFIED |
| 7 | R3 (reverse curriculum) | 2402.05808 | Feb 2024 | math/reasoning | none (demo states) | start-state curriculum sliding backward | RL (PPO, from memory) | VERIFIED |
| 8 | CSO | 2602.03412 | Feb 2026, ACL 2026 Findings | deep-research web (GAIA, XBench) | LLM PRM (Claude 3.7) candidates + policy-continuation verification | DPO at verified critical steps only | DPO | VERIFIED |
| 9 | VPPO ("Save the Good Prefix") | 2601.18984 | Jan 2026, ACL 2026 Findings | math | PRM first step < 0.8 | credit boundary: reward prefix, zero suffix | GRPO | VERIFIED |
| 10 | Agent-R | 2501.11425 | Jan 2025, preprint | WebShop/SciWorld/TextCraft | actor self-judged first error in MCTS tree | splice bad prefix→good branch; SFT | iterative SFT | VERIFIED |
| 11 | EEF | 2504.13145 | Apr 2025, preprint | WebShop/SciWorld | counterfactual rollouts from states of failed expert trajectories | data selection: train from the first "needs-recovery" state | SFT/RFT | VERIFIED |
| 12 | IPR / STeCa | 2406.11176 / 2502.14276 | EMNLP 2024 / ACL 2025 Findings | WebShop/ALFWorld/InterCodeSQL/VirtualHome | MC step reward vs expert step reward | step-DPO (IPR); rewrite deviated step + reward-weighted PG (STeCa) | DPO / PG | VERIFIED |
| 13 | SENTINEL | 2606.12908 | Jun 2026, preprint | tool-use (τ²-Retail) | LLM Controller → 12-category failure taxonomy | targeted task synthesis (curriculum) | GRPO | VERIFIED |
| 14 | Agent-World (self-evolving arena) | 2604.18292 | Apr 2026, preprint | MCP tool-use | diagnosis agent (GPT-OSS-120B) over failure traces | rank weak envs + targeted task synthesis | GRPO | VERIFIED |
| 15 | FailForge | 2608.08570 | Aug 2026, preprint | SWE-bench Verified | agent diagnosis from error feedback + traces → "skill" | hinted retry; keep successes for RFT with hint stripped | RFT (SFT) | VERIFIED |

## 2. Detailed entries

### 2.1 Localize, then restart or branch RL rollouts from the error state

#### 1. PivoARL: "Agent Reinforcement Learning via Pivotal-Aware Self-Feedback Retry" (VERIFIED)
- **arXiv:** 2607.03702
- **Date and venue:** 4 Jul 2026, preprint. Authors: Guo, Shi, Zhang, Zhu, Zhang, Li. Code: github.com/yuki-younai/PivoARL.
- **Domain:**
  - Text agents: ALFWorld, WebShop, Minesweeper, SciWorld.
  - Search-QA: NQ, HotpotQA, TriviaQA, PopQA, 2Wiki, MuSiQue, Bamboogle.
- **How the error is localized:**
  - After a failed episode, the **policy itself** gets a reflection prompt.
  - It outputs a pivotal turn index k* (the earliest wrong action) plus a remark with an improved plan.
  - There is no external judge and no counterfactual check.
  - The reflection is trained too: its reward is the return of the retry it produces, gated on success and format.
- **How it is used in training:**
  - *Start-state selection:* the next episode reuses the prefix up to k* and regenerates from k*, conditioned on the remark. Up to 3 episodes are run, stopping early on success.
  - *Credit ("pivotal isolation"):* steps before k* get their own return plus the discounted return of the successful retry (γ_traj = 0.6). Steps at or after k* get only their own return.
  - Reflection tokens get a separate group-normalized advantage.
- **Algorithm:** GiGPO by default (compatible with GRPO).
- **Base model:** Qwen3-4B, non-thinking mode.
- **Key results (from the tables):**
  - Agent-task average: 83.9 vs GiGPO 73.9, MetaRL 75.9, GRPO 67.9.
  - Minesweeper Suc@1/Suc@3: 48.4/78.1 vs GiGPO 42.2/48.4.
  - Search-QA average Pass@3: 56.9 vs MetaRL 51.0 and GiGPO 47.2.
  - Caveat: the abstract and the text disagree with the tables. The headline gain over MetaRL is given as 11.5% in one place and 10.5% in another, and the Minesweeper gain as ">45%" in one place and "27.7%" in another.
- **Relevance:** This is the nearest RL analogue of MiRL's "restart from the error prefix". It differs in two ways:
  - The localizer is the policy's own self-attribution, trained jointly with the policy.
  - Errors are handled one episode at a time, not clustered across environments.
- Its stated limitation, dependence on accurate pivot localization, is exactly the failure-attribution question.

#### 2. R³L: "Reflect-then-Retry RL with Language-Guided Exploration, Pivotal Credit, and Positive Amplification" (VERIFIED)
- **arXiv:** 2601.03715
- **Date and venue:** 7 Jan 2026 (v2 22 May 2026), preprint. Authors: Shi, Chen, Li, Pan, Sun, Xu, Zhou, Li.
- **Domain:**
  - Agents: ALFWorld, WebShop, ScienceWorld.
  - Math: trained on DAPO; evaluated on GSM8K, MATH500, Minerva, OlympiadBench, AMC23.
- **How the error is localized:**
  - The policy writes a structured self-diagnosis of its own trajectory.
  - The diagnosis contains an outcome label (success / success but inefficient / failure), a root cause, suggestions, and **k_pivot**, the turn where the problem first appeared.
- **How it is used in training:**
  - *Restart:* the policy restarts at k_pivot, conditioned on guidance built from the diagnosis.
  - *Training pair:* the original prefix plus the corrected suffix, **with the guidance stripped out** (hindsight-style internalization).
  - *Pivotal Credit:* tokens before k_pivot get gradient mask 0.
  - *Positive Amplification:* positive advantages are scaled by α = 3.
  - An SFT loss is added on verified reflection and retry data.
- **Algorithm:** GRPO variant with no importance sampling and no KL.
- **Base models:** Qwen2.5-1.5B-Instruct, Qwen2.5-7B-Instruct, Qwen3-4B, plus Llama-3.2-3B in the appendix.
- **Key results vs GRPO:**
  - 1.5B: ALFWorld 0.720 → 0.928; WebShop 0.614 → 0.663; GSM8K 0.474 → 0.721.
  - 7B: ALFWorld 0.933 → 0.948; WebShop 0.709 → 0.757.
  - The abstract claims 5–52% relative gains overall.
- **Relevance:** This is the earliest 2026 instance found of the full pattern: self-localize the pivot, restart there, and mask credit on the prefix. It shows the "strip the hint" trick that MiRL's teacher-corrected prefixes could also use.

#### 3. ELPO: "Learning from the Irrecoverable: Error-Localized Policy Optimization for Tool-Integrated LLM Reasoning" (VERIFIED)
- **arXiv:** 2602.09598
- **Date and venue:** 10 Feb 2026, preprint. Authors: Liang, Zhu, Ge, Yang, Shen, Zheng, Guo.
- **Domain:** tool-integrated reasoning with a Python tool: AIME24/25, MATH500, GSM8K, MATH, GPQA-Diamond, LiveCodeBench v6.
- **How the error is localized:**
  - It uses **counterfactual rollouts**: a binary search over the tool-call steps of a failed trajectory.
  - At each anchor step it fixes the prefix and samples suffixes. If any suffix succeeds, the prefix counts as recoverable and the search moves later; otherwise it moves earlier.
  - The search returns the **first irrecoverable step** in O(log K) probes.
  - Budget: one failed trajectory per cycle, chosen by an entropy-gap score, with more samples at anchors with high post-tool entropy.
  - The authors note that finite sampling can miss rare successes.
- **How it is used in training:**
  - The probes form a rollout tree that branches at the localized step, so localization doubles as start-state reuse within the 16-rollout budget.
  - *Hierarchical advantage:* A = 0.5·A_branch + 0.5·A_traj. A_branch normalizes each child against its siblings.
  - *Error-localized adaptive clipping:* the lower clip bound is loosened by 0.115 for all tokens from the critical step to the end, which strengthens suppression of the error suffix.
- **Algorithm:** GRPO-family, run in VERL with KL = 0.
- **Base models:** Qwen2.5-7B-Instruct and Qwen3-4B-Instruct-2507, both after cold-start SFT.
- **Key results:**
  - Average (7B): 60.7 vs DemyAgent 59.4, ARPO 55.9, GiGPO 54.0, GRPO 51.2.
  - AIME24 (7B): 48.1 vs GRPO 23.3.
  - Average (4B): 72.6 vs DemyAgent 71.9.
  - The margin over the strongest baseline is modest, and the text overstates it relative to the table.
  - Ablation on AIME24/25: removing the binary-search localization drops 48.1/31.1 to 45.8/29.1.
  - Fig. 1 (motivation, no numbers extracted): editing the **first irrecoverable** step recovers failed trajectories much more often than editing a random step or the "first error".
- **Relevance:** This is the clearest example of a **counterfactual, "point-of-no-return" definition of the decisive step used directly as an RL signal**. It operationalizes the gap between "first error" (Who&When-style labels) and "first irrecoverable error", which is central to the failure-attribution survey.

#### 4. SPROUT: "Scaling Agentic RL for Long-Horizon Software Engineering" (VERIFIED)
- **arXiv:** 2610.14405
- **Date and venue:** 9 Oct 2026, preprint (cs.SE). Authors: Liu, Wang, Nan, Wu, Li, Huang, He, Jiang, Dong.
- **Domain:** coding and terminal: DeepSWE, **Terminal-Bench 2.1**, SWE-bench Pro v2 Hard.
- **How the error is localized:**
  - The **actor model itself** works in two role prompts.
  - As "analyst", it reads one failed attempt together with the binary reward and verifier diagnostics such as failing tests.
  - As "reviewer", it reads the archive of attempts and their analyses.
  - The reviewer selects up to K branches. Each names a parent attempt and a turn boundary, and comes with a replacement "starting turn".
- **How it is used in training:**
  - The **filesystem and agent context are checkpointed after every assistant turn**, so a branch resumes from the true environment state.
  - Per task, the GRPO group has two independent roots and three retained children per root.
  - Children's loss masks cover only turns after the branch point.
  - In all-fail groups, children get the raw reward instead of a normalized advantage.
  - The learner never sees the review context. The authors call the result a distillation surrogate, not strictly on-policy training.
- **Algorithm:** GRPO-style clipped surrogate, no KL.
- **Base model:** Qwen3.8-27B (as written).
- **Key results vs basic GRPO:**
  - Terminal-Bench 2.1: 64.0 vs 39.3 (base model 49.4).
  - SWE-bench Pro v2 Hard: 84.3 vs 74.5.
  - DeepSWE: 40.7 vs 33.6.
  - Average gain +13.9 points; time per training step 3.77 h → 2.28 h.
- **Relevance:** SPROUT solves the infrastructure problem MiRL raises, that a stored prefix does not give you the container state at step k. It does so with snapshots instead of deterministic replay, which avoids MiRL's 66% prefix loss. Its backtracking choice is a verifier-grounded self-attribution step, in the same domain as MiRL. It is the most direct competitor MiRL omits.

#### 5. RTI: "Rollout-Time Intervention: Unlocking Agentic RL Beyond Policy Limits" (VERIFIED)
- **arXiv:** 2610.13438
- **Date and venue:** 9 Oct 2026 (v2 12 Oct), preprint. Authors: Chen, Ding, Wang, …, Xie, Xiong.
- **Domain:**
  - Tool-use: τ²-Bench Telecom, Retail and Airline.
  - Navigation: map-routing on real map APIs.
  - Claw-Eval-Hard20.
- **How the error is localized:**
  - It triggers only when **every rollout in a GRPO group fails**.
  - A "Reward-Oriented Trajectory Validator", by default the policy itself, checks each step against reward-side evidence (rubrics, evaluation criteria, required actions).
  - It flags task-critical deviations and returns a diagnosis and a suggested next step.
  - This is **privileged-information attribution**: the localizer sees the grader's criteria.
- **How it is used in training:**
  - A Corrector minimally rewrites the flagged step.
  - A Verifier rejects corrections that leak privileged information or fabricate tool results.
  - The rollout then continues from the corrected step. If it succeeds, it replaces one failed member of the group.
  - Off-policy control: a perplexity gate (δ = 5) on the corrected step, plus token reweighting.
- **Algorithm:** modified GRPO.
- **Base models:** Qwen3-8B and Qwen3.5-9B.
- **Key results:**
  - Qwen3-8B Pass@1: Navigation 35.33 → 57.33; Telecom 36.84 → 61.40; Claw-Eval-Hard20 22.50 → 50.00. The extract does not make clear whether "from" is the base model or GRPO.
  - Qwen3.5-9B on Claw-Eval-Hard20: 85.00 vs GRPO 52.50 and LUFFY 61.25.
- **Relevance:** RTI is "error-step rewriting, then RL" inside the rollout loop. It is close to MiRL's teacher correction of flagged steps, but the corrected step becomes a positive sample rather than a restart state. It also shows that a rubric-aware localizer can rescue groups where every rollout fails.

#### 6. PivotRL: "High Accuracy Agentic Post-Training at Low Compute Cost" (VERIFIED)
- **arXiv:** 2603.21383
- **Date and venue:** 22 Mar 2026, preprint (NVIDIA). Adopted in Nemotron-3-Super post-training.
- **Domain:** τ²-Bench, SWE-Bench Verified, Terminal-Bench, BrowseComp.
- **How the error is localized:** it is **not localized**.
  - Candidate turns come from SFT expert trajectories.
  - For each turn, K local rollouts are sampled under the frozen reference policy.
  - "Pivots" are turns with nonzero reward variance and low mean reward, i.e. turns the policy sometimes fails.
  - Turns the policy always fails are excluded because they have zero variance.
- **How it is used in training:**
  - *Start-state selection:* short single-turn rollouts from pivot states.
  - *Reward:* a binary local verifier of "functionally equivalent" actions (string/schema checks, equivalence rules, or LLM-as-judge).
- **Algorithm:** GRPO-style with KL.
- **Base model:** Qwen3-30B-A3B-Thinking-2507.
- **Key results (Base / SFT / PivotRL):**
  - τ²-Bench: 44.35 / 58.44 / 63.81.
  - SWE-V: 19.07 / 37.40 / 32.67 (below SFT).
  - Terminal-Bench: 5.42 / 13.75 / 20.00.
  - BrowseComp: 2.50 / 1.50 / 11.30.
  - Out-of-domain change: SFT −9.83, PivotRL +0.21.
  - On SWE it matches end-to-end RL (32.67) with about 4× fewer rollout turns.
- **Relevance:** PivotRL is the "outcome-variance instead of attribution" baseline for choosing start states, and it is MiRL's main conceptual comparator. Its pivot states come from expert trajectories, not from the policy's own failures.

#### 7. R3: "Training LLMs for Reasoning through Reverse Curriculum RL" (VERIFIED)
- **arXiv:** 2402.05808
- **Date and venue:** 8 Feb 2024. ICML 2024 from my memory; the arXiv page lists no venue (venue UNVERIFIED).
- **Domain:** math and general reasoning (8 tasks), plus program-based GSM8K.
- **How the error is localized:** it is not. Start states come from correct demonstrations.
- **How it is used in training:** a start-state curriculum that slides backward from the end of the demonstration toward its beginning, so outcome reward acts as a step-level signal.
- **Algorithm:** outcome-reward RL; PPO from memory, since the abstract does not name it.
- **Base models:** Llama2-7B and CodeLlama-7B, among others.
- **Key results:** +4.1 points average over the RL baseline on 8 tasks; +4.2 on program-based GSM8K across 3 backbones.
- **Relevance:** R3 is the progenitor of "RL from intermediate states". It starts from demonstration states and has no attribution.

### 2.2 Localize the error step, then use it for preferences, credit, or data (offline or non-restart)

#### 8. CSO: "Verified Critical Step Optimization for LLM Agents" (VERIFIED)
- **arXiv:** 2602.03412
- **Date and venue:** 3 Feb 2026 (v2 Apr 2026), **ACL 2026 Findings**. Authors: Li, Zeng, Fang, Liang, Song, Liu, Mi, Yu (Tencent).
- **Domain:** deep-research web agents: GAIA-Text-103, XBench-DeepSearch.
- **How the error is localized:**
  - *Candidates:* an LLM PRM (Claude 3.7 Sonnet with a rubric) scores the policy's action and 5 expert alternatives at each step of a failed trajectory. A step is a candidate if the policy scores below 0.45 and the best alternative above 0.65.
  - *Verification:* the policy continues from each alternative, and only alternatives that reach the correct outcome are kept. This is a counterfactual check of policy reachability.
- **How it is used in training:**
  - DPO pairs only at verified critical steps: the expert alternative is preferred over the policy's original action.
  - About 16% of steps are supervised.
  - Two iterative rounds (the paper is internally inconsistent: elsewhere it says four).
- **Algorithm:** DPO, β = 0.5.
- **Base model:** CK-Pro-8B, an SFT of Qwen3-8B.
- **Key results:**
  - GAIA-Text-103: 49.5 vs SFT 35.9, IPR 44.6, Step-DPO 38.9, ETO 38.9.
  - XBench-DeepSearch: 29.0 vs SFT 23.0 and IPR 24.0.
- **Relevance:** CSO is the hybrid the evidence in 2610.17633 argues for: judge-proposed error steps, then verified by counterfactual continuation. It also starts from the policy's own failures, as MiRL does.

#### 9. VPPO: "Save the Good Prefix: Precise Error Penalization via Process-Supervised RL" (VERIFIED)
- **arXiv:** 2601.18984
- **Date and venue:** 26 Jan 2026, **ACL 2026 Findings**. Authors: Haolin Liu et al. (Tencent AI Lab, UVA).
- **Domain:** math: AIME24/25, AMC23, MATH-500, Minerva, OlympiadBench, HMMT.
- **How the error is localized:** a PRM (Qwen2.5-Math-PRM-7B). The first step scoring below 0.8, a threshold tuned on ProcessBench, counts as the first error.
- **How it is used in training:**
  - The localization serves **only as a credit boundary**; PRM scores are never maximized as rewards.
  - Incorrect responses get reward α = 0.5 on a *shortened* good prefix, and the suffix gets 0.
  - Advantages are mean-subtracted without std normalization, with a ReLU for instruct models.
  - Rewarding the full prefix caused "step inflation": the model split its reasoning into many micro-steps to collect reward.
- **Algorithm:** GRPO.
- **Base models:** Qwen3-4B-Base, Qwen3-8B-Base, Qwen3-4B.
- **Key results:**
  - Avg@16 vs GRPO: 35.4 vs 33.7; 38.0 vs 36.6; 44.8 vs 42.9.
  - AIME Pass@128 (4B-Base): 49.9 → 53.4.
  - PRM-as-reward baselines underperform GRPO.
- **Relevance:** a warning that any reward built on a localizer gets hacked (step inflation). The same risk applies to MiRL's behavior-judge reward.

#### 10. Agent-R: "Training Language Model Agents to Reflect via Iterative Self-Training" (VERIFIED)
- **arXiv:** 2501.11425
- **Date and venue:** 20 Jan 2025 (v3 Mar 2025), preprint. Authors: Yuan, Chen, Xi, Ye, Du, Chen (Fudan, ByteDance Seed).
- **Domain:** WebShop, SciWorld, TextCraft (via AgentGym).
- **How the error is localized:** the **actor model judges its own failed trajectory** and flags the first step it considers wrong, within its current capability. MCTS supplies the trees and rewards, but not the error location.
- **How it is used in training:**
  - The bad trajectory is cut at the flagged step, a revision phrase is inserted, and the good branch from the shared parent node is appended.
  - The model is then fine-tuned on these revision trajectories, mixed with good trajectories and general data.
- **Algorithm:** iterative SFT, 3 iterations.
- **Base model:** Llama-3.1-8B-Instruct.
- **Key results:** average 70.71 vs ETO 65.12 and Direct-Revision 62.36. The trained models also loop less and detect errors earlier.
- **Relevance:** an offline version of "train recovery at the self-attributed error step". Localization quality is self-referential and never validated.

#### 11. EEF: "Exploring Expert Failures Improves LLM Agent Tuning" (VERIFIED)
- **arXiv:** 2504.13145
- **Date and venue:** 17 Apr 2025, preprint. Authors: Lan, Bai, Cheng, Hsieh, Zhou.
- **Domain:** WebShop, SciWorld.
- **How the error is localized:**
  - **Counterfactual rollouts** start from M evenly spaced states of *failed expert* trajectories.
  - The key state is the first i* where the policy succeeds from s_{i*−l} but fails from s_{i*}.
  - The segment in between is treated as containing a harmful action.
- **How it is used in training (data selection):**
  - For each key state, one successful solution is chosen.
  - Training covers only actions from that state onward; earlier actions are masked, which excludes the harmful segment.
- **Algorithm:** SFT/RFT.
- **Base models:** Llama-3-8B-Instruct, plus Mistral-7B.
- **Key results:**
  - WebShop-11k win rate: 62.0% vs RFT×6 53.6% and ETO 42.0%.
  - SciWorld: 68.5 vs 62.5.
- **Relevance:** an early rollout-based "point of no return" localizer, about a year before ELPO and 2610.17633, used here for data selection.

#### 12. IPR and STeCa (step-level Monte Carlo deviation detection) (both VERIFIED)
- **IPR: "Watch Every Step! LLM Agent Learning via Iterative Step-Level Process Refinement"**
  - arXiv 2406.11176; EMNLP 2024 Main.
  - Localization: the agent explores along expert trajectories, and step rewards are estimated by Monte Carlo (N = 5). A step counts as an error if its reward is lower than the expert step's by more than τ and the trajectory's outcome is also worse.
  - Training: outcome-DPO + step-DPO + SFT.
  - Base model: Llama-2-7B, on WebShop, InterCodeSQL and ALFWorld.
  - Result: average 69.4 vs ETO 66.4 and SFT 60.6.
- **STeCa: "Step-level Trajectory Calibration for LLM Agent Learning"**
  - arXiv 2502.14276; ACL 2025 Findings.
  - Localization: Monte Carlo step reward (N = 5) below the expert's → the **first deviated step**.
  - Training: GPT-4o reflection rewrites that step (ground-truth action plus a reflective thought). Calibration trajectories, expert sub-trajectories and successful runs are then used in reward-weighted policy-gradient training.
  - Base model: Llama-2-7B-Chat, on ALFWorld and VirtualHome.
  - Result: average 70.9 vs IPR 68.6, ETO 66.9, SFT 63.3.
- **Relevance:** these are the 2024–25 roots of "localize a deviation by MC rollouts, then rewrite at that step". They are anchored to expert trajectories rather than the policy's own failures.

### 2.3 Error profile drives which tasks or environments to train on (curriculum)

#### 13. SENTINEL: "Failure-Driven RL for Training Tool-Using Language Model Agents" (VERIFIED)
- **arXiv:** 2606.12908
- **Date and venue:** 11 Jun 2026, preprint. Authors: Wang, Lu, Zhang, …, Manling Li, Jing Huang, Dakuo Wang.
- **Domain:** tool-use, τ²-Bench Retail.
- **How the error is localized:**
  - An LLM Controller runs every 12 rollout batches; the model is not named.
  - It analyzes failed rollouts (reward below 0.5) using the scenario, gold actions, the Solver's tool calls, the reward breakdown and the message history.
  - It emits a **12-category failure taxonomy**, e.g. wrong_item_selection, missing_write_action, policy_violation, premature_termination. Each pattern has a frequency, examples and a root cause.
  - It tracks persistent vs resolved weaknesses across rounds.
  - There is **no per-step localization**.
- **How it is used in training:**
  - A Proposer synthesizes up to 10 executable tasks per trigger that "specifically exercise the failure patterns", favoring boundary cases that combine a mastered skill with an unresolved failure.
- **Algorithm:** GRPO (Slime framework).
- **Base model:** Qwen3-4B-Thinking-2507.
- **Key results (Pass^1 / Pass^2 / Pass^3):**
  - Base: 66.4 / 51.6 / 43.2.
  - General RL: 69.0 / 55.6 / 47.4.
  - SENTINEL: 74.9 / 60.5 / 51.2.
  - From an SFT start, Pass^1 is 78.1 vs 68.1 for General RL.
  - Caveat: no ablation isolates the Controller, and the General-RL baseline uses a different task source.
- **Relevance:** the closest analogue of MiRL's "cluster error steps into recurring misbehaviors". It uses the profile to *synthesize new tasks* instead of choosing restart states or adding a behavior reward.

#### 14. Agent-World: "Scaling Real-World Environment Synthesis for Evolving General Agent Intelligence" (VERIFIED)
- **arXiv:** 2604.18292
- **Date and venue:** 20 Apr 2026, preprint, work in progress. Authors: Dong, Lu, …, Wen, Dou.
- **Domain:** MCP and tool environments: τ²-Bench, BFCL-V4, MCP-Mark, and 23 benchmarks in total.
- **How the error is localized:**
  - An auto-diagnosis **agent** (GPT-OSS-120B with Python and search tools) reads failure traces, validator feedback and per-environment error distributions by taxonomy category.
  - It groups failures by root cause and **ranks weak environments**, returning task-generation guidelines as JSON.
  - It works on whole traces, with no step-level localization.
- **How it is used in training:**
  - Environment selection plus targeted task re-synthesis, including database "complexification" when the weakness comes from limited state diversity.
  - Training then continues with GRPO.
- **Base models:** Qwen3-8B/14B (Agent-World-8B/14B); the evolution runs start from Agent-World-14B and EnvScaler-8B.
- **Key results (Agent-World-14B, base → +1 → +2 rounds):**
  - τ²-Bench: 60.2 → 63.5 → 65.4.
  - MCP-Mark: 29.5 → 36.3 → 38.1.
  - Caveat: the text and the table give different absolute numbers, and no ablation isolates the diagnosis step.
- **Relevance:** "select environments by error profile" at scale. The attribution is coarse (environment and category level).

#### 15. FailForge: "Distilling Procedural Competence from Persistent Failures into Code Agents" (VERIFIED)
- **arXiv:** 2608.08570
- **Date and venue:** 9 Aug 2026, preprint. Authors: Lv, E, Cai, …, Nan Duan.
- **Domain:** SWE-bench Verified.
- **How the error is localized:** an agent diagnoses each failed instance from error feedback and execution traces, then distills the diagnosis into a "skill". The abstract describes no step-level localization.
- **How it is used in training:**
  - The skill is injected for a guided second attempt.
  - Successful guided trajectories are added to the RFT corpus **with the skill removed** (hindsight distillation).
- **Algorithm:** RFT/SFT (not RL).
- **Base model:** Qwen3.5-4B, the same size class as MiRL.
- **Key results:** recovers more than 26% of previously failed instances; +6.6 points resolve rate over a strong RFT baseline, with gains concentrated on the hardest problems.
- **Relevance:** failure diagnosis used as a hint generator rather than an error locator.

## 3. Secondary / context papers (shorter)

### Directly relevant cautions and counterpoints
- **"Executable Prefix Values for Locating Agent Failures"**, arXiv 2610.17633, 13 Oct 2026 (VERIFIED). This is the most important caution for MiRL-style training.
  - *Setup:* mini-swe-agent with Qwen3.6-27B (and Qwen3.5-9B) on 150 SWE-bench Verified tasks. Trajectories are replayed in fresh containers (about 74% replay cleanly), and V(h_t) is estimated with adaptive bisection, averaging 331 continuations per curve.
  - *Judges disagree:* LLM judges using a first-mistake rubric agree on the exact step in only 21/57 trajectories.
  - *Judges mark symptoms:* for 66% of judge labels, success probability does not drop at the labeled step. Only 7/162 labels name the decisive step.
  - *Restart test:* restarting at the measured restart point raises expected success from 0.44 to 0.57. Restarting at a judge's label changes it by −0.03 to −0.08.
  - *Implication:* LLM-judge localizers (MiRL's Qwen3.8-27B localizer, AgentDebug, Who&When-style labels) may pick restart states after the real decision point.
  - The paper cites a "Prefix Sampling (Zhu et al., 2026)" RL method that resamples from prefixes. **I could not locate that paper**, so its id is unknown.
- **"Environment Evolution for Terminal Agents"**, arXiv 2609.04128, Sep 2026 (VERIFIED). A counterpoint.
  - It evolves terminal environments off-policy (scenario novelty, skill rarity, length), not from the policy's weaknesses.
  - Its weakness-based co-evolution baseline (re-synthesizing every 50 RL steps) scores lower: offline peak 71.5 vs 62.9 (Qwen3.6-27B) and 64.9 vs 55.1 (35B-A3B).
  - Terminal-Bench 2.1 gains: +14.4 and +18.0 points.
  - It cites the earlier weakness-based co-evolution line: EnvGen 2403.12014, AgentGen 2408.00764, GenEnv 2512.19682, COvolve 2603.28386, SPADE 2608.19197 (I did not open EnvGen, AgentGen or COvolve).
- **FC-SWE: "Failure-Conditioned RL for Long-Horizon SWE Agents"**, arXiv 2610.07898, Oct 2026 (VERIFIED abstract).
  - Uses whole-patch failure plus verifier feedback as context for a recovery attempt from the original repository state. No step localization.
  - GRPO with trajectory-local rewards and active-set advantages, on Qwen3.5-4B with SWE-agent.
  - SWE-bench Verified Resolved@1/@2: 41.7/52.8 vs GRPO 38.9/48.5.
- **OPRD: "On-Policy Reminder Distillation for Long-Horizon Coding Agents"**, arXiv 2610.21496, Oct 2026 (VERIFIED abstract).
  - A teacher re-evaluates the student's own failed prefixes and gives reverse-KL supervision conditioned on reminders: turn-local reminders tied to the relevant observation, plus a global reminder from test diagnostics.
  - Qwen3.5-4B: +11.3 points average resolution across SWE-bench Verified, Pro and Multilingual; error events 446 → 222.
  - The exact localization mechanism is not given in the abstract.

### Lineage MiRL already cites (verified)
- **DataEnvGym**, arXiv 2410.06215; Khan, Stengel-Eskin, Cho, Bansal; ICLR 2025 Spotlight.
  - Teacher data-generation agents receive student feedback (errors or weak skills) each iteration and generate targeted data.
  - Domains: math, code, VQA, tool-use.
  - The direct precursor of MiRL's "error profile → training data" idea, from the same group.
- **LLM2LLM**, arXiv 2403.15042; Lee et al.; ACL 2024 per the arXiv comment.
  - The teacher generates new examples from the student's wrong predictions.
  - Llama-2-7B, gains of up to +24.2% on GSM8K in the low-data regime.
- **GiGPO**, arXiv 2505.10978; NeurIPS 2025.
  - Step-level advantages from anchor states that recur across rollouts. Credit assignment without attribution.
  - Qwen2.5-1.5B/3B/7B: more than +12% on ALFWorld and +9% on WebShop vs GRPO.

### Failure-driven curriculum and problem synthesis (single-turn or web)
- **SwS**, arXiv 2506.08989, Jun 2025 (VERIFIED).
  - Problems the model repeatedly fails during RL → extract core concepts → synthesize new problems.
  - +10.0 (7B) and +7.7 (32B) average across 8 reasoning benchmarks.
- **WebRL**, arXiv 2411.02337, ICLR 2025 (VERIFIED).
  - A self-evolving curriculum generates new tasks from failed attempts, with an outcome reward model.
  - WebArena-Lite: Llama-3.1-8B 4.8 → 42.4; GLM-4-9B 6.1 → 43.0.
- **LEMMA**, arXiv 2503.17439, ACL 2025 Findings (VERIFIED).
  - Error-type-based mistake augmentation plus reflection links to corrections; SFT on math.
- **Step-DPO**, arXiv 2406.18629 (VERIFIED). Step-level preference optimization on Qwen2-72B-Instruct; MATH 70.8. The abstract does not describe how the first error step is found.
- **TermiGen**, arXiv 2602.07274, Feb 2026 (VERIFIED). A Generator-Critic protocol **injects errors** while collecting terminal trajectories, to create error-correction cycles for SFT. Qwen2.5-Coder-32B, 31.3% on Terminal-Bench. MiRL cites it.

### Self-correction RL (no explicit error localization)
- **SCoRe**, arXiv 2409.12917, Sep 2024 (VERIFIED). Multi-turn online RL for self-correction on Gemini 1.0 Pro and 1.5 Flash: +15.6% MATH, +9.1% HumanEval. Whole-attempt correction, with no step localization.
- **Critique-GRPO**, arXiv 2506.03106, ICML 2026 Spotlight per the arXiv comment (VERIFIED). Natural-language critiques plus critique-guided refinements inside online RL. The abstract does not say whether the critiques localize the error.

### Failure attribution papers, and whether they are used as training signals
- **AgenTracer**, arXiv 2509.03312, ICLR 2026 (VERIFIED via search results, ICLR proceedings PDF and arXiv HTML link; I did not fetch the abstract myself).
  - It trains an attributor (Qwen3-8B, GRPO) on counterfactual-replay and fault-injection labels. It does not train the agent.
- **AgentDebug: "Where LLM Agents Fail and How They Can Learn From Failures"**, arXiv 2509.25370 (VERIFIED; ICML 2026 per the icml.cc listing in search results).
  - Taxonomy, AgentErrorBench, and root-cause isolation with corrective feedback.
  - Up to +26% relative task success. The gains appear to be test-time; weight training is not stated.
- **"Who Gets the Reward & Who Gets the Blame? Evaluation-Aligned Training Signals for Multi-LLM Agents"**, arXiv 2511.10687, NeurIPS 2025 LAW workshop (VERIFIED).
  - A **conceptual** proposal: Shapley credit for successful runs, and *first-error localization → repair-aware preferences* for failed runs.
  - No experiments. It is the only paper found that explicitly proposes Who&When-style attribution as a multi-agent training signal.
- **"Repair or Resample? Rethinking Failure Debugging in LLM MAS"**, arXiv 2608.25920 (VERIFIED abstract).
  - Shows that whole-trajectory reruns "repair" mostly by chance: 6.90% repair vs 20.15% for anchor-based intervention.
  - Evaluation only, no training.

### Other 2026 adjacent methods (abstract-level verification only)
- **UI-Voyager**, arXiv 2603.24533 (GUI, AndroidWorld 81.0% with a 4B model). "Group Relative Self-Distillation" finds fork points in group rollouts and corrects failed trajectories with successful ones. The abstract does not say how the fork points are found.
- **ReGRPO**, arXiv 2606.31392 (tool-using VLMs, GTA and GAIA). Executes near-miss actions to build (ErrorType, Evidence, FixPlan) triplets for SFT, then group-relative RL on reflection and corrective actions.
- **CLEANER**, arXiv 2601.15141. Replaces failed code-execution steps with the model's later self-corrections before optimization ("self-purified" trajectories).
- **VSR (Variance-Optimal State Resampling)**, arXiv 2610.15888. Resamples start states from a prefix replay buffer in proportion to state visitation times outcome standard deviation, and a reverse curriculum emerges. Beats GRPO and GiGPO on math, Sokoban and BabyAI. This is the principled form of PivotRL's variance filter.
- **PATR (Process-Scorer Guided Adaptive Tree Rollout)**, arXiv 2607.15610. Branches from *promising* partial trajectories rather than erroneous ones, on FrozenLake and SWE-Bench. A useful contrast.

### Ids I recall but did not open (UNVERIFIED)
- ETO, 2403.02502 (I opened the abstract: ACL 2024; trajectory-level DPO with no step localization, so it is effectively verified as a baseline).
- NAT ("Learning From Failure: Integrating Negative Examples when Fine-tuning LLMs as Agents"), 2402.11651: not opened.
- EnvGen, 2403.12014: not opened (its id is cited in 2609.04128).
- AgentGen, 2408.00764: not opened.
- COvolve, 2603.28386: not opened.

## 4. Synthesis for "failure attribution as a training signal"

- **How the error gets localized, roughly from weakest to strongest evidence:**
  1. *Self-reflection by the policy:* PivoARL, R³L, SPROUT (with verifier feedback), RTI (with rubric evidence), Agent-R. Cheap, and can be trained jointly, but never validated.
  2. *LLM judge or PRM:* MiRL (Qwen3.8-27B localizer), CSO's candidate step, VPPO (math PRM threshold).
  3. *Taxonomy or clustering of whole traces:* SENTINEL (12 categories), Agent-World (weak-environment ranking), MiRL (8 recurring misbehaviors, a step-level cluster).
  4. *Counterfactual rollouts:* ELPO (binary search for the first irrecoverable step), EEF, IPR/STeCa (MC step reward vs expert), CSO's verification stage, and 2610.17633 (V-curves with Wilson bounds).
- **How the localization gets used:**
  - *Restart state:* PivoARL, R³L, SPROUT, ELPO's tree, MiRL.
  - *Credit boundary or mask:* PivoARL pivotal isolation, R³L pivotal credit, VPPO, ELPO clipping, SPROUT loss masks.
  - *Step-level preference:* CSO, IPR, the conceptual proposal 2511.10687.
  - *Rewrite then continue:* RTI, STeCa, Agent-R.
  - *Task or environment synthesis:* SENTINEL, Agent-World, DataEnvGym, SwS, WebRL.
  - *Behavior-specific reward:* only **MiRL**, which rewards avoiding the misbehavior. No other paper found does this.
- **Gaps and open questions MiRL leaves (useful for the survey):**
  - *Unvalidated localizer:* none of the restart-RL papers that use an LLM or self localizer (MiRL, PivoARL, R³L, SPROUT, RTI) checks it against counterfactual ground truth. 2610.17633 shows judge first-mistake labels on SWE-bench usually fall after the decisive drop, and restarting at them does not help. ELPO's Fig. 1 makes the same point for "first error" vs "first irrecoverable error". A survey could frame this as *attribution accuracy → training value*.
  - *Untested benefit of error targeting:* error-profile curricula (SENTINEL, Agent-World) report no ablation that isolates the diagnosis step. 2609.04128 finds weakness-based co-evolution *underperforms* off-policy environment evolution on Terminal-Bench 2.1. Whether error-targeting itself helps, versus just more or harder data, is therefore not established. MiRL's comparison against TMax-4B at 35% of the rollouts is one data point.
  - *Restart infrastructure:* SPROUT snapshots after each turn, MiRL replays deterministically (keeping only 34% of prefixes), and 2610.17633 replays (keeping about 74%). Snapshotting may matter more than localizer quality for terminal domains.
  - *Reward hacking of localization-based rewards:* VPPO's step inflation is a warning for MiRL's behavior-judge reward, where the policy could learn to avoid the judge's surface cues rather than the underlying misbehavior.
  - *Unused attribution models:* no paper found trains an agent with a Who&When or AgenTracer-style attribution model as the localizer. 2511.10687 proposes it without experiments, and MiRL cites these models only as related evaluation tools.

## 5. Search log (abridged)
- WebSearch queries:
  - restart-from-error-step RL 2026
  - failure attribution as a training signal (Who&When, AgenTracer)
  - "first error step" plus prefix rollout
  - critical-step branching for SWE and terminal agents
  - weakness-targeted environment synthesis
  - "Save the Good Prefix"
  - attribution as a multi-agent RL reward
  - self-correction plus error-step rewriting
  - behavior or misbehavior judge rewards
  - Go-Explore and start-state selection
  - error localizer plus on-policy distillation
  - "prefix sampling" RL
  - "Pass the Baton"
- WebFetch of arxiv.org abstract and HTML pages for every VERIFIED entry above.
