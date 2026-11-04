# AgentHallu — inspection notes (G3 single-agent natural failures)

Scripts: `inspect/agenthallu_stats.py` (targeted statistics, output `results/agenthallu/stats.md`), `inspect/agenthallu_detect.py`
(ground-truth-free hallucination detection probe, `results/agenthallu/detect.jsonl`), `inspect/agenthallu_prefix.py` (copy of the
shared prefix probe with a fix for list-valued tasks, `results/agenthallu/prefix_probe_g3.jsonl`), `inspect/g3_dump.py` (readable dumps
in `inspect/g3_dumps/agenthallu__*.txt`). Baseline: `results/agenthallu/all_at_once_std.jsonl` + `_analysis.md`.

## 1. Data as loaded

- 693 records (443 hallucinated = `outcome fail`, 250 clean = `success`), 5,269 steps, 7 frameworks: BFCL function-calling 164
  (103/61 fail/clean), OpenManus 104 (84/20), Magentic-One 94 (54/40), OWL (`Camel`) 93 (57/36), SmolAgents 72 (57/34),
  OpenDeepSearch 64 (58/42... 42 clean), OctoTools 47 (30/17). Domains: Science 147, World Knowledge 184, Tool Use 164, Math 127,
  General Assistant 71.
- Categories (hallucinated): Reasoning 118, Tool-Use 103, Retrieval 82, Human-Interaction 73, Planning 67. Sub-categories as in the paper.
- **Every step has role `agent`** (the loader maps `history[].role`, which is an agent *name*, to `agent`): there are no user, tool or
  system steps. Tool calls and tool responses are rendered inside the agent step (`Tool calls: ...` / `Tool responses: ...`), and the
  simulated human's replies are *tool responses* of an `ask_human` / `ask_human_via_console` call. Consequently the
  "Human-Interaction" cases do **not** blame a user turn in the loaded data: they blame the agent step that issued the `ask_human` call
  (see §3 T4).
- **Loader quirk (shared, not fixed by me):** BFCL `question` is a JSON *list* of user turns, and the loader stores it as a list in
  `rec['task']`. `common/render.render_task` calls `.strip()` on it, so the shared `inspect/prefix_probe.py` and `baseline/all_at_once.py`
  crash on any BFCL record (`AttributeError: 'list' object has no attribute 'strip'`). I made a copy `inspect/agenthallu_prefix.py` that
  stringifies the task. The background baseline runner will hit the same crash if its sample contains a BFCL record (it does: BFCL is
  24% of the labelled records), so see §4 for how the baseline was run.
- BFCL multi-turn structure is invisible in the step list: user turns are only in `task` (a list of 2–5 instructions), the assistant's
  text replies (steps without a tool call) mark the end of a turn. `ground_truth` is the gold per-turn function-call list, `final_output`
  the list of per-turn assistant replies. `is_hallucination` for BFCL is a *state-check* failure, not an answer mismatch.
- `final_output` (`agent_answer`) is broken for 33 OpenManus runs (27/84 hallucinated, 6/20 clean): it is the last tool output
  (`Observed output of cmd terminate ... status: success`) instead of an answer (e.g. `OpenManus/051` clean, GT 120,000, the answer is
  only inside step 4's extracted page text). Any detector that reads `final_output` is blind on these.
- 112/443 gold steps are step 0; 22 are the last step; mean 7.5 steps, 8 runs > 20 steps (max 43).
- 9 Science (GPQA) tasks say "choose the correct option" / "which of the following" but the options were stripped from the prompt
  (6 hallucinated, 3 clean): `Magentic_One/010`, `OpenDeepSearch/089`, `OpenManus/082`, `OpenManus/089`, `OpenManus/090`,
  `SmolAgents/026` (fail); `Magentic_One/072`, `Magentic_One/077`, `OpenManus/001` (clean). Only 15/147 Science prompts contain options at all,
  so GPQA is posed open-ended and the "hallucination" verdict compares a free answer with the correct option text.

## 2. Close-reading notes (23 trajectories)

Convention: `[k]` = 0-based `idx` as loaded; the dataset's `hallucination_step` is `k+1`.

**Tool-Use (BFCL, all `assistant`, every step a tool call or a reply)**
- `BFCL/002` (22 steps, gold [5], Incorrect Tool Arguments). Turn 2 asks to "jot down 'X'"; the agent `echo`es a header + purpose text
  + X. No symptom ever appears: tool responses are `None`, the reply claims success, the later `diff` (step 8) even shows the extra
  lines and the agent describes them as a feature. **Agree** with the label; it is locally detectable from task + call alone. After the
  gold step the agent hits two `cp` path errors (steps 11, 13) and recovers (16–18) — recovered errors *after* the gold step that an
  error-driven scorer would pick.
- `BFCL/004` (10 steps, gold [0], Missing Required Call). `touch` without `cd communal`; the agent's own reply at [1] says "(assumed to
  be the communal folder)" — a verbalised assumption is the only signal. A *second* independent error at [8] (no `cd shared`) also fails the
  last turn; earliest wins. **Agree.**
