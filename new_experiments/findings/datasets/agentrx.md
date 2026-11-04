# AgentRx (public GitHub subset) — inspection notes (G1, 2026-11-01)

Scripts: `inspect/agentrx_stats.py` (-> `results/agentrx/stats.{txt,json}`), `inspect/who_and_when_overlap.py` (WW↔AgentRx, 44 logs), `inspect/g1_condensed.py agentrx --ids ...`. Baseline: `results/agentrx/all_at_once_std.jsonl`, `all_at_once_inventory.jsonl` (+ `_analysis.md`).

## 1. Data as loaded

- 73 records (29 τ-bench retail, 44 Magentic-One = Who&When Hand-Crafted logs), 3,265 steps. `error_steps` = all annotated failure events (335 in total; up to 55 per log), primary = `extra.root_cause_idx`; `categories` = root category; `error_agent` = `failed_agent` of the root (`Websurfer`/`WebSurfer` casing, `User` for 8 τ cases).
- τ-bench: step 0 is the policy system prompt, then alternating User / Assistant (`Action: tool(args)`) / `Tool:name` (`Observation:`) steps; `extra.expected_actions` holds the task's gold tool calls and `ground_truth` the expected outputs. Magentic-One: same text as the WW HC logs (1-based `step_number` → idx − 1), no ground truth in the files.
- Root cause ≠ earliest failure in 19/73 (2 τ, 17 Magentic); root is the *last* annotated failure in 47/73 and the only failure in 36/73.

## 2. Close-reading notes

| id | n | root (agent, category) | all failures | what happened | my reading |
|---|---|---|---|---|---|
| tau_retail/2 | 32 | 6 (Assistant, Misinterpretation) | 2, 6 | lists T-shirt variants (10 available) and says "11"; later returns are fine. | Agree. The pre-root "failure" at 2 is a policy slip (answered before authenticating) that had no consequence — a recovered/absorbed adherence failure. |
| tau_retail/3 | 34 | 6 | 2, 6 | same template as /2. | Agree. |
| tau_retail/21 | 48 | 27 (**User**, Under-specified intent) | 27, 40 | user wants to exchange a *pending* order (impossible by policy); at 27 the simulated user drops it and asks to modify another item; at 40 the assistant modifies with PayPal instead of the gift card the hidden script demanded; GC balance 86 vs GT 44.08. | The blamed "agent" is the user simulator deviating from its script; the attributor can only see this by comparing the hidden task instruction (shown in the prompt) with the dialogue. Step 40 is the assistant's only consequential action. |
| tau_retail/55, /59 (User-blamed) | 38, 26 | User | single | user script contradictions / the user never states a required detail. | "Agent" accuracy is ill-posed for these 8 cases: the failure is in the test harness. |
| magentic/e6bc9808… (= HC/6) | 8 | 6 (Orchestrator, Misinterpretation) | 4, 6 | WebSurfer reads 35% of a search page (4); orchestrator accepts "$1.08 billion" (6 = "Request satisfied"). | Agree; WW labels 5 (the ledger with the same decision). Convention gap of one step. |
| magentic/5f982798… (= HC/20) | 67 | 32 (FileSurfer, Invention) | 12, 16, 32 | WebSurfer's PDF click renders only "2103.07786" (12), "Nothing to summarize" (16); FileSurfer at **20** downloads an invented URL `export.arxiv.org/pdf/2007.xx`, at 32 opens a non-existent `path_to_july_2020_paper.pdf`; run crashes at 66. | **Both labels miss the first invention (20)**: AgentRx's root (32) is the second hallucinated path; WW (3) is the orchestrator's first instruction. The first unrecovered invention is 20. |
| magentic/624cbf11… (= HC/46) | 130 | 4 (WebSurfer, Adherence) | 25 events | 30 rounds of searching for per-train ridership. | Root = first search; the 24 later events are repeats. Budget exhaustion; no decisive step. |
| magentic/… (= HC/30) | 121 | 12 (WebSurfer, Adherence) | 8, 12, 16, 24, 35, 39, 51, 58 … | Queen Anne → Queen Anne's County drift (see who_and_when.md). | Root 12 (vague Zillow query) precedes the drift; the decisive drift step is unlabelled. |
| magentic/… (= HC/8) | 129 | 40 (WebSurfer, Adherence) | 40, 58, 89, 112, 116, 120, 128 | WW labels 8 (the second WebSurfer action). | A 32-step gap between "earliest detectable" (WW) and "first unrecovered" (AgentRx) on a max-rounds run. |
| magentic/… (= HC/3) | 93 | 55 (WebSurfer, Adherence) | 55, 63, 92 | WW labels 32 (`Tool failure`, one of the 4 records with a mistake_type). | 23-step gap; the WW step is a tool failure that AgentRx treats as recovered. |

