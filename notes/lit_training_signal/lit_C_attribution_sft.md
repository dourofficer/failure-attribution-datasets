# Lit search C: error localization / failure attribution -> SFT / DPO / self-training data for LLM agents

- Search date: 2026-10-28. Method: WebSearch + WebFetch on arxiv.org abs/HTML pages (and ACL Anthology where there is no arXiv id).
- Scope: papers (2024-2026) where the **location** of the first/decisive/critical error step in an agent trajectory decides what training data gets built (branch, splice, correction, pair, reflection, recovery).
- Status labels:
  - **VERIFIED** means the abs/HTML page was fetched and the method details below were read from it.
  - **VERIFIED (abstract only)** means the metadata and abstract were confirmed but the full text was not read.
  - **UNVERIFIED** means the item was seen only in search snippets or secondary pages.
- No arXiv id is guessed. Where none was found, the ACL Anthology id is given instead.

---

## 0. Quick map: how each method finds the step

| Localization mechanism | Papers |
|---|---|
| Actor model judges its own trajectory (self-critique) | Agent-R |
| MC rollouts from expert prefix, compared to expert step reward | IPR, STeCa |
| Rollouts from evenly spaced expert states (success at s_{i-l}, failure at s_i) | EEF |
| LLM judge picks the erroneous turn or step | SDPO (GPT-4o), GUI-Reflection (GPT-4o), RoTS (reflector) |
| PRM/LLM rubric proposes candidates, then branch rollout verifies them | CSO |
| First divergence from a successful reference trajectory | EvoCUA, Divergence-Point PL (tau2), Skill-CDPO (local vs expert rollouts) |
| Gold "lineage" of correct state values, giving the root-cause step | CUA-Recovery / ReRail |
| Implicit DPO reward finds the divergence step (loss weighting only) | dwDPO |
| Error is injected or synthesized, so its step is known by construction | AgentRefine, GUI-Reflection (offline part), PALADIN |
| Counterfactual replay: earliest correction that flips the outcome | AgenTracer (labels only, used to train the attributor), CausalFlow (pairs, no training reported) |

| What gets constructed | Papers |
|---|---|
| Spliced trajectory: bad prefix + revision signal + good suffix (SFT) | Agent-R |
| Step-level DPO pair at the located step | IPR, CSO, EvoCUA, Skill-CDPO, Divergence-Point PL |
| Segment-level DPO pair starting at the erroneous turn | SDPO |
| Corrected action + reflection thought + expert continuation (reward-weighted SFT) | STeCa |
| Recovery continuation from an erroneous state (SFT) | CUA-Recovery, RoTS, GUI-Reflection, EEF (recovery states) |
| Error turns kept in context but masked from the loss | AgentRefine, EEF (prefix masked) |
| Reflection pair at t*+1 (blind continuation rejected, reflection chosen) | EvoCUA, GUI-Reflection (post-error reflection) |

---

## A. Core papers: error location determines the training data (single-agent)

### A1. Agent-R: Training Language Model Agents to Reflect via Iterative Self-Training. **VERIFIED**
- **arXiv:** 2501.11425 (v1 20 Jan 2025; v3 24 Mar 2025). Fudan + ByteDance Seed. No venue listed on arXiv.
- **Domain:** interactive text environments (AgentGym): WebShop (web), ScienceWorld (embodied/science), TextCraft.
- **How the error step is found:**
  - MCTS builds trees of good and bad trajectories.
  - For a bad trajectory, the **actor model itself** judges each action. The first action it flags as wrong ("within its current capability") becomes the transition point t'.
- **Data constructed:**
  - "Revision trajectory" = bad prefix up to t' + revision signal + the good trajectory's suffix from the **same parent node**.
  - The revision signal is sampled from 10 hand-written revision thoughts.
  - Baseline "direct revision" puts t' at the end of the bad trajectory.
- **Training:** iterative SFT (weighted log-likelihood on the revision signal + good suffix, conditioned on the bad prefix), 3 iterations, 20% ShareGPT mixed in.
- **Base model:** Llama-3.1-8B-Instruct.
- **Key result (avg over 3 envs):**
  - Agent-R 70.71 vs ETO 65.12 vs Direct-Revision 62.36 (base 20.00).
  - In the "revision" setting (recovering from a bad prefix): Agent-R 46.75 vs direct revision 35.67 vs ETO 13.08.