- `BFCL/030` (12 steps, gold [11] = final reply, Missing Required Call). Turn 1 fails visibly at [1] (`rm` with a path → error, `rmdir`
  not empty) and the agent *honestly reports* it; in turn 2 ("what's left, incl. hidden?") it runs `ls -a` three times, then quietly
  finishes turn 1's deletions and answers "actions completed" without listing anything. The label is the last step, not the first error at
  [1], because the [1] error was recovered (in the next turn). **Disagree mildly**: the recovery in turn 2 is itself the deviation; the
  earliest-error convention (TrajErrBench/Who&When) would give [1].
- `BFCL/000` (13 steps, gold [0], Unnecessary Tool Call). `mkdir temp` in the wrong directory + `mv` with a misspelt argument
  (`sofdeurce`); the agent then `cd`s and redoes everything correctly. It *looks* fully recovered, but the stray `temp` directory
  pollutes the state check. **Agree**, but this is unrecoverable only because of a silent side effect — no trajectory-only reader can
  tell recovered from unrecovered here.
- `BFCL/015` (6 steps, gold [4], Parallel Call Conflict). `diff` and `echo` in one parallel call, the echo writes the placeholder string
  `diff_lines: file1.txt file2.txt`. Locally obvious; no later symptom. **Agree.**
- `BFCL/001` (clean, 9 steps). `mkdir archive` fails ("File exists") at [2] and is simply absorbed; at [6] the agent quotes only part of
  the grep line. A clean run with a tool error and a minor misquote.

**Human-Interaction (OWL `Camel` and OpenManus)**
- `Camel/029` (7 steps, gold [4]). Three sources say 1938; the agent asks the human "can I finalise 1938?", the simulated human says "I
  think it should be early 1939"; the agent notes the contradiction (step 5) and answers 1939. Gold is the `ask_human` step (the human's
  reply is its tool response); the reason text blames the *adoption* at step 5/6. The agent **could have known**.
- `Camel/046` (8 steps, gold [2]). The human instructs "use PubChem CID 4369359 as the ChemSpider ID"; the agent's own Google result at
  [3] shows the ChemSpider URL `Chemical-Structure.3571948` (= GT) and it still obeys the human. Could have known.
- `Camel/034` (21 steps, gold [14]). Nine steps of failed YouTube browsing (timeouts, failed clicks, broken screenshots), then the
  agent asks the human for the CFM numbers and gets fabricated ones (103.43 / 99.9). Could **not** have known; the label's rationale
  blames the agent for "wrongly assuming the info could not be obtained".
- `OpenManus/094` (4 steps, gold [0]). Step 0 is already `ask_human` ("should mirror images be identical?") and the human injects a wrong
  convention (divide by 2). 27 OpenManus HI runs have the gold at step 0 for this reason.
- Clean runs with `ask_human`: `Camel/040` the human claims Monica Bonvicini won the 2018 Kokoschka prize (GT Martha Jungwirth) and the
  agent explicitly overrides it after searching; `Camel/036` the human says "attribute it to Casliber" (GT FunkMonk), overridden;
  `Camel/035` the human guesses "wrong" (GT "Right"), overridden. **The simulated human lies in clean runs too**; whether the run is
  labelled HI depends on whether the agent resisted. In 8/31 Camel HI runs and 7/36 clean Camel runs the Planner's step-0 task text
  itself instructs "Before proceeding ... call `ask_human_via_console`", i.e. the human consultation was injected by the task prompt.

**Planning (gold = step 0 in 64/67)**
- `Magentic_One/010` (8 steps, gold [0], Fact Derive). The orchestrator's fact sheet guesses "W and Y are likely unitary". But the task
  is a GPQA question whose answer options were stripped ("choose the correct option" with no options), so the system *could not* produce
  "Y lies inside the Bloch sphere"; the code at [4] is correct. **Label is wrong / task defective.**
