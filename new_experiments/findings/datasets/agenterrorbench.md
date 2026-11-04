# AgentErrorBench (AgentDebug) — inspection notes

*G3 "single-agent natural failures". Scripts: `inspect/agenterrorbench_compact.py` (per-turn action/observation view, `results/agenterrorbench/compact/`), `inspect/agenterrorbench_stats.py` (`results/agenterrorbench/stats.md`, `stats_per_run.jsonl`), `inspect/agenterrorbench_nothing_reflection.py` (`nothing_reflection.md`), `inspect/agenterrorbench_label_consistency.py` (`label_consistency.md`); prefix probe `results/agenterrorbench/prefix_probe.jsonl`; baseline `results/agenterrorbench/all_at_once_std.jsonl` + `_analysis.md`.*

## 1. Data as loaded

- 200 records (ALFWorld 100 / GAIA 50 / WebShop 50), 10,026 steps = alternating `env` (user message: task + last observations + admissible actions) and `agent` messages; `native_step` = 1-based agent turn. 199 records have a label (`critical_failure_step` k -> message idx 2k-1); `gaia/GPT-4o_003_memory_b000_t00_e03-21a3a421` has k=3 but only 1 agent turn (see §5).
- Every ALFWorld run and 39/50 WebShop runs are exactly 30 agent turns (the cap); GAIA runs end with an `<answer>` in 48/50 cases (1–30 turns).
- Backbones: GPT-4o 81, Llama-3.3-70B 57, Qwen3-8B 62. Qwen3-8B turns carry a `<think>` block.
- Observations repeat the whole prompt + admissible-action list every turn (ALFWorld env message ≈ 3–5 k chars, WebShop/GAIA up to 50 k), so the informative part of an env step is one line ("current observation is: ...") or one tool result. All statistics below use the extracted action / observation (`compact_turns.json`), not the raw messages.
- Loader caveat (not a bug): `labels.categories` = `[module, module.failure_type]` keeps the shipped spelling; raw modules are `plan`/`planning`, `plan_inefficient`/`inefficient_plan`, `Parameter_error`, `tool_execution_error ` (trailing space); 27 records have an empty failure_type (all 23 Llama ALFWorld runs + Qwen ALFWorld 009/011/027 + Llama WebShop 020). 43 records ship no reason text.

## 2. Close-reading notes (20 trajectories)

Format: id — task; label (1-based turn, category); what happened; verdict.

