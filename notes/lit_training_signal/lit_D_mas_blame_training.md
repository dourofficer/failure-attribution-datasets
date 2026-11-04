# Lit search D: credit assignment and blame-based training in LLM multi-agent systems

Search date: 2026-10-28.

Scope: methods that work out which agent (and which step or message) caused a MAS outcome, and then use that signal to update the agents. Updates can be weights (RL, DPO, SFT), or prompts and workflows when the update is localized by blame. This is the opposite of giving every agent the same shared outcome reward.

Method: WebSearch for discovery, then WebFetch of the arxiv.org abs page (title, authors, dates, comments) and of the HTML full text for the method and result details.

Verification legend:
- **VERIFIED**: the arXiv abs page was fetched and the method details were read from the HTML full text.
- **VERIFIED-abs**: only the abs page was fetched.
- **PARTIAL**: seen only in search results or secondary pages. The id is real, but the details were not read first-hand.

Numbers are as reported by the authors. Where the fetched text showed an inconsistency, it is noted.

---

## 0. Quick map

| # | Paper | arXiv | Blame source | How blame enters the update | Update type |
|---|---|---|---|---|---|
| 1 | MALT | 2412.01928 | Monte-Carlo value over a G->V->R search tree | per-role SFT + DPO pairs | weights |
| 2 | ACC-Collab | 2411.00053 | rollout value of guided vs natural responses | per-round DPO pairs, actor/critic alternation | weights |
| 3 | CollabUIAgents | 2502.14496 | LLM critic (GPT-4o) scores each agent x round | per-agent DPO on rewarded actions | weights |
| 4 | MAPoRL | 2502.18439 | verifier score + influence on later turns | per-agent reward, multi-agent PPO | weights |
| 5 | SiriuS | 2502.04780 | outcome filter + feedback-driven per-agent regeneration | per-agent SFT on its own successful steps | weights |
| 6 | CoMAS | 2510.08529 | peer LLM scorer of solution/critique pairs | zero-sum per-agent reward, REINFORCE++ | weights |
| 7 | MarsRL | 2511.11373 | role-specific verifiable rewards (Verifier judged on its own verdict) | per-agent GRPO reward | weights |
| 8 | Who Gets the Reward & Who Gets the Blame | 2511.10687 | Shapley (success) + first-error prefix judge (failure) | per-message reward / DPO pairs (conceptual) | weights (proposed) |
| 9 | MAPPA | 2601.23228 | LLM "coach" scores every action, blames upstream agent | per-action process reward, REINFORCE++ | weights |
| 10 | SHARP | 2602.08335 | leave-one-out "Shapley" marginal credit (agent masked) | per-agent reward term + per-agent advantage norm | weights |
| 11 | C3 | 2603.06859 | counterfactual continuation per message (LOO baseline) | per-message advantage in PPO surrogate | weights |
| 12 | CCPO / SEPO | 2603.21563 | agent-removal counterfactual / self+peer eval with a lambda_blame term | role-specific rewards for GRPO/GSPO | weights |
| 13 | COSAC | 2604.17693 | additive ridge decomposition + fictitious continuations (aristocrat utility) | per-agent counterfactual advantage, PPO | weights |
| 14 | AgentGrad | 2609.08572 | sequential intervention: the agent whose fix flips the outcome | textual gradient only for that agent's prompt | prompt |
| 15 | HiveMind (CG-OPO) | 2512.06432 | DAG-Shapley over the agent workflow | refine prompt of the lowest-Shapley agent | prompt |
| 16 | LangMARL | 2604.00722 | centralized LLM critic writes per-agent credit text | language-gradient update of each agent's prompt | prompt |
| 17 | MAPRO | 2510.07475 | downstream agents generate blame for upstream agents (reverse graph walk) | blame-conditioned prompt mutation | prompt |
| 18 | TRUCE | (ICML 2026, no arXiv id found) | trajectory-aware attribution to sub-trajectories / prompt rules | unit-level edits of prompt rules | prompt |
| 19 | Temporal+Structural credit | 2605.30227 | LLM-judge role credit + per-round aggregator credit | block coordinate descent: update only low-credit roles/rounds | prompt |
| 20 | HERA | 2604.00901 | orchestrator names the "primary contributor" to failure | role-aware prompt evolution for that agent | prompt |
| 21 | Optimas | 2507.03041 | learned per-component local reward fn aligned with global reward | per-component prompt/PPO/hyperparam updates | prompt + weights |
| 22 | AgenTracer (downstream use) | 2509.03312 | trained 8B attributor (Who&When-style) | attribution reasoning fed back for 3 retry rounds | inference-time |
| 23 | DoVer | 2512.06749 | attribution hypothesis + targeted intervention | edits messages/plans to repair failed runs | inference-time |

Core list for the survey: #1-#17 and #21. #18-#20 and #22-#23 support it. Section C below holds adjacent work and shared-reward baselines.

---

## A. Weight training driven by per-agent / per-message credit or blame

