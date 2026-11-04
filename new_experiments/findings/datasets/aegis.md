# AEGIS / Aegis-Bench — inspection notes (G4)

Scripts: `inspect/aegis_stats.py`, `inspect/aegis_cues.py` (→ `results/aegis/stats.md`), dump of 39 test records with
all faulty-agent turns expanded: `results/aegis/close_reading_dump.txt` (picks in `results/aegis/picks.txt`, 10 per mode for FM-1.3, 2.6, 3.1, 2.5).

## 1. Data as loaded

- 9,533 records (600 test), 6 frameworks: agentverse 2,449, llm_debate 2,404, macnet 2,359, dylan 1,567, smoagents 481, magentic_one 273. Labels = set of (agent, mode) pairs (mean 2.3–3.0 per record except smolagents/magentic 1.0); `error_steps` from the loader = first turn with `is_injected` (MacNet only, 2,359 rows).
- **The MacNet marker is not a step label and not even an agent label.** Marked set == faulty_agents set in only 1,149/2,359 records; in 1,210 the marked turns include an agent that is *not* faulty (almost always `Node-2`, the output/sink node: its turns are flagged because they are *downstream* of an injection), and in 659 a faulty agent has no marked turn. So `is_injected` ≈ "turn produced under the influence of an injection" (contaminated), which is a different quantity from "turn that was corrupted". The loader's `error_steps` should be treated as "first turn of the first contaminated node", nothing more; the only trustworthy label is the (agent, mode) set.
- `malicious_action_description` is empty in 65% of pairs and a generic "Node 0 injected with response_corruption" otherwise: the dataset does not say *what* was injected.
- Strategies: response_corruption 11,964 / prompt_injection 10,464 / `prompt` 273 (magentic_one). Model is gpt-4o-mini everywhere.

## 2. Close-reading notes (≈20 records skimmed, 10 read closely; test split)

| id | fw | faulty (agent: mode) | what the injected turns actually do | surface cue? | mode fits text? |
|---|---|---|---|---|---|
| MATH_llm_debate_40 | debate | Assistant2: FM-1.3, Assistant3: FM-2.4 | A2: "we will go through these steps repetitively … And now again: BA = (-2,-7,1)"; A3: "The vector BA is calculated **incorrectly** as follows … Next, we **miscalculate** BC" | yes: the text announces repetition / incorrectness | 1.3 yes (caricature); 2.4 "withholding" no — it is wrong arithmetic |
| smol+gaia_smoagents_3 | smolagents | Searcher: FM-1.3 | Searcher turns are ordinary tool calls; the wrong name "Sebastian" comes back from the managed search_agent | none | no repetition anywhere |
| MMLU_macnet_24 | macnet | Node0: FM-1.3, Node3: FM-1.5 | Node0 critique: "repeat this identification multiple times"; Node0 answer header literally "**Incorrect Answer: (C)**"; Node3 denies temporal contiguity matters; final Node-2 output header "**Incorrect Answer: (B)**" | yes, including in the *final output* | 1.5 "unaware of termination" no |
| SciBench_agentverse_15 | agentverse | Solver: FM-2.1, Critic: FM-1.3, Evaluator: FM-1.1 | Solver: formula "F = q + E", "Calculating the components incorrectly:"; Critic: contradicts itself turn to turn; Evaluator: "Correctness: 0" (reasonable) | yes (Solver) | 2.1 "conversation reset" no |
| smol+gaia_smoagents_41 | smolagents | Manager: FM-1.3 | Manager plan/search/compute; computes 1/5.1 = 20% (GT 22) | none | no |
| MMLU_agentverse_4 | agentverse | RoleAssigner: FM-1.5, Critic: FM-1.4, Evaluator: FM-1.3 | RoleAssigner: "dentist with expertise in hand and nail anatomy"; Evaluator: "Let's begin by verifying the sum of 2 + 2 … again … again" in a lymph-node question | yes (absurd roles, 2+2) | 1.3 yes; 1.4/1.5 no |
| MMLU_macnet_31 | macnet | Node0: FM-1.1, Node1: FM-2.2, Node3: FM-1.3 | Node1 critique: "ignore the provided options and fabricate a new hypothesis … exotic spices"; three different answers (C, H, fibrous) across nodes | yes | 2.2 "fail to ask for clarification" no |
| GSM8K_dylan_12 | dylan | **all four** assistants faulty (1.3, 1.1, 1.2, 2.1) | each turn changes the problem's numbers (20 tickets at $2, 15 at $3, 40 at $3, half of 20 …); "I will take a creative approach and alter the assumptions" | yes | attribution is degenerate: every agent is faulty |
| GSM8K_agentverse_4 | agentverse | RoleAssigner: 1.5, Solver: 3.3, Evaluator: 1.3 | Evaluator rewrites the problem (5 cheese + 3 onion, 16 slices, 5 pizzas) and says "go through the steps repeatedly to ensure"; roles "astrology" | yes | 3.3 for the Solver: its first turn is correct |
| MMLU_llm_debate_27 | debate | A1: 2.3, A3: 2.6 | A3: "given that it doubles in mass every day" for a decay problem; A1 looks normal | partly | 2.6 "reasoning-action mismatch" ≈ reasoning error |
| MMLU_llm_debate_21 | debate | A1: 2.6, A3: 3.3 | A1's two turns are sensible and pick the right answer (H); A3 invents "chronic back pain … prolonged bed rest" | A1 none | A1 label unsupported by text (prompt injection with no visible effect) |

