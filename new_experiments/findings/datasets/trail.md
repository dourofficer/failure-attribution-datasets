# TRAIL — inspection notes (G2, Nov 2026)

Scripts: `inspect/trail_stats.py`, `trail_evidence.py`, `trail_stats2.py`, `trail_priors.py`, `trail_view.py`, `trail_inventory_match.py`;
outputs under `results/trail/` (`stats.txt`, `evidence.txt`, `stats2.txt`, `priors.txt`, `late_primary.txt`, `reads/`).

## 1. Data as loaded

- 148 traces (117 GAIA / 31 SWE-bench Lite), 4,626 spans = steps in DFS order; 839 located errors on 577 spans (2 unresolved span ids).
  Agent-role steps are LLM spans (1,974); TOOL 648; the rest (CHAIN `Step N`, AGENT, INTERNAL) are `env`.
- Primary label = `extra.primary_idx` = earliest HIGH-impact span (earliest error span if the trace has no HIGH: 38 traces, 34 with errors).
  Primary ≠ earliest error span in 58/144 traces (median gap 5 spans, mean 10, max 47).
- **Outcome is recoverable for GAIA**: the `answer_single_question` INTERNAL span (step 2) embeds the GAIA `true_answer`; comparing it with the
  `FinalAnswerTool` input gives **34 correct-ending / 83 wrong-ending GAIA traces** (semantic match; 25 would also pass GAIA exact match,
  11 answer in the verbose "### 1. Task outcome" template; 2 heuristic false positives removed by hand: `331aece5` answers 3 for 2,
  `c60ad860` Wiesner for Shannon). The report's "4 traces end correctly" is wrong — 4 traces have *no error*, ~34 end correctly.
- **Ground-truth leak**: the `true_answer` string is literally present in step 2 of **117/117** GAIA traces. Any judge that reads the
  trace (ours included, even with `--no-gt`) and every human annotator saw the gold answer. SWE-bench has no outcome label.
- Loader caveat (not a bug, a property of the traces): TOOL spans carry `output.value` in only 332/648 cases and `status_code=Error` in 174;
  the error text ("Error when executing tool page_down …") lives in the *next LLM span's input messages* (788 LLM spans contain one) and
  in 41 CHAIN spans, never in the TOOL span. The loader renders only the last input message of each LLM span, so a tool failure is visible
  at k+2 (next LLM step) only when it is the last message — which it is in smolagents. Keep this in mind for any "local" scorer.

## 2. Close-reading notes

