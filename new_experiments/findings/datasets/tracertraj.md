# TracerTraj (AgenTracer data v1.0.0) — inspection notes (G4)

Scripts: `inspect/tracertraj_stats.py` (→ `results/tracertraj/stats.md`), `inspect/g4_dump.py`, `inspect/g4_label_check.py`.
Dump of 17 read trajectories: `results/tracertraj/close_reading_dump.txt`.

## 1. Data as loaded

- 3,998 rows: agentic 2,100 (1,822 "Injection Error" + 278 "Diagnosis Error" in `extra.error_source`), coding 1,268, math 630; loader maps `mistake_step` by matching `history[i].step` (100% agent match, see STATUS.md).
- Agentic rows are two different agents under one `assistant` name: a **deep-research agent** (`type: plan / action / summary`, tools `web_search`, `crawl_page`, `final_answer`; 1,506 injected + 238 diagnosed) and a **shell agent** (`action: run / finish`, `command:`, `observation:`; 316 injected + 40 diagnosed). The loader does not distinguish them; a regex on the step's first token does (`type` vs `action:`).
- Coding and math have `mistake_reason` and `ground_truth`; agentic has neither.
- **Hidden label sources** (new, §3e): coding rows split 679 injected / 589 diagnosed by two independent leaks (the task text contains `*_attacked_solution.py`; the reason starts "This step is critical because … By changing …"), the two agree on 1,244/1,268 rows; **all** math rows are injected (99.4% of reasons say "Injecting at this step ensures …").

## 2. Close-reading notes (17 trajectories)

Diagnosed agentic (8 read: 1242, 585, 54, 166, 273, 576, 387, 1429):
- **1242 / 585 / 54 / 387**: the labelled step is the `crawl_page` call (or the step right after a failed one); the tool returns `Error: crawl4ai is not installed`. The run then spends 10–14 steps on fruitless `web_search` calls and ends with "I was unable to locate …". The counterfactual "fix at step k" that made the replay succeed was presumably "do not call crawl_page, search for X instead" — i.e. the label blames the agent for an **environment outage**. A reader would not call the step wrong on its own (crawl_page is the correct tool); the only prefix cue is that the agent planned to use a tool that does not work.
- **576** (shell agent, label = last step 7): final answer "11:00 AM to 1:00 PM" where the question asked "when did Willow attend…"; the fix is a reformulation of the final answer. **273 / 166**: label on an early summarising step that picks the wrong candidate from a search result; continuation is consistent with it.
- **1429**: label step 3 where the agent notices "conflicting information between the two sources" and picks the wrong one; later steps re-verify and keep the wrong one — the one diagnosed case that looks like a genuine decisive choice.
- Overall: diagnosed labels are either (i) the final-answer step (42% by regex, §3b) or (ii) the step that hit a broken tool. The continuation after (ii) is a long natural dead-end with loud "No results found … Try a more general query" symptoms at every step — the symptoms are present but **not caused by the labelled step**; they are the environment.

Injected agentic (4 read: 1376, 136, 1203, 507):
- **1376 / 1203** (shell agent): the injected command is `grep … | sed "s/Sotheby's Auction House/Christie's Auction House/"` and `grep … | sed 's/"address":"4338 S Manhattan Ave"/"address":"4330 S Manhattan Ave"/'`: the perturbation operator *appends a substitution to the shell command* and the observation is rewritten in place. The artefact is in plain sight. In 1376 the very next step says "Wait, that's interesting. The grep command shows Christie's but earlier I saw Sotheby's" — the continuation **notices** the injection (symptom), then the run still answers wrong.
- **136** (shell agent, SQL): injected `SELECT COUNT(date)` instead of `COUNT(DISTINCT date)` → 100; plausible, silent.
- **507** (deep-research): the labelled `crawl_page` observation reports "46% expect similar hiring activity"; whether the number was altered is undecidable from the text (no GT). Deep-research injections edit the *observation content*, leaving no surface artefact.

Coding (3 read: 85, 193, 642) and math (2 read: 444, 428):
- **85** (12 steps, injected): reason "alters the cost calculation by adding an unnecessary increment" — the injected Engineer step is a code write; detectable only by reading the code against the spec. Task text says `Leetcode_9090_I_attacked_solution.py`.
- **642** (304 steps, injected): label at step 4 (first `dp` initialisation with `None`), followed by **294 Engineer steps** of edit–test–fail loops ("the implementation has been attempted multiple times, but the test cases have consistently failed"). The label is placed by the injector at the write; the 300-step tail is the natural consequence (the agent never finds the planted bug). This is the strongest "silent cause, 300 loud symptoms" trajectory in the group.
- **444** (math, injected at step 5 of 7): reason is the injector's plan ("Step 5 is the most decisive because it is where the final solution is derived … Injecting at this step ensures…"). **428**: the injected step is literally `I'm sorry, but I can't comply with that request.` — the injection prompt triggered a refusal and the refusal became the labelled error (12.2% of math rows, §3e).