Recurring observations:
1. **Response corruptions announce themselves.** "calculated incorrectly", "we miscalculate", "again for emphasis", "Incorrect Answer:", "ignore the provided options and fabricate", "I will take a creative approach and alter the assumptions". The corrupting LLM was asked to produce mode X and wrote text *about* producing mode X. This is the opposite of Who&When Pro, where the injector keeps the agent's voice.
2. **The commonest corruption is changing the problem's numbers** (tickets, slices, charge, vector coordinates) regardless of the mode label; the mode label then rarely matches (FM-2.1/2.2/2.4/1.5 attached to plain arithmetic/fact errors). The 14 modes are near-uniform by design (report), so most pairs are "mode name + generic corruption".
3. **Prompt-injected agents can look clean** (smolagents Searcher/Manager, debate_21 A1): the injection altered the agent's *input*; the output is normal text with a wrong fact that is only wrong relative to the world (not to the prefix). These are the undetectable minority.
4. **Many records have ≥3 of 4–5 agents faulty** (dylan_12: 4/4; agentverse: Solver+Critic+Evaluator+RoleAssigner): "which agent" collapses to "which agent is *not* faulty".
5. The final output is frequently itself corrupted ("Incorrect Answer: (B)") — the sink node is contaminated (is_injected on Node-2).

## 3. Targeted statistics (`results/aegis/stats.md`)

### 3a. Structural priors

| framework | n | turns | pairs/traj | top faulty agents | strategies |
|---|---|---|---|---|---|
| agentverse | 2449 | 12.4 | 2.99 | Solver 31%, Evaluator 26%, RoleAssigner 24% | rc 4172 / pi 3154 |
| dylan | 1567 | 11.0 | 2.60 | Assistant4 14%, Assistant1 12%, Assistant3 10% | rc 2181 / pi 1894 |
| llm_debate | 2404 | 12.0 | 1.97 | Assistant1 35%, Assistant3 34%, Assistant2 30% | rc 2343 / pi 2385 |
| macnet | 2359 | 10.0 | 2.47 | Node0 44%, Node3 31%, Node1 25% | pi 2550 / rc 3268 |
| magentic_one | 273 | 16.3 | 1.00 | Orchestrator 47%, WebSurfer 27%, Coder 18% | prompt 273 |
| smoagents | 481 | 18.3 | 1.00 | Manager 56%, Searcher 44% | pi 481 |

- Constant-agent prior (most frequent faulty agent of the framework) hits a faulty agent in **72.4%** of records (agentverse 93%, macnet 85%, debate 70%, dylan 35%, smolagents 56%, magentic 47%).
- Mean 4.37 speaking agents, 2.32 faulty: **54% of the speaking agents are faulty** on average. Agent-level F1 of 76.5 (Aegis-SFT) must be read against this.

### 3b. Surface cues: faulty-agent turns vs clean-agent turns within the same trajectory

| framework | n | d chars | d hedge | d cert | d selfref | loop_words % inj/clean | ignore % | wrong_arith % |
|---|---|---|---|---|---|---|---|---|
| agentverse | 2188 | +370 | +1.52 | -1.04 | -0.62 | 4/1 | 8/1 | 11/5 |
| dylan | 1138 | -104 | +0.44 | -0.27 | +0.30 | 4/3 | 4/3 | 14/17 |
| llm_debate | 2277 | +163 | +1.65 | +0.01 | +1.36 | 8/4 | 10/2 | 25/28 |
| macnet | 2359 | +175 | +1.11 | -0.14 | +0.97 | 5/2 | 14/5 | 14/17 |
| magentic_one | 206 | -94 | -0.37 | -0.16 | -0.98 | 3/2 | 3/2 | 1/0 |
| smoagents | 481 | -3210 | -0.11 | -0.42 | +0.06 | 8/24 | 1/2 | 0/0 |

Self-announcing cue regex (incorrectly / miscalculate / again for emphasis / disregard / prematurely / Incorrect Answer …):

| framework | % faulty-agent turns with cue | % clean-agent turns with cue | records with any cue | cue-argmax agent is faulty % | constant-agent prior % |
|---|---|---|---|---|---|
| agentverse | 38.6 | 44.8 | 86% | 77.2 | 93.1 |
| dylan | 41.1 | 29.6 | 81% | 58.5 | 35.4 |
| llm_debate | **27.4** | **7.0** | 61% | **91.1** | 69.5 |
| macnet | 48.4 | 29.9 | 100% | 66.5 | 84.8 |
| magentic_one | 14.2 | 21.7 | 45% | 32.5 | 47.3 |
| smoagents | 1.2 | 1.6 | 16% | 42.7 | 55.7 |
| ALL | 36.5 | 25.6 | 78% | 72.3 | 72.4 |

