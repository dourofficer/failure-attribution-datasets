# SymTrace / SymFail (536-case package) — inspection notes (G1, 2026-11-01)

Scripts: `inspect/symtrace_stats.py` (-> `results/symtrace/stats.{txt,json}`), `inspect/g1_condensed.py symtrace --ids ...`, baseline `results/symtrace/all_at_once_std.jsonl` (+ `_analysis.md`).

## 1. Data as loaded

- 536 records (171 ag2 / 184 crewai / 181 magnetic_one), 5,548 steps = graph nodes in `topological_order`; one labelled node per record (`error_steps` = position of `failure_node_id`), label set C1–C4 (`categories`), primary label in `extra.primary_failure_label`.
- Every trajectory follows one of **four structural templates per framework** (`sys_prompt, user_input, agent_action, agent_action, final_result` is 65/171 ag2 and 119/184 crewai; Magentic-One adds two more agent_action nodes per LLM call). Max three LLM calls. 276 runs make no tool call at all.
- Each LLM call produces **two identical-content nodes** (`masd_*_assistant` "process_message_before_send" + framework "agent_step"); Magentic-One additionally inserts a `user`-agent node that *echoes* the task or the tool result. These duplicates matter for the label (below).
- `confidence` is `"high"` for all 536 records (uninformative). IAA: node unanimous 396/536 (73.9%, as in the paper), adjudicated node supported by 0 annotators in 20 cases and by 1 in 46; primary label unanimous 459/536.
- Loader caveat: the loader is fine; but note that `error_agent` for Magentic-One is the string `user` in 102 cases (see §5) — any "agent accuracy" on this dataset is meaningless.

## 2. Close-reading notes

| id | n | gold (kind) | labels | what happened | agree? |
|---|---|---|---|---|---|
| ag2/webarena_verified_hard_96 | 13 | 7 (agent_action, 2nd copy of the retry) | c1-c4, primary c3 | browse `__SHOPPING__` → MissingSchema → retry `https://__SHOPPING__` → DNS fail → answers "status unknown". The site placeholder was never substituted. | No agent mistake exists; the "failure node" is the retry. Label = environment failure. |
| ag2/assistantbench_dev_01d17367… | 15 | 3 (first browse action) | c1,c2,c3 | all Fidelity pages return "Temporarily Unavailable"; agent gives up honestly. | Environment failure labelled on the first agent action. |
| crewai/webarena_verified_hard_105 | 5 | 2 (first and only agent action) | c1,c2,c4 | answers with a fabricated `gitlab.com/...` URL without calling any tool. | Agree (answer-without-evidence); node is forced (only candidate). |
| magnetic_one/webarena_verified_hard_105 | 7 | 2 (`user` node that **echoes the task**) | c1,c3,c4 | assistant notices the `__GITLAB__` placeholder, answers with a github.com URL. | Disagree: the labelled node contains no decision; the decision is node 3/4. |
| magnetic_one/assistantbench_dev_01d17367… | 21 | 3 | c1,c2,c4 (primary c2) | assistant emits a fabricated final (FEMKX) at node 4 while the adapter keeps issuing tool calls; pages unavailable; three "final" strings in one run. | The adapter is broken (final + tool call in one turn). C2 "stalled" = budget exhaustion, not repetition. |
| magnetic_one/assistantbench_dev_84575608… | 21 | 9 | c1,c2 | IMDB returns HTTP 202 (page not rendered); retry; switch URL; **the released final answer is a `browse` action JSON** because the 3-call budget ran out. | "Failure" is the call cap. |
| crewai no-tool runs (119) | 5 | 2 | mostly c4/c1 | the model answers the WebArena task from memory in one shot; no tool. | Agree that it is a mistake, but it is the same mistake 119 times. |
| ag2 no-tool runs (65) | 5 | 4 (final_result) in 54 | c4 | same as above, but the annotators put the node on the final answer instead of the first action — framework-specific convention. | Illustrates that the node choice is a per-framework habit. |

Reading ten more at random (ag2 ×4, crewai ×3, magnetic ×3) found no case where the labelled node is a step that *could have been done otherwise given the evidence available at that node*, except the "answer without tool" ones.

## 3. Targeted statistics (`results/symtrace/stats.txt`)