### 1. MALT: Improving Reasoning with Multi-Agent LLM Training (VERIFIED)
- **arXiv:** 2412.01928. v1 2 Dec 2024, v3 6 Oct 2025. COLM 2025.
- **Authors:** Motwani, Smith, Das, Rafailov, Laptev, Torr, Pizzati, Clark, Schroeder de Witt.
- **MAS:** a sequential Generator -> Verifier -> Refiner chain, all initialised from the same base model with role prompts. Each role is trained separately into G', V', R'. At test time, MV@3.
- **How blame is computed:** a search tree with branching factor 3 gives 27 trajectories per question. Leaves are scored 1/0 against ground truth.
  - A verifier node's value is the mean of its refinement children. A generator node's value is the mean of its verifier children.
  - Values are binarized at 0.5.
  - The paper calls this identifying "which model introduced an error". In practice it is Monte-Carlo credit, and a node's value mixes its own quality with downstream behaviour.
- **How blame enters training:**
  - G: SFT on outputs labelled correct. DPO did not help G.
  - V and R: SFT, then DPO on correct/incorrect pairs that share the same parent.
  - LoRA throughout.
- **Base model:** Llama-3.1-8B-Instruct, plus Qwen-2.5-1.5B-Base on GSM8K only.
- **Result:**
  - MATH 57.25, CSQA 81.50, GSM8K 90.50.
  - Baselines: SA 49.50/74.50/84.25; MA+MV 53.50/79.00/87.00; STaR-multi-agent 52.50/75.50/80.00; debate 52.00/71.25/86.75.
  - There is **no clean ablation against a shared outcome label.** STaR-MA is the nearest proxy.
- **Relevance:** the canonical "per-role credit from outcome-only labels -> per-role DPO" recipe. It is the template that a Who&When-style attributor could replace with direct (agent, step) labels.

### 2. ACC-Collab: An Actor-Critic Approach to Multi-Agent LLM Collaboration (VERIFIED)
- **arXiv:** 2411.00053. v1 30 Oct 2024, v3 6 Mar 2025. No venue on the arXiv page.
- **MAS:** a two-agent actor (answers) and critic (feedback) team over 5 deliberation rounds.
- **How blame is computed:** each round's response is valued by rollouts, as the probability that deliberation ends correct.
  - "Guided" responses are steered toward or away from the gold answer.
  - The value differences Δy and Δ!y between guided and natural responses (threshold ε) decide which response is better.
- **How blame enters training:** per-round DPO pairs with an NLL regulariser. Training alternates: the critic is trained first as a best response, then the actor.
- **Base models:** Llama-3-8B-Instruct, Mistral-7B-Instruct, Gemma-2-2B-Instruct. Benchmarks: BoolQ, MMLU, BBH, SCIQ, ARC.
- **Result:**
  - Llama-3 BoolQ: SoM-4x 0.811 -> ACC-Collab+ 0.894.
  - Mistral BBH: DebateGPT 0.480 -> 0.601.
  - No shared-outcome baseline. Baselines are SFT, DebateTune, DebateGPT.
- **Relevance:** early per-agent, per-round counterfactual-value credit in which the critic agent's critique quality is itself trained. It fits the "one agent's error identification trains another" slot.

### 3. CollabUIAgents: Advancing Language Multi-Agent Learning with Credit Re-Assignment for Interactive Environment Generalization (VERIFIED)
- **arXiv:** 2502.14496. v1 20 Feb 2025, v3 20 Aug 2025. COLM 2025.
- **MAS:** n role-free agents (4 in the main mobile setup) on a resampled DAG, with m=3 conversation rounds per step and a majority vote over actions. Domains are mobile and web UI.
- **How blame is computed:** an LLM critic (gpt-4o-2024-08-06) reads the observation, history, full action matrix and task. It outputs a score in [0,1] for each **agent x round**, thresholded at 0.5. This is per-agent, per-round credit re-assignment (CR), and it recovers good intermediate actions from failed trajectories.
- **How blame enters training:** an adversarial agent produces a low-quality alternative for each rewarded action. The pairs are trained with DPO-style preference optimization, online and off-policy.
- **Base model:** Qwen2 7B.
- **Result:**
  - AndroidWorld/MMiniWoB++ SR: 29.3/61.2 full.
  - w/o CR, i.e. outcome reward with trajectory-level DPO: 25.0/56.4.
  - Untrained 4-agent: 21.4/53.2.
- **Relevance:** the clearest early example of a **judge-produced (agent, round) blame matrix used directly as the training signal**, with an ablation against outcome-level training.

### 4. MAPoRL: Multi-Agent Post-Co-Training for Collaborative LLMs with RL (VERIFIED)
- **arXiv:** 2502.18439. v1 25 Feb 2025, v2 12 Jul 2025. arXiv comment: "version for ACL" (ACL 2025).
- **MAS:** Du-et-al. style debate. Training uses 2 agents x 3 turns, evaluation 3 agents x 3 turns. Majority vote.
- **How blame is computed:** a trained verifier scores each agent's answer. The "influence-aware" reward adds discounted future verifier scores of all agents. Incentive terms α0/α1/β0/β1 reward correcting, being persuaded toward the right answer, and persuading others, and penalise the reverse.
- **How blame enters training:** a per-agent reward with multi-agent PPO (a per-turn policy and value, GAE, KL), using QLoRA.
- **Base models:** Phi-3-mini (3.4B), Qwen2.5-3B, Llama-3-8B.
- **Result:**
  - ANLI->GSM8K transfer at turn 3: 0.720 vs 0.640 off-the-shelf.
  - SFT on top trajectories hurts (turn-3 Δ −0.114).
  - No explicit shared-reward ablation was found in the fetched text.