**ALFWorld**
1. `Qwen3-8B_001_id_1` — hot apple in fridge; **turn 30, system.step_limit**. 30 clean, non-repeating exploration moves (4 countertops, 7 cabinets, drawer, sink, stove), 0 "Nothing happens", apple never seen. There is no decisive wrong action; the only weak decision is turn 20 (arrives at closed cabinet 8 and leaves without opening) and never opening fridge/microwave. **No decisive step exists; the label is a placeholder at the last turn.** 8 of the 10 `step_limit` labels are Qwen runs with this exact profile (0 invalid actions, distinct-action fraction 1.0).
2. `Qwen3-8B_006_id_6` — clean ladle -> diningtable; **turn 1, planning.inefficient_plan**. Opens cabinets 1–13 one by one (turns 1–25), finds the ladle on countertop 1 at turn 27, takes it and at turn 30 moves it to the dining table *without cleaning it*. Reason: "concentrating the search on consecutive cabinet openings ... ignoring higher-prior countertops". The label is the *strategy choice* at turn 1, which only hindsight (the ladle is on the countertop) makes wrong; the uncleaned move at turn 30 is the last decisive error. Counterfactually defensible, not locally detectable.
3. `GPT-4o_007_alfworld_task_007` — clean apple -> sidetable; **turn 3, reflection.outcome_misinterpretation**. From turn 2 the agent emits actions wrapped in quotes (`'go to countertop 1'`); ALFWorld answers "Nothing happens" (17 of 30 turns). The agent alternates quoted (fails) and unquoted (works) forms for 30 turns without noticing, and its reflections read "Nothing happens" as "no apple at the countertop". The reason says "actually action 'go to fridge' was successful" — factually wrong (nothing executed). The first format error is turn 2; the label is the first misreading at turn 3. Root module should be action/format.
4. `GPT-4o_029_alfworld_task_029` — two toiletpaper -> shelf; **turn 21, memory.hallucination**. 13 quoted actions -> 13 "Nothing happens"; still finds toiletpaper 2 and places it on shelf 1 (turn 22); runs out of steps looking for the second. Label = the 10th quoted action (memory contradiction between turns 20 and 21). The budget was lost to format errors beginning at turn 2.
5. `Llama3.3-70B-Turbo_018_045` — two cellphones -> bed; **turn 1, action.(empty)**. Llama writes "I choose the action: 'look'." inside `<action>` (and sometimes outside the tag) -> "Nothing happens" in 17/30 turns; it does pick up cellphone 2 at turn 4. Turn 1 (`go to desk 1`, which reveals the cellphone) is a *correct* action; the first malformed one is turn 2. **Label wrong.**
6. `GPT-4o_015_alfworld_task_015` — pillow on sofa; **turn 1, system.environment_error**, reason "the environment never presented a pillow". The agent's quoted `'go to sofa 1'`/`'go to armchair 1'` never execute; its one unquoted move (turn 18, coffeetable) works. The pillow is on the sofa/armchair it never reached. **Label blames the environment for the agent's format error.**
7. `Qwen3-8B_008_id_8` — newspaper in sofa; **turn 3, reflection.outcome_misinterpretation**. Linear sweep of sidetables 1–5 and drawers 1–14; the sofa (turn 27) holds no newspaper. The reason text ("after opening fridge 1 the agent saw bread and concluded there was no lettuce") refers to objects absent from this run. **Label copied from another trajectory.**
8. `GPT-4o_020_alfworld_task_020` — cool pot -> countertop; **turn 11, reflection.outcome_misinterpretation**. Quoted `'go to fridge 1'` fails 10 times (turns 2–25), unquoted succeeds at 25, pot cooled at 28, then `'move pot 1 to countertop 1'` quoted at 29 and 30 -> cap. Label = one of the ten identical quoted failures.
9. `Llama3.3-70B-Turbo_014_014` — creditcard -> coffeetable; **turn 10, memory.(empty)**. Prose-wrapped actions -> "Nothing happens" in 9 of the first 10 turns; the labelled turn 10 is a valid `examine coffeetable 1`. **Label wrong.**
10. `GPT-4o_021_alfworld_task_021` — newspaper -> sofa; **turn 30, system.step_limit**; reason "nearly finished: had found the newspaper and gone to the sofa but the step limit ran out" — 7 "Nothing happens" turns earlier in the run are the real cost.

**GAIA**
11. `GPT-4o_003_memory_b000_t00_e03` — Tizin translation, 1 agent turn; label step 3 with reason "inefficient plan by redo similar stuffs". The run has one step whose answer "Maktay Zapple Pa" is wrong (the liker is the object: "Maktay mato apple"). **Label belongs to another run.**
12. `GPT-4o_004_memory_b000_t00_e04` — commutativity table, 1 turn; **planning.constraint_ignorance "not including all required elements"**. The agent misreads the table (claims b*a=c, table says b) and answers {a,b,c,e} (gold {b,e}) — it includes *too many* elements. Step trivially right, category and reason wrong.
13. `Qwen3-8B_011_memory_b001_t00_e01` — fish-bag volume; **turn 5, system.tool_execution_error**. 403 on the paper PDF (turn 3), empty mirror (turn 4), then at turn 5 the agent invents "716 kg of fish" and calls the python tool, which answers 404 "model qwen3-8b does not exist" — 16 identical retries, final answer 0.716 m³ (gold 0.1777). The labelled turn is right but the decisive content is the fabricated premise, not the tool error; the tool error is the loud, repeated symptom.
14. `Llama3.3-70B-Turbo_008_memory_b000_t00_e09` — BASE DDC 633; **turn 7, planning.impossible_action** (arxiv search with string "size"). The agent has no browser, 404s on BASE (turn 4), repeats the same Google query 8× from turn 12 and answers "Germany" (gold Guatemala). No step could have succeeded with these tools; the label is one arbitrary bad tool call.
15. `GPT-4o_015_memory_b001_t00_e07` — Murano's first paper; **turn 4, reflection.outcome_misinterpretation**. Turn 4's reflection is accurate (Scholar profile found) and its action gets a 429. The misinterpretation is at turn 13, where the agent reads the publications page and declares a 2005 paper the earliest (gold: 2001). **Label step should be 13 (the answer step).**
16. `GPT-4o_006_memory_b000_t00_e06` — Box Office Mojo top-10 overlap; **turn 3, memory.over_simplification**. Memory at turn 3 summarises the worldwide list; the python tool then fails 8× with the same "set is not JSON serializable"; final answer 3 (gold 6). Plausible label; the conspicuous part of the run is the 8 identical tool errors.

