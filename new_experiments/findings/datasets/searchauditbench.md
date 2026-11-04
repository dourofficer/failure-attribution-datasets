# SearchAuditBench — inspection notes (G2, Nov 2026)

Scripts: `inspect/searchauditbench_index.py` (per-record index -> `results/searchauditbench/index.jsonl`),
`inspect/searchauditbench_echo.py` (query-echo pollution, empty-return fatigue, rationale references -> `echo.jsonl`),
`inspect/searchauditbench_goldctx.py` (where the gold answer appears in tool returns), `inspect/searchauditbench_retract.py`
(LLM probe: does the agent later retract the labelled decision / was the mechanism present earlier -> `retract.jsonl`),
`inspect/searchauditbench_baseline_by_rc.py` (baseline joined with the index). Close-reading dumps are in
`results/searchauditbench/reads/<id>.txt` (made with `inspect/g2_dump.py`).

## 1. Data as loaded

- 1,243 records, one per failed run; steps = messages (system, user, assistant, tool). `error_step()` = `extra.critical_idx`
  (always an assistant message); `error_steps` = critical + the other messages of the tolerance span (sorted).
  Agent is always `assistant`, so agent accuracy is meaningless here (100% by construction).
- Per record (index): 73.1 messages mean / 43 median; 34.3 assistant decisions mean / 20 median. Critical step is the
  **final answer in 210/1,243 (16.9%)**; it carries a `search` call in 715, a `visit` call in 317, none in 210 (the final
  answers) and one `download`.
- Root causes: Candidate Mismanagement 338, Search Coverage Gap 284, Constraint Neglect 238, Unverified Source Reliance 205,
  Entity–Relation Misbinding 141, Unsupported Answer 37. Models: GLM-5.2 175, Kimi-K2.6 164, OpenSeeker 160,
  OpenResearcher 159, DeepSeek-V4-Pro 158, Quest-35B 156, Tongyi-DR-30B 146, Qwen3.5-397B 125.
- Generating models differ enormously in length and in where the label sits: Qwen3.5-397B and Tongyi-DR answer after a
  median of 6 decisions and have the label on the final answer in 30% / 39% of their runs; OpenSeeker runs a median of 73
  decisions and DeepSeek-V4-Pro 38, with the final answer labelled in only 14% / 4%. "Position of the critical step" is
  therefore mostly a property of the generating model, not of the failure.
- Loader caveats: none found. `native_step == idx` everywhere. The gold answer is in `ground_truth` (hidden from the
  auditor in the official protocol; the baseline here is run with `--no-gt`).

## 2. Close-reading notes

Fourteen trajectories read end to end (ids are the `index` field). Verdict = do I agree with the labelled critical step.

