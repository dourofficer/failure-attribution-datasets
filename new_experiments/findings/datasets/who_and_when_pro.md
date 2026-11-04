# Who&When Pro (text split) — inspection notes (G4, injected-fault group)

Scripts: `inspect/g4_common.py` (re-joins the injection / replay / live flags the shared loader strips), `inspect/who_and_when_pro_stats.py`
(→ `results/who_and_when_pro/stats.md`), `inspect/g4_dump.py`, `inspect/g4_label_check.py`, shared `inspect/prefix_probe.py`,
`baseline/all_at_once.py`. Dumps and outputs under `results/who_and_when_pro/`.

## 1. Data as loaded

- 6,257 rows, 8 frameworks (smolagents 3,276 / mathchat 920 / magentic-one 811 / debate 445 / alfagent 311 / macnet 261 / dylan 152 / metagpt 81), one injected step per row, `error_steps` = the injected step (debate/dylan: the injected turns of the labelled round), mode in `labels.extra.mode`.
- The shared loader drops the raw flags. Re-joined here per step: `injected`, `replayed` (prefix copied from the seed success), `live` (on-policy continuation), `final_answer` (Magentic-One), `injection_via` (Magentic-One: `client_patch` 128 / `direct_chat_completion` 619). smolagents and alfagent rows carry **no flags at all** in the release; for them "injected" = the labelled step by construction.
- Loader caveat worth knowing: in smolagents the first entry is usually a malformed planning/action pair (`Thought/Code: ... </code> Observation:` empty) followed by the same code re-issued at step 1; this is in the data, not a loader bug, but it means step 0 is almost never scorable in practice.
- No ground truth for macnet/metagpt (livecodebench_pro/bigcodebench, 129 rows); the Magentic-One `extras.final_answer` the loader puts in `final_output` is frequently a stray number extracted from the answer text ("2019", "249.9"); use the `FINAL ANSWER:` line of the last step instead (done in the stats script).

## 2. Close-reading notes (13 trajectories, `results/who_and_when_pro/close_reading_dump.txt`)

| id | fw / mode | what the injected step does | visibly wrong from the prefix? | how the continuation treats it | where symptoms are |
|---|---|---|---|---|---|
| simpleqa_verified_magentic-one_0058 | M1 / R.1 | orchestrator final answer "8 children" one step after the search page literally shows "they had 18 children" | yes: contradicts evidence in the previous step | none (injected step IS the final answer) | none |
| simpleqa_verified_magentic-one_0190 | M1 / R.4 | step 0 orchestrator asks for the *year* the crater was named instead of its pre-naming designation | yes vs task | **recovered**: live step 2 asks the right question; the run then fails for a natural reason (cannot find the designation, answers with coordinates) | natural dead-end at 3–6, unrelated to the label |
| simpleqa_verified_magentic-one_0499 | M1 / R.2 | websurfer search step; nothing visibly wrong (the page shows Niloufar Bayani) | no | continuation answers "Niloufar Bayani" = correct; GT in the release is misspelt "Niloufar Bayan"; row is a false failure | none |
| tablebench_smolagents_0814 | smol / A.3 | `idxmax` instead of `idxmin` for "best position" right after the agent wrote "best = lowest numerical value" | yes: contradicts its own step 0 plan | last step | none |
| tablebench_smolagents_0811 | smol / R.4 | restricts the correlation to the 5 largest townships after already computing the full-sample r=-0.10 | yes-ish (unjustified narrowing) | step 6 answers with the correct full-sample number plus the subset claim; then a natural AgentParsingError + retry (6–7) | symptoms are natural format errors, not caused by the injection |
| dabench_smolagents_0298 | smol / R.3 | `std(ddof=0)` instead of pandas default `ddof=1` (9.46 vs 9.57) | only to a careful reader | step 3 computes the answer; then 5 steps of a natural `<code>` parsing loop ending in `final_answer("YOUR FINAL ANSWER HERE")` | loud natural A.4 loop at 4–8; the labelled step is silent |
| mmlu_pro_mathchat_0055 | mathchat / R.3 | code omits the valence 2 (Q = m/M·F) | yes if you know Faraday | **rationalised**: live step 3 re-derives "n_e = 2·n_Zn … Q = 0.003059·96485 ≈ 147.57" — an arithmetic impossibility written to agree with the injected number | none visible |
| math_mathchat_0121 | mathchat / R.2 | computes "exactly one pair" instead of "at least two" | yes | **recovered**: step 3 says "the previous approach … but the problem asks for at least two", answers 49/54 = 0.9074; GT `\dfrac{49}{54}`; failure is decimal-vs-fraction grading | ImportError at step 2 (natural) |
| mmlu_pro_debate_0036 | debate / C.3 | round-1 agent_1 and agent_2 restate D with new reasoning | no: the two injected turns are well-argued | the *replayed* step 3 (agent_0 switching from H to D "given the consensus") is the real over-reliance, but is part of the "correct" prefix | none |
| livecodebench_pro_macnet_0043 | macnet / R.2 | author node_0 code with a wrong reconstruction rule | only by solving the problem | critic rewrites the algorithm at step 1; sink copies the critic. Whether the final code is wrong is not decidable from text (no GT) | none |
| livecodebench_pro_metagpt_0036 | metagpt / A.1 | engineer C++ with a subtle error in a 200-line DP | no | reviewer: "No issues found" (verification theatre) | none |
| scibench_dylan_0029 | dylan / R.2 | agent_1 asserts "the gas expands as it is heated" in a constant-volume problem after three identical correct solutions | yes vs task and vs 3 prior agents | — | none |
| alfworld_alfagent_0108 | alfagent / A.4 | repeated action in a 30-step budget run | pattern, not a step | 21 further steps of the budget | repetition itself |