**WebShop**
17. `GPT-4o_001_chat_b000_t00_e00` — **turn 29, planning.inefficient_plan** ("loops back to the very beginning"). Four near-identical searches; clicks `next >` on result pages that list no products 7 times (pages 6–12); never opens a product although a plausible one (Amazon Essentials oxford, B07F2G93BJ) appears on turn 2. The labelled step is the *fourth* repetition of the loop, one turn before the cap.
18. `GPT-4o_012_chat_b000_t00_e11` — **turn 13, planning.constraint_ignorance** ("reformulated as women's fit"). The task itself says "men's shirts ... fit type: women"; the agent copied it. Never opens a product; pages through empty pages twice. Reason contradicts the task text.
19. `Llama3.3-70B-Turbo_009_webshop_task_009` — suits under $20 (no such product); **turn 9, action.parameter_error** (no reason). Malformed tags (`[action>`) at 5 turns leave the page unchanged; the labelled turn is a valid `click[back to search]`.
20. `Qwen3-8B_014_chat_b000_t00_e14` — **turn 4 (last), reflection.progress_misjudge**: selects colour and size, buys without checking "machine wash". Agree. `GPT-4o_004_chat_b000_t00_e03` — **turn 2 of 21**: the reflection says "no relevant results" while page 1 lists two matching Henley shirts; agree, and the evidence is in the immediately preceding observation.

Summary of verdicts: agree 5 (1 trivially), partially agree 4, disagree 9, unusable 2.

## 3. Targeted statistics

### 3.1 The malformed-action signature (ALFWorld and WebShop)

An action is *malformed* when the string inside `<action>` is not in the admissible list but its de-quoted / de-prosed form is (`'go to fridge 1'`, `I choose the action: 'look'.`); *inadmissible* when neither is. ALFWorld answers both with "Nothing happens".

| env | backbone | runs | turns | valid | malformed | inadmissible | obs "Nothing happens" | runs with >=1 malformed | runs with >=50 % "Nothing" turns |
|---|---|---|---|---|---|---|---|---|---|
| alfworld | GPT-4o | 50 | 1500 | 970 | **493 (33 %)** | 37 | 517 | 49 | 12 |
| alfworld | Llama-3.3-70B | 23 | 690 | 359 | 156 | 175 | 317 (46 %) | 22 | 11 |
| alfworld | Qwen3-8B | 27 | 810 | 801 | 0 | 9 | 9 | 0 | 0 |
| webshop | GPT-4o / Llama / Qwen | 15/17/18 | | 421/435/360 | 0 | 5/75/0 (broken tags) | 0 | | |

Half of the ALFWorld budget of GPT-4o and Llama runs is burnt on a surface-form error that the environment flags on the very next line. Where is the human label relative to it?

| relation of the label turn to ... | first malformed action | first inadmissible action | first "Nothing happens" |
|---|---|---|---|
| no such turn in the run | 29 | 59 | 23 |
| label earlier | 14 | 22 | 14 |
| label == that turn | 6 | 5 | 9 |
| **label later** | **51** | 14 | **54** |

In 51 of the 71 runs that contain a malformed action the label is *later* than the first one; only 14/100 ALFWorld labels have module `action`, and 24 of the 25 runs with >=10 malformed actions are labelled planning/memory/reflection/system instead. By module, the labelled turn is itself a "Nothing happens" turn in 33/100 cases and follows one in 25/100 (`stats.md` §2b).

### 3.2 How the agent reads "Nothing happens" (`nothing_reflection.md`)

| backbone | agent turns after "Nothing happens" | reflection mentions format/quotes/admissible | reads it as a semantic outcome ("fridge was empty", "action unsuccessful") | other |
|---|---|---|---|---|
| GPT-4o | 517 | 86 (17 %) | **429 (83 %)** | 2 |
| Llama-3.3-70B | 317 | 155 | 140 | 22 |
| Qwen3-8B | 9 | 5 | 3 | 1 |

The ALFWorld "misinterpretation" labels are therefore mostly *the same event repeated*: a format error producing a null observation that the agent reads as world state. The annotator picks one of the repetitions (median 8.5 "Nothing" turns in reflection-labelled runs).

### 3.3 Repetition before vs after the labelled turn (cap runs, label strictly inside)