- **Relevance:** This is the canonical "splice at the first error step" recipe. Moving the splice from the end of the trajectory to the first error is the ablation that isolates the value of localization (+8.35 avg over direct revision). A Who&When/AgenTracer attributor could replace the self-judge.

### A2. Watch Every Step! LLM Agent Learning via Iterative Step-Level Process Refinement (IPR). **VERIFIED**
- **arXiv:** 2406.11176 (Jun 2024). EMNLP 2024 Main.
- **Domain:** WebShop (web), InterCodeSQL (coding/SQL), ALFWorld (embodied).
- **How the error step is found:**
  - MC step reward: 5 rollouts per step from the SFT agent.
  - The agent continues from an expert prefix. A step is a "mistake" when its MC reward is lower than the expert step's reward by more than a threshold τ and its outcome is worse.
- **Data constructed:** step-level win/lose pairs (expert continuation vs agent continuation from step t), plus outcome-level pairs.
- **Training:** SFT + outcome-DPO + step-DPO, iterated up to 4 rounds.
- **Base model:** Llama-2-7B (also Mistral-7B, Llama-2-13B, Llama-3-8B).
- **Key result:** avg 69.4 vs ETO 66.4 vs RFT 62.3 vs SFT 60.6 vs PPO 42.0.
- **Relevance:** This is the standard MC-rollout localizer. Each step that differs from the expert gets a contrastive pair. It needs expert trajectories, though, so it cannot be applied directly to policy failures.

### A3. STeCa: Step-level Trajectory Calibration for LLM Agent Learning. **VERIFIED**
- **arXiv:** 2502.14276 (Feb 2025). Findings of ACL 2025.
- **Domain:** VirtualHome, ALFWorld (embodied). ScienceWorld is in the appendix.
- **How the error step is found:**
  - The agent explores from an expert sub-trajectory.
  - MC step reward uses N=5 rollouts.
  - An action is "deviated" if its step reward minus the previous expert step's reward is below δ=0.
  - The **first** deviated action is used.
- **Data constructed:**
  - GPT-4o replaces the deviated action with the ground-truth action and writes a **reflective thought**.
  - Calibrated trajectory = prefix + reflection + corrected action + rest of the expert trajectory.
  - The deviated trajectory is also kept.
- **Training:** SFT warm-up, then reward-weighted log-likelihood ("reinforced training") over calibrated, expert-subtrajectory and successful explored data.
- **Base model:** Llama-2-7B-Chat (also Mistral-7B, Llama-3-8B-Instruct).
- **Key result:** avg success 70.9 vs IPR 68.6 vs ETO 66.9 vs SFT 63.3.
- **Relevance:** This is the most direct "reflection text at the mistake step" construction. It shows that calibration at the first deviation beats step-pair DPO (IPR).

### A4. Exploring Expert Failures Improves LLM Agent Tuning (EEF). **VERIFIED**
- **arXiv:** 2504.13145 (Apr 2025). arXiv preprint (no venue listed).
- **Domain:** WebShop (web), ScienceWorld.
- **How the error step is found:**
  - Policy rollouts start from M=5 evenly spaced states along each (possibly failed) GPT-4 expert trajectory.
  - If the policy succeeds from s_{i-l} but fails from s_i, then the expert actions a_{i-l:i-1} are **harmful**, and s_i is a "state requiring recovery". Only the first such state per trajectory is kept.
- **Data constructed:**
  - Positive trajectories that start from "important states" (subtask starts + recovery states).
  - Loss applies only from the important state onward; the earlier prefix is masked.
- **Training:** iterative SFT (RFT-style).
- **Base model:** Llama-3-8B-Instruct.
- **Key result (win rate):** WebShop-11k 62.0% (EEF GPT-3&4) / 58.4% (EEF GPT-4) vs RFT 52.0%, RFT×6 53.6%, ETO 42.0%, NAT 37.2%, GPT-4 35.6%. SciWorld-2k 68.5 vs RFT×6 62.5.
- **Relevance:** This is coarse-grained (segment-level) error localization by rollout on *expert* failures. It turns failed demonstrations into recovery training data instead of throwing them away.