| id | model / source / rc | n msgs, k | what happened | verdict |
|---|---|---|---|---|
| 953 | Kimi-K2.6, SEALQA, Candidate Mismgmt | 13, k=8 (span 8–12) | Oppenheimer's first Best-Film win. Step 7 surfaces Atlanta FCC (8 Dec 2023); step 8 reasons "the question uses the word *ceremony*, which implies a televised event" and narrows to the Golden Globes; the same narrowing was already voiced at step 4, *before* the regional wins were visible. Gold (St Louis FCA) never appears in any tool return. | Agree with 8 as *commit* step; but the mechanism first appears at 4. The annotator anchors the label on the first decision made *after* the disconfirming evidence is in context, not on the first occurrence of the wrong framing. The agent writes "I'm not entirely sure" at k. |
| 221 | GLM-5.2, DeepSearchQA, Unverified Source | 11, k=10 (final) | Census QuickFacts: the agent visits census.gov for all five counties and reads Barrow County poverty 8.6% (gold list includes Barrow, i.e. the page said >9% when the question was written). The agent did exactly what the query asked. | **Disagree: not an agent error.** The gold is stale (QuickFacts vintage changed). The rationale rationalises it as "accepts a near-threshold value without checking the vintage". Not auditable from the trajectory. |
| 392 | GLM-5.2, SEALQA, Entity–Relation | 15, k=14 (final) | Last Bayern player in Ballon d'Or top 3. Tool return 13 lists "2, Sadio Mane" (2022) without a club; the final table writes "Mané" with no club and concludes Lewandowski 2021. | Agree. The error is created at the final message, but it needs world knowledge (Mané was at Bayern in Oct 2022) — not decidable from the trajectory alone; an auditor can only flag "club of Mané unverified". |
| 405 | Qwen3.5-397B, BrowseComp, Search Coverage Gap | 11, k=10 (final) | Four searches, no candidate author found; step 8 is a 10 k-char loop of "let's search…"; final message is `<answer>Carlos</answer>` with zero evidence. | Agree with k; the category should be Unsupported Answer (the rationale itself says "unsupported by the observed evidence"). Fabrication is decidable from the trajectory. |
| 261 | Tongyi-DR-30B, BrowseComp-ZH, Unverified Source | 9, k=8 (final) | Four-heroine business-sim game. Three searches return mostly Instagram "popular/<query>" tag pages (query echo); one snippet mentions 《太太！我喜欢你！》 as a 同人女 business sim; the agent answers it without a visit. | Agree. Decidable from the trajectory (no visit, snippet-only). The answer string first appears in tool return 7. |
| 299 | Qwen3.5-397B, DeepSearchQA, Unverified Source | 13, k=4 (span 4–5) | Guardian medicine top-20 "2024": step 4 visits the **2025/26** league-table URL while instructing the tool to treat it as 2024. **Step 9 notices** ("actually showed the 2025 rankings, not 2024"), visits the 2024 overall page (no subject data), then at step 12 silently falls back on the 2025 list. | Agree that 4 is the earliest; the *decisive* step is 12 where the agent, aware of the mismatch, re-commits. Earliest-vs-decisive (P2) in one trajectory. Also partly a source-availability problem (the 2024 subject table was never reachable). |
| 377 | Tongyi-DR-30B, BrowseComp, Entity–Relation | 17, k=2 (span 2–3) | Author-bibliography riddle. Rationale: at message 2 the agent "collapses the sea-related clue into the 2003 title". True at step 2, but step 4 and step 6 explicitly correct this reading ("the 2003 novel may be a different one"); the run then fails because the author is never identified (13 generic searches) and step 16 answers a 2003 sea-titled book from a snippet. | **Disagree.** The labelled mechanism was retracted two messages later; the unrecovered error is the never-executed author search (Search Coverage Gap) and the step-16 commitment. Label = first occurrence of a mechanism that was recovered. |
| 74 | Quest-35B, SEALQA, Search Coverage Gap | 27, k=12 (span 12–16) | UN "World's Women 2015" PDF visited twice (steps 5, 11); the visit tool summarises the PDF and never surfaces the regional table. Step 12 switches to IPU country data and averages countries. | Weakly agree. The decisive event is that the *tool* failed to extract the table; the agent's substitution at 12 is the best it could do without re-trying the PDF. Not decidable without knowing the gold (21.8) exists in that PDF. |
| 1188 | Quest-35B, SEALQA, Candidate Mismgmt | 21, k=20 (final) | Tropical storm with most deaths that stayed a TS. Tool return 7 states "Tropical Storm Barry … 45 mph … 8 deaths" (gold); step 15 again summarises Barry as a TS with 8 deaths. The final step misreads "Barry: Hurricane (Category 1)" and answers Melissa (a Cat-5). | Agree. Reasoning collapse at the final message with all evidence visible — the kind of final-step error that *is* defensible. |
| 305 | Qwen3.5-397B, BrowseComp, Constraint Neglect | 47, k=46 (final) | LoL match riddle; the agent cycles candidates for 20 decisions, sees conflicting durations (38 m vs 41:31) and at the final message asserts exact CS/duration values for SKT–G2 MSI 2017 as verified. | Agree with the final step; the span 41–46 covers the last five candidate decisions, i.e. the annotator could not pick one. |
| 819 | Kimi-K2.6, XBench-DeepSearch, Constraint Neglect | 13, k=8 (span 5–8) | Chinese chain riddle: Iron Man's actor's first *four-character-titled* film after Endgame (gold 《奥本海默》, which is visible in snippet 5: "2020's Dolittle and 2023's Oppenheimer"). Step 8 writes "Dolittle 的中文译名没有 4 个字的" and proceeds with Dolittle anyway. | Agree. The agent verbalises the violated constraint at k and overrides it. First chance to apply the constraint was step 6; annotator chose the explicit override at 8. |
| 1109 | Kimi-K2.6, BrowseComp-ZH, Constraint Neglect | 37, k=24 (span 21–26) | 1980 film, boy sings a 2'22" song. Candidate 《苗苗》/《小鸟小鸟》 has duration 2'33" (noticed at 22). Step 24 accepts an SEO page whose *title echoes the question* ("小鸟小鸟电影苗苗插曲时长2分22秒") as confirmation; the visit returns a Chaturbate spam page (25); step 36 still commits because "multiple search results say 2分22秒" — all of them query-echo spam. | Agree. Textbook **query-echo pollution**: search engines return pages that mirror the query text; the agent treats the echo as confirmation. Decidable from the trajectory. |
| 122 | OpenResearcher, BrowseComp, Unverified Source | 59, k=52 (span 52–58) | 1900s American Magazine Tiffany directory (gold "Russian"). 25 decisions of failed searches / Instagram echo pages / wrong PDFs; step 52 pivots to a generic "Tiffany 'R' pattern" content-farm page and answers "R pattern" with 95% confidence. | Agree. Pivot-to-substitute after exhaustion; decidable from the trajectory (the source never mentions the magazine). |
| 971 | Qwen3.5-397B, SEALQA, Unverified Source | 13, k=6 (span 6–9) | Women in parliament, Northern Africa 2021 (gold 24.3). Step 6 anchors on a recalled value 24.2 and then runs "exact-match confirmation searches" for 24.2. | Agree. Memory-origin answer followed by confirmation search; the value 24.2 appears in no tool return before step 6. |
| 30 | Qwen3.5-397B, XBench, Unverified Source | 29, k=28 (final) | NSFC 2023 funding ratio; after official annual-report pages, the agent accepts a secondary summary's figures and computes 1.42 (gold 1.7). | Agree; span 26–28 includes the decision to visit the secondary source. |

