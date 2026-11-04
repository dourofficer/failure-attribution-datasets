# Lit search E: Error-localizing critics, judges and attributors used as reward or feedback for agent training

Search date: 2026-10-28. Method: WebSearch to find candidates, then WebFetch on arxiv.org (abs and/or HTML) for each paper listed as VERIFIED. "VERIFIED" means the arXiv id, title and the mechanism/numbers quoted here were read on arxiv.org. "PARTIAL" means id and title were confirmed on arxiv.org but some details come only from the abstract. "UNVERIFIED" means the paper was seen only in search snippets or secondary pages.

Notation used below:
- **Output**: what the critic or attributor emits (step index, category, text, score).
- **Producer**: prompted LLM, trained model, the policy itself, or a human.
- **Use**: reward/advantage, filter, SFT target, DPO pair, or inference-time feedback only.

---

## 0. Key takeaways

- **No failure-attribution benchmark paper trains an agent with its attributor.** Every "downstream" experiment in AgenTracer, AgentDebug, CORRECT, SearchAuditor and SymTrace happens at inference time: the attribution is turned into a prompt and the run is re-rolled or resumed. Aegis, AgentRx, TraceElephant, Who&When Pro and MP-Bench have no downstream experiment at all. Aegis, Who&When Pro and MP-Bench name self-repair or self-evolution only as future work.
- **Resuming at the localized step consistently beats restarting from scratch.**
  - SymTrace: one replay from the suspicious node repairs 20.15% of failures; three full reruns repair 6.90%.
  - SearchAuditor: resuming at its critical step with its repair directive fixes 17.37% of Kimi-K2.6 failures; an unguided retry fixes 9.39%.
  - CORRECT: restarting from its step instead of a random step doubles success, from 10% to 20%.
  - SearchAuditor also shows the content of the feedback matters. A generic hint injected at the same predicted step fixes only 5.63%, so the gain is not from localization alone.
- **Training-time use of localization comes from outside the attribution-benchmark community, and the strongest designs are recent (2025–2026).** The mechanisms fall into four groups:
  1. **Judge-gated reward on rollouts that start from an error prefix.** MiRL (2610.35697) is the clearest example and the only paper that closes the full loop: profile errors, train, then re-measure the errors on unseen prefixes.
  2. **Per-step GOOD/BAD attribution turned into dense advantages.** AgentEvolver (2511.10395) does this for a single agent; MAPPA (2601.23228) does it per agent in a multi-agent pipeline, with blame assigned by an LLM coach.
  3. **The policy localizes its own pivotal turn, retries from it, and the retry's success rewards the localization.** PivoARL (2607.03702) trains the attributor and the agent jointly this way.
  4. **Critique or guidance drives a re-attempt, and the successful re-attempt becomes training data.** Agent-RLVR (2506.11425, DPO), Critique-GRPO (2506.03106, mixed into the GRPO group), NLAC (2512.04601), CGI (2503.16024), Agent-R (2501.11425), STeCa (2502.14276) and SRR-Judge (2602.07773).
- **Methods that turn step or span localization into token-level reward** (Text2Grad, CAPO, VPPO) exist for reasoning and text tasks but have not been applied to multi-agent trajectories.
  - VPPO (2601.18984) argues that a PRM should be used only for first-error localization, because that is what PRMs are evaluated on, rather than for its raw scores.
  - This is the strongest argument in the literature that the Who&When-style "decisive step" output is the right interface for a reward.
- **A critic can be trained by whether its feedback leads to a successful repair.** CTRL (2502.03492) uses GRPO with reward "revised code passes the tests". The same recipe would apply to an attributor, rewarding it when a resume from its predicted step succeeds. PivoARL does this implicitly for a self-attributor.
- **Open gap relevant to our survey.** No paper yet uses a trained failure attributor (AgenTracer-8B, Aegis-SFT/GRPO, or an attributor trained on Who&When Pro, TracerTraj or CORRECT-Error) as the reward signal for training agents. Nor has anyone checked whether attribution accuracy on these benchmarks predicts downstream training utility. VPPO assumes the link without testing it. The audit in 2608.19760 finds that step-credit scores can correlate with counterfactual replay without ordering steps reliably.

---

## Part A. Downstream experiments inside failure-attribution benchmark papers