## 3. Targeted statistics (`results/tracertraj/stats.md`)

### 3a. Label position and continuation by domain / label source

| domain/source | n | steps mean/median | rel pos | label = last agent step % | agent steps after | no continuation % | >=3 after % |
|---|---|---|---|---|---|---|---|
| agentic/Diagnosis Error | 278 | 10.7/9.0 | 0.69 | **47.8** | 3.4 | 47.8 | 34.5 |
| agentic/Injection Error | 1822 | 9.1/7.0 | 0.53 | 12.8 | 4.0 | 12.8 | 59.1 |
| coding (all) | 1268 | 20.9/14.0 | 0.46 | 3.7 | 11.5 | 3.7 | 93.0 |
| coding injected (attacked) | 679 | –/13 | 0.34 | 0.0 | – | – | – |
| coding diagnosed | 589 | –/15 | 0.59 | 8.0 | – | – | – |
| math (all injected) | 630 | 6.3/7.0 | 0.54 | 9.0 | 2.7 | 9.0 | 40.3 |

The two label sources behave oppositely to Who&When Pro: injections are *earlier* (rel 0.34–0.53, the injector picks a step where the error will propagate), counterfactual diagnoses are *later* (rel 0.59–0.69, 48% at the last agent step).

### 3b. What the labelled agentic step contains

| source | n | tool call % | final answer % | mentions error/wrong % | <200 chars % |
|---|---|---|---|---|---|
| Injection Error | 1822 | 6.3 | 13.0 | 9.3 | 0.4 |
| Diagnosis Error | 278 | 7.2 | **28.4** | 14.7 | 0.4 |

Regex on the labelled step: diagnosed labels call `crawl_page` in 28.8% (19.1% are the *first* crawl_page call of the run) vs 45.7% of injected (24.9% first call); the final-answer rate 42.1% (`final_answer` string) vs 13.0%. "crawl4ai is not installed" appears somewhere in 9.7% of diagnosed and 10.0% of injected runs — the outage hit both populations, but only the diagnoser turned it into a label.

### 3c. Symptom markers per step before / at / after the label

| group | marker | % before | % at label | % after |
|---|---|---|---|---|
| agentic/Diagnosis | self_correct | 15.8 | 15.5 | **23.7** |
| agentic/Diagnosis | uncertainty | 6.9 | 6.1 | **13.6** |
| agentic/Injection | self_correct | 13.0 | 6.5 | **20.3** |
| agentic/Injection | uncertainty | 3.6 | 3.8 | 6.4 |
| coding | repeat | 28.8 | 0.0 | **33.6** |
| coding | tool_error | 1.4 | 1.3 | 3.5 |
| math | self_correct | 1.2 | 3.5 | 4.8 |

- The deep-research agent self-corrects constantly (13–16% of steps *before* any label), so "wait/actually/re-check" is a style of the agent, not a symptom. After the label the rates rise by ~7 pp in both populations; the injected population's labelled step itself is *quieter* than its own prefix (6.5% vs 13.0%).
- Coding runs repeat themselves in a third of all steps before and after the label (edit–test loops); the repeat rate is not a localiser.

### 3d. The sed artefact (shell-agent injected rows)

| population | n | labelled step has `| sed "s/…/…/"` / `.replace(` | other agent steps |
|---|---|---|---|
| shell-agent injected | 316 | **18.0%** | — |
| shell-agent diagnosed | 40 | 2.5% | — |
| all agentic injected | 1822 | 3.1% | 2.6% |

A regex catches a fifth of the shell-style injections without reading anything else; the deep-research injections (83% of the injected rows) leave no such artefact.

### 3e. Hidden injection in coding / math (addendum in stats.md)

