# G1 — output-only multi-agent logs: Who&When, MP-Bench, AgentRx, SymTrace (synthesis, 2026-11-01)

Per-dataset notes: `findings/datasets/{who_and_when,mp_bench,agentrx,symtrace}.md`. Scripts in `inspect/` (`who_and_when_stats.py`, `who_and_when_overlap.py`, `who_and_when_signals.py`, `mp_bench_stats.py`, `agentrx_stats.py`, `symtrace_stats.py`, `g1_gt_visibility.py`, `g1_dump.py`, `g1_condensed.py`); outputs in `results/<slug>/`.

The four datasets are one corpus seen through four annotation conventions: 44 of AgentRx's 73 and 177 of MP-Bench's 289 logs *are* Who&When logs (resolved step-for-step, `results/who_and_when/overlap_map.json`), and SymTrace re-runs Magentic-One/AssistantBench with thin adapters. That makes the group a label-reliability experiment as much as a benchmark.

## 1. Phenomena that recur across the group

**G1-A. There is often no decisive step; labels are stop rules.** 13/58 Who&When HC runs end by budget exhaustion (max time/rounds/replans); SymTrace C2 (69 cases) is "the 3-call budget ran out"; AgentRx roots on the same runs are "first search" with 7–24 adherence repeats after. On such runs the three annotation teams do not coincide: WW vs AgentRx exact 16/44 (36%), WW step unflagged by all three MP-Bench annotators in 26/57 HC logs, and the gaps are 20–74 steps on exhaustion runs (HC/2, 8, 19, 30, 46). Short single-commission runs (AG, τ-retail) are reproducible instead: WW AG step has ≥2 MP-Bench votes in 116/120 (3 votes in 74); τ-retail root = only failure in 22/29.

**G1-B. Consensus concentrates on symptoms; causes get one vote.** MP-Bench manual: 3-vote steps have median relative position 0.82, 24% are the FINAL ANSWER step, error-string rate 0.27 vs 0.05 on unflagged steps; 77% of 1-vote flags are after the earliest majority step. AgentRx Magentic-One: annotated-failure density 0.041/step before the root vs 0.145 after. Who&When HC: the system's own loop flags, stalls and repeated actions follow the label by a median of 4–22 steps (`results/who_and_when/signals.txt`). The *cause* steps in the read cases (manual/116 step 12, manual/18 step 3, HC/12 step 12, 5f982798 step 20) carry 0–1 votes or no label.

**G1-C. Evidence gap → fabrication, and annotators split between the omission and the commission.** AG/3 (pip timeout → assumed numbers), AG/10 (manual-lookup requests → fabricated census figures), HC/12 (domestic chart never loaded → list from memory), 5f982798 (PDF not rendered → invented arXiv id), SymTrace no-tool runs (184 "answer from memory"). MP-Bench majority is strictly earlier than WW in 28/120 AG logs, always on an omission step. AgentRx resolves the split by type: WebSurfer-Adherence omissions are "recovered" (25/26 pre-root events), orchestrator Misinterpretation/acceptance is "root" (22/73).

**G1-D. Recovery is silent.** 0/24 recovered WebSurfer failures in AgentRx carry an error string; only 6/24 are followed by a ledger loop/no-progress flag; the orchestrator never repeats the identical instruction (it paraphrases). 22/58 WW HC logs are missing the erroring specialist turn altogether (37 events). The only visible trace of a recoverable failure is a paraphrased re-ask.

**G1-E. Step identity is a framework artefact.** Magentic-One emits ledger → instruction → "Next speaker" triples with the same text (WW `-> X` labels get 0 MP-Bench votes 6/6 because MP-Bench flags the ledger; AgentRx root = "Request satisfied" where WW = the ledger before it); SymTrace duplicates every LLM call into two identical nodes and labels one copy in 357/536 cases, and labels the task-echo node in 100/181 Magentic-One runs. ±1 tolerance is a *necessity* on these logs, not leniency; exact-step accuracy differences below ~5 pp are convention noise.

**G1-F. Environment failures are labelled on agents.** SymTrace: 450/536 runs never reached a usable page; the label goes to the action that issued the doomed call (C3) or the first action. Who&When HC/48 (Azure content filter), AG/3 (install timeout), the 37 missing WebSurfer turns; AgentRx "Guardrails Triggered" 9/44 roots, "System Failure" 2. No dataset has a "no attributable step" class, so an attributor is forced to blame someone.