| Paper | arXiv | Downstream experiment? | How attribution is fed back | Training of agent? | Headline numbers |
|---|---|---|---|---|---|
| AgenTracer | 2509.03312 | Yes (Sec. 5.3 "Boosting Mainstream MAS") | AgenTracer-8B's `<think>` reasoning on the failed trajectory (no ground truth given) is injected into the next round of solving; 3 iterations | No (inference-time) | +4.8% (OWL on GAIA) up to +14.21% (MaAS on MATH-500); CRITIC baseline drops −4.9%/−5.5% at iterations 2/3 on MaAS-GAIA |
| AgentDebug | 2509.25370 | Yes (Sec. 4.2, Alg. 1) | Detector (GPT-4.1) finds earliest critical step + error type; re-roll from that step with corrective guidance; refine and repeat up to N=5 | No (paper says training a debugger was too costly) | ALFWorld successes 21→55 (GPT-4o-mini), 48→74 (Qwen3-8B), 60→84 (Qwen3-Next-80B), units/denominator not stated; "up to 26%" relative gain, comparator unstated |
| CORRECT | 2509.24088 | Yes, small ("Decisive Interventions") | Targeted restart from CORRECT-identified step vs. random step | No (CORRECT is training-free) | End-to-end success 10% → 20% on Who&When Hand-Crafted; task count and restart modification not reported |
| SearchAuditor | 2608.05212 | Yes (Sec. 5.4 "Boosting Search Agents with Audits") | Keep prefix up to predicted critical step, append repair directive as a user message, continue under original scaffold | No | LiveBrowseComp (335 Q): Kimi-K2.6 acc 34.03 → 45.07 (fix rate 17.37% vs 9.39% unguided retry, 5.63% generic hint, 6.10% AgentRx repair); Quest-35B 8.96 → 18.21 |
| SymTrace | 2608.25920 | Yes (the paper is about repair) | LLM judge + rules score nodes; highest-scoring node = anchor; selective replay of prefix; re-generate node with C1–C4-conditioned repair instruction; 1 attempt | No (deepseek-v4-flash, temp 0) | 536 failures (AG2/CrewAI/Magentic-One): Suspicious-Node pass@1 20.15% vs Full Rerun pass@3 6.90%, Self-Reflection 4.29%, Critic-Agent 3.73%, Random-Node 3.73%, Last-Node 1.31% |
| Conformal Agent Error Attribution | 2605.06788 | Yes (Sec. 3.3/5.5) | Roll back to first step of the conformal step-set (80% coverage) and restart with the failed trace in the prompt | Attributor scorer is a fine-tuned Qwen3-1.7B; agent not trained | 100 MacNet GSM8K trajectories per variant; success 0.68–0.77 (LF) vs 0.67–0.76 (Top-1), within about 1 s.d. |
| TraceElephant | 2604.22708 | No repair; "Dynamic Agentic" replay only validates candidate attributions | Replay + modify input at candidate step, check next 3 steps | No (fine-tuning only future work) | Step acc 33.3% (dynamic) vs 30.3% (static) |
| Aegis | 2509.14295 | No | (attributors trained with SFT / GRPO / DCL; output = agent–error-mode pairs, no step) | No; "self-repairing agentic systems" future work | Attribution-only results |
| AgentRx | 2602.02475 | No | (diagnosis only) | No | — |
| Who&When Pro | 2607.09996 | No (checklist: "We do not train models") | — | No | — |
| MP-Bench | 2603.25001 | No | — | No | — |
| AgentLocate | 2607.07989 (COLM 2026) | No MAS repair found in abstract; verified judgments are used to lightly fine-tune the judge itself | — | Judge only | PARTIAL: abstract only, no numbers on page |

### A.1 Details per paper

**AgenTracer: Who Is Inducing Failure in the LLM Agentic Systems?** (arXiv 2509.03312, Sep 2025) — VERIFIED
- **Attributor:** AgenTracer-8B, trained from Qwen3-8B with GRPO (no KL term, dynamic clipping).
- **Reward:** format gate × [0.5·Gaussian step-distance reward (σ=1) + 0.5·binary agent match].
- **Output:** agentID|stepID plus a `<think>` rationale.
- **Downstream use:** on MaAS, OWL-Workforce and MetaGPT over GAIA, HumanEval+ and MATH-500, the tracer's think-block is given to the system as reflection for the next round, over 3 rounds. Baselines are Self-Refine and CRITIC with GPT-4.1. The gain ranges from 4.8% to 14.2%.
- **Relevance:** This is the reference "feedback" claim in the field. It is purely in-context reflection: no agent weights change, and the round-by-round numbers are only in Fig. 3.

**Where LLM Agents Fail and How They Can Learn From Failures (AgentDebug / AgentErrorTaxonomy / AgentErrorBench)** (arXiv 2509.25370, 29 Sep 2025) — VERIFIED
- **Output:** earliest critical step, the responsible module (memory/reflection/planning/action/system), the error type, and `correction_guidance` text.
- **Producer:** prompted GPT-4.1.
- **Use:** re-rollout from the critical step with that feedback, iterating up to 5 times. Baselines are Self-Refine, a Vanilla Debugger, ToT and Best-of-N, matched by token budget.
- **Relevance:** This is the canonical "localize, then re-roll from the step" design. The title says agents "learn", but nothing is learned in weights, and the paper's own internal numbers are inconsistent (Table 1 vs. Sec. 4.2 text).