| env | runs | repeat-action frac before / after | bigram repeat before / after | novel-observation frac before / after | "Nothing" per turn before / after | median max run of identical actions |
|---|---|---|---|---|---|---|
| alfworld | 86 | 0.10 / **0.38** | 0.02 / **0.18** | 0.83 / 0.54 | 0.25 / 0.30 | 2 |
| webshop | 34 | 0.30 / **0.64** | 0.26 / 0.45 | 0.87 / 0.60 | 0 / 0 | 6 |
| gaia | 15 | 0.01 / **0.58** | 0.00 / 0.36 | 0.91 / 0.31 | 0 / 0 | 2 |

After the label the agent repeats itself 4–50× more often and sees new observations half as often. 34/100 ALFWorld, 36/50 WebShop and 9/50 GAIA runs have a distinct-action fraction below 0.5; 26/50 WebShop runs contain >=5 consecutive identical actions (`click[next >]`). The post-label trajectory is a *loop*, i.e. the label does sit at the loop entry more often than inside it — but see 3.1: the loop entry is usually the first repetition of a symptom (a null observation, an empty page) rather than a new decision.

### 3.4 WebShop: searching without ever looking

| backbone | runs | `next >` clicks on result pages that list **no products** | runs with such clicks | **runs that never open a product page** | median searches / run | median `next` clicks / run |
|---|---|---|---|---|---|---|
| GPT-4o | 15 | 80 | 15 | 10 | 5 | 20 |
| Llama-3.3-70B | 17 | 26 | 4 | 12 | 6 | 12 |
| Qwen3-8B | 18 | 46 | 6 | 7 | 3 | 12 |

29/50 WebShop runs (58 %) never click a product; they alternate `search[...]` and `click[next >]`, including 152 clicks on pages that show only "Page k (Total results: 50)" and no items. The 11 runs that do reach `buy now` are labelled at the buy step or the product-selection step (9/11 in the last 3 turns) — a genuinely decisive, locally checkable step (the required attribute is visible on the product page). The two WebShop regimes have opposite label positions: median label turn 13 for cap runs vs last turn for buy runs.

### 3.5 Termination and label position

| env | runs | ends with answer | ends with buy | hits cap | runs with >=1 error-like tool observation | label at last turn |
|---|---|---|---|---|---|---|
| alfworld | 100 | 0 | 0 | 100 | 0 | 10 |
| webshop | 50 | 0 | 11 | 39 | 0 | 7 |
| gaia | 50 | 48 | 0 | 0 | 24 | 12 |

GAIA: 24/50 runs contain a tool error (403/404/429, "model does not exist", "set is not JSON serializable"); in 9 of them the same failing call is repeated >=5 times. Labels in GAIA are at the answer step in 12/50 (10 of them runs with <=4 turns).

### 3.6 Prefix probe (local detectability)

`python3 -I inspect/prefix_probe.py agenterrorbench --n 20 --max-steps 60 --window 6 --workers 2` (122 probes, 20 records:
9 ALFWorld / 6 WebShop / 5 GAIA; `results/agenterrorbench/prefix_probe.jsonl`). Monitor sees task + prefix only.

| metric | value |
|---|---|
| gold turn flagged as a mistake | 8/20 (40 %) — ALFWorld 2/9, WebShop 3/6, GAIA 3/5 |
| earliest flagged turn == gold | 5/20 (25 %) |
| argmax-confidence turn == gold | 3/20 (15 %) |
| flag rate on agent turns before gold | 4/50 (8 %) |
| flag rate on agent turns after gold | 29/52 (56 %) |

- The 12 unflagged golds are judged *reasonable* with confidence 0.72–1.0: "taking the cup from the countertop is a valid
  necessary step" (`GPT-4o_010`, gold turn 4), "going to the dresser is a valid admissible action" (`GPT-4o_039`), "clicking
  next page is a reasonable way to continue browsing" (`GPT-4o_009_webshop`, `Llama_011/014_webshop`), "a logical
  continuation of the systematic search" (`Qwen3-8B_007`, gold = turn 30, the cap). These are exactly the exploration-order
  / hindsight labels of H4 and the step-limit labels of H3: nothing in the prefix marks them.
- The 8 flagged golds are the locally contradictory ones: returning to a desk already seen empty (`GPT-4o_047/049`),
  repeating the same failed search (`Llama_018_webshop`), computing a check digit for an ID never found (`Llama_002_gaia`),
  answering before the search returns (`Qwen_006_gaia`), ignoring a confirmed matching product (`Llama_017_webshop`).