- `Magentic_One/061` (43 steps, gold [0], Fact Derive). The fact sheet reads "the 2019 game that won" as "a game released in 2019" and
  42 steps then count revisions for the wrong game, coherently and without any symptom. **Agree**; a prefix monitor needs task
  comprehension, not anomaly detection, to catch it.
- `Camel/016` (9 steps, gold [0], Task Decompose). The Planner splits "affiliations of A and B" into two sub-tasks; the Search Agent
  finds both affiliations in one PDF (step 2 contains the full answer) and reports each separately; OWL returns the *last* sub-task's
  result as the final answer. The failure is a framework aggregation bug; blaming the decomposition is the counterfactual choice. Agree.

**Retrieval**
- `OpenDeepSearch/004` (9 steps, gold [4], Summarize Misalign). ODS's `web_search` returns LLM-written summaries; the summary at [4]
  states "1.4" (wrong), earlier summaries at [2]/[3] said 1.2.4.1. The agent never misquotes anything — **the tool hallucinated** and the
  label sits on the step whose *observation* is wrong. The only prefix-visible signal is the 1.2.4.1-vs-1.4 inconsistency across
  summaries.
- `Magentic_One/008` (6 steps, gold [2], Context Misalign). The orchestrator's own fact sheet at [0] guesses the right answer
  (Indonesia, Myanmar); WebSurfer's Bing search at [2] shows a Jakarta–Bangkok snippet; the orchestrator at [3] asserts "Wikipedia
  indicated Jakarta/Bangkok" and the Coder formats it. Gold = the fetch step [2]; the misreading is at [3]. Fetch-vs-adopt ambiguity.
- `Octotools/026` (6 steps, gold [4], Query Misalign). The RIAA page extracted at [4] lists both the Gold (2018) and Platinum (2020)
  certifications; the agent reads the Platinum date at [5]. Again the fetch step is blamed, the misreading step is next.
- `Camel/049` (13 steps, gold [4], Context Misalign). Sources conflict (English Wikipedia "Gualba" = GT vs SITUR Boyacá + Spanish
  Wikipedia "Grijalba"); the agent documents the conflict and chooses the official government source. **This is a GT ambiguity, not a
  hallucination.**

**Reasoning**
- `Camel/006` (3 steps, gold [2]). The Developer Agent's Cassie–Baxter computation gives 144.91° / 125.48°; GT "144°, 125°". The
  oil value is right, the water value is off by 0.5° (arccos slip). Labelled hallucinated. A judge comparing with the GT would call it
  correct; **near-miss label**.
- `Camel/000` (14 steps, gold [7]). Plan note at [7] assumes every S(ρ) is the image of one character; computation at [8]–[9] follows; final 6
  vs GT 8. Gold is the plan note that *states* the false assumption, the computation that *uses* it is [8]: ±1 ambiguity by construction.
  Tool errors at [4]–[5] (`read_note` of unregistered notes) are noise before the gold.
- `Magentic_One/054` (39 steps, gold [25]). Twelve WebSurfer steps with a cookie banner, a failed year filter (`ValueError`, step 6), a
  scroll loop (8–12), the dropdown finally showing "2012 (4)" at [18], then a Playwright crash at [20]; the orchestrator hands over to
  the Coder who fabricates "a 2012 article on metallic nanotip arrays → silver" at [25]. Gold = the fabrication, which is the *symptom*
  of abandoning the browser at [21]. Loud symptoms (errors, loop) precede the gold by 5–19 steps.
- `Magentic_One/093` (18 steps, gold [17] = final). The Coder computes a+b+c = 62 at [16]; the orchestrator's final message says 50.
  Pure last-step fabrication; the reason text says "Step 3" (typo).
- `BFCL/110` (8 steps, gold [6]): `get_user_id` and `send_message` in parallel with a placeholder id; the reason text says "step 1"
  (turn-relative). Label index right, rationale numbering wrong.

**Clean runs**: `OpenManus/051` (answer €120,000 found at step 4, `agent_answer` field broken), `Camel/010` (long multi-note
computation, final $8.00 = GT 8), `SmolAgents/071` (−11.42 kJ = −2.73 kcal ≈ GT −2.72 kcal), `BFCL/001`, `Camel/035/036/040`
(adversarial human overridden).

## 3. Targeted statistics (`results/agenthallu/stats.md`)

**T1. The kind of step that gets blamed is almost determined by the category.**