- **Relevance:** a per-agent reward that credits an agent for its effect on teammates' later correctness. This is a crude "who caused the team to go right or wrong" signal.

### 5. SiriuS: Self-improving Multi-agent Systems via Bootstrapped Reasoning (VERIFIED)
- **arXiv:** 2502.04780. v1 7 Feb 2025. No venue on the arXiv page.
- **Authors:** Zhao, Yuksekgonul, Wu, Zou.
- **MAS:** three settings.
  - Sequential expert chains: Physicist/Chemist -> Mathematician -> Summarizer; Context Analyst -> Solver.
  - Actor / Judgment / Critic.
  - Two-player negotiation games.
- **How blame is computed:** coarse. Successful trajectories go to an experience library. For failures, Algorithm 2 loops over **every** agent k. An external feedback model, which sees the gold answer, critiques k's response, and k regenerates; downstream agents re-run. There is **no explicit identification of the faulty agent.**
- **How blame enters training:** per-agent SFT on its own steps from successful or repaired trajectories, via the OpenAI fine-tuning API.
- **Base models:** gpt-3.5-turbo-0125, gpt-4o-mini.
- **Result:**
  - GPT-3.5 Chemistry 56.92 vs STaR 47.69 and CoMM 50.77.
  - The augmentation ablation is small: PubMedQA 74.20 vs 73.40.
- **Relevance:** the "augment failed trajectories, then SFT" baseline. Swapping its brute-force loop over agents for an attributor (repair only the blamed agent) is an obvious and still untested extension.

### 6. CoMAS: Co-Evolving Multi-Agent Systems via Interaction Rewards (VERIFIED)
- **arXiv:** 2510.08529. v1 9 Oct 2025, v2 9 Feb 2026. No venue on the arXiv page.
- **Authors:** Xue, Zhou, G. Zhang, ..., Torr, Ouyang, Bai.
- **MAS:** 4 agents. In each round one proposes a solution, one critiques it, and a scorer rates the pair from 1 to 3.
- **How blame is computed:** the LLM-as-judge score τ̂ is split zero-sum: r(solver) = (τ̂−1)/2 and r(evaluator) = 1 − r(solver). The scorer is penalised for an invalid format. Reward is per solution/critique pair, with **no step-level blame**.
- **How blame enters training:** per-agent REINFORCE++ with separate replay buffers. GRPO was rejected because there is no same-prompt group.
- **Base model:** Qwen2.5-3B-Instruct. Heterogeneous variant: Qwen + Llama-3.2-3B. Qwen2.5-7B in the appendix.
- **Result:**
  - AutoGen GSM8K 52.60 -> 72.40.
  - MAPoRL 50.00 and TTRL 41.00 in the same setting.
  - Removing the scorer leads to reward hacking.
- **Relevance:** a judge-derived per-agent reward with no external verifier. It shows that peer blame can be hacked unless it is anchored.

### 7. MarsRL: Advancing Multi-Agent Reasoning System via RL with Agentic Pipeline Parallelism (VERIFIED)
- **arXiv:** 2511.11373. v1 Nov 2025. Tencent Hunyuan.
- **MAS:** Solver -> Verifier1 -> Corrector1 -> Verifier2 -> Corrector2.
- **How blame is computed:** individualized verifiable rewards.
  - Solver and Corrector: correctness of their own output.
  - **Verifier: rewarded on whether its verdict matches the true correctness of the solution it judged.**
  - The paper's own example: under a shared reward, a Verifier that wrongly flags a correct solution is still rewarded if the Corrector ends correct. MarsRL avoids this.
- **How blame enters training:** per-agent rewards in GRPO with UloRL segment rollouts.
- **Base model:** Qwen3-30B-A3B-Thinking-2507.
- **Result:**
  - AIME-2025 system 85.6 -> 93.3; BeyondAIME 63.3 -> 73.8.
  - **No ablation of individual vs shared reward** in the fetched text.
- **Relevance:** the simplest version of "do not reward an agent for an outcome it did not cause". It is the self-correction / critic-training case.