| id | n | primary | outcome | what happened / where the label is / do I agree |
|---|---|---|---|---|
| gaia/5e5dc94e… | 11 | 8 (3 HIGH) | correct (6) | Manager answers BERT-vs-Transformer layer difference from memory, no tool. Labels: step 6 plan "assumes facts" (MEDIUM), step 8 Task Orchestration + Tool Selection + Instruction Non-compliance (all HIGH). The run is correct; the HIGH labels are compliance labels ("did not use tools"), not causal. |
| gaia/0140b3f6… | 60 | 22 (HIGH Formatting) | correct (Louvrier) | search_agent calls `page_down` with `{"": ""}` five times (steps 22,27,30,33,36 — each labelled HIGH Formatting; 36 also Resource Abuse), replans at 39 (MEDIUM), recovers with `find_on_page_ctrl_f`, finds "Louvrier", typo "Louvrrier" at 52 (LOW). Primary = a recovered tool-argument bug. 5 HIGH labels for one repeated mistake; "mark the first instance" rule not applied. |
| gaia/14be0e98… | 84 | 19 (HIGH Formatting + Context) | correct (80GSFC21M0002) | Same `page_down` bug 7 times (19, 22, 27, 30, 33, 36 unlabelled; 50, 55, 58, 64 labelled HIGH) — labelled inconsistently within one trace; the agent later finds the NASA award through `find_on_page` + `inspect_file_as_text`. Primary is a recovered error; the run succeeds. |
| gaia/0242ca25… | 15 | 8 (HIGH Formatting) | wrong | Step 8 code prints the task string instead of calling `search_agent` (labelled HIGH); step 10 repeats it (unlabelled); step 12 fabricates "negative binomial" (3 HIGH: Poor Info Retrieval, Language-only, Goal Deviation). Cause at 8, loud symptom at 12. Agree with the primary. |
| gaia/041b7f9c… | 15 | 10 (HIGH Tool-related ×2) | wrong (20 vs 41) | Step 8 makes the *identical* print-instead-of-call mistake as 0242ca25/8 but is **unlabelled**; step 10 says "after a search … a reliable source indicates 484" with no search in the trace (hallucinated observation, labelled). Label sits on the symptom; root (8) missed. |
| gaia/01c57271… | 52 | 47 (HIGH Goal Deviation) | wrong (0 vs 3) | search_agent visits OpenReview, `page_down` bug twice (MEDIUM), replans, broad re-search (MEDIUM), then `final_answer` "0 papers" without finishing the plan (HIGH at 47). LOW `<end_plan>` labels at 6 and 11 precede everything. Primary is the last search_agent decision = the first *unrecoverable* step; earlier MEDIUM steps are the actual loss of progress. |
| gaia/0adc4f3b… | 11 | 6 (LOW only) | correct (100) | Pure logic puzzle solved in one step. Only error: missing `<end_plan>` tag. Noise label on a correct run. |
| gaia/d2868d12… | 21 | none | correct | search_agent answers from search snippets after one `web_search`, no page visit; 0 errors. |
| gaia/331aece5… | 18 | 6 (LOW only) | **wrong** (3 vs 2) | search_agent gives `final_answer` after **zero** tool calls (step 13: "based on archived Wikipedia…" from memory); manager relays. Only two LOW `<end_plan>` labels. The decisive error (13) is unlabelled; same process as d2868d12 which is correct and unlabelled. |
| gaia/2c77a8fe… | 21 | 18 (HIGH Tool-related) | correct (2) | Steps 8, 10, 12, 14 all print the task instead of calling `search_agent` (4 unlabelled repeats; CodeAgent even says "I have not received an answer yet"); step 18 fabricates "verified through cross-references" and answers 2 (HIGH, correct by luck); step 20 (framework final LLM) HIGH Instruction Non-compliance. Label on the symptom; root unlabelled; outcome correct. |
| gaia/3acaa315… | 32 | 29 (HIGH Tool-related + Goal Dev.) | wrong (27 vs 3) | Task needs watching a YouTube video; four `web_search` calls return "No results" (each MEDIUM Poor Information Retrieval), search_agent gives up, manager guesses 27. Earliest HIGH = the final guess; the real cause is tool infeasibility (no video tool). |
| swe_bench/0f7f322d… | 52 | 51 (HIGH Language-only on `FinalAnswerTool`) | n/a | 24 steps of directory-tree printing (LOW/MEDIUM), several "printed >500 chars" Instruction Non-compliance (MEDIUM), patch judged wrong at the final tool span. Primary = last step. |
| swe_bench/c104d0e2… | 34 | 22 (LOW+MEDIUM) | n/a | No HIGH; labels are "printed too much" compliance notes (22, 28) and the FinalAnswerTool span labelled "model didn't provide the final answer, stops on the tool call" (MEDIUM Context Handling) — a misreading of the framework (the tool span *is* the answer). |
| swe_bench/a18532f8… | 22 | none | n/a | Locates file after 3 wrong paths, patches `_infer_str_format_call`; 0 errors. Same exploration pattern as the labelled SWE traces. |

Where the visible symptoms are: tool failures surface two spans after the LLM span that caused them (next LLM input), fabrications are
visible in the step itself (claims of "search" or "verification" with no preceding TOOL span), and the manager's final step repeats the
search_agent's report — so in 2-agent traces the loud symptom is the manager's final LLM span, 10–40 spans after the search_agent's error.