| category | n | gold has tool call | tool error in its response | gold is `ask_human` | is last step | is step 0 | is final-answer step |
|---|---|---|---|---|---|---|---|
| Human-Interaction | 73 | 100% | 0% | **100%** | 0% | 37% | 0% |
| Planning | 67 | 0% | 0% | 3% | 0% | **96%** | 3% |
| Reasoning | 118 | 67% | 8% | 0% | 16% | 10% | 14% |
| Retrieval | 82 | 100% | 11% | 0% | 0% | 0% | 0% |
| Tool-Use | 103 | 91% | 35% | 0% | 3% | 9% | 0% |

**T1b. Position-only rules reproduce the gold step (exact %):**

| category | n | step 0 | first `ask_human` | first search call | first call | middle (n//2) | last call | last−1 | last | best rule |
|---|---|---|---|---|---|---|---|---|---|---|
| Human-Interaction | 73 | 37 | **89** | 36 | 77 | 16 | 8 | 18 | 0 | first ask_human 89% |
| Planning | 67 | **96** | 96 | 43 | 6 | 0 | 0 | 0 | 0 | step 0 96% |
| Reasoning | 118 | 10 | 10 | 11 | 31 | 27 | 28 | **38** | 16 | last−1 38% |
| Retrieval | 82 | 0 | 0 | 27 | 28 | **56** | 9 | 51 | 0 | middle 56% |
| Tool-Use | 103 | 9 | 9 | 10 | 9 | 15 | **26** | 26 | 3 | last call 26% |
| ALL | 443 | 25 | 34 | 23 | 29 | 24 | 16 | 29 | 5 | first ask_human 34% |

With the oracle category, the best single positional rule per category scores **55.8% exact (247/443)** — above the best published
LLM attributor (Gemini-2.5-Pro 41.1%, GPT-5 32.7%, incremental GPT-5 42.7%). Without the category, "first `ask_human` if any else step 0"
gives 34%, i.e. the paper's GPT-5 level. The labelled step is largely a *category convention* (plan → step 0; human → the ask step;
retrieval → the fetch step; reasoning → the last computation / penultimate step).

**T2. Tool errors (regex on tool responses) do not separate hallucinated from clean runs.**

| class | framework | n | runs with ≥1 tool-error step | tool-error steps / all steps | error before / at / after gold |
|---|---|---|---|---|---|
| hallucinated | BFCL | 103 | 68% | 10.4% | 30% / 35% / 17% |
| clean | BFCL | 61 | 46% | 7.8% | – |
| hallucinated | Camel (OWL) | 57 | 53% | 11.9% | 25% / 4% / 32% |
| clean | Camel | 36 | 50% | 13.3% | – |
| hallucinated | SmolAgents | 57 | 46% | 14.2% | 16% / 9% / 26% |
| clean | SmolAgents | 34 | 53% | 12.7% | – |
| hallucinated | Octotools | 30 | 43% | 16.6% | 23% / 17% / 17% |
| clean | Octotools | 17 | 24% | 8.1% | – |
| hallucinated | OpenDeepSearch | 58 | 33% | 9.0% | 21% / 9% / 14% |
| clean | OpenDeepSearch | 42 | 7% | 1.6% | – |
| hallucinated | OpenManus | 84 | 20% | 7.3% | 15% / 0% / 6% |
| clean | OpenManus | 20 | 30% | 6.9% | – |
| hallucinated | Magentic-One | 54 | 7% | 1.8% | 4% / 2% / 4% |
| clean | Magentic-One | 40 | 18% | 2.7% | – |

84/250 clean runs (33.6%) contain at least one tool-error step (recovered-error proxy) vs 179/443 (40.4%) hallucinated. Only
in BFCL Missing-Required-Call (56%) and Parallel-Call-Conflict (50%) is the gold step itself a visibly failing call; for
Human-Interaction, Planning and most Retrieval/Reasoning the gold step has no error marker at all.

**T3. Was the correct answer visible in the trajectory? (exact normalised GT string ≤ 40 chars, non-BFCL, 245 evaluable hallucinated runs)**

| category | n | GT visible before gold | at gold | after gold | never |
|---|---|---|---|---|---|
| Human-Interaction | 55 | 3 (5%) | 4 (7%) | 2 (4%) | 46 (84%) |
| Planning | 48 | 0 | 2 (4%) | 8 (17%) | 38 (79%) |
| Reasoning | 75 | 2 (3%) | 1 (1%) | 2 (3%) | 70 (93%) |
| Retrieval | 67 | 10 (15%) | 3 (4%) | 3 (4%) | 51 (76%) |
| ALL | 245 | 15 (6%) | 10 (4%) | 15 (6%) | 205 (84%) |