**3.1 Environment reach.** Runs whose every tool result failed ("env_blocked") or that never called a tool:

| MAS | n | no tool call | all tool results failed | placeholder hit (`__SHOPPING__` etc.) | ≥1 successful fetch | final says "unable/cannot" |
|---|---|---|---|---|---|---|
| ag2 | 171 | 65 | 72 | 75 | 34 | 52 |
| crewai | 184 | 119 | 43 | 41 | 22 | 58 |
| magnetic_one | 181 | 92 | 59 | 57 | 30 | 45 |

450/536 (84%) runs never obtained a usable page; only 86 ever had a successful fetch (and "successful" includes HTTP 202 shells and "Temporarily Unavailable" pages, so the true figure is lower). 155 finals explicitly give up.

**3.2 Label is predictable from structure.** Majority-class primary label (C3) = 37.9%. Majority label per (MAS, failure-node kind, env situation) = **63.8%**, + "final gives up" flag = 66.6%. Failure-node *position* from (MAS, node-kind template, env situation) = **70.3%** (377/536), from (MAS, template) alone 68.5%. Both label and node are mostly a function of the framework template and whether the tool worked — not of content.

| MAS × situation | c1 | c2 | c3 | c4 | n | gold = first agent action | gold = final |
|---|---|---|---|---|---|---|---|
| ag2 env_blocked | 9 | 0 | 58 | 5 | 72 | 0 | 23 |
| ag2 no_tool | 5 | 0 | 6 | 54 | 65 | 1 | 54 |
| ag2 reached_env | 23 | 2 | 8 | 1 | 34 | 0 | 5 |
| crewai env_blocked | 4 | 18 | 17 | 4 | 43 | 14 | 14 |
| crewai no_tool | 35 | 0 | 17 | 67 | 119 | 117 | 1 |
| crewai reached_env | 10 | 3 | 2 | 7 | 22 | 14 | 0 |
| magnetic env_blocked | 10 | 17 | 32 | 0 | 59 | 19 | 1 |
| magnetic no_tool | 19 | 22 | 50 | 1 | 92 | 73 | 0 |
| magnetic reached_env | 10 | 7 | 13 | 0 | 30 | 8 | 0 |

**3.3 Node identity is a framework artefact.** The failure node is the *second* of two identical-content nodes in 199 cases and the *first* in 158 (357/536 = 67% of labels sit on one copy of a duplicated node). In Magentic-One the labelled node is the `user`-agent **task echo** (verbatim copy of `user_input`) in 100/181 cases — a node that contains no decision at all.

**3.4 C2 "repeated / stalled progress" without repetition.** 69 primary-C2 cases; 0 contain two identical tool calls; 22 contain no tool call. In Magentic-One (46 C2) the pattern is "the 3-call budget ran out while still retrying/browsing" (final answer = an action JSON) — budget exhaustion is labelled as a stall.

**3.5 Failure node vs first failed tool result.** 224 runs have a failed tool result; the node is *before* it in 148 (median −2, i.e. the action that issued the call, counting the duplicate), after it in 74. So when there is a visible failure signal, the label sits one decision before it: C3 means "the action whose tool result then failed", not the node that reacted badly.

**3.6 Give-up vs confident finals.** Among the 155 give-up finals, primary labels are C3 94 / C2 31 / C1 22 / C4 8; among confident finals C4 131 / C3 109 / C1 103 / C2 38. C4 (plan–action–outcome inconsistency) is essentially "answered confidently without evidence".

Prefix probe: not run (median trajectory has one LLM call and the label is structural; the probe would measure the template, not detectability).

## 4. Baseline error analysis

(filled in from `results/symtrace/all_at_once_std.jsonl` — see §4 below once the run finished)

## 5. Annotation issues (prevalence)

