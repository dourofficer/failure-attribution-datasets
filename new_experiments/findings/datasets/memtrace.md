# MemTrace — spot-check notes (G2, 2026-11-01)

Scripts: `inspect/memtrace_dump.py` (listing + condensed reads), `inspect/memtrace_opstats.py` (gold op among same-name ops,
evermemos reads), `inspect/memtrace_evidence_loss.py` (evidence words through inputs/outputs). Outputs in `results/memtrace/`
(`list.tsv`, `opstats.json`, `evidence_loss.json`, `reads/`).

## 1. Data as loaded

- 160 records (40 per system), 128,774 steps; a step is an operation in the backward dependency slice of the prediction node,
  chronological. Slice median: mem0 107, rag 500, evermemos 1,505, long_context 497 ops. Faulty op inside the slice in 140/160
  (misses: 17 mem0 — 13 Extraction + 4 Update, 1 evermemos, 2 long_context).
- **Loader caveat found while reading**: the slice is polluted by *other queries'* retrieval operations. Memory-entry nodes are
  shared output nodes of every `search_vector_store` / `agentic_*` op in the conversation, so the backward walk from one prediction
  pulls in the retrieval ops of all sibling queries (mem0 locomo-qa-1-14: steps 22–119 are 98 `search_vector_store` ops, step 33 is the
  search for `locomo-qa-1-1`; evermemos locomo-qa-1-10: 124 `agentic_final_rerank` ops in the slice, step 961 is round-1 for
  `locomo-qa-1-11`). For single-query graphs (longmemeval, realmem) the slice is clean. Not fixed here (shared loader); any attributor
  run on these slices gets ~100 decoy retrieval ops whose input query differs from the target query, which is trivially filterable.
- Gold op names: mem0 `search_vector_store` 14 / `update_memory_decision` 4 / `extract_facts` 4 / QA 1 (of 23 in-slice); rag
  `retrieve` 37 / QA 3; evermemos `agentic_final_rerank` 22 / QA 14 / `agentic_round2_bundle` 3; long_context `memory_update` 22 / QA 16.

## 2. Close-reading notes (8 records)

| id | type | slice / gold | what happened | verdict |
|---|---|---|---|---|
| mem0 locomo-1 qa-1-14 | Retrieval | 120 / 32 | the store holds "thinking of working with trans people... counseling" memories; top-10 search for "career path" returns art/mentoring memories; answer says art | agree; the faulty op is the one search op whose input is this query |
| mem0 locomo-1 qa-1-55 | Update | 114 / 17 | `update_memory_decision` on 2023-10-13 emits event UPDATE with *identical* text for "Created a self-portrait last week" (old_memory == text); mem0 rewrites the timestamp to 2023-10-13; the later answer dates the portrait to October | agree; mechanism is a **no-op UPDATE that bumps the timestamp** (system bug, not an LLM error); visible in the step only if one knows the semantics of UPDATE |
| mem0 longmemeval c9f37c46 | Response | 12 / 11 | retrieval returns both facts ("3 months ago" as of 05-20, "open mic last month"); QA fails the temporal subtraction | agree; gold = last step |
| mem0 locomo-1 qa-1-36 | Update (out of slice) | 144 / none | the 07-17 memory "went camping two weekends ago" is overwritten on 09-13 by "went camping with the kids a few weeks ago"; the prediction uses a different memory, so the overwriting op has no edge to the prediction | label is right but **unreachable by backward tracing** |
| rag longmemeval 60159905 | Retrieval | 380 / 378 | 378 `message_buffer_update` ops, one `retrieve` (gold), one QA; retrieved chunks miss the two dinner-party messages; the QA says "no information" | agree; localisation trivial, typing (Retrieval vs Response) needs evidence-vs-retrieved comparison |
| long_context realmem Adeleke a9706c77 | Update (out of slice) | 274 / none | a `memory_update` (context-window maintenance) dropped the message that fixed the license type; the model restarts the workflow at a different step | label right; the op that *deleted* the evidence leaves no dependency edge |
| evermemos locomo-1 qa-1-10 | Retrieval | 1,380 / 960 | round-1 and round-2 both return the right episode; `agentic_final_rerank` drops it from the top-10; answer uses a later picnic | agree; the gold is the last of a 3-op retrieval pipeline, and the decisive information (candidate present in inputs, absent in outputs) is *visible in the gold step* |
| evermemos locomo-1 qa-1-143 | Response | 1,389 / 1,388 | the right episode is in the QA input; the answer is a generic summary | agree; gold = last step |

## 3. Targeted statistics

**3a. Localisation reduces to op-type lookup for Retrieval/Response errors.** The gold op is the only op of its name in the
slice in rag 24/40, evermemos 22/39 (single-query graphs), and steps after gold are median 1 (rag) / 36 (mem0) / 90 (evermemos).
For Response errors the gold is always the final `question-answering` op (34/34). For Retrieval errors the gold op has the target
query as an input (rag 40/40; mem0 14/14 in-slice retrievals; evermemos 17/25 — the other 8 are rerank/bundle ops whose inputs are
candidate ids, not the query). So for 110/160 cases the step is determined by (error type, query id); the attribution problem is
*typing*, i.e. deciding whether the evidence was in the store (Retrieval) or in the QA context (Response).

