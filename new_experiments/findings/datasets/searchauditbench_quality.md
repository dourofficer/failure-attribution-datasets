# SearchAuditBench: label-quality audit (2026-11-02)

Sources: the raw JSONL (`data/searchauditbench/extracted/benchmark_data_1243.jsonl`) and the survey report section
(`report/6_related/searchauditbench/searchauditbench.tex`) only. No LLM calls. Scripts: `inspect/sab_quality/`
(run `load.py` first). Record ids below are the dataset's `index` field.

## Verdict

Structurally clean and useful for step localisation with the tolerance span. Not a high-quality gold for root cause.
Treat CS-Loose as the primary signal and RC-Acc, Diag and FPS as noisy. Filter the subsets in §3 before using it as
attribution ground truth.

## 1. What holds up

| check | result |
|---|---|
| critical step is an assistant message inside its span | 1243/1243 |
| message_index matches position; no duplicate (query, model) | yes |
| first message number cited in the rationale equals the label | 1218/1219 (24 cite none) |
| gold string inside repair directive / rubrics | 0 / 1, so repair grading does not need the answer |
| prediction contains the gold string | 73; the ones read name the gold as a rejected or extra candidate, not evaluator false negatives |
| final answer already stated as `<answer>` before the labelled span | 12/298 checkable runs (e.g. 324: XH558 at msg 6, label 14) |
| last-assistant-step baseline | CS-Strict 16.9%, CS-Loose 31.1% (paper: All-at-Once 47.1, SearchAuditor 54.8 CS-Loose) |
| majority root cause | 27.2% |

## 2. Problems

1. **Root cause is not separable at category boundaries.** 198 queries were failed by two or more models; 136 of
   them get different root causes. Where the rationales describe one mechanism, the labels still differ:
   - YouTube Music 2018 (gold 4; 1038, 901, 1086, 959): all four rationales say "used the combined 17-country rollout
     instead of the initial row" and get Candidate Mismanagement ×2, Entity–Relation Misbinding, Constraint Neglect.
   - Latest-eruption query (629, 548, 213): all say "did not resolve the later eruption"; Search Coverage Gap ×2,
     Candidate Mismanagement ×1.
   One annotator per case, no agreement reported, so the RC ceiling is unknown and well below 100%.
2. **Text fields are templated and look LLM-drafted.** 783 rationales open "Message N is the", 348 open "The earliest
   decisive error"; 80% are 74–106 words; 95% of 5,437 rubrics open "A valid"; 75% of directives open "Return to".
   23 rationales carry revision notes ("Message 6 remains the critical step, but the span should be narrowed", 1049).
   The pre-screen is Claude Opus 4.6 and the paper's main auditor backbone is Claude Opus 4.8: anchoring on the
   pre-screen would favour that family.
3. **Ambiguous golds are kept and the agent's reading is labelled the error.** The rationale reconstructs the gold's
   interpretation from hindsight; an auditor without the gold cannot recover it.
   - 42 (presidents, gold 2): "The prompt could instead require…", labelled Candidate Mismanagement.
   - 992 / 313 / 634 (《攀高枝》 ch. 9, gold 王神医): three models answer 陈宝香; "The prompt did not explicitly
     restrict counting…", labelled Entity–Relation Misbinding.
   - Ballon d'Or (80, 454, 724, 645, 392): Lewandowski 2021 vs Mané 2022 is an affiliation-timing reading.
   - Heaviest animals > 60 t (gold 6): four of five models answer 7 (sperm whale borderline).
   Interpretation language appears in 115 rationales (9.3%), 36/217 in SEALQA; an upper bound, not all are gold issues.
4. **Failure regimes outside the six-way taxonomy are forced into it.**
   - Tool misuse: DeepSeek-V4-Pro passed the query list as a string 1,602 times; 37.6% return "No results found" vs
     2.6% for real lists. 27 runs have ≥50% empty searches (e.g. 757, labelled Search Coverage Gap at msg 38).
   - Degeneration: 48 runs end with ≥30% repeated 4-grams in the final reasoning or answer (647, 566, 337 answer with
     repeated `</think>`); 134 collapses into "We… Okay… We" and fabricates data, labelled at an early reasonable search.
   - Budget exhaustion: 103 runs were forced to answer ("FINAL ANSWER MODE"), 92 of 160 OpenSeeker runs; the critical
     step sits a median 94 messages before the cut.
5. **Time-relative questions.** Runs are dated 2026-06-14…24; 166 queries (13%) use "latest / most recent / currently"
   wording (e.g. YouTube videos over 7 B views, gold 5). Drift risk, not verified per item.

## 3. Suggested filters

Drop or report separately: forced-final runs (103), degenerate endings (48), runs with ≥50% empty searches (27),
interpretation-dependent items after manual review (≤115). Score RC with a confusion-tolerant metric or not at all.

## 4. Report correction

The report says several models reason in Chinese "even on English benchmarks". The data shows 0.0–0.1% Chinese
reasoning on English queries for every model; Chinese reasoning occurs only on Chinese queries (DeepSeek 99.7%,
OpenSeeker 99.7%, Kimi 85.7%, Tongyi 76.9%, Qwen 62.6%, Quest 30.1%, GLM 6.2%, OpenResearcher 2.7%).