Recurring observations from the reading:
1. **The injected step usually contradicts something already in the prefix** (its own plan, the previous observation, the task statement, the other agents): 0058, 0814, 0811, 0055, 0121, 0029, 0036-style. Injection prompts produce "deviate from what you were about to do", which is detectable against the prefix. Code-level injections (macnet, metagpt, smolagents ddof) are the exception: silent.
2. **The continuation is generated after the injection and is loyal to it.** It either (a) stops immediately (final answer injected), (b) rationalises the wrong number with internally inconsistent arithmetic (0055), or (c) recovers and the row fails for an unrelated reason (0190, 0121). Natural symptom patterns (retries, "wait", tool errors) after the injected step are rare except for format loops that smolagents produces anyway (see §3d).
3. **Mode labels are the injection *instruction*, not a description of the text.** A.3 "premature termination" for a max/min swap (0814), C.3 "over-reliance" for two agents restating their own answer (0036), A.1 "tool parameter" for a DP bug (0036 metagpt). The mode is what the injector was asked to do; what the base agent actually wrote under that instruction is often a different mode.

## 3. Targeted statistics (`results/who_and_when_pro/stats.md`)

### 3a. Position prior: half the split has no continuation

| framework | n | label = last agent step % | label = last step of its agent % | agent steps after label (mean) | no continuation % | >=3 continuation steps % |
|---|---|---|---|---|---|---|
| alfagent | 311 | 0.0 | 0.0 | 21.03 | 0.0 | 99.4 |
| debate | 445 | 32.4 | 45.8 | 2.11 | 32.4 | 54.2 |
| dylan | 152 | 0.0 | 14.5 | 6.09 | 0.0 | 100.0 |
| macnet | 261 | 0.0 | 58.2 | 2.58 | 0.0 | 58.2 |
| magentic-one | 811 | 56.0 | 69.5 | 1.92 | 56.0 | 26.9 |
| mathchat | 920 | 78.8 | 78.8 | 0.31 | 78.8 | 1.1 |
| metagpt | 81 | 0.0 | 100.0 | 1.83 | 0.0 | 0.0 |
| smolagents | 3276 | 52.1 | 52.1 | 1.11 | 52.1 | 13.6 |
| ALL | 6257 | **48.4** | 55.2 | 2.35 | 48.4 | 24.4 |