- In debate the cue alone attributes the agent at 91% (vs 70% prior); in dylan 58% (vs 35%). In agentverse/macnet the *critic* roles legitimately say "incorrect", so the cue is diluted — but note that in those frameworks the constant-agent prior is already 85–93%.
- Per mode, faulty turns carry a cue in 30–43% for every mode except FM-1.3 (56%): the cue is a property of the corruption generator, not of the mode.
- smolagents / magentic_one (prompt-injection-only, long tool traces) show no cue and no length signal: the injection is invisible in text.

### 3c. What the loader's `error_steps` measures (MacNet)
- marked == faulty agents: 48.7%; marked ⊃ non-faulty (sink) : 51.3%; faulty agent with no marked turn: 27.9%; first marked turn = first turn of that agent: 72.1%.

## 4. Baseline error analysis

PENDING — `all_at_once.py aegis --n 60` (runner chain C). Only agent accuracy is meaningful; `score()` compares the predicted agent with `faulty_agents[0]`, so "agent_ok" undercounts (any faulty agent should count). Will recompute against the set and split by framework and by whether the predicted agent's turns carry a cue.

## 5. Annotation / construction issues (prevalence)

1. **No step label; the MacNet flag marks contamination, not corruption** (51% of flagged records include the clean sink node). Any step-level use of AEGIS is unsupported.
2. **Mode labels rarely describe the text** (8 of 10 closely read pairs mismatched; modes near-uniform by design while corruptions are mostly "change a number / state a wrong fact"). Error-level F1 ≈ 20–27% in the paper is probably the ceiling of what the text supports.
3. **Self-announcing corruptions** in 27–48% of faulty turns (regex lower bound): a classifier can learn "says incorrectly" instead of "is incorrect"; explains SFT's +40 pp agent F1 and its drop on Who&When (report).
4. **Majority-faulty records**: 54% of agents faulty on average; several records with all agents faulty.
5. **Prompt-injected agents with no visible effect** are still labelled faulty (debate_21 A1): the label is the *plan*, and `is_injection_successful` is always true at the record level, not per pair.
6. The `malicious_action_description` is empty/generic: the dataset cannot be used to learn "what" beyond the mode name.

## 6. Candidate hypotheses

**H1 — The AEGIS signal is an authorial voice, not an error.** Corrupted turns are written by a different "author" (an LLM told to misbehave) and carry announcements, number changes and absurd roles; clean turns are the base agent. Test: train a turn-level stylistic classifier (TF-IDF or small encoder) on faulty vs clean turns with the *problem content masked* (numbers and nouns replaced); if accuracy stays ≫ chance, the signal is stylistic; then apply it to Who&When Pro injected turns (expect chance) and to natural data (expect chance). Shared with: tracertraj sed/refusal artefacts; not with WWP (z selfref ≈ 0).

**H2 — "Which agent is clean" is the easier dual problem on AEGIS.** With 54% of agents faulty and up to 4/4, the complement is smaller. Test: score an attributor by predicting the *clean* set and inverting; compare agent F1.

**H3 — Prompt injection vs response corruption are two datasets.** Response corruptions leave cues (§3b); prompt injections leave normal-looking text whose only tell is a wrong fact (smolagents/magentic: cue rate ≈ clean). Test: split every metric by `injection_strategy`; expect agent F1 to differ by ≥20 pp; models trained on rc should not transfer to pi. Shared with: WWP Magentic-One `client_patch` vs `direct_chat_completion`.

**H4 — Mode is not recoverable from the turn; it is recoverable from the framework.** Modes are uniform by design but each framework's corruptor has a house style (agentverse: roles; debate: numbers; macnet: critique inversions). Test: predict mode from (framework, agent role) only vs from text only.

**H5 — Downstream contamination is flagged, not corruption (MacNet).** The `is_injected` flag on Node-2 is exactly the "inherited error" of P1. Test: in MacNet records where Node-2 is flagged but not faulty, measure whether the final answer differs from the GT more often than in records where it is not flagged — if yes, the flag tracks *propagated* error and could serve as a free propagation label for a P1 study (the only such label in the group).

## 7. Open questions

- What did the `prompt` strategy (magentic_one, 273) do — is it a system-prompt change to the orchestrator?
- `num_injected_agents` ≠ number of pairs in 22% of records (report): are the extra pairs post-hoc "refinements" for DyLAN, i.e. labels added after seeing the run?
- Does `is_injection_successful` mean "final answer wrong" only, so that absorbed injections (the agent ignored the corrupted input) are still labelled faulty?