### 8. Who Gets the Reward & Who Gets the Blame? Evaluation-Aligned Training Signals for Multi-LLM Agents (VERIFIED)
- **arXiv:** 2511.10687. v1 11 Nov 2025, v2 withdrawn, v3 1 Jul 2026. NeurIPS 2025 LAW workshop.
- **Authors:** Yang, Mallick, Chen, Raghavan, Gueroudji, Foster, Thakur (Argonne).
- **MAS:** a worked example with Planner, Database agent and Analyst on data-analysis tasks.
- **How blame is computed:**
  - Successful runs: a Shapley value per agent over counterfactual replays, where absent agents emit baseline/no-op output with frozen seeds. A judge or PRM then labels each message −1/0/+1, and the agent's φ_i is split across its messages so that credit is conserved.
  - Failed runs: a **prefix judge** (execution check, rubric LLM judge, or PRM) finds the **first erroneous message t\***, using binary search. A failure-alignment judge then credits later repair attempts.
- **How blame enters training:**
  - Success route: per-message dense rewards for PPO/GRPO.
  - Failure route: (H_{t*−1}, y⁺, y⁻) preference pairs for DPO.
- **Experiments:** **none**. The abstract says "Our contribution is conceptual."
- **Relevance:** the most explicit statement of the pipeline our survey cares about, a Who&When-style "first decisive error" turned into DPO pairs on the blamed agent. It is untested.

### 9. MAPPA: Scaling Multiagent Systems with Process Rewards (VERIFIED)
- **arXiv:** 2601.23228. v1 30 Jan 2026, v2 4 Feb 2026. ICLR 2026 Workshop on AI with Recursive Self-Improvement, confirmed on iclr.cc as a workshop poster.
- **Authors:** Ed Li, Junyu Ren, Cat Yan.
- **MAS:**
  - MathChat: Problem Solver -> Code Executor -> Verifier.
  - DSBench: Data Engineer -> Modeler -> Analyst, passing files between them.
- **How blame is computed:** an LLM **coach** (Gemini 2.5 Flash or Pro) scores **every action** from the agent's role, its input, its action and the tool stdout/stderr.
  - The coach explicitly blames upstream agents. A downstream FileNotFoundError for X_test.pkl is charged to the Data Engineer, not the agent that hit it.
  - Ground truth is used only for the final action.
- **How blame enters training:** per-action process reward with REINFORCE++. Return-to-go advantages are normalised across agents, with a PPO clip. Each agent has its own weights.
- **Base models:** DeepSeek-R1-Distill-Qwen-1.5B, Qwen3-4B.
- **Result:**
  - Qwen3-4B AIME 49.2 -> 66.7; R1-Distill-1.5B AMC 60.9 -> 78.1.
  - DSBench success 50.0 -> 66.7.
  - **No outcome-only (shared reward) ablation.** Single runs, small eval sets (30 AIME, 6 DSBench tasks).
  - The paper is inconsistent about the score range (0-10 vs [0,1]).
- **Relevance:** the closest "judge-based failure attribution used as an RL reward" in a weight-training loop. In effect the coach is a step-level attributor applied online.

### 10. SHARP, "Who Deserves the Reward? SHARP: Shapley Credit-based Optimization for Multi-Agent System" (VERIFIED)
- **arXiv:** 2602.08335. v1 9 Feb 2026, v2 2 Jun 2026. No venue on the arXiv page.
- **Authors:** Y. Li, X. Zhang, ..., L. Shen.
- **MAS:** a planner plus worker agents with code-executor and browsing tools. One shared policy plays all roles. Trained on MuSiQue. Eval: MuSiQue, GAIA-text, WebWalkerQA, FRAMES.
- **How blame is computed:** the Shapley formula is stated, but in practice it is a **leave-one-out counterfactual**: credit = R_acc(τ) − R_acc(τ with agent m masked). Planner credit is λ times the mean of positive worker credits.
- **How blame enters training:** R = 0.9·R_broadcast + 0.9·R_marginal + 0.1·R_tool, normalised per agent identity, with a GRPO-style objective.
- **Base model:** Qwen3-8B, plus a Llama-3.1-8B variant.
- **Result:**
  - Avg 32.56 vs MATPO 30.81 and single-agent GRPO 27.89.
  - **MuSiQue ablation: no-Shapley (broadcast only) 47.00 vs full 50.76.**
  - Harmful-subagent share 5.48% -> 4.40%.
  - The headline "+23.66% / +14.05%" did not obviously reproduce from the table.
- **Relevance:** a direct counterfactual-removal credit vs broadcast-reward ablation in a tool-using hierarchical MAS.

### 11. C3, retitled "The Trace Is the State: Exact Credit Assignment for LLM Agent Teams"; v1 title "Contextual Counterfactual Credit Assignment for Multi-Agent Reinforcement Learning in LLM Collaboration" (VERIFIED)
- **arXiv:** 2603.06859. v1 6 Mar 2026, v4 7 Oct 2026. No venue on the arXiv page. Code: github.com/EIT-EAST-Lab/C3.
- **Authors:** Y. Chen, Sun, H. Wang, J. Wang, X. Zhang, X. Shen, W. Li, W. Zhang.
- **MAS:** a Reasoner -> Actor chain (from MARFT). Analysis also covers 3-agent (+Verifier), 4-turn, 5- and 10-agent chains, and a branching planner/2 solvers/integrator. Math tasks.
- **How blame is computed:** **counterfactual continuation**. Reset to the recorded trace prefix, substitute an alternative message, regenerate only the downstream messages, and score the final reward.
  - Leave-one-out baseline over the alternatives at the same decision point.
  - Exact when the trace is the full state.
  - Budget: 8 rollouts, i.e. 2 Reasoner alternatives x 4 Actor alternatives.