**CORRECT: Condensed Error Recognition via Knowledge Transfer in Multi-Agent Systems** (arXiv 2509.24088, 28 Sep 2025) — VERIFIED
- **Method:** training-free. It caches LLM-distilled "error schemata" and retrieves them for the detector.
- **Downstream use:** a one-paragraph experiment shows a targeted restart from the detected step doubles success (10% → 20%) compared with a random-step restart on Who&When-HC.
- **Feedback loop (for the cache, not the agent):** user-confirmed detections add new schemata to the cache.

**SearchAuditor: Auditing and Attributing Failures in Long-Horizon Search Agents** (arXiv 2608.05212, 5 Aug 2026) — VERIFIED
- **Output:** critical step (with tolerance span), one of 6 root-cause classes, a rationale, and a repair directive graded against rubrics.
- **Producer:** GPT-5.5 auditor.
- **Use:** inference-time resume from the critical step with the directive.
- **Key ablation:** a generic hint at the same step does worse than an unguided retry, and the authors explain this as "resumption asymmetry".
- **Relevance:** This is the cleanest evidence that both where and what matter. Inaccurate guidance anchors the agent on its flawed prefix.

**Repair or Resample? Rethinking Failure Debugging in LLM Multi-Agent Systems (SymTrace / SymFail)** (arXiv 2608.25920, Aug 2026) — VERIFIED
- **Output:** suspicious node plus a C1–C4 symptom category.
- **Producer:** fused LLM-judge and rule score, c_mix = 0.55·LLM + 0.45·rules.
- **Use:** selective replay of the prefix and a single category-conditioned re-generation of the node.
- **Relevance:** It argues that rerun-based "repairs" are mostly resampling, and gives a strong baseline protocol (Last-Node, Random-Node, Full Rerun) that any attribution-to-repair claim should be compared against.

**Conformal Agent Error Attribution** (arXiv 2605.06788, 7 May 2026) — VERIFIED
- **Output:** a contiguous set of steps with a finite-sample coverage guarantee, scored by a fine-tuned Qwen3-1.7B decisive-error scorer.
- **Use:** roll back to the start of the set and restart with the failed trace in the prompt.
- **Relevance:** It is a principled answer to "how far back to resume". The gains over Top-1 are within noise.

---

## Part B. (i) Training-time use: localized critique or attribution changes agent weights

### B1. Judge or attributor localizes the error, which gates or shapes the RL reward for agents

**1. MiRL: Error-Targeted Reinforcement Learning for Correcting Terminal Agent Misbehaviors** (arXiv 2610.35697, 26 Oct 2026; Tian, Khan, Wang, Chen, Bansal) — VERIFIED (reference example)
- **Output:**
  - Profiling stage: per-step good/bad labels with a corrected step.
  - Taxonomy stage: one of 8 recurring "misbehavior" types, covering 52.1% of wrong steps.
  - RL stage: a binary r_e meaning "misbehavior avoided in the next m=5 steps".
- **Producer:**
  - Error localizer and teacher: Qwen3.8-27B.
  - Taxonomy annotator: Claude Opus 5.
  - Behavior judge: Gemini 3.8 Flash, prompted with the misbehavior definition and examples.
- **Use:** 219 replay-verified error prefixes are kept out of 640 sampled. Rollouts start at the prefix, with reward r = r_outcome ∧ r_e.
- **Algorithm:** DPPO (TMax recipe), group size 16, 160 steps.
- **Base model:** Qwen3.5-4B.
- **Key results:**
  - Terminal-Bench Lite 51.8% vs. TMax-4B 47.4%; Terminal-Bench 2.1 21.3% vs. 20.6%.
  - Uses 35% of TMax-4B's rollouts.
  - Misbehaviors fall 43–57% on unseen prefixes ("false claims about tests" 26.7% → 8.1%).
  - Ablations: starting from prefixes adds +7.9 and the behavior reward adds +6.5 on TB-Lite.
- **Relevance:** This is the only paper found that runs the full loop "attribute → targeted RL → re-attribute". Attribution selects where rollouts start, and a judge reading the post-prefix steps gates the reward.

**2. AgentEvolver: Towards Efficient Self-Evolving Agent System** (arXiv 2511.10395, 13 Nov 2025; Tongyi Lab, Alibaba) — VERIFIED
- **Output:** per-step GOOD/BAD with reasoning, produced in one pass over the whole trajectory. For failed outcomes, a step is GOOD only if it "actively corrected or mitigated an error".
- **Producer:** prompted LLM (Qwen-Max).
- **Use:**
  - Attribution rewards are standardized per trajectory and fused with the group-normalized outcome reward: r̂_t = α·r̂_t^attr + 1{t=T}·r̂^out, with α in [0.10, 0.20] recommended.
  - The step advantage is the sum of future fused rewards, broadcast to tokens.