## 3. Targeted statistics (`results/agentrx/stats.txt`)

**3.1 Root vs other failure events.**

| | τ-retail (29) | Magentic-One (44) |
|---|---|---|
| root ≠ first failure | 2 (gap 4 steps) | 17 (median gap 2, max 20) |
| root is the only failure | 22 | 14 |
| root is the last failure | 24 | 23 |
| failure density before root (events/step) | 0.003 | 0.041 |
| failure density after root | 0.023 | **0.145** |
| root step contains an error string | 0/29 | 9/44 |
| error-string rate at root / pre-root / post-root / unflagged agent steps | 0 / 0 / 0 / 0.05 | 0.20 / 0.00 / 0.07 / 0.06 |

After the Magentic-One root the annotated-failure density is 3.5× that before it (P1: cascade of symptoms). The **recovered (pre-root) failures carry no error string at all** (0/24): they are silent partial reads and scrolls, not tool errors.

**3.2 What is "recovered".** Category of the 335 events by role:

| category | root | pre-root (recovered) | post-root (symptom) |
|---|---|---|---|
| Misinterpretation of tool output | 22 | 0 | 9 |
| Intent–plan misalignment | 11 | 1 | 15 |
| Instruction/plan adherence | 11 | **25** | **167** |
| Guardrails triggered | 9 | 0 | 15 |
| Under-specified user intent | 8 | 0 | 2 |
| Intent not supported | 5 | 0 | 19 |
| Invention of new information | 4 | 0 | 4 |
| System failure | 2 | 0 | 0 |
| Invalid invocation | 1 | 0 | 4 |

Recovered events are Adherence failures of the WebSurfer in 23/26 cases; roots are Misinterpretation (orchestrator accepting partial evidence) in 22/73. I.e. the *type* decides the role: a specialist that reads too little is "recovered" by definition (the orchestrator re-asks), the orchestrator's acceptance of what it got is "root".

**3.3 How visible is a recovery?** The step after a recovered WebSurfer failure is always an orchestrator ledger (24/24); only 6/24 of those ledgers say `is_in_loop=true` or `is_progress_being_made=false`; the orchestrator never re-issues the identical instruction (0/24, text match on the first 80 chars) — it rephrases. So recovery is *silent*: no error string (0/24), no ledger flag (18/24), a rephrased instruction. A prefix monitor has nothing to key on.

**3.4 Who is blamed vs who could have caught it.** Magentic-One roots: Orchestrator 23, WebSurfer 18, Assistant 2, FileSurfer 1; pre-root events: WebSurfer 23, Orchestrator 1. The orchestrator is blamed for *accepting*, the WebSurfer for *looping*. In τ-retail: Assistant 21, User 8 — 28% of the τ labels blame the simulator.

**3.5 Overlap with Who&When (44 logs).** Exact agreement 16 (36%), ±1 21, ±3 25; AgentRx later in 16, earlier in 12; WW step inside AgentRx's failure set 27/44; the two "first failure" notions coincide in 15/44; blamed agent agrees 27/44. The ±1 cases are the ledger/"Request satisfied"/instruction triples (HC/6, 10, 17, 31, 36, 50). The 20+-step cases are budget-exhaustion runs (§2).

**3.6 Label hygiene.** `Websurfer` (2 roots) vs `WebSurfer`; `Instruction Adherence Failure` vs `Instruction/Plan Adherence Failure`; `Underspecified` vs `Under-specified`; one `failure_id` is a string.

Prefix probe: not run separately (the 44 Magentic logs are WW HC logs; τ logs are 20–62 steps, half of them would be probed — deferred to keep server load down; see §7).

## 4. Baseline error analysis (`results/agentrx/all_at_once_std.jsonl`, 73 records; inventory variant pending)

| subset | n | agent | step exact (root) | within ±1 | within ±3 | in full failure set | later / earlier / exact | pred == first failure |
|---|---|---|---|---|---|---|---|---|
| τ-retail | 29 | 69.0 | 37.9 | 55 | 65.5 | 41.4 | 5 / 13 / 11 | 9 |
| Magentic-One | 44 | 68.2 | 22.7 | 41 | 56.8 | 38.6 | 16 / 18 / 10 | 12 |
| all | 73 | 68.5 | 28.8 | — | 60.3 | 39.7 | — | — |