- **How blame enters training:** a per-message advantage in a PPO clipped surrogate.
- **Base model:** Qwen3-4B-Instruct-2507.
- **Result:**
  - MATH500 82.8 vs MAGRPO 74.5 and MAPPO 69.3. Avg 90.9 vs 88.0 vs 85.8. 5 seeds.
  - 37% fewer training tokens than MAPPO.
  - C3 credit rank-correlates 0.69 with a 16-continuation reference; a learned critic reaches 0.29.
- **Relevance:** the training-side twin of AgenTracer's counterfactual-replay labelling. It also gives a reliability metric for credit (split-half reliability drops to 0.01 at 10 agents), which bears on how trustworthy step-level blame labels can be.

### 12. CCPO / SEPO: Counterfactual Credit Policy Optimization for Multi-Agent Collaboration (VERIFIED)
- **arXiv:** 2603.21563. v1 23 Mar 2026, v5 11 Jun 2026. No venue on the arXiv page. Code: github.com/bhai114/ccpo.
- **Authors:** Z. Li, Tian, Chen, H. Zhang, Y. Liu, Ban, Zhuang.
- **MAS:** a Think -> Solve dyad.
- **How blame is computed:**
  - **CCPO:** Thinker credit Δ1 = R_joint − R_solo, where the Solver answers without the Thinker's trace. The Solver gets a gated fusion of joint and solo signals.
  - **SEPO:** constrained self- and peer-evaluation scores, anchored to the verifier. On failure the role reward is R_ver − **λ_blame**·bonus_i, so the agent judged more responsible loses more.
- **How blame enters training:** role-specific rewards, z-normalised, into GRPO or GSPO. The method is claimed optimizer-agnostic.
- **Base models:** Qwen2.5-1.5B/7B, Llama3.1-8B, Qwen3-4B-Base, OLMo3-7B.
- **Result:**
  - **Shared-reward vs CCPO on MATH500:** 60.0->61.0, 51.8->53.4, 75.4->77.6, 78.0->79.4.
  - Mixed elsewhere, e.g. Qwen2.5-7B AMC23 57.5 -> 45.0 and Qwen3-4B AIME25 13.3 -> 6.7.
- **Relevance:** one of few papers with a head-to-head comparison against a shared reward, and the gains are **not uniform**. SEPO is an explicit self/peer "blame" coefficient.

### 13. COSAC: Counterfactual Credit Assignment in Sequential Cooperative Teams (VERIFIED)
- **arXiv:** 2604.17693. v1 20 Apr 2026, v2 9 May 2026. No venue on the arXiv page.
- **Authors:** Deshmukh, Subramanian, Addanki, Vlassis.
- **MAS:** a fixed-order team. LLM experiment: 4 Qwen3-0.6B agents (LoRA) answer ARC questions in turn.
- **How blame is computed:** a ridge-regression additive decomposition of team reward over per-agent (binned) actions. "Sequential Aristocrat Utility" counterfactual advantages are built from fictitious continuations of the current policy, with no extra reward calls.
- **How blame enters training:** per-agent PPO-clipped updates, applied in execution order.
- **Result:**
  - AUC at α=0: 0.721 vs MA-GRPO 0.663 and C3 0.564.
  - At α=1 (independent reward) COSAC ties MA-GRPO.
  - Only 10 questions, so preliminary.
- **Relevance:** brings the classical difference-reward / aristocrat-utility family into LLM teams. Its theory says shared reward hurts most when the reward is team-coupled.

---

## B. Prompt / workflow optimization that uses localized blame (not weight training)

### 14. AgentGrad: Intervention-guided Prompt Optimization for Multi-Agent Systems (VERIFIED)
- **arXiv:** 2609.08572. v1 8 Sep 2026, v2 29 Sep 2026. **NeurIPS 2026**, per the arXiv comment.
- **Authors:** Chu, Seo, Cho, Na, Xiong, Kim, H. J. Kim.
- **MAS:** chains of N agents, using the GEPA setups for HotpotQA, HoVer, IFBench and PUPA, and MACM for MATH.
- **How blame is computed:** **sequential intervention**, in reverse execution order. A hint built from gold answers or constraints is added to one agent at a time. The target is the first agent whose corrected output makes the whole system succeed. This is the Who&When "decisive error" definition, made operational.
- **How blame enters the update:** a textual gradient from (prompt, input, original output, corrected output) **for that agent only**. Gradients are clustered semantically and abstracted. A candidate prompt is accepted only if it improves validation.
- **Base LLMs:** GPT-5-mini, Qwen3-8B.
- **Result:**
  - Avg gain +11.76 vs GEPA +9.24, TextGrad +6.33, MIPROv2 +5.66 (GPT-5-mini).
  - 2.5x faster and 21.8% cheaper than GEPA.
  - It does **not** compare against LLM-judge attribution (e.g. Who&When all-at-once) for picking the target.