- **Algorithm:** GRPO-style. The repo calls it ADCA-GRPO.
- **Base model:** Qwen2.5-7B and 14B-Instruct.
- **Benchmarks:** AppWorld and BFCL-v3.
- **Key results:**
  - Ablation (avg@8): outcome-only 41.3 / 57.4 (7B / 14B), attribution-only 35.7 / 53.0, both 47.6 / 62.0.
  - Reaches 90% of the baseline's final performance in 55–67% fewer steps.
- **Relevance:** This is the closest single-agent analogue of "attributor output as a dense reward". Who&When Pro cites it as coupling attribution rewards with self-improving agents.

**3. Scaling Multiagent Systems with Process Rewards (MAPPA)** (arXiv 2601.23228, 30 Jan 2026; Yale; listed on the ICLR 2026 virtual site, track unconfirmed) — VERIFIED
- **Output:** a 0–10 score with a rationale for every action of every agent. The coach sees the role, inputs, outputs and tool stdout/stderr, and assigns blame upstream. For example, a missing X_test.pkl is the Data Engineer's fault, not the downstream agent's.
- **Producer:** prompted Gemini 2.5 Flash (MathChat) or Gemini 2.5 Pro (DSBench).
- **Use:** per-action reward = coach score − KL penalty; advantage = sum of future rewards, normalized across agents. Each agent has independent weights.
- **Algorithm:** REINFORCE++ with PPO clipping, chosen over GRPO because agents do not share input states.
- **Base models:** DeepSeek-R1-Distill-Qwen-1.5B and Qwen3-4B.
- **Key results:**
  - MathChat AIME +5.0 to +17.5 pp and AMC +7.8 to +17.2 pp.
  - DSBench held-out success 50.0 → 66.7%. The abstract says +12.5 pp, which does not match the table.
- **Relevance:** This is the multi-agent version of attribution-as-reward. The coach does who-and-when blame at every action, which is exactly the Who&When signal used densely.

**4. Agent Reinforcement Learning via Pivotal-Aware Self-Feedback Retry (PivoARL)** (arXiv 2607.03702, 4 Jul 2026; HIT Shenzhen) — VERIFIED
- **Output:** a structured reflection, `<turn_idx>` (the earliest erroneous "pivotal" turn) plus a `<remark>`.
- **Producer:** the policy itself.
- **Use:**
  - The retry keeps the prefix before the pivotal turn and adds the remark to the prompt, for up to 3 episodes.
  - Prefix steps get discounted credit from the successful retry; the erroneous suffix is isolated from it.
  - The reflection, including the turn index, is rewarded by the retry's discounted success, so self-attribution is trained by downstream repair success.
- **Algorithm:** GiGPO (GRPO-compatible), with separate action and reflection advantages.
- **Base model:** Qwen3-4B.
- **Key results:**
  - Agent tasks (ALFWorld, WebShop, Minesweeper, SciWorld) average Suc@1/2/3: 83.9 vs. MetaRL 75.9, GiGPO 73.9, GRPO 67.9.
  - Search-QA average Pass@3: 56.9 vs. 47.2 (GiGPO).
  - The abstract and body disagree on some margins.
- **Relevance:** The attributor and agent are trained jointly, with "resume from the attributed step succeeds" as the attributor's reward. This is the closed loop in its tightest form.

**5. Who Gets the Reward & Who Gets the Blame? Evaluation-Aligned Training Signals for Multi-LLM Agents** (arXiv 2511.10687, Nov 2025, v3 Jul 2026; Argonne; NeurIPS 2025 LAW workshop) — VERIFIED, conceptual only
- **Proposal:**
  - Successful episodes: Shapley credit per agent.
  - Failed episodes: binary search over prefixes with a "prefix judge" (an LLM judge, executable checks or a compact PRM) to find the first harmful message, plus a judge that credits later repair attempts.
  - Each error becomes a DPO/GRPO preference pair.
- **No experiments.** It is useful as a formal statement of how Who&When-style "first decisive error" labels could become training signals.

### B2. Critique or guidance drives a re-attempt, and the successful re-attempt is trained on

**6. Agent-RLVR: Training Software Engineering Agents via Guidance and Environment Rewards** (arXiv 2506.11425, Jun 2025; Scale AI) — VERIFIED
- **Output:** short hints of three kinds: a plan, environment feedback explaining the stack trace or failing test of the previous patch, and environment interaction (file, line and function to edit).
- **Producer:** claude-3-7-sonnet, with the problem, reference patch, previous trajectory and environment feedback.
- **Use:** the guided retry is scored by unit tests, and (guided success, unguided failure) pairs are trained with offline DPO after SFT. Guidance is used only at training time.
- **Base model:** Qwen2.5-72B-Instruct, 817 environments.
- **Key result:** SWE-bench Verified 9.4% → 22.4% (27.8% with best-of-32 RM); guided rollouts 16.9% → 20.3% success.
- **Relevance:** A teacher-critic diagnoses the failure, the agent retries, and the success is trained on. This is the SFT/DPO route for using attribution feedback.