Median signed offset 0 in both subsets; no late bias. By length: ≤10 steps 60% exact, 11–30 37%, >30 19.5%. The paper's gpt-5 judge-only ablation gives 29.9 (τ) / 32.6 (Magentic); Qwen all-at-once is 37.9 / 22.7, i.e. comparable on τ, worse on the long Magentic logs.

**Root ≠ first failure (19 logs):** the model hits the root in 4 (2 τ, 2 Magentic), the first failure in 4, and goes *earlier than the root* in 6 Magentic cases — it does not systematically pick the first failure either; on these logs it picks a third step.

**User-blamed τ cases (8):** agent accuracy 0/8, the model always blames the Assistant (28/29 predictions are `Assistant`). For tau_retail/21 it picks step 26, the assistant's refusal to modify the pending order instead of offering the policy-compliant equivalent ("instead of recognizing that modifying items in a pending order is the correct equivalent action") — one step before the User label (27) and a better diagnosis than the label. For tau_retail/59 it picks the final incomplete answer (24; gold 13 User): with no visible user error it defaults to the last assistant message. "Under-specified user intent" is not a category an output-only judge will produce unless told the simulator can fail.

**By root category (Magentic):** Guardrails Triggered 5/9 exact (content-filter/404 steps are loud), Misinterpretation 3/15, Adherence 0/8, Invention 1/4, Intent-not-supported 0/3. The *acceptance* roots (Misinterpretation) are missed mostly by ±1: e6bc9808 (= HC/6) pred 5 (the ledger that accepts $1.08B) vs root 6 ("Request satisfied") — the same decision; 18/44 Magentic predictions are within ±1 of the root. Adherence roots (first search of an exhaustion run) are never hit: 9e31099f (= HC/8) pred 16 vs root 40 ("clicked the IPO press release instead of searching for the C-suite"), 2ddae3b7 (= HC/30) pred 66 vs root 12.

**The same log, two renders, two answers.** HC/30 appears in Who&When (with ground truth 1010000, final 445000) and in AgentRx (no ground truth). On the WW render the model picks step 8 — it *traces the final value 445,000 back to the step where it first appeared* ("introducing the irrelevant value that later became the final answer"); on the AgentRx render it picks 66 — the step that "searched 'Queen Anne property records January 2023' without specifying Seattle", i.e. the actual drift into Queen Anne's County, MD, which no annotator labelled. Outcome knowledge changes the heuristic (answer-origin tracing vs process reading), not just the step — the P3/P4 "hindsight" effect observed in a judge.