- **Relevance:** the strongest 2026 evidence that intervention-verified blame beats unverified target selection for MAS updates. It is a natural consumer of attribution-benchmark methods.

### 15. HiveMind: Contribution-Guided Online Prompt Optimization of LLM Multi-Agent Systems (VERIFIED)
- **arXiv:** 2512.06432. v1 6 Dec 2025. **AAAI 2026**.
- **MAS:** a 7-agent DAG for stock trading: 3 analysts -> 3 outlook agents -> trader.
- **How blame is computed:** **DAG-Shapley** with v(S) = Sharpe ratio of the coalition. Non-viable coalitions are pruned (128 -> 49) and intermediate outputs are reused (448 -> 73 LLM calls). It is claimed identical to exact Shapley.
- **How blame enters the update:** each cycle, the agent with the lowest Shapley value, if below a threshold τ, gets lessons from its failure and success cases appended to its prompt.
- **Base LLM:** GLM-4-Flash.
- **Result:**
  - META bull market 13.72% vs 4.44% without CG-OPO.
  - There is no comparison against random or all-agent selection.
- **Relevance:** exact Shapley blame drives a selective, single-agent update.

### 16. LangMARL: Natural Language Multi-Agent Reinforcement Learning (VERIFIED)
- **arXiv:** 2604.00722. v1 1 Apr 2026.
- **Venue:** an ACL Anthology entry 2026.emnlp-main.1837 appeared in search with the subtitle "...via Semantic Credit Assignment". That page was not fetched.
- **MAS:** Overcooked-AI (2 agents), Pistonball (10-20 agents), and HumanEval/HotpotQA/MATH recast as multi-agent tasks.
- **How blame is computed:** a centralized LLM critic reads the episode and writes, **per agent**, how that agent's actions helped or hurt. This is Monte-Carlo, text-valued credit.
- **How blame enters the update:** per-agent language gradients are merged semantically, and an LLM optimizer rewrites that agent's prompt policy (CTDE).
- **Base LLMs:** GPT-3.5-turbo, GPT-4o-mini.
- **Result:**
  - Best in every row vs Reflexion, TextGrad and Symbolic, which use joint/team feedback. E.g. Pistonball N=12: 29.6 vs TextGrad 24.3.
  - The ablation "shared global reward instead of credit" shows a clear drop, but the numbers are in figures only.
- **Relevance:** the direct LLM-era analogue of COMA's per-agent critic, done in language space.

### 17. MAPRO: Recasting Multi-Agent Prompt Optimization as Maximum a Posteriori Inference (VERIFIED)
- **arXiv:** 2510.07475. v1 8 Oct 2025. No venue on the arXiv page.
- **MAS:** Chain, DMAD and ChatEval topologies on code, QA and math tasks.
- **How blame is computed:** a global execution-feedback signal, plus **local blame generated by walking the graph in reverse**: each downstream agent's LLM writes blame for its upstream agents.
- **How blame enters the update:** the MAP-selected prompts are mutated using global and local feedback. Belief propagation over node and edge reward models selects prompts.
- **Base LLMs:** Claude Haiku 3.5, Llama-3.3-70B.
- **Result:** HumanEval-ET 80.21 vs raw 69.38 and TPE (MASS-like) 75.00 on Chain.
- **Relevance:** explicit LLM-generated "downstream blames upstream" signals, localizing prompt updates.

### 18. TRUCE, "From Interaction Trajectories to Prompt Rules: Credit Assignment for Multi-Agent Prompt Optimization" (VERIFIED via PMLR; no arXiv id found)
- **Venue:** ICML 2026, PMLR 306:137252-137271. OpenReview pXF0puBofz. Code: github.com/bingo-w/TRUCE.
- **Authors:** B. Wu, H. Xu, Zhuang, Z. Chen, Z. Li, Yilmaz, Q. Zhang.
- **Method:** "Trajectory-based Rule Credit Estimation" links outcome feedback to informative sub-trajectories, then makes unit-level edits to the prompt-defined behavioural rules responsible, with roles and topology fixed.
- **Not read in detail:** the full text (MAS, base models, numbers).
- **Relevance:** credit at the level of sub-trajectory and prompt rule, which is finer than the agent level.

### 19. Unifying Temporal and Structural Credit Assignment in LLM-Based Multi-Agent Prompt Optimization (VERIFIED)
- **arXiv:** 2605.30227. v1 28 May 2026. No venue.
- **MAS:** LLM-Debate and DyLAN on AQuA, MedMCQA, GPQA and MMLU.
- **How blame is computed:**
  - Structural credit per role: an LLM-judge score plus a peer-view proxy.
  - Temporal credit: a per-round aggregator score, updated only on "informative failures" (aggregator wrong, some agent right).
- **How blame enters the update:** verbalized block coordinate descent that updates only the bottom-K roles (the two worst) or the low-credit round aggregators.
- **Base LLMs:** Qwen2.5-7B, Llama3-8B, Gemma-7B.
- **Result:**
  - MedMCQA Llama3-8B debate 55.13 -> 64.63.
  - Some cells regress, and the table looked internally inconsistent.
  - No random-selection ablation.