**7. Critique-GRPO: Advancing LLM Reasoning with Natural Language and Numerical Feedback** (arXiv 2506.03106, Jun 2025, v7 Jun 2026; ICML 2026 Spotlight) — VERIFIED (math reasoning, not agents)
- **Output:** a rule-based indicative critique, or a CoT critique with step-by-step evaluation and a correctness label. Critics tested include GPT-4o, Llama3.1-405B and DeepCritic-7B.
- **Use:** when all n responses in a group fail, the model writes critique-conditioned refinements. k refinements join the group under a shared advantage, with shaping ρ = π/(π+γ) to upweight unfamiliar valid refinements and no KL term.
- **Base models:** Qwen2.5-7B, Qwen3-8B, Llama-3.2-3B and others.
- **Key result:** average Pass@1 R1-GRPO 41.18 → 47.08 (Qwen2.5-7B) and 63.75 → 68.26 (Qwen3-8B).
- **Relevance:** Prop. 4.1 formalizes why a critique that localizes the first error (and suggests a fix) collapses search complexity. This is a theoretical argument for step-localizing feedback.

**8. Natural Language Actor-Critic: Scalable Off-Policy Learning in Language Space (NLAC)** (arXiv 2512.04601, Dec 2025, v2 Feb 2026; Berkeley/ByteDance Seed; listed as a NeurIPS 2026 poster) — VERIFIED
- **Output:** a textual critique of an action: predicted future, whether the action is optimal, and how to improve it.
- **Producer:** the same LLM in a critic role, trained by a "language Bellman backup" off-policy.
- **Use:** a refinement policy rewrites the action given the critique, and the policy is trained by log-likelihood (distillation) on the refined action.
- **Base models:** Qwen2.5-7B and QwQ-32B.
- **Key results:** τ-bench retail/airline 0.56/0.43 (QwQ-32B); about 30% over RL fine-tuning on 20Q and τ-retail; does not beat baselines on MATH.
- **Relevance:** It shows that a natural-language "why this step is bad" signal can replace a scalar value in agent RL.

**9. The Lighthouse of Language: Enhancing LLM Agents via Critique-Guided Improvement (CGI)** (arXiv 2503.16024, Mar 2025; NeurIPS 2025) — VERIFIED
- **Output:** a per-candidate-action assessment (contribution, feasibility, efficiency), a grade, and a revision suggestion.
- **Producer:** a trained critic (Llama-3-8B-Instruct SFT on GPT-4o critiques).
- **Use (both):** the actor is trained with 3 rounds of iterative SFT on critique-action pairs and correct trajectories, and critiques are also used at inference (M=5 candidates).
- **Environments:** WebShop, ScienceWorld, TextCraft.
- **Key results:** a trained 8B critic beats GPT-4o as critic (61.44 vs. 32.28); the CGI actor reaches 74.20 vs. 58.21 for iterative SFT.
- **Relevance:** A small trained critic beats a frontier prompted critic, which parallels AgenTracer-8B beating large prompted attributors.

**10. Agent-R: Training Language Model Agents to Reflect via Iterative Self-Training** (arXiv 2501.11425, Jan 2025; ByteDance) — VERIFIED
- **Output:** the first error step in the actor's own bad MCTS trajectory.
- **Producer:** the actor model.
- **Use:**
  - Revision trajectory = bad prefix up to the error, a hand-written revision signal, and the good continuation from the same MCTS parent.
  - SFT on these, iterated 3 times.
- **Base model:** Llama-3.1-8B-Instruct.
- **Environments:** WebShop, SciWorld, TextCraft.
- **Key result:** average 70.71 vs. ETO 65.12.
- **Relevance:** This is the earliest clean instance of "self-attribute the first error → splice → SFT". The attributor improves as the policy improves across iterations.