**G1-G. Labels are outcome-informed and sometimes wrong.** MP-Bench reasons quote the ground truth; AG/82's `mistake_reason` contradicts the log (the run computed 17,000 h = GT 17); HC/2 ends with the correct answer; AG/79 is an over-specified correct answer. MP-Bench annotators 1 and 3 are verbatim identical on 19/169 manual logs (and 1/2 on 8), inflating consensus and producing `Next speaker` lines as majority primaries in 7 logs.

## 2. Where the datasets differ, and why

| | Who&When HC | Who&When AG | MP-Bench manual | AgentRx τ | AgentRx Magentic | SymTrace |
|---|---|---|---|---|---|---|
| failure shape | long loops, exhaustion 22% | short, one fabrication | same logs + MAST | one policy/count slip | same HC logs | one-shot answer or blocked env |
| label reproducible? | no (23% unanimous in MPB, 36% vs ARx) | yes (62% unanimous) | set-valued | single, clean | last failure before answer | structural (70% from template) |
| decisive step exists? | often not | yes | n/a | yes | often not | rarely |
| baseline step exact (Qwen 27B) | 31.0 | 48.4 | pending | 37.9 (root) | 22.7 (root), 38.6 in failure set | pending |

The difference is driven by *run length and termination type*, not by MAS type: long Magentic-One runs end by exhaustion, where the "earliest step whose correction would have succeeded" is undefined; short CaptainAgent/τ runs end on a wrong answer that a single commission produced. AgentRx's "first unrecovered" rule and Who&When's "earliest detectable" rule agree on the short runs and diverge by 20–70 steps on the exhausted ones. SymTrace differs for a different reason: the runs are three calls long and the labels encode the framework template.

## 3. Baseline (all-at-once, Qwen3.8-27B) across the group

Who&When: agent 63%, step 42.9% (HC 31.0 / AG 48.4), within ±3 67.9%; **no late bias** (HC 20 earlier vs 15 later, median signed 0; predictions median rel. position 0.29 vs gold 0.33). Half of the HC misses and most AG misses are steps endorsed by the other annotation team (prediction has ≥2 MP-Bench votes in 20/57 HC and 91/120 AG logs; the WW gold itself has ≥2 votes in 17/57 HC). The model's explicit heuristics in its reasoning: trace the wrong final answer backward to where the number first appeared (earlier-biased, HC/30 → step 8); name the first omission in the plan (HC/2 → 25); and "which step would the annotator pick, the ledger or the instruction?" (HC/19). Failure modes: 8 truncations on ≥80-step logs, one thinking loop (HC/9).

AgentRx: agent 68.5%, root exact 28.8% (τ 37.9 / Magentic 22.7), within ±3 60.3%, inside the full failure set 39.7%; median signed offset 0 in both subsets; the model never blames the simulated `User` (0/8) and goes *earlier* than the root in 6 of the 17 Magentic root≠first logs. The same log rendered with (Who&When) and without (AgentRx) the ground truth gets different predictions (HC/30: step 8 by tracing the wrong final value back to its first appearance vs step 66, the actual drift step) — outcome knowledge switches the judge's heuristic.

MP-Bench / SymTrace baselines: see the per-dataset §4 (pending at the time of writing; the exact commands are in the task brief and the cache makes re-runs instant).

## 4. Literature phenomena P1–P8 on this group

- **P1 downstream contamination / late localisation** — *confirmed for the signals and the annotators, refuted for the prompted judge.* Signals: first ledger loop flag after the label in 22/36 HC logs (median +4.5), first repeated WebSurfer action +8, first stall +22, first paraphrased instruction +4 (41/58 logs); AgentRx failure density 3.5× after the root; MP-Bench unanimity at rel. position 0.82. Judge: Qwen all-at-once with a "decisive, not symptom" prompt shows median signed offset 0 on HC and AG, and its >3-step-late picks are not last-step picks (1/14). The signed offset the literature never reports is ≈ 0 here; late bias is a property of per-step scorers and of annotator consensus, not of this judge.
- **P2 conventions differ** — *confirmed with numbers*: WW vs AgentRx exact 36%, ±3 57%, gaps up to 74 steps on the same logs; WW vs MP-Bench majority: 9/57 HC, 91/120 AG. The divergence is concentrated on exhaustion runs (G1-A).
- **P3 anchoring on outcome / drafts** — *confirmed for outcome*: MP-Bench reasons cite the ground truth and flag FINAL ANSWER steps unanimously (73 unanimous flags); SymTrace's adjudicator over-rides all three annotators in 20 cases; no LLM drafting in these four, but MP-Bench's duplicated annotator (19 logs) is a different kind of non-independence.
- **P4 outcome-only judges fooled by assertive closings** — *not testable* (no successes released); the related fact: 148/536 SymTrace finals honestly say "unable", and those get C3 (tool) labels, confident finals get C4 (fabrication).
- **P5 length degrades step localisation** — *confirmed*: Who&When exact 50% (≤10 steps) → 32% (11–30) → 21% (>30); 8 truncations all on ≥80-step logs; but *agent* accuracy is flat (64/63/59), as P5 states.
- **P6 normal-flow premise** — *weakly supported in the narrow sense*: SymTrace has four structural templates per framework and 70% of labels are predictable from (template, tool status); Magentic-One ledgers follow a fixed protocol whose flags are themselves annotated (H-M3: loop-flag ledgers voted 58% vs 27% normal ledgers). Not testable against successes.
- **P7 absorption vs cascade by type** — *confirmed*: AgentRx recovered events are Adherence 25/26, roots are Misinterpretation 22/73; the orchestrator absorbs specialist omissions by re-asking and the failure becomes irrecoverable at the acceptance step.
- **P8 verification theatre / false success as the dominant late symptom** — *confirmed on MP-Bench*: 24% of unanimous manual flags are the FINAL ANSWER step and `is_request_satisfied=true` ledgers are voted 16/18; AgentRx root = orchestrator acceptance 22/73.