1. **Environment failure labelled as a failure node (~84%)**: 450/536 runs never reached a usable page (placeholders unsubstituted, sites blocking). The annotators then pick, by convention, the action that issued the doomed call (C3) or the first agent action (C1/C4). There is no agent decision that would have changed the outcome in these runs; the dataset is a *failure-signal* set, as the authors themselves say ("intervention signals rather than failure verdicts").
2. **Decision-free nodes as labels**: 100 Magentic-One labels are the task-echo node; 357 labels sit on one copy of duplicated content. A step-level attributor is scored on which *copy* it names.
3. **C2 without repetition** (69 cases, §3.4).
4. **Adjudication over-rides**: 20 final nodes are supported by none of the three annotators, 46 by one; `confidence` is "high" everywhere.
5. **The same mistake repeated**: 119 CrewAI and 65 AG2 runs are the identical "answer from memory with no tool" pattern on different tasks; label diversity is an illusion of task diversity.
6. **Broken adapter**: Magentic-One runs emit "final" strings and tool calls in the same turn, and the released `final_answer` can be an action dict (assistantbench_dev_84575608…).

## 6. Candidate hypotheses

**H-S1 "Template labels": on fixed-protocol MAS, the failure node is a function of the framework template and the environment outcome, not of step content.** Evidence: 70% node position and 64% primary label from structure alone (§3.2), vs 38% majority class. Test: train a tiny classifier on (MAS, template, tool-status sequence) with no text — if it matches the LLM baseline, the dataset cannot discriminate attribution methods. Shared with: WW-HC (ledger duplication), AgentRx Magentic-One (first/second copy of orchestrator decisions); opposite of long natural logs. A targeted method would *detect* templated datasets by measuring label entropy conditional on structure and refuse to over-interpret step accuracy on them.

**H-S2 "Blocked environment → earliest-action label": when no evidence ever arrives, annotators regress to the first agent action (or the final answer), and this choice is framework-specific (ag2 → final, crewai/magnetic → first action).** Evidence: §3.2 rows env_blocked/no_tool. Test: relabel 50 env_blocked runs with annotators who are told the environment was broken; measure how many pick "no actionable node". A method should emit an explicit "environment failure, no attributable step" class (cf. AgentRx System Failure, MP-Bench System Error) instead of a step.

**H-S3 "Budget exhaustion masquerades as stall (C2)".** Evidence: §3.4. Shared with WW-HC (max-time/max-rounds runs labelled on a stall/replan step, see who_and_when.md §3). Test: compare C2 labels to the call-cap flag; a method should treat "cap reached" as a run-level outcome, not a step.

**H-S4 "Give-up finals are honest and confident finals are the symptom".** Give-up finals are C3-dominated (tool problem), confident finals C4-dominated (fabrication). Shared with P8/false-success literature; here the honest-failure share (29%) is high because the adapters are thin.

## 7. Open questions

- The 64 successful runs are not released: the "normal flow" (P6) cannot be tested, but the four-template structure suggests successes look identical to failures up to the tool result.
- Do the authors' repair numbers (20% pass) come almost entirely from the 86 reached_env runs? The release does not say.
- Whether the adjudicator's rule "earliest trace-supported actionable node" is applied consistently across frameworks — the ag2-final vs crewai-first-action split suggests not.


## 4b. Baseline results (filled from results/symtrace/ after the runner finished, 2026-11-01)

Qwen3.8-27B all-at-once, gold = failure node; `step_in_set` counts a prediction inside the full labelled set.
Signed categories: `later` = predicted after the gold (symptom side), `earlier` = before it. Reasoning excerpts for
failures and successes are in `results/symtrace/all_at_once_std_analysis.md`.

| subset | n | agent_ok | step_exact | step_within_3 | step_in_set |
|---|---|---|---|---|---|
| crewai | 13 | 100.0 | 61.5 | 84.6 | 61.5 |
| magnetic_one | 25 | 52.0 | 24.0 | 84.0 | 24.0 |
| ag2 | 22 | 95.5 | 4.5 | 59.1 | 4.5 |
| ALL | 60 | 78.3 | 25.0 | 75.0 | 25.0 |

categories: {'later(+1..3)': 17, 'exact': 15, 'later(>3)': 5, 'earlier(<-3)': 10, 'earlier(-1..3)': 13}
agent right but step wrong: 32; step right but agent wrong: 0
| n_steps | n | step_exact% | within3% | agent% |
|---|---|---|---|---|
| 0-10 | 29 | 37.9 | 96.6 | 69.0 |
| 11-30 | 31 | 12.9 | 54.8 | 87.1 |
| 31-1000 | 0 | 0.0 | 0.0 | 0.0 |
wrote results/symtrace/all_at_once_std_analysis.md