- After the gold the flag rate jumps 8 % → 56 %: the monitor sees the loop/stagnation phase (H2) as a run of mistakes, so
  "earliest flag" lands before the label in only 1 run but "argmax" lands after it in most — the SOAP contamination pattern
  with the label at the *entry* of the symptom phase rather than at a cause.

### 3.7 No-LLM first-symptom heuristics vs the human label (`inspect/agenterrorbench_heuristics.py`, `results/agenterrorbench/heuristics.md`, turn units)

| env | turn 1 | last turn | first malformed/inadmissible | first "Nothing happens" | first repeated action | first repeated observation | first tool error | **first anomaly (min of symptom turns)** |
|---|---|---|---|---|---|---|---|---|
| alfworld (100) exact / ±3 | 4 / 36 % | 10 / 10 % | 9 / 34 % | 9 / 35 % | 13 / 53 % | 11 / 49 % | – | **17 / 47 %** |
| webshop (50) | 10 / 42 % | 14 / 18 % | – | – | 6 / 50 % | 12 / 54 % | – | **14 / 52 %** |
| gaia (49) | 18 / 76 % | 24 / 43 % | – | – | 4 / 33 % | 12 / 59 % | 12 / 31 % | **20 / 61 %** |

A regex "first anomaly" detector (no LLM) reaches 17 / 14 / 20 % exact — the same range as TrajDebug's re-evaluation of direct LLM prompting on these runs (9–19 / 14–32 / 20–35 %) and close to our own 24 / 29 / 33 % baseline (§4). Labels sit *near* the first mechanical anomaly (±3 turns in ~50 %) but rarely *at* it.

## 4. Baseline error analysis (all-at-once, Qwen3.8-27B, n=60)

`python3 -I baseline/all_at_once.py agenterrorbench --n 60 --workers 2` (seed 0, cache shared with the background runner, which has since written `DONE`), then `inspect/analyze_baseline.py agenterrorbench` and `inspect/agenterrorbench_baseline_vs_symptoms.py` (`results/agenterrorbench/baseline_vs_symptoms.md`).

| subset | n | agent_ok | step exact | within ±3 msgs | pred earlier (turns) | pred later | within ±1 turn |
|---|---|---|---|---|---|---|---|
| alfworld | 25 | 100 | 24.0 | 52.0 | 11 | 8 | 13 |
| webshop | 17 | 100 | 29.4 | 35.3 | **12** | 0 | 6 |
| gaia | 18 | 100 | 33.3 | 50.0 | 4 | 8 | 9 |
| ALL | 60 | 100 | **28.3** | 46.7 | 27 | 16 | 28 |

28.3 % exact reproduces the paper's direct-prompting figure (28 %). Categories: exact 17, earlier(<−3 msgs) 20, earlier(−1..3) 7, later(+1..3) 4, later(>3) 12. **Misses are mostly *earlier* than the label (27/43)** — the opposite of the late bias of P1 — and the direction is env-specific: WebShop 12/12 misses earlier (median signed offset −4 turns), GAIA 8/12 later, ALFWorld split 11/8. Only 4/43 misses land exactly on the first malformed / "Nothing happens" turn, so the judge is early for a different reason than the regex heuristic: it blames the first *decision* it considers suboptimal.

Why earlier (reasoning excerpts):
- WebShop: the judge blames the *first search query* (turn 1) in 7/17 runs: "The initial search query was overly verbose and over-constrained, including price text and multiple material phrases that the WebShop search likely handled poorly" (`Llama_011_webshop`, gold turn 4; `GPT-4o_011_webshop`, gold turn 21). Annotators label a later re-search ("queries too similar to previous ones"). Both are defensible; the judge applies "earliest" literally, the annotators label the point where the agent *should have learned* (H2).
- ALFWorld: the judge finds the quote format error and names it: "The agent included single quotes around the action string, so the environment did not parse it; this first happened on the first task-relevant attempt to move to drawer 1" (`GPT-4o_039`, pred turn 3, gold turn 4 memory.over_simplification); "failed to recognize that the 'go to sidetable 1' action in the previous step was malformed ... which caused a cascade of failed 'move' attempts" (`GPT-4o_010`, pred 5, gold 4). In `GPT-4o_021` (gold turn 30, step_limit) it predicts turn 3 = the first quoted action. The judge sees the mechanical cause the annotators skip (H1) and is scored wrong for it.
- The judge reasons explicitly about *what the benchmark expects* rather than about the run: "Which is more likely expected? Let's think about root cause definitions in these debugging tasks" (`GPT-4o_009`), "Let's weigh expected answer. The user likely…" (`GPT-4o_039`), "They may expect…" (`GPT-4o_047`). Step choice is partly label-convention guessing.