- In Magentic-One 44.6% of injected steps carry the `final_answer` phase flag: the injection *is* the final answer. Mean live (post-injection) steps 1.92.
- A trivial "last agent step" predictor scores 48.4% step accuracy on the text split (paper SOTA 72–74%); "last step of the framework's usual culprit" 55.2%. In metagpt the label is always the last turn of its agent (architect 83% / engineer 17%).
- Only alfagent, dylan and macnet always have a continuation; alfagent's continuation is the fixed 30-step budget.

### 3b. Construction check: does the final output disagree with the GT?

Lenient match (normalised string, numeric within 0.1%, fraction = decimal): **51 / 5,807 comparable rows (0.9%)** have a final output equal to the GT (mathchat 9: decimal vs `\dfrac`; magentic-one 28: rounding and a GT typo "Niloufar Bayan"; dylan/debate: rounding). So "false failure" is rare (~1%); the grader is strict but not broken. The more important construction issue (recovered injection + unrelated natural failure, as in 0190 / 0121) cannot be string-matched; see the LLM label check in §3e.

### 3c. Style: the injected turn vs the same agent's other turns in the same trajectory

z-score of the injected turn's feature against the agent's other turns (clipped ±5), and whether the injected turn is the argmax of |z| over (length, hedging, digit density) among the agent's turns:

| framework | n | z chars | z words | z hedge | z cert | z selfref | z digits | z newlines | injected is longest % | shortest % | argmax |z| % | chance % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alfagent | 311 | +1.64 | +1.50 | +0.21 | +0.14 | -0.00 | -0.81 | -1.51 | 14 | 0 | 13 | 3 |
| dylan | 112 | -1.49 | -1.34 | +0.16 | -2.09 | -1.35 | +0.28 | -1.57 | 16 | 57 | 83 | 33 |
| magentic-one | 376 | +1.77 | +1.75 | +0.23 | +1.08 | +0.08 | -0.05 | +1.45 | 53 | 6 | 62 | 25 |
| mathchat | 95 | -2.16 | -2.35 | +0.14 | +0.16 | -0.23 | -2.67 | -1.44 | 8 | 65 | 92 | 27 |
| smolagents | 2599 | -0.93 | -1.05 | +0.16 | +0.01 | +0.05 | -0.58 | -0.92 | 8 | 36 | 50 | 23 |
| ALL | 3493 | -0.46 | -0.57 | +0.17 | +0.07 | -0.01 | -0.57 | -0.75 |  |  |  |  |

- **Length alone is a strong tell, but its sign is framework-specific**: the injected Magentic-One orchestrator turn is the *longest* of its turns in 53% (it is usually the final-answer prose, z=+1.8); the injected mathchat / smolagents / dylan turn is the *shortest* (z≈-1 to -2.2, fewer digits, fewer newlines: a truncated computation). A 3-feature argmax picks the injected turn in 50–92% vs 23–33% chance, with no outcome information.
- Hedging and certainty words carry almost no signal (|z|<0.25) except dylan (injected turns less certain, z cert -2.1). Self-reference to error ("mistake", "incorrect") is absent (z≈0): unlike AEGIS, the Who&When Pro injector does not make the agent announce the deviation.
- Caveat: this is a within-agent comparison, so it is only available where the agent has ≥2 other turns (3,493 rows); the confound is position (the final step is naturally different). Restricting to rows where the injected step is **not** the last turn of its agent (stats.md §g): smolagents collapses to 28% vs 19% chance (the signal was the short `final_answer` step), alfagent 13% vs 3%, but magentic-one 50% vs 23%, mathchat 85% vs 31%, dylan 83% vs 33% keep a real style signal — in the multi-turn reasoning frameworks the injected turn is genuinely written differently (a truncated derivation), independent of position.

### 3d. Continuation symptoms: after the injected step vs after natural labels (Who&When)