## 3. Targeted statistics

**3.1 Errors inside correct-ending runs (P6/P7).** GAIA: 34 correct vs 83 wrong.

| | correct (34) | wrong (83) |
|---|---|---|
| mean errors / trace | 4.29 | 5.29 |
| mean HIGH / trace | 2.03 | 2.51 |
| share with 0 HIGH | 32% | 12% |
| traces with ≥1 HIGH | 23 (68%) | 73 (88%) |
| human overall score (mean / median) | 3.60 / 3.75 | 3.17 / 3.0 |
| human reliability score | 2.88 | 2.19 |

P(correct | category present): Formatting 0.29, Instruction Non-compliance 0.28, Task Orchestration 0.29, Context Handling 0.28,
Language-only 0.25, Tool Selection 0.22, Goal Deviation 0.18, Tool-related 0.17, Resource Abuse 0.17, Poor Information Retrieval 0.13,
Tool Output Misinterpretation 0.15 (base rate 0.29). Only retrieval/misinterpretation/hallucination categories are below base rate;
formatting / instruction / orchestration errors are outcome-neutral. Primary category vs outcome: Formatting 7 correct / 5 wrong,
Goal Deviation 0 / 9, Language-only 2 / 12, Tool-related 5 / 18.

**3.2 Earliest span vs primary HIGH.** 86 traces: primary is the earliest error span; 58: earlier LOW (32) / MEDIUM (17) / both (9) errors
precede it, median 5 spans earlier. 29 of the 154 pre-primary errors are the missing `<end_plan>` tag (47 such labels in total, 43 LOW:
o3-mini never emits the tag; it is labelled in ~40% of traces and never matters). 30% of all errors (249/839) repeat a
(category, impact) already labelled in the same trace; 43 traces have ≥3 repeats.

**3.3 Where the annotator's evidence text is (string match, 839 errors).** In the labelled step's rendered content 482 (57%); in the span's
full attributes (input history) 45; in *another* span 44 (offsets +2: 17, +3: 18 — the next LLM/CHAIN span that carries the tool error);
nowhere (paraphrase) 267 (32%). By span kind: LLM 470/744 visible, **TOOL 12/95** — errors placed on TOOL spans are justified by text that
is not in the tool span. Evidence of the primary error quotes an execution error message in only 23/297 cases.

**3.4 Structural priors on the primary (`trail_priors.py`).**

| subset | prior | exact | within 3 | in error set |
|---|---|---|---|---|
| GAIA (114) | first CodeAgent action LLM span (idx 8) | **40.4%** | 63.2% | 46.5% |
| GAIA | last CodeAgent LLM span before final_answer | 39.5% | 61.4% | 64.0% |
| GAIA | LLM span before the first TOOL span with status Error (fires 42) | 9.6% | 17.5% | 16.7% |
| GAIA | random LLM span | 13.9% | | |
| SWE (30) | first action span | 3.3% | 50.0% | 3.3% |
| SWE | last CodeAgent LLM span | 6.7% | 16.7% | 26.7% |
| SWE | random LLM span | 9.0% | | |