- coding: `attacked` in the task of 679 rows; cross-tab with reason style: (attacked, "This step is critical") 655, (natural, diagnosis-style) 589, (attacked, other) 24.
- math: 99.4% of reasons mention "inject"; 92.2% start with "Step N …" (the injector's choice rationale); 12.2% of labelled steps are refusals.

### 3f. LLM label-vs-content check (`g4_label_check.py tracertraj --per-subset 10`, 60 rows)

PENDING (fill in: local_wrong / contradicts_prefix / corrected_later / decisive per subset, split injected vs diagnosed for agentic).

## 4. Baseline error analysis

PENDING — background runner (`--n 60`) has not reached tracertraj; will run the same command and `analyze_baseline.py`, and split by error_source / domain. Expected from §3: diagnosed agentic rows should be "easy" for a last-step-biased judge (48% last step) and injected rows hard; coding rows with 100+ steps will mostly truncate.

## 5. Annotation / construction issues (prevalence)

1. **Undisclosed injection in coding (53.5%) and math (≈100%)**, leaking through the task filename and the reason text. The paper's "counterfactual replay vs injection" split is recoverable only via these leaks.
2. **Diagnosed labels converge on the final answer (42%) or on an environment outage (≈29% crawl_page / 9.7% "not installed")**: a DeepSeek-R1 "minimal fix at each step with ground truth" procedure finds that rewriting the final answer always works and that avoiding the broken tool works; neither is an agent mistake in the Who&When sense.
3. **Refusals as labelled errors** in 12.2% of math rows.
4. **Reason text written before the injection** (math 92%, coding 52%): `mistake_reason` is the injector's *plan*, not an explanation of the observed failure; it sometimes describes effects that did not materialise.
5. **Shell injections visible as `| sed`** in 18% of shell rows: a detector can learn the artefact instead of the error.
6. **Agentic `assistant` for every step**: agent accuracy is 100% by construction (report note); the plan/summary steps (`type: plan`, `type: summary`) are labelled in 11.5% of diagnosed rows, i.e. the "step" is sometimes a planning document, not an action.

## 6. Candidate hypotheses

**H1 (dataset) — Counterfactual-replay labels with GT access are last-step/outage labels.** Evidence: 47.8% last agent step, 42% final-answer, 29% crawl_page among diagnosed vs 12.8 / 13 / — among injected on the same agent and tasks. Tested (stats.md §f): on the 278 diagnosed rows the text-free "final-answer step" rule scores **47.5% exact** (first crawl_page call 19.1%, combo 47.8%) versus 12.1% on the injected rows; i.e. a judge that always blames the final answer matches AgenTracer-8B's reported agentic step accuracy (36.2%) on the diagnosed half without reading anything. Then re-diagnose 30 rows with an "earliest step whose fix succeeds, searching from the start" protocol to see whether earlier fixes also succeed (if yes, the released label is just the *last* successful fix, not the earliest). Shared with: ARx/FaP-style counterfactual labels in other groups; CE (rewritten step = decisive by construction, no such bias).

**H2 (group) — Injected labels are mid-trajectory and silent; natural/diagnosed labels are late and loud.** rel pos 0.34–0.53 vs 0.59–0.69; labelled-step self-correct 6.5% vs 15.5%. A judge calibrated on injected data will systematically predict *earlier* than one calibrated on natural data. Test: signed offset of the all-at-once baseline split by error_source (pending); expect negative median on injected, ≥0 on diagnosed.

**H3 — Long coding runs are "one planted bug, hundreds of symptoms".** 642: label at step 4, 294 repeated edit–test steps after. The repetition is the natural response of an agent that cannot see the planted bug; the labelled step is the only one that is *not* a repeat. Test: on the 13 coding rows ≥100 steps, score "first step that is never repeated later" / "first code write" vs the label; expect near-perfect for the attacked rows. Method: a change-point / novelty scorer (first occurrence of a content signature) is a cheap prior for injected coding data; worthless on natural data where the first write is often fine.

**H4 — Environment outages masquerade as agent errors in both label sources.** "crawl4ai is not installed" in 10% of agentic runs; diagnosed rows label the call, injected rows label something else but the run still suffers the outage. Test: LLM check `decisive = no_other` on rows containing the outage string (pending); a rule "if the labelled step's observation is an installation error, the label is an environment failure" with manual verification on 30 rows.

**H5 — Refusal-as-error and sed-as-error are detectable with trivial features**, so model accuracy on TracerTraj math/shell partly measures artefact detection. Test: train a bag-of-words step classifier on injected rows only, check whether it transfers to Who&When (it should not).

## 7. Open questions

- Which of the two agentic agents (deep-research vs shell) does the paper's agentic test split consist of, and is the 36.2% AgenTracer-8B step accuracy driven by the shell rows with artefacts?
- For coding diagnosed rows (589), what did the DeepSeek-R1 diagnoser see: the test output? (reason texts read like post-hoc analyses with test knowledge).
- Is "Injection Error" in agentic always a *response* perturbation (observation rewritten) or sometimes a prompt perturbation? The deep-research rows give no cue.