Additional spot checks (not read end to end): 1220 (SEALQA, gold "5 videos > 7 B views"; the trajectory itself shows the
count became 6 in June 2026 — gold stale), 1241 (SEALQA, count of >60 t animals, gold 6, Wikipedia table now gives 7 —
rationale says "without verifying the source version"), 536 (same YouTube question, answer 3 under a stricter definition).

## 3. Targeted statistics (full set, n = 1,243)

### 3.1 Tolerance spans: they extend *downstream* of the critical step

| | n | % |
|---|---|---|
| span length 1 / 2 / 3 / 4 / 5 / 6–12 messages | 140 / 117 / 249 / 170 / 238 / 329 | 11 / 9 / 20 / 14 / 19 / 26 |
| critical is the **first** agent message of its span | 528 | 42.5 |
| critical is the **only** agent message of its span | 304 | 24.5 |
| critical is the **last** agent message of its span | 240 | 19.3 |
| critical is in the middle | 171 | 13.8 |
| span begins with a tool return (evidence step included) | 360 | 29.0 |
| span ends at the last message of the run | 387 | 31.1 |

So in two thirds of the cases the "equally defensible adjacent decisions" are *later* than the critical step: the span is
critical + its immediate propagation, rarely an earlier alternative. CS-Loose therefore rewards late predictions much more than
early ones (a prediction one decision too early is inside the span in only ~33% of cases, one decision too late in ~56%).

### 3.2 Where the gold answer first becomes visible

Strict string match of the gold answer (whole-token for numeric golds) against tool returns:

| | n | % |
|---|---|---|
| gold string appears in at least one tool return | 410 | 33.0 |
| … and already *before* the critical step | 354 | 28.5 |
| … only after the critical step | 56 | 4.5 |
| among the 354: critical = first assistant message after the first gold-bearing return | 66 | 18.6 |
| among the 354: critical is later than that; gap in assistant decisions median 4, mean 12.4, p90 38; ≥10 decisions in 117 (33%) | 288 | 81.4 |

By root cause the gold is visible before k in 44% of Entity–Relation Misbinding and 41% of Candidate Mismanagement cases but
only 15% of Search Coverage Gap and 21% of Constraint Neglect. Conclusion: the annotators do **not** label the first missed
opportunity; they label the *commit / dismissal* decision, often many decisions after the evidence surfaced. Any attributor
that scores "first step after which the answer was in context" will be early relative to the label by a median of 4 decisions.

### 3.3 Query-echo pollution (search results that mirror the query)

`instagram.com/popular/<query-words>` tag pages, `facebook.com/fb-answers/…` and SEO titles with ≥70% query-token overlap:

| | n | % |
|---|---|---|
| runs with ≥1 echo page in a tool return | 907 | 73.0 |
| … by source: BrowseComp 239/251, BrowseComp-En 47/50, DeepSearchQA 211/255, SEALQA 156/217, BrowseComp-ZH 147/236, XBench 107/234 | | |
| echo page in the tool return *immediately before* the critical step | 253 | 20.4 |
| … by root cause: Unverified Source 34%, Unsupported Answer 27%, Candidate Mismgmt 20%, Search Coverage 17%, Constraint 17%, Entity–Relation 12% | | |
| … by generating model: Qwen3.5-397B 41%, Tongyi-DR 33%, Kimi 24%, Quest 19%, OpenSeeker 18%, GLM 15%, DeepSeek 10%, OpenResearcher 9% | | |

Echo pages are long-query artefacts (BrowseComp riddles are reproduced verbatim as Instagram tag pages). The models that
answer after few decisions (Qwen3.5, Tongyi) are the ones that commit right after an echo-polluted return (261, 1109, 122).

### 3.4 Visible error signs after vs before the label

