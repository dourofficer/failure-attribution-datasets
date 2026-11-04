# MAST-Data (MAD) — spot check (G4)

Scripts: `inspect/mast_data_probe.py` (LLM: list the MAST modes present and the step where each first appears; → `results/mast_data/mode_probe.jsonl`),
`inspect/g4_dump.py`. Picks: `results/mast_data/picks.txt` (35 parsed traces, 5 per framework, 3–60 steps, ≥1 mode); 9 read by hand:
`results/mast_data/close_reading_dump.txt`.

## 1. Data as loaded

- 1,642 traces, trace-level binary mode vector (o1 judge), no step, no agent, no outcome; 32 traces unparsed (one step). Steps come from heuristic splitters; for ChatDev every step re-embeds the full role prompt (~1.3k chars of boilerplate per step), for AG2 MathChat the first step is the framing prompt, for Magentic-One the orchestrator's ledger re-plans appear as ordinary steps.
- Mode frequency in the corpus is dominated by 1.3 / 3.3 / 2.6 / 3.2 / 1.1 (≈600 traces each); several traces carry 8–9 modes (OpenManus/7: 8, MagenticOne_GAIA/21: 9).

## 2. Close-reading notes (9 traces)

| id | fw / n | modes (o1) | what I see | step-localisable? |
|---|---|---|---|---|
| MetaGPT_ProgramDev2_GPT4o/72 | MetaGPT / 6 | 1.3, 2.5 | Coder writes a correct csv→json CLI; Tester writes tests; Reviewer asks for a data-type test; Tester resubmits the *same* tests (step 4 ≈ step 2); Reviewer repeats the comment | 2.5 at step 4 (ignores step 3's request) — visible only by comparing 2↔4↔3; 1.3 is the pair (2,4). Outcome: the code is fine; "failure" is a process judgement |
| AppWorld_Test-C_GPT-4o/15 | AppWorld / 11 | 2.2, 2.5, 2.6, 3.1 | Spotify agent asks for an access token (3); Supervisor guesses the account password is the token (6–7); token invalid (9); Supervisor marks the task failed (10) | 3.1 at step 10; the real error is the guess at 6 (not a listed mode); 2.2 "fail to ask for clarification" is arguable at 4–6; 2.5 not visible |
| AG2_Olympiad_GPT4o/184 | AG2 / 6 | 1.3, 3.3 | assistant writes code, proxy runs it (n=93), assistant re-sends the same code (3), proxy prints 93 twice, assistant answers 93 | 93 is **correct** (33, 85, 93 are the first three such n); the "failure" modes are a redundant re-run (1.3 at 3) and a "verification" that just restates (3.3 at 5). A success trace carrying modes (P6) |
| AG2_GSM_Plus_Claude/145 | AG2 / 6 | 1.1, 2.6 | code prints "Total apples gathered: x + 455.0" (unsolved symbol) while the text asserts 3; assistant fixes and verifies 500 | 2.6 at step 1/2 (printed x+455 vs claimed 3), corrected at 3; final answer 3 is right; 1.1 (decimals printed) is a format nit |
| ChatDev_ProgramDev2_GPT4o/19 | ChatDev / 26 | 1.1 | CEO/CPO/CTO phases (modality, language) then Programmer writes the Base64 CLI; the 1.1 is presumably a spec detail in the code | not localisable without running the code; the mode is a property of the final artefact |
| Magentic_One_GPT4o/44 | Magentic / 37 | 1.3, 2.6, 3.1, 3.3 | 1928 Olympics athlete counts: WebSurfer opens the Wikipedia page, scrolls, goes back to Bing, re-opens the same page three times (5, 26, 31); orchestrator re-plans at 27 ("By targeting navigation errors…"); never reaches the table | 1.3 is the pattern {5, 26, 31} (first repeat at 26); 3.1/3.3 at the end; 2.6 nowhere obvious |
| MagenticOne_GAIA_GPT4o/21 | Magentic / 43 | 9 modes | long GAIA navigation run (not read in full) | — |
| OpenManus_ProgramDev_GPT4o/7 | OpenManus / 26 | 8 modes | (skimmed) a ReAct coder repeating file writes and "Executing step n" to the step budget | 1.3/1.5 as a tail pattern |
| HyperAgent_SWE-Bench-Lite_Claude/0 | HyperAgent / 36 | 1.3, 2.6, 3.2 | (skimmed) navigator/editor logger lines; repeated code-search rounds | pattern |

Observations:
1. **Verification modes (3.x) and termination modes (1.5, 3.1) sit at the end** of the trace by definition — they are localisable but the step is always the last one or two.
2. **Repetition (1.3) is a relation between two steps**, not a step: the localisable event is the *second* occurrence, which is a symptom of whatever made the first attempt fail (Magentic/44: the page scroll did not reveal the table).
3. **Inter-agent modes (2.x) are localisable only by comparing a turn with an earlier turn of another agent** (2.5: ignored input ↔ the input turn; 2.6: claim ↔ its own code output).
4. **Correct-answer traces carry failure modes** (AG2/184, AG2/145, MetaGPT/72): without an outcome label, MAST modes are process observations; at least 3 of the 9 read traces end with a right answer / working code.
5. The o1 label set is inflated on long traces (8–9 modes on OpenManus/7, GAIA/21): long traces give the judge more opportunities, so mode count correlates with length, not with distinct failures.

## 3. Targeted statistics

### 3a. LLM mode-localisation probe (35 traces; PENDING, server queue)

Fill in: precision/recall of predicted modes vs o1 labels; per mode: count predicted as "step" vs "pattern"; mean relative first-step position per mode; success judgements (expect a sizeable "true" share, cf. §2.4).

### 3b. Structural expectations to verify against the probe
- Expected step-localisable with a *single* step: 1.1 (first violating action), 1.2, 2.1, 2.2 (the turn that should have asked), 2.3 (first off-task action), 2.4, 3.1 (the terminating turn).
- Expected pattern-only: 1.3 (needs ≥2 steps), 1.4 (needs the forgotten turn and the forgetting turn), 1.5 (absence of termination = the tail), 2.5 (needs the ignored input), 2.6 (needs reasoning + action of the same turn or the tool output), 3.2 (absence of a verification step), 3.3 (a verification turn + the fact it is wrong, which needs the outcome).
- So roughly half the taxonomy (1.3, 1.4, 1.5, 2.5, 3.2, 3.3 ≈ 2,850 of the 5,159 corpus flags) is not a step property; a step-level benchmark built from MAST modes (AEGIS does this) inherits the mismatch.

## 4. Baseline error analysis

Not applicable (no step labels); not run.

## 5. Annotation / construction issues

1. Trace-level labels on traces that may have succeeded (3/9 read); the corpus has no outcome field, so "failure mode" ≠ "failure".
2. Mode count grows with length (8–9 modes on the longest traces) — an o1 judge property.
3. Splitter artefacts (ChatDev boilerplate per step, AG2 framing step) would dominate any token-level model.
4. 32 traces unparsed.

## 6. Candidate hypotheses

**H1 — Half of the MAST modes are relations, not steps; step-level attribution of those modes is to the *second* element of the relation, which is a symptom.** (1.3 second occurrence, 2.5 the ignoring turn, 3.3 the final check.) Test: the probe's "kind" field and the position of the first step per mode (pending); then in AEGIS, check whether the modes that AEGIS injects as single-turn corruptions (1.3, 1.5, 3.2 …) are exactly those a reader cannot see in one turn — predicts the mode-text mismatch found in AEGIS §2.

**H2 — Process-mode presence does not predict outcome in templated math/code systems.** AG2 traces with modes end correctly (2/2 read). Test: re-grade the 223 AG2 GSM-Plus traces (answers are extractable, GSM-Plus GT is public) and compute P(correct | any mode) vs P(correct | no mode); if the gap is small, MAST modes are the "errors inside successes" of P6 and useless as a failure signal without the outcome. Shared with: agenthallu/horizon (G3) which have successes.

**H3 — Length-conditioned judge inflation.** Modes per trace ∝ steps. Test: regress mode count on log(steps) per framework; compare the human-labelled 19 traces. Implication for AEGIS/TRAIL-style multi-label targets: a judge-labelled set needs length-stratified evaluation.

## 7. Open questions

- Which traces are failures at all? The paper's human study annotated failed runs; the released corpus mixes (per the report, "no outcome").
- Are the 1.3 flags in Magentic-One traces mostly browser-navigation repeats (a WebSurfer property) rather than reasoning loops?