- **Relevance:** separates "which agent" (structural) from "which round" (temporal), the same two axes as Who&When's agent and step.

### 20. HERA, "Experience as a Compass: Multi-agent RAG with Evolving Orchestration and Agent Prompts" (VERIFIED)
- **arXiv:** 2604.00901. v2 2 Apr 2026. No venue on the arXiv page.
- **MAS:** an orchestrator that composes an 8-agent RAG roster per query.
- **How blame is computed:** the orchestrator LLM names the "primary contributor to the trajectory's failure".
- **How blame enters the update:** Role-Aware Prompt Evolution for that agent, using contrastive prompt variants plus operational rules and behavioural principles.
- **Base LLMs:** Llama-3.1-8B or Qwen3-14B orchestrator; GPT-4o-mini agents.
- **Result:** removing prompt evolution costs up to about 30% relative on 2WikiQA. No credit-assignment-specific ablation.
- **Relevance:** LLM-judge blame (all-at-once style) used to choose which prompt to evolve.

### 21. Optimas: Optimizing Compound AI Systems with Globally Aligned Local Rewards (VERIFIED)
- **arXiv:** 2507.03041. v4 9 Feb 2026. **ICLR 2026**.
- **Authors:** S. Wu, Sarthi, ..., Zou, Leskovec.
- **MAS:** compound pipelines (Amazon rec, PubMedQA, STaRK-Prime, HotpotQA, BigCodeBench) with 3-5 components each.
- **How blame is computed:** each component has a learned local reward function. It is trained on preference pairs in which **two outputs of one component are compared by the Monte-Carlo expected global reward**, with upstream fixed and downstream sampled. A component's credit is therefore "how much this output moves the final score".
- **How blame enters the update:** a randomly chosen component is updated with OPRO-style prompts, **PPO on weights** (Qwen2.5-1.5B modules), or hyperparameter sampling, and accepted only if global reward improves.
- **Result:**
  - Avg +11.92% over the best baselines.
  - Its local reward function ranks pairs at 77.96% accuracy vs an LLM judge at 49.52%.
- **Relevance:** shows that learned, outcome-grounded per-component credit beats LLM-judge credit at ranking, a useful contrast for judge-based blame.

### 22. AgenTracer, downstream "feedback" experiment (VERIFIED, sec. 5.3)
- **arXiv:** 2509.03312. **ICLR 2026**.
- **How blame is used:** AgenTracer-8B, a Qwen3-8B model trained with GRPO on TracerTraj counterfactual/fault-injection labels, reads a failed trajectory with no ground truth. Its reasoning is **injected into the MAS in the next attempt**, iterated for 3 rounds.
- **Training:** none of the MAS agents. Systems: MaAS, OWL Workforce, MetaGPT.
- **Result:**
  - +4.8% OWL/GAIA, up to +14.21% MaAS/MATH-500.
  - CRITIC (GPT-4.1) degrades MaAS/GAIA by −4.9% and −5.5% at rounds 2 and 3.
- **Relevance:** the only verified use of a Who&When-style **trained attributor** to improve a MAS. It acts at inference time; it was **not** used as a training reward.

### 23. DoVer: Intervention-Driven Auto Debugging for LLM Multi-Agent Systems (VERIFIED-abs)
- **arXiv:** 2512.06749. v3 31 Jan 2026. Microsoft.
- **Method:** turns log-based attribution hypotheses into targeted interventions (message edits, plan changes) and measures repair rather than attribution accuracy.
- **Result:**
  - Magentic-One on GAIA/AssistantBench subsets: 18-28% of failed trials repaired, and 30-60% of hypotheses validated or refuted.
  - AG2/GSMPlus: 49% recovered.
- **Relevance:** argues that single (agent, step) attribution is often ill-defined. That bears on any training scheme that consumes single-point blame labels.

---

## C. Adjacent work and shared-reward baselines (short, for context)