**3b. Update/Extraction errors are the hard half and the slice hides them.** long_context Update errors: gold `memory_update` is one
of median 459 identically named ops, median 180 ops before the prediction; the op is the one whose output window no longer contains
the evidence message — detectable only by tracking the evidence forward. mem0 Extraction errors: 13/14 are outside the slice
(the fact never became a memory unit: no edge). Across systems 20/160 gold ops have no dependency path to the prediction.

**3c. Evidence is paraphrased out of string reach.** ≥50% of the evidence's content words appear in some op *output* in rag 40/40
and evermemos 40/40 (verbatim chunks / episodes) but only 5/40 in mem0 (facts are rewritten) and 35/40 in long_context. A
string-matching tracer works for chunk-based systems and fails for extractive ones; a semantic tracer is needed for mem0.

**3d. Position prior.** Relative position of the gold op in the slice: median 0.90 overall (report); by type, Response = 1.0 by
construction, Retrieval ≈ 0.85–1.0 (rag), Update/Extraction early-to-mid (mem0 0.09–0.73). "Blame the last op" is right for 34/140
in-slice cases; "blame the last query-bearing retrieval op" for a further ~70.

## 4. Baseline error analysis

(`results/memtrace/all_at_once_std.jsonl`, n=30, running; filled when finished.)

## 5. Annotation issues

- Labels are consistent with the reasons in all 8 read cases; the released `reason` texts are long, specific and name the op id.
- The benchmark's own filtering (Annotation-Error / Judge-Error classes, 78 of 238 annotations) is the main label-quality step; two
  of the eight read cases have gold answers that are themselves fuzzy ("two weekends before 17 July", "an ongoing adventure of
  learning and growing") so the Response-error class partly measures judge strictness (P4), not memory faults.
- mem0 Update errors are a *system bug* (no-op UPDATE resets timestamps; 3 of the 7 mem0 Update cases read/listed show this
  pattern) rather than a decision error; attributing them to "the update op" is right but the fix is in the system code.

## 6. Candidate hypotheses

- **H-MT1 "Omission errors have no backward trace"**: any attributor that walks producer→consumer edges backward from the failed
  output (MemTrace's own method, SOAP/EMFA-style tracing, our slice) cannot reach deletion/overwrite/extraction-miss ops; 20/160 here,
  and the long_context Update class (24) is reachable only nominally (the op is in the slice but is indistinguishable from 458
  siblings). A targeted method must trace the *expected* flow forward from the evidence (gold or retrieved) and report the first op
  whose output no longer carries it. Test: implement the forward tracer (string for rag/long_context/evermemos, embedding for mem0)
  and score OIA on the 50 Update+Extraction cases vs MemTrace-OBS (35–55%). Shares the mechanism with LongRCA hand-off omissions and
  TRAIL "Poor Information Retrieval" spans, and with TraceElephant "seen-but-dropped answers" (H-TE5).
- **H-MT2 "Localisation is free, typing is the task"**: for Retrieval/Response errors the op is fixed by the query id and error type;
  OIA differences between methods on these classes measure error typing, not localisation. Test: recompute OIA conditioned on ETA
  correctness; expect OIA|ETA-correct ≈ 100% for rag/evermemos single-query graphs.
- **H-MT3 "Slice pollution as a decoy test"**: the sibling-query retrieval ops in multi-query graphs are a natural distractor set; an
  attributor that blames a retrieval op for the wrong query is making a pure attention error. Cheap to measure on our baseline output.

## 7. Open questions

- Is the no-op-UPDATE timestamp bump (qa-1-55) the mechanism behind most mem0 Update errors (7) and some long_context ones? Needs a
  pass over all update-gold ops comparing old/new text and timestamps.
- Whether MemTrace-OBS's 46.3% OIA is dominated by the trivial classes (3a) — the paper's per-system table (RAG 87.5, LongCtx 7.5) says yes.


## 4b. Baseline results (filled from results/memtrace/ after the rerun, 2026-11-01)

Qwen3.8-27B all-at-once, gold = final_op_id inside the prediction slice; first attempt exceeded the 200k context on the longest records, rerun with
`--budget-tokens 110000` (records that still overflow are rows with `error` set). Reasoning excerpts in
`results/memtrace/all_at_once_std_analysis.md`.

| subset | n | agent_ok | step_exact | step_within_3 | step_in_set |
|---|---|---|---|---|---|
| rag | 9 | 0.0 | 22.2 | 44.4 | 22.2 |
| mem0 | 7 | 14.3 | 57.1 | 57.1 | 57.1 |
| long_context | 10 | 0.0 | 20.0 | 30.0 | 20.0 |
| evermemos | 4 | 0.0 | 25.0 | 25.0 | 25.0 |
| ALL | 30 | 3.3 | 30.0 | 40.0 | 30.0 |

categories: {'later(+1..3)': 2, 'earlier(<-3)': 6, 'later(>3)': 9, 'exact': 9, 'parse_fail': 3, 'earlier(-1..3)': 1}
agent right but step wrong: 0; step right but agent wrong: 8
| n_steps | n | step_exact% | within3% | agent% |
|---|---|---|---|---|
| 0-10 | 0 | 0.0 | 0.0 | 0.0 |
| 11-30 | 1 | 100.0 | 100.0 | 0.0 |
| 31-1000 | 24 | 29.2 | 41.7 | 4.2 |
wrote results/memtrace/all_at_once_std_analysis.md