**Successes read:** tau_retail/2 (miscount 11 vs 10 → 6, exact; the model recounts the variants itself), 2dfc4c37 (= HC/12, Assistant's wrong domestic list → 16, exact, with the row-level evidence from step 12 quoted), 2aa5dd83 (= HC/48, WebSurfer stops at the search page → 4, exact; the model notes the content-filter error but keeps the WebSurfer step). 5f982798 (= HC/20): pred 39 (WebSurfer returns unrelated papers), gold 32, first invention 20 — all three miss the first hallucinated URL.

**Model reasoning patterns:** (a) "first time it asserts the answer" as the root criterion (e6bc9808); (b) explicit omission-vs-commission deliberation ("It didn't make an active wrong action; it omitted necessary action. The next step 12 is active wrong action", HC/30); (c) re-deriving the answer from the observations to locate the wrong number (τ/2, HC/12); (d) exact-agent-name care. The 13 "earlier (< −3)" misses are mostly omission steps picked over the labelled commission/acceptance step.

## 5. Annotation issues (prevalence)

1. **"First unrecovered" is applied as "last failure before the answer"** in practice: root = last annotated failure in 47/73 (64%), and in the 17 Magentic gap cases the root is the orchestrator's acceptance of partial evidence after several silent WebSurfer failures. This is a defensible convention but it is *the* late-bias convention: the label is the step that locks in the symptom, and it sits after every recoverable failure.
2. **Missed first invention** (5f982798: root at 32, first hallucinated URL at 20, unflagged).
3. **User-blamed τ cases (8/29)**: the failure is in the simulated user's deviation from its script; agent accuracy is undefined.
4. **Exhaustion runs** (HC/46 ↔ 624cbf11, HC/8/15, HC/44): root = first search, 7–24 "adherence" repeats after it; no decisive step exists.
5. **Casing/wording** (§3.6).
6. Paper reports κ = 0.89 on 30 trajectories labelled by all three annotators; the public files carry one merged label, so this cannot be checked. Against Who&When's independent experts the agreement is 36% exact / 57% within ±3.

## 6. Candidate hypotheses

**H-A1 "Silent recovery": recoverable failures leave no textual trace (no error string, 75% no ledger flag, rephrased instruction), so the only visible evidence of a recovered failure is the *orchestrator's next instruction being a paraphrase of the previous one*.** Evidence: §3.1, §3.3. Test: embed consecutive orchestrator instructions; the paraphrase rate (sim > 0.85) after pre-root failures vs after unflagged WebSurfer steps. Shared with WW-HC (same logs), MP-Bench manual (1-vote flags on paraphrased re-asks). Method: a "re-ask detector" on orchestrator instructions gives an early-failure channel that is independent of error strings.

**H-A2 "Root = acceptance step": in orchestrated MAS, the labelled root cause is the orchestrator's acceptance (`is_request_satisfied=true` or an instruction that assumes the missing evidence) of a specialist's partial output, not the specialist's partial output itself.** Evidence: Misinterpretation 22/73 roots, 0 recovered; HC/6, /10, /31, /36, /50 (root on the ledger). Test: for every Magentic root, check whether the ledger at the root (or at root+1) states satisfaction/progress that contradicts the specialist output; predicted ≥ 70%. Method: score ledgers by *claim–evidence mismatch* (what the ledger says was gathered vs what the previous specialist step contains); this directly targets the convention and would also transfer to MP-Bench where ledgers are 18% of unanimous flags.

**H-A3 "Type decides role, not position": whether a failure event is recovered or root is predictable from its category and agent (WebSurfer-Adherence → recovered, Orchestrator-Misinterpretation → root) with ≈ 90% accuracy, independent of its position.** Evidence: §3.2. Test: logistic regression on (agent, category) vs (relative position); if category dominates, the "first unrecovered" definition reduces to "first orchestrator misjudgement". Shared with FaP/DRIFT fatality-by-type findings (P7).

**H-A4 "Cascade density as a label locator": the labelled root is the step after which annotated-failure density jumps (0.041 → 0.145 per step).** Test: for each log, find the change-point of the model-flagged-mistake rate (from the inventory baseline) and compare with the root; a change-point locator may beat argmax selection on these logs. Shared with WW-HC, MP-Bench.

## 7. Open questions

- The τ User-blamed cases: does the hidden user script actually contain the information (e.g. "use GC") that the simulator withheld? If so the label should be "simulator failure", a class the taxonomy lacks.
- A prefix probe on the 29 τ logs (≈ 500 probes) would show whether the root (count errors, wrong payment method) is locally detectable with the policy in view; deferred for server load.
- Whether the gated HF release (170 trajectories) contains the Flash/RelWork logs where AgentRx reports 61–82% step accuracy — the public 73 are the hard half.


## 4b. Baseline results (filled from results/agentrx/ after the runner finished, 2026-11-01)

Qwen3.8-27B all-at-once, gold = root-cause step; `step_in_set` counts a prediction inside the full labelled set.
Signed categories: `later` = predicted after the gold (symptom side), `earlier` = before it. Reasoning excerpts for
failures and successes are in `results/agentrx/all_at_once_std_analysis.md`.

| subset | n | agent_ok | step_exact | step_within_3 | step_in_set |
|---|---|---|---|---|---|
| magentic_one | 44 | 68.2 | 22.7 | 56.8 | 38.6 |
| tau_retail | 29 | 69.0 | 37.9 | 65.5 | 41.4 |
| ALL | 73 | 68.5 | 28.8 | 60.3 | 39.7 |

categories: {'earlier(-1..3)': 14, 'earlier(<-3)': 13, 'exact': 21, 'in_label_set': 8, 'later(>3)': 13, 'later(+1..3)': 4}
agent right but step wrong: 29; step right but agent wrong: 0
| n_steps | n | step_exact% | within3% | agent% |
|---|---|---|---|---|
| 0-10 | 5 | 60.0 | 80.0 | 100.0 |
| 11-30 | 27 | 37.0 | 74.1 | 77.8 |
| 31-1000 | 41 | 19.5 | 48.8 | 58.5 |
wrote results/agentrx/all_at_once_std_analysis.md

Inventory variant (same ids):

| subset | n | agent_ok | step_exact | step_within_3 | step_in_set |
|---|---|---|---|---|---|
| magentic_one | 44 | 70.5 | 25.0 | 59.1 | 38.6 |
| tau_retail | 29 | 72.4 | 34.5 | 58.6 | 37.9 |
| ALL | 73 | 71.2 | 28.8 | 58.9 | 38.4 |

categories: {'earlier(-1..3)': 15, 'later(>3)': 11, 'exact': 21, 'earlier(<-3)': 17, 'in_label_set': 7, 'later(+1..3)': 2}
agent right but step wrong: 31; step right but agent wrong: 0