Share of agent/tool steps carrying a marker (regex; `tool_error` = Traceback/Error:/Exception, `self_correct` = wait/actually/mistake/retry/re-check, `uncertainty` = unable/could not/not found, `repeat` = exact repeat of a step's first 400 chars):

| set | marker | records | % before label | % at label | % after label |
|---|---|---|---|---|---|
| WWP all | tool_error | 6257 | 1.2 | 2.8 | 4.7 |
| WWP all | self_correct | 6257 | 2.7 | 3.5 | 7.4 |
| WWP all | uncertainty | 6257 | 1.6 | 1.3 | 3.1 |
| WWP all | repeat | 6257 | 1.2 | 0.0 | 13.3 |
| WWP smolagents | tool_error | 3276 | 1.0 | 3.3 | 11.6 |
| WWP smolagents | uncertainty | 3276 | 1.9 | 1.9 | 10.4 |
| WWP magentic-one | self_correct | 811 | 1.4 | 0.7 | 0.8 |
| WWP mathchat | self_correct | 920 | 2.1 | 2.5 | 9.5 |
| WWP alfagent | repeat | 311 | 0.0 | 0.0 | 26.0 |
| WW hand-crafted | tool_error | 58 | 0.5 | **12.1** | 1.3 |
| WW hand-crafted | self_correct | 58 | 10.1 | **22.4** | 7.0 |
| WW hand-crafted | loop_marker | 58 | 15.8 | 3.4 | 13.9 |
| WW hand-crafted | repeat | 58 | 13.5 | 0.0 | 22.9 |
| WW alg-generated | tool_error | 126 | 10.3 | 6.3 | 11.3 |
| WW all | self_correct | 184 | 8.9 | 11.4 | 6.3 |

- **Natural labelled steps are loud; injected ones are silent.** In Who&When hand-crafted, 12% of labelled steps contain a tool error and 22% a self-correction phrase, i.e. the annotated "cause" coincides with a visible symptom in a third of cases; in WWP the labelled step carries a marker in 2.8% / 3.5%, no higher than the clean prefix.
- **After** the label, WWP does show more markers than before (tool errors 1.2→4.7%, self-corrections 2.7→7.4%), mostly in smolagents (format-parsing loops, "unable to"), and `repeat` jumps to 13% (alfagent's budget loop, mathchat's user_proxy prompts). But the post-label rates in WWP are at or below Who&When's *baseline* rates before the label (WW HC: self-correct 10%, loop 16%, repeat 13.5% before the label): WWP trajectories are cleaner everywhere, and the continuation does not reach natural-failure levels of visible trouble.

### 3e. LLM label-vs-content check (`inspect/g4_label_check.py`, 64 rows, 8 per framework, outcome and GT hidden, labelled step marked)

PENDING — server queue (fill in: local_wrong %, contradicts_prefix %, corrected_later %, decisive yes / no_earlier / no_later / no_other %, style_odd %, per framework).

### 3f. Prefix probe (`inspect/prefix_probe.py who_and_when_pro --n 20 --max-steps 30`)

20 records (smolagents 11, magentic-one 3, debate 3, macnet 2, mathchat 1), 105 probes, prefix only, no GT, no outcome (`results/who_and_when_pro/prefix_probe.jsonl`):

| metric | value |
|---|---|
| gold (injected) step flagged as a mistake | **20/20 (100%)**, confidence 0.75–1.0 |
| earliest flagged step == gold | 17/20 (85%) |
| argmax-confidence step == gold | 15/20 (75%) |
| flag rate on steps BEFORE gold (replayed prefix) | 3/42 (7.1%) |
| flag rate on steps AFTER gold (live continuation) | 25/43 (58.1%) |

- The injected step is **locally detectable in every probed row** and is the earliest flagged step in 85%: the monitor's one-line reasons are prefix contradictions ("computed the correlation with col (m) instead of prominence (m) while claiming it was prominence", "asks for gold medals instead of the requested bronze", "ignores the initial kinetic energy and contradicts the prior correct calculation"). This is the direct test of H1 — on natural Who&When data the same probe (G1's run, `results/who_and_when/prefix_probe.jsonl`) had only one record finished at hand-back, so the natural comparison is still open; the literature's 3.5–25% step accuracy on WW with prefix-style judges is the reference point.
- The replayed prefix is almost never flagged (7.1%): the "successful prefix" assumption holds for the monitor (H6 weakly refuted on this sample; debate 0036-type cases are rare).
- 58% of live continuation steps are flagged: the continuation inherits the error and is judged wrong step after step — on injected data "downstream contamination" exists for a *prefix-only* judge, but the earliest flag is still the cause (85%), i.e. an earliest-flag rule beats argmax-confidence (75%) and there is no P1-style late bias.