| signal | before k | after k |
|---|---|---|
| empty / failed tool returns (no results, 403/404, login page, "no information"), rate per tool return | 0.072 | 0.108 |
| same, last 6 tool returns before k | 0.075 | – |
| records where the 6 returns before k have a *higher* empty rate than the run average / lower | 212 | 451 |

The critical step is not preceded by a run of dead ends; dead ends accumulate *after* it (the agent keeps searching for a
candidate that does not exist). Repeated identical queries: mean 2.4 per run (Entity–Relation 2.8, Constraint 2.7, Search
Coverage 1.2).

### 3.5 Verbalised doubt in `reasoning_content` (doubt words per 1,000 chars; English + Chinese lexicon)

| root cause | at k | mean before k | mean after k | final msg | doubt-argmax = k |
|---|---|---|---|---|---|
| Constraint Neglect | 3.35 | 2.71 | 1.70 | 1.64 | 11% |
| Candidate Mismgmt | 2.56 | 2.07 | 1.64 | 1.21 | 9% |
| Entity–Relation | 1.81 | 1.43 | 1.13 | 0.86 | 9% |
| Unverified Source | 1.48 | 1.62 | 1.11 | 0.80 | 11% |
| Search Coverage | 2.05 | 1.46 | 1.50 | 1.39 | 12% |
| Unsupported Answer | 1.54 | 2.35 | 0.23 | 1.41 | 8% |

Doubt at k exceeds the pre-k mean in 647/1,243 (52%) and the post-k mean in 734 (59%); the doubt-argmax message is before k
in 652, at k in 126 (10.1% vs 8.2% for a uniform guess), after k in 465. So doubt rises slightly at the labelled step
(Constraint Neglect and Candidate Mismanagement: the agent says "but this does not match …" and proceeds) and then *falls*:
after the commit the agent stops hedging. Verbalised doubt is a weak local signal and a decent "commit happened before here" signal.

### 3.6 Answer origin (296 records whose core answer is ≤ 60 chars)

| first message containing the predicted answer string | n |
|---|---|
| a tool return (evidence-origin) | 133 |
| an assistant message before any tool return containing it (memory-origin) | 81 |
| nowhere before the final message (fabricated / paraphrased at the end) | 82 |

Memory-origin answers are 21/76 in Constraint Neglect and 28/90 in Candidate Mismanagement; Unverified Source answers are
mostly evidence-origin (29/52); Unsupported Answers mostly appear nowhere (5/10).

### 3.7 Rationale text

Only 109/1,243 rationales cite another message index besides k: 76 cite an *earlier* message (the evidence the agent had),
28 a later one, 5 both. 346 use commit / finalise vocabulary, 295 "unsupported / never opens / fabricated", 76 mention
vintage / version / outdated / mismatched data (candidate gold-drift cases, see §5).

## 4. Baseline error analysis

(filled below)

## 5. Annotation issues

(filled below)

## 6. Candidate hypotheses

(filled below)

## 7. Open questions

(filled below)


## 4b. Baseline results (filled from results/searchauditbench/ after the rerun, 2026-11-01)

Qwen3.8-27B all-at-once, gold = critical message (gold answer and web hidden); first attempt exceeded the 200k context on the longest records, rerun with
`--budget-tokens 110000` (records that still overflow are rows with `error` set). Reasoning excerpts in
`results/searchauditbench/all_at_once_std_nogt_analysis.md`.

| subset | n | agent_ok | step_exact | step_within_3 | step_in_set |
|---|---|---|---|---|---|
| BrowseComp-ZH | 8 | 100.0 | 50.0 | 50.0 | 50.0 |
| XBench-DeepSearch | 10 | 100.0 | 30.0 | 30.0 | 30.0 |
| DeepSearchQA | 6 | 100.0 | 33.3 | 50.0 | 50.0 |
| SEALQA | 7 | 100.0 | 42.9 | 57.1 | 57.1 |
| BrowseComp | 7 | 85.7 | 42.9 | 42.9 | 57.1 |
| BrowseComp English | 2 | 100.0 | 50.0 | 50.0 | 50.0 |
| ALL | 40 | 97.5 | 40.0 | 45.0 | 47.5 |

categories: {'later(>3)': 6, 'earlier(<-3)': 14, 'exact': 16, 'in_label_set': 3, 'truncated': 1}
agent right but step wrong: 23; step right but agent wrong: 0
| n_steps | n | step_exact% | within3% | agent% |
|---|---|---|---|---|
| 0-10 | 5 | 60.0 | 80.0 | 100.0 |
| 11-30 | 11 | 45.5 | 45.5 | 90.9 |
| 31-1000 | 24 | 33.3 | 37.5 | 100.0 |
wrote results/searchauditbench/all_at_once_std_nogt_analysis.md