## 5. Ranked hypotheses (what a targeted method would do)

1. **Episode, not step, on exhaustion runs** (G1-A; WW H-W1, SymTrace H-S3). Classify the run first (decisive-mistake vs exhaustion/blocked); for the latter output the first repeated-action episode or "no attributable step". Evidence: 22% of HC and 84% of SymTrace runs; cross-team agreement on them ≈ 0–36%. Test: re-annotate the 13 HC exhaustion runs under both definitions; measure agreement separately. Expensive part: new annotation.
2. **Claim–evidence mismatch at the acceptance step** (AgentRx H-A2, MP-Bench H-M3). Score each orchestrator ledger by whether its "gathered/satisfied" claim is supported by the preceding specialist output; roots are Misinterpretation 22/73 and satisfied-ledgers are voted 89%. Test: automatic claim-vs-evidence check on all 102 Magentic logs; predicted ≥70% hit on roots. Cheap (one call per ledger).
3. **Omission→commission pairs** (G1-C; WW H-W5, MP-Bench H-M2). Predict the pair (evidence gap, fabrication) and accept either member; 28/120 AG majority-earlier cases and all read HC fabrication cases have this shape. Test: LLM-classify flagged steps as omission/commission across WW/MPB/ARx and measure which member each convention picks.
4. **Paraphrased re-ask as the early signal** (G1-D; WW H-W2, AgentRx H-A1). First paraphrased orchestrator instruction is present in 41/58 HC logs, closer to the label than the ledger flag in 20/33, still median +4. Test: embedding-based paraphrase detector vs ledger flags on all 102 Magentic logs + MAST; cheap.
5. **Convention-aware scoring** (G1-E). Collapse ledger/instruction/next-speaker triples and SymTrace duplicate nodes into one decision before scoring; report ±1 as the primary metric on Magentic logs. Test: recompute all published WW-HC numbers with the collapse; expected +5–10 pp for every method, with rank changes.
6. **Annotation-set hygiene** (G1-G): drop MP-Bench's 19 duplicated manual logs, recompute consensus with de-duplicated votes (26 logs lose their majority), exclude HC/2, AG/82, AG/79 from WW, add a "no attributable step / environment" class. Cheap, and it changes the HC leaderboard denominator by ~10%.
7. **Answer-origin back-tracing as a judge heuristic** (observed in the baseline reasoning, HC/30): the model locates where the wrong final value first entered the log. Worth measuring as a feature: distance from the label to the first occurrence of the final-answer string (we measured GT visibility: GT seen before the label in 5/58 HC, 19/169 MPB manual).
8. **Template detector** (SymTrace H-S1): before trusting step accuracy on a dataset, measure label entropy conditional on structure; SymTrace is 70% structural.

## 6. What was skipped / still pending

- Prefix probe on Who&When (216 probes) was queued but had not landed when this file was written; AgentRx τ and SymTrace probes were deliberately not run (server load; SymTrace labels are structural).
- Baseline error analyses for MP-Bench, AgentRx and SymTrace: jobs running (`results/<slug>/all_at_once_std.jsonl`); the per-dataset §4 sections say "pending" until they land.
- H-A2 (claim–evidence mismatch) and H-W5/H-M2 (omission/commission classification) need one LLM call per ledger/flag and were left as future experiments.