### 3g. Mode / agent priors

| framework | n | top modes | top labelled agents |
|---|---|---|---|
| alfagent | 311 | R.4 19%, V.2 19%, R.2 19%, A.4 17% | — (single agent) |
| debate | 445 | C.3 46%, R.1 17%, R.4 14%, R.2 14% | agent_2 29%, agent_1 16%, agent_0 10% |
| dylan | 152 | R.2 32%, R.1 28%, R.4 19%, R.3 17% | agent_3 28%, agent_2 26%, agent_1 24% |
| macnet | 261 | C.3 42%, R.4 26%, A.1 9%, R.2 9% | node_0 58%, node_1 42% |
| magentic-one | 811 | R.1 31%, V.2 30%, R.4 12%, R.2 9% | orchestrator 78%, websurfer 11%, coder 9% |
| mathchat | 920 | R.2 32%, R.3 31%, R.4 29%, R.1 9% | assistant 100% |
| metagpt | 81 | R.4 32%, R.2 30%, PL.1 21%, A.1 10% | architect 83%, engineer 17% |
| smolagents | 3276 | A.3 35%, R.4 16%, R.2 16%, R.3 11% | — |

Mode is nearly a function of (framework, position): smolagents A.3 (35%) = "call final_answer now", which is why 52% of smolagents labels are the last step; macnet/debate C.3 = "agree with the other node".

Magentic-One has two injection mechanisms with different signatures (stats.md §h): `direct_chat_completion` (619 rows) rewrites the **orchestrator's** LLM output — 100% orchestrator, 58% of them the final answer, no tool action; `client_patch` (128 rows) patches the **websurfer/coder** tool client — 0% final answer, 56% contain a tool `Action:`, modes R.1/R.2/V.2/C.3. The former is the "assertive wrong closing" of P4/P8; the latter is a corrupted observation that the orchestrator then trusts (over-reliance), the only Magentic-One rows with a genuine continuation.

## 4. Baseline error analysis

PENDING — `results/who_and_when_pro/all_at_once_std.jsonl` (100 rows, chain C of the background runner) has not finished; plan: `analyze_baseline.py`, then re-run the same ids with `--mask-last 1` and `--no-gt` to measure how much of the step accuracy is the last-step prior (§3a predicts ≥48 pp of it).

## 5. Annotation / construction issues (prevalence)

1. **No continuation in 48.4% of rows** (§3a): the "when" label is the last agent step; nothing downstream can be a symptom; any attributor that sees the trajectory end gets those for free. Magentic-One: 44.6% of injections are the final answer itself.
2. **Mode ≠ what the text does** (3 of 13 read; LLM check pending): the mode is the injector's instruction; the "what" axis of the benchmark is partly unlearnable from the text.
3. **Recovered injections kept as failures**: 2 of 13 read rows (0190, 0121) recovered from the injected step and failed for another reason (natural dead end, grading format). Prevalence to be estimated from the LLM check (`decisive = no_other / no_later`).
4. **False failures ≈ 0.9%** by lenient matching (§3b): GT typos ("Niloufar Bayan"), decimal/fraction, rounding.
5. **Replayed "correct" prefixes contain real errors**: debate 0036's agent_0 flips to the wrong answer in the replayed prefix; the "successful" seed run succeeded by majority despite it. The construction assumes the seed prefix is error-free (P6).
6. **Flags leak** in the raw rows (`phase`, `is_injected`, `injection_via`, `ledger`); the official renderers strip them, our loader does too; any script that reads `text.jsonl` directly must strip them.
7. **Injected step in smolagents is a *shorter* code step** (§3c): style/length is a label artefact an attributor can exploit without understanding the error.