Why later (GAIA): the judge picks the fabrication / answer step: "The agent had not found the actual Tropicos ID and instead began assuming a fabricated ID, 100001055 ... All later calculations and the final answer inherit this unsupported premise" (`Llama_002_gaia`, pred turn 14, gold turn 10 "low efficient plan"); "prematurely provided the final answer based on its prior knowledge without using url_text_extractor" (`Qwen_007_gaia`, pred 3, gold 2). In both the judge's step is the decisive one under the counterfactual definition and the gold is a vague earlier "inefficient plan" carrying the 7×-duplicated template reason. I side with the judge.

Step-limit runs: `Qwen3-8B_007` (gold 30) → pred 26 "left drawer 12 unopened, breaking its systematic search"; the judge manufactures a decisive step where none exists (H3), its thinking conceding "the agent's exhaustive search is the only way".

Successes (4 read): `GPT-4o_047` / `_049` (memory.over_simplification): the judge never reasons about memory; it finds "returned to the already-explored desk 1 instead of searching unexplored receptacles" — the same turn via a different route (the first *revisit* of an exhausted location, a locally checkable event). `GPT-4o_019` (action.misalignment: took the ladle without cleaning it) and `Qwen_006_gaia` (one-step hallucinated answer) are locally evident. Pattern: the baseline succeeds when the labelled turn is a *revisit*, a *commit without check* or the *only* step; it fails when the label is a strategy choice (H4: `Qwen3-8B_006` turn 1 → pred 29, `_014` 11 → 30, `GPT-4o_022` 9 → 23), the n-th repetition (H2), a `<memory>`-block defect (the judge never treats the memory summary as the object of judgement) or a placeholder (H3). Length: exact 60 % on ≤10-step runs vs 24.5 % on >30-step runs. No record hit the token budget; 1 fallback without thinking (`GPT-4o_010`).

## 5. Annotation issues (prevalence)