- **MAGRPO, "LLM Collaboration With Multi-Agent Reinforcement Learning"** (2508.04652, v7 Dec 2025; VERIFIED-abs). The canonical **shared-reward** multi-agent GRPO baseline that C3 and COSAC beat. Writing and coding tasks.
- **Dr. MAS: Stable RL for Multi-Agent LLM Systems** (2602.08847, NeurIPS 2026; VERIFIED-abs). Per-agent advantage normalization to fix gradient blow-up under a global GRPO baseline. Not blame, but a necessary stabiliser for per-agent signals. Math +5.6 and search +15.2 avg@16 vs GRPO.
- **M-GRPO, "Multi-Agent Deep Research: Training Multi-Agent Systems with M-GRPO"** (2511.13288; PARTIAL). Hierarchical main-agent/sub-agent group-relative advantages. Role-level, not blame.
- **JoyAgents-R1**, now retitled "HiMA-Ecom ..." (2506.19846, v3 27 Oct 2026; VERIFIED-abs). The current version's VR-GRPO "updates agents with the highest reward variance". This is selective per-agent updating, but by variance, not blame. Note the id now resolves to a different title.
- **TreeMem: Tree-based Credit Assignment for Multi-Agent Memory System** (2605.04811; VERIFIED-abs). MALT-style tree Monte-Carlo credit for builder/summarizer/retriever agents.
- **MASPRM: Multi-Agent System Process Reward Model** (2510.24803; PARTIAL). A per-agent, per-action value model trained from MCTS outcome labels and used for inference-time search, not policy training.
- **LCA, "Speaking the Language of Teamwork: LLM-Guided Credit Assignment in MARL"** (2502.03723; VERIFIED-abs). An LLM ranks states per agent to produce potential-based dense rewards. The trained agents are **classic MARL policies, not LLMs**.
- **Shapley-Coop** (2506.07388, NeurIPS 2025; PARTIAL). Shapley chain-of-thought pricing and reward redistribution among self-interested LLM agents, at inference time.
- **CausalFlow: Causal Attribution and Counterfactual Repair for LLM Agent Failures** (2605.25338; PARTIAL). Single-agent. Counterfactual step-responsibility scores plus minimal repairs, giving (wrong step, fixed step) pairs proposed for DPO. Multi-agent is left as future work. A close single-agent sibling of MiRL.
- **EvoMAC: Self-Evolving Multi-Agent Collaboration Networks for Software Development** (2410.16946; VERIFIED-abs). Textual back-propagation from test feedback updates agents, but blame is not localized explicitly.
- **MASPO** (2605.06623, ICML 2026; VERIFIED-abs). Scores a prompt by its successors' success, which is implicit downstream credit. Mechanism not confirmed.
- **Surveys useful for snowballing:**
  - "Reinforcement Learning for LLM-based Multi-Agent Systems through Orchestration Traces" (2605.02801). Credit taxonomy at team, role, message and token level.
  - "Beyond Individual Intelligence: ... Collaboration, Failure Attribution, and Self-Evolution in LLM-based MAS" (2605.14892, May 2026). Frames attribution -> self-evolution as a causal chain.
- **"Credit Without Ground Truth"** (2608.19760; VERIFIED-abs). Single-agent ALFWorld audit. It finds that replay-based step credit has weak pooled ordering, and that its usefulness for hindsight training is "unestablished". This is a cautionary note for step-level blame used as reward.

---

## D. Observations for the survey

1. **No verified paper closes the loop from a trained attributor to MAS weight training.** No paper uses a Who&When/AgenTracer/Aegis-style attributor as a reward model or data selector for RL/DPO/SFT of the MAS agents.
   - AgenTracer uses its attributor at inference time only (3 feedback rounds).
   - 2511.10687 proposes first-error-localization -> DPO for MAS, but it is conceptual.
   - CausalFlow proposes it for single agents.
   - MAPPA is closest: an off-the-shelf LLM coach does online per-action blame that feeds REINFORCE++. It is not benchmarked as an attributor, and there is no ablation against a shared reward.
2. **Blame sources used in practice, by family:**
   - Monte-Carlo or counterfactual continuation: MALT, ACC-Collab, C3, TreeMem, Optimas, COSAC with fictitious continuations.
   - Agent removal or leave-one-out: CCPO, SHARP.
   - Exact or DAG-pruned Shapley: HiveMind, 2511.10687.
   - LLM judge/coach: CollabUIAgents, MAPPA, CoMAS, LangMARL, HERA, MAPRO, SEPO, 2605.30227.
   - Role-specific verifiable rewards: MarsRL, MAPoRL.
   - Intervention-verified attribution: AgentGrad, DoVer.
   - The counterfactual families match the "decisive error = first step whose fix flips the outcome" definition in Who&When/AgenTracer.
3. **Few clean ablations against a shared reward:**
   - Available: CCPO (Table 1), SHARP (47.00 vs 50.76), C3 vs MAGRPO, COSAC vs MA-GRPO, CollabUIAgents (w/o CR), and LangMARL (figure only).
   - Missing: MALT, MAPPA, MarsRL, SiriuS, AgentGrad (no judge-attribution baseline).
   - Gains are often modest or non-uniform. CCPO loses on several AMC/AIME cells.
4. **Attribution quality and training benefit are never measured together.** None of the training papers check their credit signal against Who&When/TracerTraj/Aegis labels.
   - C3 reports reliability against a continuation reference and finds it collapses at 10 agents.
   - Optimas reports judge-vs-learned ranking accuracy (49.5% vs 78.0%).
   - "Credit Without Ground Truth" warns that step credit may not help training.
   - This gap is a natural evaluation axis to propose: blame accuracy on attribution benchmarks vs downstream training gain.
5. **The prompt-level work leads the weight-level work on using localized blame.** AgentGrad (NeurIPS 2026), HiveMind (AAAI 2026), TRUCE (ICML 2026) and LangMARL all update only the blamed agent, and AgentGrad shows that verified targeting helps. The RL side mostly still uses dense per-agent credit rather than "update only the culprit".