## 6. Candidate hypotheses

**H1 — Prefix-contradiction, not outcome, is what makes injected steps detectable.** Injected steps deviate from a correct prefix, so they contradict their own plan / the previous observation / the task (7 of 13 read). Natural causes (Who&When) are more often *consistent* with their prefix and only become visible through later symptoms. Evidence: §2; WWP labelled steps carry no symptom markers (§3d) yet SOTA reaches 72% step accuracy. Test: prefix_probe on WWP vs WW (same model); LLM check `contradicts_prefix` rate (pending); a "consistency with the prefix" scorer (entailment of step k against steps <k) should rank injected steps top-1 far above its rank on WW. Shared with: correct_error (rewritten step contradicts its own previous turn), aegis (number changes), tracertraj injected rows. Method: a two-channel attributor — prefix-contradiction channel (for injected-style errors) + downstream-symptom back-propagation channel (SOAP-style, for natural errors) — with a gate learned from whether the trajectory has loud symptoms at all.

**H2 — A last-step / style prior explains most of the reported step accuracy on injected data.** 48.4% of labels are the last agent step; the injected turn is the length outlier of its agent in 50–92% of rows. Test: baseline with `--mask-last 1` (pending); a logistic model on (is_last_agent_step, |z_len|, fw) with no text; compare to the paper's 72%. Shared with: correct_error (50% last step, 74% Planner), tracertraj diagnosed (48% last). Method implication: any evaluation on injected data must report accuracy *conditional on label ≠ last step*.

**H3 — Loyal continuations remove the symptom channel; only format loops survive.** The on-policy continuation is conditioned on the injected step, so it rationalises it (0055) or ends immediately; post-label marker rates (§3d) stay below Who&When's *pre-label* rates. Where symptoms do appear (smolagents parsing loops, alfagent budget loops) they are natural artefacts of the framework, not consequences of the injection, so they *mislead* a symptom-based attributor (dabench_0298: loud loop at 4–8, silent cause at 2). Test: LLM check `symptoms_later` (pending) split by whether the symptom step depends on the injected content; compare SOAP/EMFA-style back-propagation gains on WWP vs WW (literature: SOAP +8.5 pp on WW-AG, +0.4 on CE). Shared with: correct_error, aegis.

**H4 — Modes are injection instructions; "what" is not recoverable from "when".** The injector's instruction leaves a text that a reader classifies differently (A.3 for max/min swap, C.3 for restating one's own answer). Test: LLM free-text mode on the marked step vs label (pending); human re-labelling of 50 modes. Predicts the benchmark's low Error accuracy (15–19%) is a label property, not a judge limit.

**H5 — Recovered injections produce a floor of unattributable rows.** Prefix must be clean (late injection) and only failing continuations are kept, but the continuation may fix the injected error and fail for a natural reason; the label then points at a step that is not the cause. Test: LLM check `decisive ≠ yes` rate (pending) + manual read of those rows; expected 5–15% in Magentic-One/mathchat (2/13 read). Shared with: tracertraj (diagnosed labels on crawl_page failures), aegis (injection absorbed but outcome wrong anyway).

**H6 — Replayed successful prefixes carry real errors, so "earliest error" ≠ injected step.** debate 0036. Test: run prefix_probe on replayed steps only and count flags before the injection (false-flag rate on the "clean" prefix is the measurement; pending); compare to the flag rate on Who&When pre-label steps.

## 7. Open questions

- How much of the 72% paper step accuracy survives when rows whose label is the last agent step are removed? (needs the mask-last run)
- Does Step@1 tolerance (+13.9 pp in the paper) mostly absorb "predicted the live step after the injection" errors, i.e. is the judge's miss direction *later* on injected data as it is on natural data?
- Are Magentic-One `client_patch` vs `direct_chat_completion` injections different in detectability (the former patches the tool client, the latter rewrites the LLM output)?
- Video/image splits (not loaded) have relative position 1.0 median — the last-step prior is presumably even stronger there.