Clean runs under the same filter: GT visible in 101/143. "Visible evidence ignored" (TrajErrBench's dominant mode) is rare here: in 84% of
hallucinated runs the correct answer never enters the context, so the failure is *absence of the right evidence*, not neglect of it. The
exceptions are Retrieval (15% before gold: `Magentic_One/008`, `OpenDeepSearch/007/013/069`, ...) and HI (`Camel/029`, `Camel/037`).

**T4. `ask_human` steps and the Human-Interaction label.**

| class | n | runs with `ask_human` | `ask_human` per such run | gold is an `ask_human` step | gold is the FIRST `ask_human` |
|---|---|---|---|---|---|
| HI (hallucinated) | 73 | 73 | 1.33 | **73** | 65 |
| other hallucinated | 370 | 10 | 1.30 | 2 | 2 |
| clean | 250 | 23 | 1.35 | – | – |

Among runs with `ask_human`, the ask is the *first* tool call in 25/31 Camel-HI, 31/42 OpenManus-HI, 13/18 Camel-clean, 4/5
OpenManus-clean: the agent consults the human before gathering any evidence. The human's reply contains the GT string in 8/97 HI replies and
2/31 clean replies; in 25/73 HI runs a number from the human reply is copied into the final answer. Reading the clean cases shows the
same adversarial human (wrong names, wrong guesses), overridden by the agent. So HI ≈ **an injection experiment**: 106 runs received a
(mostly wrong) human message; 73 propagated (labelled HI), 23 were absorbed (clean), 10 failed for another reason.

**T5. BFCL turn structure.** The gold step is a tool call in 97% of Incorrect-Argument, 100% of Parallel-Conflict and Unnecessary-Call, but
only 75% of Missing-Required-Call cases (the rest blame the reply that claims completion, e.g. `BFCL/030`). The gold response is a visible
error in 56% / 50% / 22% / 19% of the four sub-types, a silent `None` in 8–22%. The gold is in the first user turn in 8–43% and in the
last turn in 22–50%: multi-turn tasks fail in different turns, and each turn is checked independently by BFCL, so "earliest failing turn"
and "the turn the annotator looked at" can differ (`BFCL/030`).

**T6. Internal consistency.** The step number quoted in `hallucination_reason` agrees with `hallucination_step` in 439/443; the 3
disagreements (`BFCL/110`, `Magentic_One/093`, `SmolAgents/009`) are numbering slips in the rationale, the index is right.

**T7. gold = step 0 (112 runs).** OpenManus HI 27 (the `ask_human` is the first action), SmolAgents Planning 25 and OpenDeepSearch
Planning 16 (the "facts survey / plan" step), Magentic-One Planning 17 (orchestrator fact sheet), OpenManus Reasoning 12, BFCL 9, Camel
Planner 5. Share by framework: OpenManus 39/84, SmolAgents 25/57, Magentic-One 17/54, OpenDeepSearch 16/58, BFCL 9/103, Camel 5/57.

**T8. Who is blamed in the multi-agent frameworks.** Magentic-One: Orchestrator 25, WebSurfer 15, Coder 14 (never ComputerTerminal);
OWL: Search Agent 31, Developer Agent 19, Planner 5. Gold = a search/browse *tool-call* step in 11/54 (Magentic) and 31/57 (OWL): in
those the wrong fact arrives in the tool response and the step that *adopts* it is the next agent step.

## 4. Baseline error analysis

**4a. All-at-once baseline — PENDING.** The shared `baseline/all_at_once.py agenthallu --n 80` crashes on BFCL records whose
`task` is a list (`render_task` calls `.strip()`), so the runner's DONE mark is empty. A list-safe copy was started:
`python3 -I inspect/agenthallu_baseline.py agenthallu --n 40 --workers 2` (writes `results/agenthallu/all_at_once_std.jsonl`,
40 records); when it finishes run `python3 -I inspect/analyze_baseline.py agenthallu`. Expected from §3/§5: a +1 mode on
Retrieval (adopt vs fetch, H-AH2), near-100 % on Planning only if the model picks step 0, and Tool-Use far below the rest.

**4b. What exists now — the two probes.**

Detection probe (`inspect/agenthallu_detect.py`, 40 clean + 40 hallucinated, no ground truth; `results/agenthallu/detect.jsonl`):
- hallucinated detected 23/40 (57.5 %), clean false alarms 8/40 (20 %); by category: Planning 6/7 detected, Reasoning 10/17,
  Retrieval 3/7, Human-Interaction 2/3, **Tool-Use 2/6** (mean confidence 0.40); by framework the clean false alarms come from
  BFCL 3/6, Magentic-One 2/6, OpenDeepSearch 2/6.
- Attribution is conditional on detection: `suspect_step == gold` in **8/23 detected and 0/17 missed** hallucinated runs;
  within ±1 15/40. Confidence bins: exact-step 0/15 below 0.5, 8/24 at ≥ 0.8. Without the verdict the model does not know
  what to look for; with it, the step follows in a third of cases.
- The 8 clean false alarms are the "clean runs that contain steps that look like mistakes": tool errors, a rounding
  discrepancy, an adversarial human reply that the agent overrode (`Camel/035`-type) — recovered errors flagged as
  hallucinations (P7).

Prefix probe (`python3 -I inspect/prefix_probe.py agenthallu --n 20 --max-steps 40 --workers 2`, 176 probes,
`results/agenthallu/prefix_probe_g3.jsonl`): gold flagged 9/20 (45 %), earliest flag = gold 4/20, argmax = gold 3/20, flag
rate before gold 11/93 (11.8 %) vs after 22/63 (34.9 %). The unflagged golds are the convention steps of §5 (a plan at step 0,
an `ask_human` call, a search that returned bad evidence) — nothing is locally wrong at them.

## 5. Annotation issues (prevalence estimates)

1. **Fetch-vs-adopt convention (Retrieval, 82 runs; also part of Reasoning).** The gold is the step whose tool response contained the
   wrong/ambiguous evidence, not the step that misread or adopted it (`Magentic_One/008`, `Octotools/026`, `OpenDeepSearch/004`). This is
   consistent (T1: 100% of Retrieval golds have a tool call) but it makes the label systematically one step *earlier* than the agent's
   own mistake, and the blamed step is often a perfectly reasonable search. Estimated ≥ 40% of Retrieval labels (31/57 OWL golds and
   11/54 Magentic golds are search/browse calls).
2. **Human-Interaction is injected, and the label is the call, not the adoption.** All 73 HI golds are `ask_human` steps (T4); the
   same adversarial human appears in 23 clean runs. The rationale often blames the agent for *asking* (`Camel/034`) — a
   counterfactual that punishes seeking help. Prevalence: 73/443 = 16.5% of labels.
3. **Planning = step 0 (64/67).** Any plan/fact-sheet step is a legitimate target for "if this had been better the run would have
   succeeded", so the counterfactual criterion degenerates to the first step. Prevalence 15% of labels; in Magentic-One 17/54.
4. **Near-miss and GT-ambiguity "hallucinations"**: `Camel/006` (144.91° vs 144°), `Camel/049` (two spellings in the sources),
   `OpenManus/053` (official 2022 vs public 2023 rebrand), `OpenManus/058` (district split), `Camel/033`-type rounding in clean runs is
   accepted. From the 12 flagged candidates I read, 4 are debatable; a crude estimate is 3–5% of hallucinated labels.
5. **Defective tasks**: 6 hallucinated runs on GPQA questions with stripped options (`Magentic_One/010` is unanswerable as posed) =
   1.4% of labels; 27 hallucinated OpenManus runs whose `agent_answer` is a tool-output string.
6. **Rationale numbering**: 3/443 rationales quote the wrong step number (index itself consistent).
7. **Role information lost by the loader**: `history[].role` is an agent name, not a chat role; everything is `agent`, so the baseline's
   `agent_ok` metric is trivially the name of the blamed step and the human/tool distinction cannot be exploited or scored.

## 6. Candidate hypotheses

**H-AH1. Category-conditioned position prior ("the label is where the category says it is").**
Statement: in AgentHallu the gold step is a near-deterministic function of the failure category and the trajectory's structural
landmarks (plan step, first `ask_human`, fetch step, last computation), so an attributor that first classifies the *kind* of
hallucination and then applies a structural rule beats trajectory-wide step scoring.
Evidence: T1/T1b — oracle-category rules reach 55.8% exact vs 41.1% for the best published LLM; Planning→step 0 (96%), HI→first
`ask_human` (89%), Retrieval→fetch step (100% tool-call steps, 56% at n//2), Tool-Use→last call (26%).
How to test: (i) two-stage prompting: predict category, then the step, on the 443 runs; (ii) measure the category accuracy of the
all-at-once baseline from its reasoning and the step accuracy conditional on a correct category; (iii) the same on AgentErrorBench
(module label) and TrajErrBench (module.subtype), where the report already shows module-dependent positions.
Shared with: AgentErrorBench (system.step_limit → last step; planning → early), TrajErrBench (VERIFY.* → last steps, PLAN.* → early),
FaP (trigger mechanism vs t_err position). A targeted method would learn P(step | category, landmarks) and use the LLM only to pick the
category — the opposite of the current step-first pipelines.

**H-AH2. Fetch-vs-adopt: the label precedes the agent's mistake by one hop.**
Statement: for Retrieval (and the Science/Math part of Reasoning), the gold step is the step whose *observation* introduced the wrong
fact; the first step that *asserts* the wrong fact is the next agent step. An attributor reasoning about "who said something false"
will systematically land one step late (predicted − gold = +1), and a prefix monitor cannot flag the gold step because the agent did
nothing wrong at it.
Evidence: `Magentic_One/008`, `Octotools/026`, `OpenDeepSearch/004`, `Camel/049`; T8 (31/57 OWL and 11/54 Magentic golds are search/browse
calls); T1 (100% of Retrieval golds carry a tool call, 0% are the final-answer step).
How to test: signed offset histogram of baseline predictions per category (expect a +1 mode for Retrieval); re-score the baseline with a
"shift the blame to the fetch step that supplied the evidence" post-hoc rule; check the same on TrajErrBench OBS.* labels and
SearchAuditBench (where the critical message is also often the one that *read* the page).
Targeted method: attribute to the *evidence provenance* step — trace the wrong claim in the final answer back to the tool response
that first contains it (string/entity overlap), and blame that step.

**H-AH3. Hallucination here is mostly "the right evidence never arrived", not "evidence ignored".**
Statement: in 84% of evaluable hallucinated runs the GT string never appears in any step (T3), and tool errors occur at the same rate in
clean runs (T2). Therefore anomaly-style monitors (loops, tool errors, retries) have little signal; the discriminative signal is the
*provenance* of the final claim (did any observation support it?) rather than the presence of trouble.
Evidence: T2 (clean 33.6% vs hallucinated 40.4% runs with tool errors; per-framework rates equal within noise); T3; close reading of
`Magentic_One/061` (43 coherent steps on the wrong game, no symptom) and `BFCL/002/004/015` (silent `None` responses).
How to test: train/evaluate a claim-support classifier (final answer claim ↔ best-supporting observation) on the 693 runs and compare its
hallucination-detection AUROC to the Qwen judge probe (§4b); test the same on TRAIL/SearchAuditBench where "unsupported claim" is a
category.
Shared with: SearchAuditBench, TrajErrBench REASON.MissingAssumptionCheck; contrasts with TrajErrBench REASON.WrongChoice (evidence
visible and ignored) and AgentErrorBench GAIA.

**H-AH4. The Human-Interaction category is an absorbed-vs-propagated injection experiment hidden in a "natural" dataset.**
Statement: the simulated human is adversarial in both classes; whether a run is labelled HI depends on whether the agent resisted. The
agent could have known in a minority of cases (GT visible before the gold step in 3/55; the ask is the first tool call in 56/73).
Evidence: T4; `Camel/040`, `Camel/036`, `Camel/035` (clean, human wrong, overridden); `Camel/029`, `Camel/046` (evidence contradicts the
human, agent complies); step-0 Planner text forcing `ask_human` in 8 HI + 7 clean Camel runs.
How to test: (i) label the 106 `ask_human` runs by "human reply contradicts evidence already in context" vs "human reply is the only
evidence" and measure absorption per condition; (ii) compare with Aegis (injected messages, 23–66% absorbed) and AgentRx recovered
failures; (iii) check if a prefix monitor flags the *adoption* step (agent restates the human's claim) — it cannot flag the ask step.
Targeted method: a "source trust" feature — claims that originate from a user/human turn and conflict with tool evidence get the blame
at the adoption step; the dataset convention, however, scores the ask step, so the method needs a convention-aware offset.

**H-AH5. Tool-Use (BFCL) labels are state-check failures with no textual symptom, and the decisive step is the earliest *unrecovered*
call, where "unrecovered" depends on hidden side effects.**
Statement: the 14.6% ceiling on Tool-Use is caused by (a) silent `None` responses and confident replies, (b) multi-turn tasks where each
turn is checked separately so several independent errors coexist (`BFCL/004`), (c) errors that look recovered but leave state
(`BFCL/000`), and (d) the invisible turn boundaries (user turns are not steps). An attributor needs the BFCL state semantics (cwd,
path rules) rather than the trajectory text.
Evidence: T5 (gold response visibly errors in only 19–56%; silent in 8–22%; gold in the last turn in 22–50%); close reading.
How to test: give the baseline the per-turn gold function list (oracle "which turn failed") and measure the gain; emulate the BFCL file
system to replay the calls and mark the first call whose post-state differs from the gold post-state (a cheap exact label).
Shared with: TrajErrBench τ² (DB-state failures, policy violations), AgentRx τ-bench. Targeted method: state replay / executable
checker instead of a reader.

**H-AH6. Late symptoms precede late golds in the long Magentic-One runs (P1 holds only on the ≥ 20-step tail).**
Statement: in the 8 runs > 20 steps the gold is a fabrication/assertion that follows loud symptoms (tool errors, scroll loops) by 5–19
steps; for the other 435 runs (median 6 steps) there is no symptom–cause gap to speak of.
Evidence: `Magentic_One/054` (errors at 6, 20; loop 8–12; gold 25), `Magentic_One/061` (no symptom, gold 0), T2 Magentic (tool errors
in 7% of runs only).
How to test: prefix-probe false-flag rates before vs after the gold step as a function of length (§4b); replicate on Who&When-HC and
TraceElephant.

## 7. Open questions

- The paper's category labels are human-chosen after seeing an LLM-drafted "oracle reasoning path"; how often would blind annotators
  put the Retrieval gold on the adoption step instead of the fetch step? (Needs a relabelling study, 50 runs.)
- BFCL: can the gold be recomputed mechanically by replaying the calls against the GorillaFileSystem/stock/travel simulators and
  diffing states per turn? If yes, AgentHallu-Tool-Use becomes an *exact* benchmark with turn-level labels.
- Does the detection judge's confidence on OpenManus runs with a broken `agent_answer` field (33 runs) reflect the field rather than the
  trajectory? (Rerun the detection probe with the last substantive step as the answer.)
- Human-Interaction: who generated the human replies (an LLM told to mislead?) — the paper does not say; the clean-run replies look
  equally adversarial. If the injection prompt is recoverable, the 106 runs give a clean absorbed/propagated split for P7.


## 4b. Baseline results (filled from results/agenthallu/ after the runner finished, 2026-11-01)

Qwen3.8-27B all-at-once, gold = hallucination_step; `step_in_set` counts a prediction inside the full labelled set.
Signed categories: `later` = predicted after the gold (symptom side), `earlier` = before it. Reasoning excerpts for
failures and successes are in `results/agenthallu/all_at_once_std_analysis.md`.

| subset | n | agent_ok | step_exact | step_within_3 | step_in_set |
|---|---|---|---|---|---|
| OpenManus | 12 | 100.0 | 50.0 | 91.7 | 50.0 |
| BFCL | 22 | 100.0 | 86.4 | 95.5 | 86.4 |
| Octotools | 2 | 100.0 | 100.0 | 100.0 | 100.0 |
| OpenDeepSearch | 11 | 100.0 | 54.5 | 100.0 | 54.5 |
| Magentic_One | 11 | 72.7 | 72.7 | 100.0 | 72.7 |
| Camel | 12 | 83.3 | 66.7 | 91.7 | 66.7 |
| SmolAgents | 10 | 100.0 | 60.0 | 100.0 | 60.0 |
| ALL | 80 | 93.8 | 68.8 | 96.2 | 68.8 |

categories: {'exact': 55, 'later(+1..3)': 18, 'earlier(-1..3)': 4, 'later(>3)': 2, 'earlier(<-3)': 1}
agent right but step wrong: 20; step right but agent wrong: 0
| n_steps | n | step_exact% | within3% | agent% |
|---|---|---|---|---|
| 0-10 | 58 | 67.2 | 98.3 | 94.8 |
| 11-30 | 21 | 71.4 | 90.5 | 90.5 |
| 31-1000 | 1 | 100.0 | 100.0 | 100.0 |
wrote results/agenthallu/all_at_once_std_analysis.md