### A5. SDPO: Segment-Level Direct Preference Optimization for Social Agents. **VERIFIED**
- **arXiv:** 2501.01821 (Jan 2025). ACL 2025 Long (2025.acl-long.607).
- **Domain:** multi-turn social dialogue agents (SOTOPIA). This is interactive, but not tools or web.
- **How the error step is found:** a **GPT-4o judge** marks the erroneous turn in a negative session (goal score <7). The turn must be critical to the goal and leave room for improvement.
- **Data constructed:**
  - The agent is rolled back to the history before the erroneous turn and 5 sessions are resampled. The best one is the positive if it beats the negative.
  - GPT-4o picks the key segment in the positive session (usually 3 turns), which is paired with a same-length negative segment.
- **Training:** BC (SFT) then segment-level DPO; the loss covers only turns inside the segments.
- **Base model:** Llama-3.1-8B-Chat (also Mistral-v0.3).
- **Key result (SOTOPIA avg):** 5.63 vs ETO 5.45, DMPO 5.43, turn-DPO 5.34, GPT-4o 5.17, BC 5.16.
- **Relevance:** This is the cleanest "branch at the judged error turn, then contrast" design. Session-level DPO (ETO/DMPO) is the outcome-only control, and it loses.

### A6. Verified Critical Step Optimization for LLM Agents (CSO). **VERIFIED**
- **arXiv:** 2602.03412 (Feb 2026; v2 Apr 2026). ACL 2026 Findings. Tencent AI Lab.
- **Domain:** deep-search / tool-using agents (GAIA-Text-103, XBench-DeepSearch).
- **How the error step is found:**
  - A **PRM**, Claude-3.7-Sonnet with a rubric, scores the policy's action at each step of a *failed policy trajectory*. A step is a candidate when the policy action scores below 0.45 and some expert alternative scores above 0.65.
  - The expert (Claude-3.7-Sonnet) proposes K=5 alternatives.
  - **Verification:** each alternative is swapped in and the *policy* continues to the end. The step counts as critical only if the outcome flips to success.
- **Data constructed:** step-level DPO pairs (s_t, a+ = verified expert alternative, a- = original policy action).
- **Training:** DPO (β=0.5).
- **Base model:** CK-Pro-8B (SFT of Qwen3-8B).
- **Key result:**
  - GAIA-Text 49.5% vs IPR 44.6, Step-DPO 38.9, ETO 38.9, SFT 35.9, RFT 34.9.
  - XBench 29.0 vs 25.0 / 24.0 / 22.0 / 23.0 / 20.0 (Step-DPO / IPR / ETO / SFT / RFT).
  - Supervision covers only about 16% of steps.
- **Relevance:** This closely matches the Who&When "decisive error" definition (a counterfactual flip from failure to success), used as a **training-data filter**. It is the strongest evidence that counterfactually verified decisive steps beat MC-estimated step rewards.

### A7. EvoCUA: Evolving Computer Use Agents via Learning from Scalable Synthetic Experience. **VERIFIED**
- **arXiv:** 2601.15876 (Jan 2026). Meituan et al.
- **Domain:** computer use / GUI (OSWorld).
- **How the error step is found:** reference-guided diagnosis. The "**Critical Deviation Step**" t* is the first timestamp where the failed rollout's action diverges from a successful reference trajectory while the environment states are still functionally equivalent.
- **Data constructed:** two step-level preference pairs.
  - At t* (action correction): rejected = failed thought+action; chosen = aligned reference or a synthesized correct action.
  - At t*+1 (reflection/recovery): rejected = blind continuation; chosen = a reflection trace that notices the unexpected state and plans a remedy.
- **Training:** offline step-level DPO (one stage of a larger SFT/RL pipeline).
- **Base model:** Qwen3-VL-32B-Thinking (EvoCUA-32B); also OpenCUA-72B.
- **Key result:** EvoCUA-32B reaches 56.7% on OSWorld. The DPO stage adds +3.21 pts (32B) and +3.02 pts (OpenCUA-72B) in ablations.
- **Relevance:** This is an industrial-scale instance of "pair at the first divergence step + reflection pair at the next step". It localizes by comparison to a reference trajectory, not with a judge.