**11. STeCa: Step-level Trajectory Calibration for LLM Agent Learning** (arXiv 2502.14276, Feb 2025; ACL 2025 Findings) — VERIFIED
- **Output:** a deviated step (MC step reward of the explored action < the expert's, N=5 rollouts), then a GPT-4o reflection with a corrected action.
- **Use:** calibrated trajectories, expert sub-trajectories and successful explorations are combined in reward-weighted (DTW) policy-gradient training after an SFT warm-up.
- **Base model:** Llama-2-7B-Chat, plus Mistral-7B and Llama-3-8B.
- **Benchmarks:** ALFWorld, VirtualHome.
- **Key result:** average 70.9 vs. IPR 68.6 and ETO 66.9.
- **Relevance:** Localization here is MC/counterfactual, the same principle as Who&When's decisive error, and the LLM supplies only the fix.

**12. SRR-Judge: Step-Level Rating and Refinement for Enhancing Search-Integrated Reasoning in Search Agents** (arXiv 2602.07773, Feb 2026) — VERIFIED
- **Output:** per-step JSON with a 1–5 rating, an explanation, a refined thought and a refined search query.
- **Producer:** QwQ-32B SFT'd on DeepSeek-V3.1 self-consistency annotations, filtered by correlation with final correctness.
- **Use (both):**
  - Inference-time rate-and-refine.
  - 2 rounds of rejection-sampling fine-tuning of the QwQ-32B agent on judge-refined trajectories.
- **Key results:**
  - Inference refinement: BrowseComp 5.4 → 9.1, BrowseComp-ZH 23.4 → 29.2, xbench-DS 46.0 → 53.3.
  - After RFT: 16.2 / 38.3 / 61.3.
  - Caveat: refining a stronger agent (DeepSeek-V3.1) hurts it.
- **Relevance:** A deep-search counterpart to SearchAuditor, but used for training.

### B3. Step or span localization becomes a token-level reward (reasoning/text; not yet applied to agent trajectories)

**13. Text2Grad: Reinforcement Learning from Natural Language Feedback** (arXiv 2505.22338, May 2025, v2 Jan 2026; Microsoft; ICLR 2026 poster) — VERIFIED
- **Output:** a critique plus a JSON of quoted "good" and "poor" spans.
- **Producer:**
  - Labels: GPT-4o.
  - Online: a Llama-3.1-8B reward model trained to generate critique and spans.
- **Use:** +1/−1 per span token, then GAE, then PPO.
- **Key results:**
  - SLF5K ROUGE-L 0.291 vs. 0.262 (scalar PPO).
  - KodCode average pass@1 66.1 vs. 62.5.
  - Span-level rewards beat dense token labels.
- **Relevance:** This is the template for turning an attributor's step span into a reward.

**14. CAPO: Towards Enhancing LLM Reasoning through Generative Credit Assignment** (arXiv 2508.02298, Aug 2025, v4 Oct 2025) — VERIFIED
- **Output:** indices of wrong steps from k=4 critiques, aggregated by voting.
- **Producer:** an off-the-shelf prompted Qwen2.5-72B or Llama-3-70B.
- **Use:** R_t = r_v·W_whole − 1[t in wrong step]·W_process, with GRPO.
- **Key result:** gains of about 1–3 points, e.g. Qwen2.5-7B math mean 34.5 → 37.0.
- **Relevance:** It is the direct "LLM judge pinpoints error steps → token penalty" design. The gains are small, which is a useful calibration for expectations.

**15. Save the Good Prefix: Precise Error Penalization via Process-Supervised RL (VPPO)** (arXiv 2601.18984, Jan 2026; Tencent AI Lab et al.) — VERIFIED
- **Output:** the first error step, where the PRM score falls below 0.8 (threshold tuned on ProcessBench).
- **Producer:** Qwen2.5-Math-PRM-7B.
- **Use:** a correct response gets reward 1. A failed response gets α=0.5 at the last token of the good prefix, and the group-mean advantage pushes the suffix down.
- **Base models:** Qwen3-4B/8B-Base and Qwen3-4B.
- **Key result:** Average@16 33.7 → 35.4, 36.6 → 38.0 and 42.9 → 44.8 over GRPO.
- **Relevance:** It explicitly argues that PRMs should be used for first-error localization, the quantity they are benchmarked on, rather than for raw step scores. This is the cleanest bridge from first-error benchmarks to reward design. It does not test whether localization accuracy predicts RL gain.

### B4. Agent reward models and PRMs (step scores, mostly not explicit localization)

**16. Process Reward Models for LLM Agents: Practical Framework and Directions (AgentPRM / InversePRM)** (arXiv 2502.10325, Feb 2025; Cornell) — VERIFIED
- **Output:** a turn-level Q(s,a) learned from Monte Carlo rollout targets.
- **Use:** the policy maximizes the PRM with a KL penalty (Online DPO), over 3 iterations of 10k rollouts; BoN at inference.
- **Base model:** Llama-3.2-3B (both PRM and policy).
- **Benchmark:** ALFWorld.
- **Key result:** π3 88.1% (BoN 91.0%) vs. GPT-4o ReAct 65.7%.
- **Caveat:** reward hacking, where validation process reward rises while success falls from about 82% to 70%.
- **Relevance:** A cautionary point for any attributor used as a dense reward.

**17. AgentRM: Enhancing Agent Generalization with Reward Modeling** (arXiv 2502.18407, Feb 2025; ACL 2025) — PARTIAL (abstract)
- **Comparison:** explicit, implicit and LLM-as-judge reward models; the explicit one wins.
- **Use:** test-time only (Best-of-N and step-level beam search), not RL.
- **Key results:** +8.8 average over 9 tasks, and +12.6 on a LLaMA-3-70B policy (weak-to-strong).
- **Relevance:** Mainly inference-time reranking.

**18. Web-Shepherd: Advancing PRMs for Reinforcing Web Agents** (arXiv 2505.15277, May 2025; NeurIPS 2025 Spotlight) — PARTIAL (abstract)
- **Training data:** a checklist-based step-level PRM trained on the WebPRM Collection (40K step preference pairs with checklists).
- **Use:** the reported experiment uses it as a verifier for GPT-4o-mini on WebArena-lite.
- **Key results:** +10.9 points over GPT-4o-mini as verifier; about 30 points over GPT-4o on WebRewardBench.

**19. Agent-RewardBench: Towards a Unified Benchmark for Reward Modeling across Perception, Planning, and Safety in Real-World Multimodal Agents** (arXiv 2506.21252, Jun 2025; ACL 2025) — PARTIAL (abstract)
- **Content:** a step-level benchmark of reward models over 7 scenarios.
- **Finding:** even SOTA MLLMs perform poorly, so specialized training is needed.
- **Relevance:** It is the reward-model analogue of failure-attribution benchmarks.

### B5. Training the critic itself by downstream repair success

**20. Teaching Language Models to Critique via Reinforcement Learning (CTRL)** (arXiv 2502.03492, Feb 2025, v2 Nov 2025) — VERIFIED
- **Critic:** Qwen2.5-Coder-32B-Instruct.
- **Stage I:** SFT on execution-hint-guided critiques, with the hints then removed.
- **Stage II:** GRPO where the critique's reward is whether the frozen generator's revision passes the unit tests.
- **Use:** test-time iterative critique-revision. The generator is not trained.
- **Key result:** CodeContests 7.88 → 16.24 (5 iterations, about 106% relative); GPT-4o generator 20.61 → 25.45.
- **Relevance:** This is the recipe for training an attributor or auditor whose reward is "resume from my step with my directive succeeds", rather than agreement with injected labels.

**21. LLM Critics Help Catch LLM Bugs (CriticGPT)** (arXiv 2407.00215, Jun 2024; OpenAI) — PARTIAL (abstract)
- **Training:** RLHF-trained code critics.
- **Use:** they help human labelers in RLHF; model critiques are preferred over human ones 63% of the time on natural bugs.
- **Relevance:** Training-time use is indirect (it assists the humans who produce the reward). It is background for "critic assists the reward channel".

---

## Part C. (ii) Inference-time feedback only (no weight updates to the agent)

- AgenTracer, AgentDebug, CORRECT, SearchAuditor, SymTrace and Conformal Agent Error Attribution: see Part A.
- **Learning from Failure: Inference-Time Self-Improvement for Computer-Use Agents** (arXiv 2606.31270, Jun 2026; ECCV 2026 per page) — PARTIAL.
  - An LLM diagnoses failure modes in failed OSWorld trajectories (grounding, competency gaps, knowledge, loops) and writes code/strategy patches.
  - Humans lightly verify the patches.
  - OpenCUA-72B 42.3% → 48.9%.
- **FlowFixer: Diagnosis-Driven Automatic Repair for Agentic Workflow via Symbolic Inference** (arXiv 2607.02882, Jul 2026) — PARTIAL.
  - Symbolic traces and specification verification yield failure attribution and root cause, then targeted workflow patches.
  - Repair success 71.3% on Dify/Coze/n8n workflow failures.
- **CTRL** test-time critique-revision and the **CGI** / **SRR-Judge** inference modes (see Part B).
- **Agent-as-a-Judge: Evaluate Agents with Agents** (arXiv 2410.10934, Oct 2024) — PARTIAL. Evaluation only (DevAI, 55 tasks / 365 requirements); reward use is named only as future work.

---

## Part D. The closed loop "attribute failure → train agent → re-attribute": what exists

| Loop stage | Papers that implement it |
|---|---|
| Attribution selects what to train on (where rollouts start, which steps to fix) | MiRL (error prefixes of recurring misbehaviors), Agent-R (first self-identified error → splice), STeCa (MC-detected deviation → calibrate), PivoARL (self-identified pivotal turn → retry) |
| Attribution shapes the reward or advantage | MiRL (judge gate), AgentEvolver (GOOD/BAD step reward), MAPPA (per-agent action score), CAPO / VPPO / Text2Grad (token-level) |
| Attribution / critique becomes a training target | Agent-RLVR (DPO on guided successes), CGI (SFT on critique-action pairs), NLAC (distill refined action), SRR-Judge (RFT), Critique-GRPO (refinements in group), CFT 2501.17703 (critique as SFT target, math) |
| Attributor trained by downstream success | CTRL (critic reward = repair passes tests), PivoARL (reflection reward = retry success) |
| Re-attribute after training to measure whether the targeted failures went away | **MiRL only** (misbehavior recurrence on unseen prefixes falls 43–57%). Iterative re-localization with an improving self-attributor: Agent-R (3 iterations), AgentPRM (3 iterations), CGI (3 rounds), SRR-Judge (2 rounds) |

### Gaps relevant to the survey

1. No paper trains agents with a benchmark-trained failure attributor (AgenTracer-8B, Aegis models) as the reward or filter. AgenTracer's own downstream use is in-context reflection.
2. No paper reports whether attribution accuracy (Who&When step accuracy, CS-Strict, nDCG) predicts downstream utility. Three results bear on it:
   - SearchAuditor: AgentRx's repair, despite reasonable localization, adds little; the content of the directive dominates.
   - VPPO: assumes first-error accuracy is the right proxy, without testing it.
   - Credit Without Ground Truth (arXiv 2608.19760, Aug 2026, single author) — PARTIAL (abstract): judge-based step credit correlates with executed replay (Pearson 0.736) but orders steps poorly (Spearman 0.330), and a short hindsight-training pilot showed no incremental utility.
3. The baseline protocol for repair claims should follow SymTrace: Last-Node, Random-Node and Full Rerun at matched budget. Most attribution papers compare only against no-feedback, Self-Refine or CRITIC.
4. Reward hacking with dense attributor rewards is documented (AgentPRM) and should be guarded against. Options include gating with outcome reward, as MiRL does with r_o ∧ r_e and AgentEvolver with a small α.

---

## Part E. Verification status

**VERIFIED on arxiv.org (abs and/or HTML read):**
- Benchmark-paper downstream experiments (Part A): 2509.03312 (AgenTracer), 2509.14295 (Aegis, no downstream), 2509.25370 (AgentDebug), 2509.24088 (CORRECT), 2602.02475 (AgentRx, no downstream), 2604.22708 (TraceElephant), 2607.09996 (Who&When Pro, no downstream), 2603.25001 (MP-Bench, no downstream), 2608.05212 (SearchAuditor), 2608.25920 (SymTrace), 2605.06788 (Conformal).
- Training-time and adjacent methods: 2610.35697 (MiRL), 2511.10395 (AgentEvolver), 2601.23228 (MAPPA), 2607.03702 (PivoARL), 2511.10687 (Who Gets the Reward, conceptual), 2506.11425 (Agent-RLVR), 2506.03106 (Critique-GRPO), 2512.04601 (NLAC), 2503.16024 (CGI), 2501.11425 (Agent-R), 2502.14276 (STeCa), 2602.07773 (SRR-Judge), 2505.22338 (Text2Grad), 2508.02298 (CAPO), 2601.18984 (VPPO), 2502.10325 (AgentPRM), 2502.03492 (CTRL).

**PARTIAL (id and title confirmed on arxiv.org; details from the abstract only):**
- 2607.07989 (AgentLocate, COLM 2026), 2502.18407 (AgentRM), 2505.15277 (Web-Shepherd), 2506.21252 (Agent-RewardBench), 2407.00215 (CriticGPT), 2410.10934 (Agent-as-a-Judge), 2606.31270 (Learning from Failure CUA), 2607.02882 (FlowFixer).
- 2501.17703 (Critique Fine-Tuning; SFT on GPT-4o critiques of noisy responses, +4–10% over SFT on math).
- 2602.02482 (RLTF: "Expanding the Capabilities of RL via Text Feedback", CMU et al., Feb 2026; RLTF-SD self-distillation toward feedback-conditioned second attempts, RLTF-FM feedback-prediction auxiliary; reasoning puzzles, math, creative writing; no numbers on abstract page).
- 2505.11595 (SGPO, TMLR; step-wise judge diversifies all-negative GRPO groups; output format not confirmed).
- 2608.19760 (Credit Without Ground Truth).

**UNVERIFIED (seen only in search snippets or secondary pages; not opened on arxiv.org):**
- 2603.06859 (C3, counterfactual message-level credit for multi-agent LLM RL; leave-one-out replay rather than a judge).
- 2604.14820 (SWE-TRACE, rubric-based PRM with a rubric agent giving dense step feedback in SWE agentic RL).
- 2604.10493 (SWE-Shepherd, PRM for code agents).
- 2502.16863 (LLM-MCA, LLM centralized critic for MARL credit).
- 2502.03723 (LCA, LLM-guided credit assignment in classical MARL).
- 2608.03222 (Fail-Fast, Restart-Smart, an inference-time failure predictor and restart for SWE agents).
- 2605.02801 (RL for LLM MAS through orchestration traces, survey-like).

**Not found as a distinct paper:**
- "Who&When"-style attributor used as the RL reward for MAS agents (see Gap 1).
- "verbal reinforcement" 2024–2026 agent-training papers beyond those above. Reflexion (2023) is the inference-time ancestor and is out of the date range.