Reason: **37/117 GAIA traces are 11–13-span "answer from memory" runs** (facts, plan, one action = `final_answer`): primary = step 8 in all
of them (10 of the 37 are correct). 46/117 GAIA primaries sit in the last three spans (the manager's final LLM call): 37 memory answers,
3 after the search_agent reported failure, 6 after a search_agent run.

**3.5 Unlabelled identical mistakes (label consistency).** The CodeAgent "print the task string instead of calling `search_agent`"
mistake occurs 28 times in 15 traces; 18 are labelled, **10 are not** (041b7f9c/8, 2c77a8fe/8,10,12,14, 6e64c2e5/8, d857dc7d/8, 0242ca25/10,
1dd91d38/10, 3205fa0c/13). search_agent `final_answer` with no `visit_page` in its run: 13 traces, 5 labelled; 3 correct.
GAIA wrong-ending traces with **no HIGH error at all: 10/83** (21f0c6c8, 27a6c5eb, 2cb6924c, 331aece5, 72877db5, b7f8fcd4, bc9c8f8d,
dcb89b6b, ee9335fb, f5a297c9) — the decisive mistake is unlabelled or rated LOW/MEDIUM.

**3.6 SWE-bench.** 31 traces, 27 HIGH in total; primary impact is HIGH in only 11; 17/31 traces carry the same MEDIUM "Context Handling
Failures" label on the `FinalAnswerTool` span ("the model didn't provide the final answer, as it stops on the tool call") — the tool span
*is* the patch submission; this is one annotator's misreading repeated 17 times. Other SWE labels are overwhelmingly "printed more than 500
characters" Instruction Non-compliance (MEDIUM) and directory-tree Formatting (LOW).

**3.7 Prefix probe (local detectability; 12 traces ≤60 spans, window ±6 LLM spans, 62 calls, `results/trail/prefix_probe.jsonl`).**
Gold step flagged as a mistake when seen without the future: **4/12 (33%)**; earliest flagged = gold 2/12; flag rate on steps *before*
the gold 4/23 (17%) vs *after* it 15/28 (**54%**). The 4 detections are fabrications / print-instead-of-call steps (1dd91d38/8 "only
prints the search_agent task string", b5576ffc/8 "fabricates a file inspection", cac8b6b2/27, 75121379/6). All 4 SWE golds (LOW/MEDIUM
Formatting on exploratory steps) are rated "reasonable exploratory attempt". In the two *correct-ending* memory runs the monitor rates the
gold step as fine ("the final answer 12 correctly counts…", "'diamond' matches the required compound") — it reads the leaked `true_answer`
in step 2, so even the prefix monitor is outcome-informed on TRAIL-GAIA.

## 4. Baseline error analysis

**4.1 All-at-once std (Qwen3.8-27B, n=40: 35 GAIA / 5 SWE, gold = primary HIGH span, `results/trail/all_at_once_std.jsonl`).**
agent 85.0% (trivial: 1–2 agents), step exact **27.5%**, within-3 42.5%, in the full error-span set 40.0%; 11–30 spans: 38.5% exact,
>30 spans: 7.1%. Signed offset: 16 later, 13 earlier, 11 exact — no net late bias (mean relative position pred 0.68 vs gold 0.58).
Joined with trace type (`results/trail/std_join.txt`):

| trace type | n | exact | earlier | later |
|---|---|---|---|---|
| memory answer (no tool; incl. 5 SWE) | 23 | 9 | 7 | 7 |
| search_agent used | 14 | 1 | 5 | 8 |
| tools, no search_agent | 3 | 1 | 1 | 1 |

Categories of the 29 misses:
- *earlier, plausible-but-not-decisive* (7 GAIA memory runs): the model blames the facts survey (step 5) or the plan (step 6) because they
  already contain the wrong assumption (75121379: "the survey prematurely associated Metamorphosis with Demon Hunter"; b7f8fcd4 step 5
  grammatical-role error) — the gold is the action step 8 that answers without tools. For b7f8fcd4 the gold is a LOW `<end_plan>` label
  (wrong run with no HIGH error), so the model's step is the better label.
- *earlier = the model finds the unlabelled root* (search_agent runs): 2c77a8fe pred 8 (the unlabelled print-instead-of-call step; gold 18 is
  the fabrication), 3205fa0c pred 8 vs gold 35, 6cc6dc35 pred 7/8 ("CodeAgent formulated the wrong task for search_agent", gold 83 = a
  MEDIUM page_down formatting error 75 spans later), a99faf78 pred 8 vs gold 19 (a *correct-ending* run).
- *later = symptom, by choice* (8 search_agent runs + 2 memory): the model explicitly rejects the recovered tool-argument errors and blames
  the manager's fabrication / final decision: 860f9d45 (gold 82 = HIGH page_down Formatting; pred 160 "accepted the unverified 1981"),
  c60ad860 (gold 19 Formatting; pred 69), 396b6aa1 (gold 36 Formatting; pred 72 — the run is correct), 41bbc898 ("instead of trying the
  full path, it fabricated page numbers", gold = MEDIUM plan non-compliance at 8), d9a8dff7 (gold 8 = print-instead-of-call; pred 12 "assumed
  plausible values" — its reasoning names step 8 and discards it: "if step 8 had been done correctly the search_agent would have found…
  the hallucination is what directly produced the wrong answer"), 0242ca25 (same pattern, pred 12 vs gold 8).
- *SWE* (5): gold 6–18 are LOW/MEDIUM "printed the tree" / "printed >500 chars" labels; the model picks the wrong-fix decision at 24–36
  (af1931b7: "suppress the safety check rather than fix the parser"; 0e6f7928: "identified the root cause in schema.py but patched
  fields.py"). The model's step is a causal diagnosis of the patch; the gold is a style label. 0/5 exact, 1/5 in set.
- *ill-posed*: 9 of the 40 sampled runs end with the correct answer (dbc070b9, 7bf0addd exact; 0adc4f3b, 33cedc57, a99faf78, aa76e85e,
  2c77a8fe, 396b6aa1, 62df2a06 missed) while the prompt asserts the system FAILED; the model obliges and invents a failure.

Successes (9/11 exact are memory-answer runs): the model's reason is always the same sentence — "abandoned its plan and answered from
memory/hallucinated without calling search_agent" (4ae16319, dbc070b9, 6e64c2e5, 9e67afe0). It wins because gold = step 8 in all 37 memory
runs: a structural prior reproduces these 9 hits (first-action prior 40.4% on GAIA vs the model's 31.4%). The two non-trivial successes:
cac8b6b2 (Tool Output Misinterpretation at 27, the search_agent's reading of a page) and 7bf0addd (Environment Setup at 8).

What the model reads: it uses the leaked/explicit ground truth to decide *which* claim is wrong (6e64c2e5: "the ground truth says 8 …
so the person ended up at Shaw-Howard"); it reasons about harness artefacts ("step 4 is the CodeAgent.run wrapper", "is step 7 a
chain that executed a snippet?") in 3 of 13 excerpts; and it applies a counterfactual rule ("had step 8 been done correctly…") that
systematically prefers the *last fabrication* over an *earlier recovered* error — the opposite of TRAIL's earliest-HIGH convention.

**4.2 Inventory variant (same 40 traces; list every mistake, then the decisive one; `results/trail/inventory_match.txt`).**
Decisive step: exact 27.5% (same as std), within-3 50.0%, offset 18 earlier / 11 later / 11 exact — listing all mistakes first shifts the
decisive choice *earlier* (std: 13 earlier / 16 later). The model lists 4.0 mistake steps per trace (gold 3.6 error spans); 75/159 hit a
gold span (±1), 84 do not (43 before / 41 after the primary). The primary HIGH span is in the predicted set in 27/40 traces but chosen as
decisive in 11 — the model *sees* the labelled step and prefers another one.

Recall of gold errors by impact: **HIGH 73% (70/96), MEDIUM 39%, LOW 32%**; by span kind LLM 55%, TOOL 35%. By category: Language-only
92%, Tool Selection 88%, Incorrect Problem Identification 80%, Goal Deviation 79%, Tool-related 73%, Task Orchestration 67%, Tool Output
Misinterpretation 56%; **Formatting 40%, Instruction Non-compliance 30%, Context Handling 29%, Poor Information Retrieval 25%, Resource
Abuse 11%**. With full observability the model still misses (i) compliance/format labels (missing `<end_plan>`, ">500 chars printed",
malformed `page_down` args — it often lists only the first of a repeated series: dcb89b6b "causing repeated tool errors (steps 27-45)"),
(ii) Resource Abuse (defined over several spans), (iii) Poor Information Retrieval on search queries whose outcome is only visible
two spans later.

The 84 unmatched predictions are not noise: 20 are the facts/plan steps 5–6/10–11 ("prematurely suggests 'negative binomial' before any
research"), 5 are the unlabelled print-instead-of-call steps (672d36d8 8/10/12, 3205fa0c 13), 13 are non-LLM spans (final_answer tool or
the framework's step 2 — 0adc4f3b: "passed the example containing true_answer '100' into the answering pipeline": the model noticed the
leak), 46 are other LLM steps (irrelevant page visits, repeated bad `page_down` calls that the annotators did not label either,
confirmation-bias searches). I.e. the model's inventory is a plausible second annotator with a different convention (earlier, more
process-focused), not a degraded copy of the gold.

## 5. Annotation issues (prevalence estimates)

1. **Hindsight/outcome leak**: gold answer visible in step 2 of 117/117 GAIA traces; correct runs get fewer HIGH labels (32% vs 12% zero-HIGH)
   and +0.4 overall score, yet 68% of correct runs still carry a HIGH error. Annotators labelled *process compliance* with the outcome known.
2. **Repeated-instance labelling**: 30% of errors are repeats; the guideline "mark the first instance" was applied inconsistently
   (14be0e98: first 6 occurrences unlabelled, last 4 labelled HIGH; 0140b3f6: all 5 labelled HIGH).
3. **Template noise**: 47 `<end_plan>` labels (5.6% of all errors, 27% of LOW) on a tag o3-mini never produces; 40% of traces.
4. **Symptom-located labels**: in ≥3 of 11 read GAIA traces (041b7f9c, 2c77a8fe, 3acaa315) the earliest HIGH is the fabricated final
   answer while the unlabelled or MEDIUM-rated root is 2–16 spans earlier; 46/117 GAIA primaries are in the last 3 spans.
5. **Unlabelled identical mistakes**: 10/28 print-instead-of-call occurrences, 8/13 no-visit final answers; 10/83 wrong runs with no HIGH.
6. **SWE FinalAnswerTool artefact**: 17/31 traces.
7. **Span-location convention**: the same malformed `page_down` call is placed on the LLM span in some traces and on the TOOL span
   (Resource Abuse / Tool-related, 25 cases on `PageDownTool`) in others; TOOL-span evidence is visible in the tool span in 12/95 cases.
8. Category spelling variants (31) and HIGH/MEDIUM inconsistency for the same mistake (page_down: HIGH in 0140b3f6/14be0e98, MEDIUM in 01c57271).

## 6. Candidate hypotheses

**H1. TRAIL labels are process-compliance annotations, not causal attributions; the "earliest HIGH" primary is an outcome-neutral
structural mark.** Evidence: 68% of correct-ending GAIA runs carry ≥1 HIGH; P(correct | Formatting / Instruction / Orchestration error)
equals the base rate; the first-action prior hits the primary 40% exactly (random 14%); 37/117 GAIA runs are memory answers with
primary = step 8 whether right (10) or wrong (27). Test: re-score every attributor against (a) primary, (b) earliest error span,
(c) a counterfactual label from re-running the run with the primary span fixed (replayable: smolagents + o3-mini); predict that
(a) and (c) agree in < 40% of GAIA traces. Shared with: SWE labels in TRAIL, AgentErrorBench/MAST style taxonomies (G4), and any
"all errors" multi-label set. Targeted method: train the attributor on error *presence* (multi-label span detection) and use outcome +
a replay/counterfactual to pick the decisive one; do not train "decisive" on these labels.

**H2. Recovered errors carry HIGH labels: the primary is a *recovered* tool-argument bug in a large share of search-agent runs.**
Evidence: primary = Formatting in 12 GAIA runs, 7 of them correct-ending; 0140b3f6 / 14be0e98 / 860f9d45 / c60ad860 / 396b6aa1 all have
primary = malformed `page_down` that the agent worked around (find_on_page) before the real loss of progress; the LLM baseline rejects
these in 8/14 search-agent runs and blames the later fabrication. Test: for each primary, check whether a later TOOL span of the same
agent succeeds on the same goal (recovery marker); predict ≥ 40% of HIGH Formatting primaries are recovered. Shared with: AgentRx
(recovered events), FaP PASS error events. Targeted method: a recovery detector (same tool, later success) that demotes a candidate
cause; attribution should look for the *first unrecovered* error, which in TRAIL is 2–50 spans later than the primary.

**H3. Downstream contamination is real on TRAIL and is where the attributor and the annotators disagree in opposite directions.**
Evidence: prefix probe flags 54% of post-gold LLM steps vs 17% pre-gold; the all-at-once model's counterfactual rule ("had step k
been done right…") picks the *last fabrication* in 8 search-agent runs while gold is the earliest HIGH; conversely in memory runs the
model goes *earlier* (facts/plan steps 5–6, 7 cases) because the wrong assumption is already in the plan. Net signed offset ≈ 0
(16 later / 13 earlier), so TRAIL does not show a uniform late bias; it shows a convention mismatch in both directions. Test: score
with three gold conventions (earliest error, earliest HIGH, last fabrication) and report per-convention accuracy; predict the model's
"last fabrication" accuracy > 60% on wrong-ending search-agent runs. Shared with: Who&When/TraceElephant (earliest-decisive) vs
AgentRx (first unrecovered). Targeted method: output a *chain* (root → propagation → symptom) rather than a step, and let the metric
pick the convention.

**H4. The loud symptom is two spans downstream of the LLM span that caused it and in another agent's turn.** Evidence: tool failure
text lives in the next LLM span's input (788 LLM spans, 0 TOOL spans); annotator evidence found at +2/+3 in 35 cases; TOOL-span evidence
visible in the tool span in 12/95; in 2-agent runs the manager's final LLM (10–40 spans later) restates the sub-agent's failure as a
confident answer. Test: per-step scorer with vs without the k+2 observation attached to step k; predict local detectability of
Formatting / Poor-Retrieval primaries rises from ~0 to > 50% when the observation is attached. Shared with: TraceElephant (tool
observations rendered on the calling step by the loader), SearchAuditBench (tool returns as separate messages). Targeted method:
"observation-attached" step units: fold each tool return into the LLM span that issued the call before scoring (the G2 traceelephant
loader already does this; TRAIL's loader does not).

**H5. Label fabrication tracks outcome knowledge even though the label text never mentions it.** Evidence: gold answer visible in step 2
of all 117 GAIA traces; wrong runs have 2.2× the share of HIGH-bearing traces (88% vs 68%), −0.4 overall score, −0.7 reliability; the
same unlabelled process (search_agent answering with zero page visits) is labelled in 5/13 runs, all 3 correct ones unlabelled; only 1/839
error texts mentions "wrong answer". Test (Caplan design): re-annotate 40 GAIA traces with step 2 and the final answer masked;
predict HIGH counts converge (correct-run HIGH rate rises) and the 10 wrong-no-HIGH traces gain a HIGH. Shared with: every drafted
dataset (P3), TraceElephant (ground truth in metadata). Targeted method: when training on TRAIL, drop step 0–3 and the final
framework LLM span from the input, or the model learns to read the leak (the inventory model already flagged it in 0adc4f3b).

**H6. Repeated-instance labels inflate HIGH counts and make set-valued metrics reward symptom listing.** Evidence: 30% of errors repeat a
(category, impact) in the same trace; 5–7 identical `page_down` HIGH labels per trace; inventory recall of HIGH is 73% but Resource
Abuse 11% because it is defined over a series. Test: collapse consecutive identical (category, agent, tool) errors to the first
instance and recompute Joint accuracy of the paper's judges; predict Location accuracy rises for every judge. Targeted method: score
runs of identical mistakes as one event with a span; attribute to the first.

**H7. Infeasible-tool tasks produce "final guess" labels that no trajectory-only attributor can predict.** Evidence: 3acaa315 (video
question, no video tool: four "No results" searches rated MEDIUM, the guess rated HIGH), 41bbc898 (audio file path unavailable:
fabricated page numbers), a32806e1; 46/117 primaries are the manager's final LLM call. Test: tag tasks whose required modality is not
covered by the tool set (video/audio/archived page); predict primary = final step in > 80% of them and attributor exact accuracy
≈ last-step prior there. Shared with: SearchAuditBench Unsupported Answer (critical = final answer 17%). Targeted method: a
"doomed-at-step-0" / infeasibility atom in the attributor (cf. cure models), so the answer is "no recoverable step" rather than a step.

## 7. Open questions

- Which of the 34 correct-ending runs would the GAIA scorer accept? 11 answer in the verbose "### 1. Task outcome" template that the final
  framework LLM then compresses — is the *framework's* FINAL ANSWER (step n−1) the scored output, and should it be a step at all?
- SWE-bench has no outcome: the 31 traces' FAIL_TO_PASS lists are in step 0 (`process_item` args) — running the tests on the submitted
  patch would give a true outcome and a decisive-step convention for the 20 traces whose labels are all LOW/MEDIUM.
- Are the 58 "earlier LOW/MEDIUM then HIGH" traces really two events, or one event whose severity annotators escalated after seeing
  repeats (14be0e98: unlabelled → HIGH on the 7th repeat)?
- Does the 54% post-gold flag rate come from the probe reading the leaked answer (the correct-ending runs show it does), i.e. is P1 on
  TRAIL partly an artefact of the step-2 leak? Re-run the probe with steps 0–3 removed.
- Is the inventory model's "earlier" convention (plan/facts step) closer to AgentErrata's "earliest detectable" or to nothing — a
  third annotator pass on 20 traces would settle whether the 84 unmatched predictions are misses or alternative truths.

## P1–P8 on TRAIL (numbers)

- P1 downstream contamination: **confirmed** for the prefix monitor (post-gold flag rate 54% vs 17% pre-gold, n=12) and for the
  all-at-once judge on search-agent runs (8/14 later, median +22 spans); **not** a net late bias overall (16 later / 13 earlier / 11 exact).
- P2 convention gap: **confirmed** — primary (earliest HIGH) ≠ earliest span in 58/144 (median 5, max 47); model's implicit convention
  (last fabrication / first wrong assumption) disagrees with both.
- P3 anchoring on outcome: **confirmed in aggregate** (gold leaked in 117/117; HIGH-bearing 88% wrong vs 68% correct; score −0.4), refuted
  at the text level (1/839 descriptions mention the wrong answer).
- P4 outcome-only judging: the std judge is told "FAILED" and invents a failure in 9/40 correct runs — **confirmed**.
- P5 length: exact 38.5% (11–30 spans) → 7.1% (>30 spans) — **confirmed**.
- P6 successes contain errors: **confirmed strongly** — 31/34 correct GAIA runs have ≥1 error, 23/34 ≥1 HIGH, mean 4.3 errors.
- P7 absorption by type: **confirmed** — Formatting / Instruction / Orchestration errors are outcome-neutral (P(correct)=0.28–0.29 vs
  base 0.29); Poor Information Retrieval (0.13), Tool-related hallucination (0.17), Goal Deviation (0.18) cascade.
- P8 verification theatre / false success: 46/117 primaries are the final manager call; fabricated "I have verified…" claims in
  2c77a8fe, 041b7f9c, 6cc6dc35, 3acaa315 — **confirmed** as the dominant late symptom; 37 memory-answer runs are the extreme case.