### A8. GUI-Reflection: Empowering Multimodal GUI Models with Self-Reflection Behavior. **VERIFIED**
- **arXiv:** 2506.08012 (Jun 2025). NeurIPS 2025 poster (per neurips.cc listing). Wu, Ma, Wang, Yu, Lu, Liu.
- **Domain:** mobile GUI agents (AndroidWorld and a custom Android env).
- **How the error step is found:**
  - Offline: errors are synthesized (goal rewriting so that a correct action becomes wrong, or inserting ineffective actions), so their location is known by construction.
  - Online: a task verifier (programmatic or Gemini-2.0-Flash) flags the failure, then **GPT-4o identifies the first incorrect step**.
- **Data constructed:** a pre-error correction (the right action at the error step), plus a post-error reflection at the next step (recognize the mistake, e.g. Press Back, then retry).
- **Training:** GUI pre-training on a reflection task suite, offline SFT, then iterative online reflection tuning (iterated SFT on collected data).
- **Base model:** InternVL2.5-8B.
- **Key result (level-2 online tasks):** filtered BC without reflection 14.58%, + reflection SFT 23.61%, + online reflection tuning 34.72%. AndroidWorld 34.5%.
- **Relevance:** This is a first-error judge plus correction/reflection data in a multimodal agent. Filtered BC is the outcome-only control.

### A9. CUA-Recovery: Benchmarking Error Recovery in Long-Horizon Computer-Use Agents (ReRail pipeline). **VERIFIED**
- **arXiv:** 2610.27645 (20 Oct 2026). No venue.
- **Domain:** desktop computer use (MyPCBench, Odysseys).
- **How the error step is found:**
  - Each failed rollout is compared against the task's **gold lineage** (correct value at every step). This gives the root-cause step t_r ("the earliest action the agent does not undo"), the error type, and the step t_e where the error becomes explicit.
  - Humans verify these on the test split. Training cases with type confidence below 0.7 are dropped.
- **Data constructed:**
  - The erroneous state is rebuilt by replaying the prefix after repairing unrelated earlier mistakes, so the root cause is the only error. It is replayed at "takeover depths" of 0-25 steps after the root cause.
  - The base model retries with escalating hints (or a teacher if needed). The first verifier-accepted continuation becomes the target, and the hints are stripped from the training input.
- **Training:** SFT (1 epoch, 8,577 verified recovery trajectories).
- **Base model:** Qwen3.5-35B-A3B.
- **Key result:**
  - Error Awareness Rate 19.9 to 35.2% vs 23.6% for a **token-matched successful-trajectory control**.
  - Clean-start MyPCBench Pass@3 24.5 vs 13.8 (control), and 9.2 for the base model.
- **Relevance:** This is the most direct "localize the root cause, then replay the erroneous state, then train recovery" pipeline. The success-only control is token-matched, which makes it a clean comparison against outcome-only data.

### A10. Recovering Policy-Induced Errors: Benchmarking and Trajectory Synthesis for Robust GUI Agents (RoTS / GUI-RobustEval). **VERIFIED**
- **arXiv:** 2605.29447 (May 2026). ICML 2026 Spotlight.
- **Domain:** GUI / computer use (OSWorld, GUI-RobustEval).
- **How the error step is found:**
  - Tree of rollouts, split into success and failure subtrees by WebJudge (an outcome reward model).
  - On failed branches, a **reflector model** reads the failed trajectory plus sibling-branch experience. It proposes candidate error steps, each with recovery guidance and a priority, and a UCB rule picks one.
  - On successful branches, "fragility-driven exploration" uses a progress critic to find fragile nodes.
- **Data constructed:** the environment is restored to the chosen error state and a recovery actor rolls out with guidance. Step-level SFT samples are produced (720k agnostic + 80k reflection-related).
- **Training:** SFT only.
- **Base model:** Qwen2.5-VL-7B / 32B.
- **Key result:**
  - Ablation (7B, 100k): parallel sampling only gives OSWorld 18.1 / All-Pass@4 8.6. Adding error-informed recovery (EIR) gives 19.5 / 12.1, and the full pipeline gives 21.4 / 14.1.
  - RoTS-32B reaches 47.4% on OSWorld.
- **Relevance:** Error localization by a reflector drives where branches are expanded. Most of the gain shows up on robustness metrics (All-Pass@4, post-success), not raw success.