| issue | evidence | estimated prevalence |
|---|---|---|
| Label copied from / written for another trajectory | `alfworld/Qwen3-8B_008` (reason about fridge/bread/lettuce in a newspaper task); `gaia/GPT-4o_003` (step 3 in a 1-turn run) | 2/200 certain (1/74 ALFWorld reasons mention objects absent from the run) |
| Labelled turn is a *correct* action | `Llama_018_045` turn 1 (`go to desk 1` reveals the target), `Llama_014_014` turn 10, `Llama_009_webshop` turn 9 | all 23 Llama-ALFWorld labels have no type and no reason; ≥3/23 read as wrong |
| Format error attributed to cognition or environment | 51/71 ALFWorld runs with malformed actions are labelled after the first one; 24/25 runs with >=10 malformed actions are not labelled `action`; `GPT-4o_015` blames the environment | ~50 % of ALFWorld labels |
| "No decisive step" runs labelled at the last turn | 8 Qwen `step_limit` runs with 0 invalid actions and 100 % novel moves; `GPT-4o_021` "nearly finished" | 10/100 ALFWorld, plus ~5 GAIA runs where the task is infeasible with the tools (`Llama_008`) |
| Reason text contradicts the run | `GPT-4o_007` ("go to fridge was successful"), `GPT-4o_012_webshop` ("diverged to women's fit" — the task says women's fit), `GPT-4o_004_gaia` ("not including all required elements" — it included too many) | ≥3/157 reasons |
| Label step at the symptom's n-th repetition rather than its first | `GPT-4o_020` (10th quoted action), `GPT-4o_001_webshop` (4th identical re-search, turn 29 of 30), `GPT-4o_029` | see 3.1: label later than first malformed in 51/71 runs |
| Template / duplicated reasons | "Inefficient plan by redo similar stuffs" ×7, "The new search query is very similar..." ×3, `Qwen3-8B_018`/`_022` identical | 19/157 reasons are reused verbatim |
| Taxonomy spelling | `plan`/`planning`, `plan_inefficient`/`inefficient_plan`, `Parameter_error`, trailing-space type; 27 empty types; 43 missing reasons | 27 + 43 records |

The paper's κ = 0.55 understates the problem for ALFWorld: the labels are *consistent* in choosing a cognitive module, and consistently ignore the mechanical cause that the environment reports.

## 6. Candidate hypotheses

**H1. Null-observation blindness ("Nothing happens" is read as world state).** In ALFWorld 33 % of GPT-4o turns and 48 % of Llama turns are surface-form errors (quoted or prose-wrapped actions) that the environment answers with "Nothing happens"; the agent's reflection reads this null observation as a semantic fact ("the fridge was empty", "the action was unsuccessful") in 83 % of GPT-4o cases and never corrects the form. The failure is therefore one mechanical error *repeated 10–20 times*, each repetition being a locally detectable symptom. Evidence: §3.1–3.2. Test: re-run the 73 GPT-4o/Llama ALFWorld runs with a one-line action sanitiser (strip quotes/prose) and count successes — if >30 % succeed, the sanitiser step is the counterfactual root cause for those runs and no cognitive label is needed. Shared with: TrajErrBench ACT.ToolSchemaMismatch, TRAIL formatting errors, Who&When WebSurfer format loops. A targeted method should (i) detect the environment's null response pattern directly from observations (`stats_per_run` does it with a regex), (ii) credit the *first* occurrence, not the one the annotator picked, and (iii) report the mechanical cause separately from the cognitive module.

**H2. Labels point at the n-th repetition of a symptom, not its first occurrence (late-label bias inside a loop).** The human label is later than the first malformed action in 51/71 ALFWorld runs that contain one, later than the first "Nothing happens" in 54/77, and in WebShop the labelled re-search is the 2nd–4th identical query (e.g. `GPT-4o_001` turn 29/30). After the label the action-repeat fraction rises from 0.10 to 0.38 (ALFWorld), 0.30 to 0.64 (WebShop), 0.01 to 0.58 (GAIA), so the label marks the *entry* into a stagnation phase, but the stagnation is itself a repetition of earlier null steps. Test: for every run compute the first turn whose (action, observation) pair recurs later; the human label should fall after it in >60 % of runs; then ask annotators to re-label with the first occurrence highlighted. Shared with: FaP t_err vs t_lock gap, Who&When HC (AgentErrata App. C), TrajErrBench VERIFY.InfiniteRetry. Method: a loop-aware scorer that collapses identical (action, observation) repeats and attributes to the first element of the equivalence class, then re-scores with the position prior of the collapsed trajectory.

**H3. "No decisive step" runs exist and are labelled at the last turn.** 8 Qwen3-8B ALFWorld runs explore 30 distinct locations with 0 invalid actions and simply run out of budget; 2 GPT-4o runs "nearly finish"; ~5 GAIA runs are infeasible with the given tools (no browser: `Llama_008`, 403s on every source: `Qwen_011`). The dataset encodes these as `system.step_limit` at turn 30 or as an arbitrary bad tool call. For an attributor this is a *refusal* class: the correct output is "no single step; cause = budget/tooling". Test: pass^k re-runs of the same task with the same agent and 60 steps — if the task succeeds with more budget, the run had no decisive step. Shared with: FaP capability-limitation triggers (8.8 %), TrajErrBench 17 null types, AgentHallu clean runs with errors. Method: predict a "no decisive step" flag from (distinct-action fraction ≈ 1, 0 null observations, unexplored receptacles remain) before attempting step attribution.

**H4. Exploration-order labels are hindsight labels.** `Qwen3-8B_006` (turn 1), `_010` (turn 13), `_021` (turn 5), `_023` (turn 4), `_026` (turn 1): the label is the point where the agent chose a search order that, *given where the object actually was*, is wasteful. The annotator knows the object location (from later observations); a prefix monitor cannot. Prefix probe (§3.6): exploration-order gold turns were flagged 0/4, revisit/commit gold turns 6/8; the all-at-once judge misses every exploration-order label it saw (`Qwen3-8B_006` turn 1 → pred 29, `_014` turn 11 → 30, `GPT-4o_022` 9 → 23). Shared with: Who&When "earliest step whose correction would succeed" (same counterfactual definition produces the same hindsight), FaP false-premise triggers. Method: separate "locally wrong" (contradicts visible evidence) from "globally suboptimal" (only wrong given the hidden state), and evaluate attributors on the first class only, or give the attributor the environment's hidden state (object location) as the oracle the annotators effectively had.

**H5. WebShop failures bifurcate into "never looked" and "looked and misjudged", with opposite label positions.** 29/50 runs never open a product (median label turn 13, symptom = search/next loop with 152 clicks on empty pages); 11/50 buy a product and are labelled at the buy/selection turn (9/11 in the last 3 turns) where the missing attribute is visible on the product page. Test: a two-feature classifier (any product opened? run length) predicts label-in-last-3-turns with high accuracy; then evaluate attributors separately on the two regimes — expected: near-ceiling on the buy regime (local evidence), near-prior on the loop regime. Shared with: AgentHallu Tool-Use vs Reasoning split, τ²-bench policy-violation vs reasoning split in TrajErrBench. Method: regime detection first, then (buy regime) check the committed item against the task constraints; (loop regime) H2's loop collapse.

**H6. Repeated identical tool errors are the loudest GAIA symptom and crowd out the real cause.** 24/50 GAIA runs contain tool errors; 9 repeat the same failing call >=5 times (max 16). The labelled step is the first such call in only 3 runs (`system.tool_execution_error`); elsewhere the cause is a fabricated premise (`Qwen_011`: "716 kg") or a misread page at the answer step (`GPT-4o_015`). §4: the judge instead lands on the fabrication / answer step (8/12 GAIA misses are *later* than the label), i.e. it discounts tool errors and blames the step that commits to unverified content — arguably the right convention, which the template labels ("inefficient plan by redo similar stuffs" ×7) do not follow. Shared with: TrajErrBench OBS.IgnoreOutput, TRAIL tool errors, SearchAuditBench retrieval failures. Method: treat error-identical retries as one event and ask whether the information needed for the answer was ever obtained; if not, the cause is the step where the agent stopped trying alternatives (or the final answer step with fabricated content), not the error.

## 6b. Literature phenomena (P1–P8) on this dataset

- **P1 (downstream contamination / late localisation): half confirmed.** The prefix monitor flags 56 % of steps after the label vs 8 % before (7×), so symptoms do dominate the post-label region. But the *all-at-once* judge is **early**, not late (27 earlier vs 16 later of 43 misses; WebShop 12/0), because it takes "earliest" literally and because the first mechanical anomaly (format error, first query) precedes the human label (§3.1). Late bias is a property of per-step scorers, not of a whole-trajectory judge on this data.
- **P2 (label convention):** confirmed and quantifiable: "first mechanical anomaly" vs "first cognitive misjudgement" differ by a median of several turns (label later than first malformed action in 51/71 runs); "no decisive step" runs (10 %) get a last-turn placeholder.
- **P3 (anchoring on outcome):** exploration-order labels (H4) are pure hindsight; the κ = 0.55 reported is consistent with the duplicated template reasons and 27 missing types.
- **P4:** not testable (no successes); but 48/50 GAIA runs end with a confident `<answer>` and 12 labels sit on it.
- **P5 (length):** baseline exact 60 % on ≤10-step runs vs 24.5 % on >30-step runs; the ALFWorld/WebShop cap runs are the hard ones, and length here means *loop length*.
- **P6:** untestable (no successes) — but Qwen3-8B's ALFWorld runs show that the "normal flow" (clean systematic search) can fail with no deviation at all (H3), a counter-example to the premise.
- **P7 (absorption):** GPT-4o ALFWorld runs absorb 33 % malformed actions and still sometimes achieve sub-goals (`GPT-4o_029` places the first roll); format errors are absorbed *per step* but fatal *in aggregate* through the step budget — a cost model (steps wasted) rather than a cascade model fits.
- **P8 (verification theatre / false success):** present in the buy regime (11 WebShop runs buy an item that violates a visible constraint; 9/11 labelled there) and in GAIA answer steps with fabricated premises (`Qwen_011`, `Llama_002`).

## 7. Open questions

- Did the AgentDebug authors' action parser strip quotes at run time (so that "Nothing happens" came from the environment for other reasons)? The env message echoes `Action 2: ''go to countertop 1''`, i.e. the quotes reached the environment; but the paper should be checked for a post-processing step.
- The paper reports multi-step annotation (minimal root-cause *set*); the release has one step per run. Were the 23 Llama ALFWorld labels (no type, no reason, several at correct actions) produced by a different annotator batch?
- `Qwen3-8B_012` reason says the task *was* fulfilled at turn 7 ("cooling the mug and placing it in the sidetable") but the run continued — is that an environment-success-check failure (an outcome-label error, i.e. the run is not a failure)?
- Would annotators given the de-duplicated (loop-collapsed) trajectory choose earlier steps? This is the cheapest test of H2 and of P3 (annotators anchoring on what is conspicuous).
- For the 29 "never looked" WebShop runs, what is the counterfactual? Many tasks look unsatisfiable (suits under $20); the dataset may contain task-level impossibility that no step label can express.