### A11. AgentRefine: Enhancing Agent Generalization through Refinement Tuning. **VERIFIED**
- **arXiv:** 2501.01702 (Jan 2025). ICLR 2025.
- **Domain:** synthetic text environments; evaluated held-out on SciWorld, BabyAI, PDDL, Jericho, ALFWorld.
- **How the error step is found:** by construction. GPT-4o simulates a DM and a player; the player makes errors and the DM turn flags parameter, place or logic errors. A rule verifier checks format and action validity and requires at least 2 error-refine turns.
- **Data constructed:** trajectories with error turns followed by refinements. **Erroneous turns stay in context but are masked from the loss.**
- **Training:** SFT.
- **Base model:** Llama-3-8B / 70B (also Mistral-7B).
- **Key result:**
  - Held-out: SciWorld 14.4 vs Agent-FLAN 1.1, PDDL 16.6 vs 8.3.
  - Ablation: removing the error-turn masking drops SciWorld 7.7 to 3.3; removing refinement data drops it to 5.5.
- **Relevance:** Knowing which turns are errors, and masking them, is what produces the benefit. This links directly to "error-step annotated SFT". The errors are synthetic, though, not attributed.

### A12. Skill-CDPO: Evolving Agent Tool-Use via Critical Step Preference Optimization. **VERIFIED (abstract only; ACL Anthology)**
- **ID:** ACL Anthology 2026.findings-emnlp.1985 (Findings of EMNLP 2026). **No arXiv id found.**
- **Domain:** medical deep-research / tool use (PubMed Search, CureBench, MedBrowseComp).
- **How the error step is found:** "critical steps" are steps where rollouts from the local policy and from an expert model diverge (the policy's capability is the bottleneck). No PRM is used.
- **Data constructed:** distributional preference pairs at critical steps, weighted by step criticality and score gap.
- **Training:** Critical-Step DPO, after an inference-time skill-acquisition stage.
- **Base model:** an unnamed 8B deep-research model.
- **Key result:** beats SFT and trajectory-level DPO (no numbers in the abstract); claimed to be competitive with GPT-5.2 on retrieval-heavy tasks.
- **Relevance:** Another critical-step DPO variant, where the location comes from where the policy and expert rollouts diverge.

### A13. dwDPO: Training Multi-Turn LLM Agents via Divergence-Weighted Direct Preference Optimization. **VERIFIED (abstract only; ACL Anthology)**
- **ID:** ACL Anthology 2026.emnlp-main.2406 (EMNLP 2026 Main). **No arXiv id found.**
- **Domain:** deep-research agents (6 benchmarks).
- **How the error step is found:** the first divergence step between chosen and rejected trajectories, detected with the **implicit DPO reward**.
- **Data / loss:** the trajectory pairs are unchanged; an asymmetric kernel concentrates the DPO loss around the divergence step, with a closed-form scale that preserves Bradley-Terry. Standard DPO is a special case.
- **Training:** DPO variant.
- **Key result:** outperforms open baselines of similar scale (no numbers in the abstract).
- **Relevance:** Location sets the **loss weighting** rather than the data. It is a cheap way to turn ETO-style trajectory pairs into error-step-focused training.

### A14. Self-Evolution for Multi-Turn Tool-Calling Agents via Divergence-Point Preference Learning (ToolGraph). **VERIFIED (abstract only)**
- **arXiv:** 2606.23112 (Jun 2026). Single author, 7-page preprint.
- **Domain:** tool calling (tau2-bench, 375 tasks).
- **How the error step is found:** the divergence point between successful and failed trajectories, via state matching with a fallback to prefix alignment, filtered by action-correctness annotations.
- **Data constructed:** 161 DPO pairs at divergence points (chosen from the agent's own successes).
- **Training:** DPO under the same ToolGraph context used at inference.
- **Key result:** weighted reward 0.304 (baseline) to 0.338 (ToolGraph) to 0.355 (+DPO). The gain is concentrated in airline and retail.
- **Relevance:** Small-scale confirmation of divergence-point pairs on tau2. It is weak evidence (161 pairs, single run).

### Partial matches: branch-level or per-step, not first-error-specific (verified)
- **Agent Q: Advanced Reasoning and Learning for Autonomous AI Agents.** arXiv 2408.07199 (Aug 2024).
  - What it does: MCTS + AI self-critique; preference pairs at **every tree node** (Q-value-ranked branches); off-policy DPO; Llama-3-70B; WebShop + real booking (18.6% to 81.7%, 95.4% with search).
  - Why it is partial: step-level branching, but no first-error localization. **VERIFIED (abstract only).**
- **Better than Your Teacher: LLM Agents that Learn from Privileged AI Feedback (LEAP).** arXiv 2410.05434 (Oct 2024).
  - What it does: a privileged GPT-4o teacher relabels the student's *failed* trajectories step by step with corrected reason+action, DAgger-style; SFT by default (DPO/KTO ablations are worse); Llama-3-8B; ALFWorld OOD 65.7 to 91.8, WebShop 29.4 to 61.8.
  - Why it is partial: correction happens at the student's own states, but every step is relabeled rather than just the first error. **VERIFIED.**
- **WebCoT: Enhancing Web Agent Reasoning by Reconstructing Chain-of-Thought in Reflection, Branching, and Rollback.** arXiv 2505.20013. Findings of EMNLP 2025.
  - What it does: localizes failure *segments* by detecting loops (a repeated observation) and cuts them out; builds rollback data by substituting a failing action at a chosen state, followed by a "goback" with a rationale; SFT of Llama-3.3-70B; WebVoyager 41.04 vs 29.50 for rejection sampling.
  - Why it is partial: the localization is heuristic. **VERIFIED.**

---

## B. Multi-agent variants (training MAS from blame)

No paper was found that **fine-tunes MAS agents on Who&When / AgenTracer / Aegis decisive-error labels** with corrected-step data. This looks like an open gap. Closest items:

### B1. Scaling Multiagent Systems with Process Rewards (MAPPA). **VERIFIED**
- **arXiv:** 2601.23228 (Jan 2026). Appears on an iclr.cc 2026 listing (track not confirmed).
- **Domain:** 3-agent sequential MAS (MathChat: Solver, Executor, Verifier; DSBench: Data Engineer, Modeler, Analyst).
- **How blame is assigned:** an LLM coach (Gemini 2.5 Flash/Pro) scores every agent action 0-10 given role, input and tool output, and can **shift blame upstream**. For example, a downstream file-not-found error lowers the upstream producer's score.
- **Training:** REINFORCE++ with separate weights per agent.
- **Base model:** DeepSeek-R1-Distill-Qwen-1.5B and Qwen3-4B.
- **Key result:** AIME +5.0 to +17.5 pp, AMC +7.8 to +17.2 pp, DSBench +16.7 pp. **No outcome-only baseline is reported**, and these are single runs.
- **Relevance:** Attribution here is dense per-action credit inside RL rather than decisive-step data construction. It shows that LLM-judge blame can drive MAS training.

### B2. Who Gets the Reward & Who Gets the Blame? Evaluation-Aligned Training Signals for Multi-LLM Agents. **VERIFIED (abstract)**
- **arXiv:** 2511.10687 (Nov 2025; v3 Jul 2026). NeurIPS 2025 Workshop (LAW).
- **What it proposes:**
  - Shapley credit across agents, refined into per-message rewards for successful runs.
  - For failed runs, **first-error localization** to the earliest harmful message, yielding "repair-aware" preference pairs (chosen = corrected edit / successful-context message / human or LLM fix).
  - Intended to be compatible with DPO/GRPO.
- **Status:** "Our contribution is conceptual". There are **no experiments**.
- **Relevance:** This is the only paper that explicitly proposes Who&When-style first-error localization, followed by MAS preference training. It is the blueprint the survey can cite as unvalidated.

### B3. Counterfactual Credit Policy Optimization for Multi-Agent Collaboration (CCPO / SEPO). **VERIFIED (abstract)**
- **arXiv:** 2603.21563 (Mar 2026; v5 Jun 2026).
- **What it does:** agent-level counterfactual credit (outcome with vs without the agent) feeds role-specific advantages into GRPO/GSPO/REINFORCE++, in a Think-Solve dual-agent setup on math. Results are mixed across models.
- **Relevance:** This is counterfactual blame at the agent level, not the step level. It is outcome-derived credit, not data construction.

### B4. Related MAS items that are *not* agent training (verified)
- **AgenTracer: Who Is Inducing Failure in the LLM Agentic Systems?** arXiv 2509.03312.
  - Counterfactual replay: DeepSeek-R1 proposes a minimal fix at each step t, and the first step whose fix flips the outcome is labeled decisive.
  - Plus fault injection, giving the TracerTraj dataset.
  - Trains **the attributor** (Qwen3-8B, GRPO, Gaussian step-proximity reward).
  - Downstream gains (MaAS +14.21% on MATH-500, OWL +4.8% on GAIA) come from **inference-time** injection of the tracer's reasoning over 3 rounds, with no agent weight updates.
- **SiriuS: Self-improving Multi-agent Systems via Bootstrapped Reasoning.** arXiv 2502.04780. NeurIPS 2025.
  - Builds an experience library from successful MAS trajectories. Failed attempts are resampled with feedback from a ground-truth-aware agent, then SFT is applied.
  - Augmentation is at the trajectory or agent level and not step-localized. **VERIFIED (search abstract only).**

---

## C. Known/related works checked: outcome-only or inference-only (useful as controls)

| Paper | arXiv / venue | Status | Why it is *not* location-based |
|---|---|---|---|
| ETO: Trial and Error: Exploration-Based Trajectory Optimization for LLM Agents | 2403.02502, ACL 2024 | VERIFIED | Trajectory-level success/failure DPO pairs. It is the standard outcome-only baseline (beaten by IPR, STeCa, Agent-R, SDPO, CSO, EEF). |
| NAT: Learning From Failure: Integrating Negative Examples when Fine-tuning LLMs as Agents | 2402.11651 | VERIFIED | Whole-trajectory success/failure control token (prefix/suffix), with no step localization. |
| SCoRe: Training Language Models to Self-Correct via RL | 2409.12917 | VERIFIED (abstract) | Multi-turn RL on second-attempt correctness for math and code. Not agentic, not step-localized. |
| Re-ReST: Reflection-Reinforced Self-Training for Language Agents | 2406.01495 | VERIFIED (abstract) | A reflector revises whole failed samples using env feedback. No step localization is described. |
| ReTerm: Recovery Training for Self-Improving Terminal Agents | 2610.18484 | VERIFIED | Recovery SFT (ReTerm-10K) + ReTerm-GRPO fork from the **end state** of a failed run. The error step is **not** localized. GRPO 28.0 vs ReTerm-GRPO 34.8 on Terminal-Bench 2.0 (Qwen3.5-9B). Good contrast: recovery data without localization. |
| AgentDebug / AgentErrorBench: Where LLM Agents Fail and How They Can Learn From Failures | 2509.25370 | VERIFIED | GPT-4.1 detector finds the earliest critical step, then re-rolls from t* with feedback, up to 5 times. **No training**; the Limitations section says training a debugger is too expensive. ALFWorld: GPT-4o-mini 21 to 55, Qwen3-8B 48 to 74. |
| AgentRewind: Recoverable Execution for Long-Horizon LLM Agents | 2608.14380 (Aug 2026) | VERIFIED (abstract) | Runtime checkpoint/rollback of context + environment (MettleBench). No training. Rollback-target selection not described in the abstract. |
| TrajDebug: Tracing Error Lifecycle to Identify Critical Failures | 2608.06346 (Aug 2026) | VERIFIED | Earliest critical error detection (TrajErrBench: tau2 + SWE-Bench Pro). Diagnoses are used **only as prompt feedback** (repair +10.8 avg, memory transfer +5.7). |
| Locating Hidden Failures Makes Long-Horizon Agents More Reliable (Traverse / Scout-4B) | 2609.17930 (Sep 2026) | VERIFIED (abstract) | Trains a 4B first-mistake **verifier** and uses it for test-time selection "without retraining the agent". |

---

## D. Adjacent anchors (non-agent, or the training part is not shown)

- **Step-DPO: Step-wise Preference Optimization for Long-chain Reasoning of LLMs.** arXiv 2406.18629 (math).
  - The originating "first erroneous step + correct-step resample" pair recipe that agent works (CSO baseline, IPR) build on. **VERIFIED (abstract)**.
- **Reflective Recovery: A Self-Supervised Method for Reasoning by Learning from Mistakes.** arXiv 2609.19156 (Jul 2026, math).
  - Initial segments of failed attempts are reused as prefixes for recovery data. AIME25 30.0 to 37.5 (R1-Distill-Qwen-7B).
  - Not agentic; the localization is heuristic. **VERIFIED (abstract)**.
- **CausalFlow: Causal Attribution and Counterfactual Repair for LLM Agent Failures.** arXiv 2605.25338 (May 2026).
  - Step-level counterfactual intervention yields Causal Responsibility Scores and validated (wrong step, corrected step) pairs, described as "suitable for" DPO or reward modeling.
  - **No trained model is reported in the abstract.** **VERIFIED (abstract)**. It is a natural data generator for the pipeline the survey describes.
- **PALADIN: Self-Correcting Language Model Agents to Cure Tool-Failure Cases.** arXiv 2509.25238.
  - More than 50k recovery-annotated ToolBench trajectories built by **systematic failure injection** (location known by construction); LoRA SFT.
  - Recovery rate 32.76 to 89.68%. **VERIFIED (abstract)**.
- **Failure Makes the Agent Stronger: Structured Reflection for Reliable Tool Interactions.** arXiv 2509.18847 (ACL per comments).
  - Mini-trajectories of erroneous call, then reflection, then corrected call; trained with DAPO/GSPO; BFCL v3. The error-generation details are not in the abstract. **VERIFIED (abstract)**.
- **ATLaS: Agent Tuning via Learning Critical Steps.** arXiv 2503.02197.
  - SFT on the ~30% "critical steps" of **expert** trajectories, which beats training on all steps.
  - It is about critical decision steps, not errors. **VERIFIED (search abstract)**.
- **Agentic-DPO: From Imitation to Agentic Policy Optimization on Expert Trajectories.** arXiv 2607.10601 (Jul 2026).
  - State-level DPO: at each expert state, the student's own one-step wrong actions are the negatives. tau-bench 9B: 21.7 (SFT) to 41.4.
  - Every state is used, not a located error. **VERIFIED (abstract)**.
- **"How to Learn from Negative Trajectories in Coding Agents"** (Microsoft debug-gym blog, Aug 2026).
  - Verified-wrong facts from failed SWE trajectories are added as privileged info in an `<information>` block, then SFT. +4.1% over positive-only SFT (Qwen3-32B).
  - **No arXiv paper found**, so this is blog-level only. The localization is at the fact level, not the step level.
- **Not found or unverified:**
  - "BacktrackAgent": no arXiv page was found by name, so it is **UNVERIFIED** and excluded.
  - InfiGUI-R1 (2504.14239) "error recovery scenario construction": seen only in a search snippet, **UNVERIFIED** detail.

---

## E. Takeaways for the failure-attribution survey

- **Localization recipes used in training papers, roughly from cheapest to most faithful:**
  - Self-judge (Agent-R).
  - Rule- or loop-detection (WebCoT).
  - LLM judge (SDPO, GUI-Reflection, RoTS).
  - Divergence from a reference trajectory (EvoCUA, Skill-CDPO, ToolGraph).
  - MC rollout value (IPR, STeCa, EEF).
  - Judge proposal + counterfactual branch verification (CSO).
  - Gold-lineage root cause + human check (CUA-Recovery).
- **CSO and AgenTracer use the same definition** (the earliest step whose replacement flips failure to success). CSO uses it as a DPO data filter; AgenTracer uses it to label attribution data. Bridging the two is a concrete opportunity: attributor-located steps would replace or complement the PRM proposal stage and cut rollout cost.
- **The controls show localization beats outcome-only:**
  - Agent-R vs direct revision: +8.35 avg.
  - SDPO vs session-DPO (ETO/DMPO): +0.18 to 0.20.
  - CSO vs ETO/RFT: +10.6 / +14.6 on GAIA.
  - STeCa / IPR vs ETO: +4.0 / +3.0.
  - CUA-Recovery vs token-matched success-only control: +11.6 EAR.
  - GUI-Reflection vs filtered BC: +9 pts at level 2.
- **Gap (MAS):** no paper trains MAS agents with decisive-step corrected data from Who&When / AgenTracer / Aegis labels. The only blueprint is 2511.10687, which is conceptual. MAPPA (dense coach blame) and CCPO (agent-level counterfactual) are RL-credit alternatives.
- **Recurrent design choices worth tabulating:**
  - Whether the error prefix stays in context: Agent-R, CUA-Recovery and AgentRefine keep it; EEF masks it.
  - Whether the loss covers the prefix: AgentRefine and EEF mask it.
  - Whether a reflection step is inserted: STeCa, GUI-Reflection, EvoCUA t*+1, Agent-R revision signal.
  - Whether the correction comes from an expert or from the policy's own branch: the CSO verify-by-policy rollout is key to "realizability", echoed by LEAP's realizability argument.
