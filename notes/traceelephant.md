# TraceElephant — dataset notes

## Identity

| Field | Value |
|---|---|
| Full title | *Seeing the Whole Elephant: A Benchmark for Failure Attribution in LLM-based Multi-Agent Systems* |
| Authors / affiliation | Mengzhuo Chen, Junjie Wang, Fangwen Mu, Yawen Wang, Zhe Liu, Huanxiang Feng, Qing Wang — State Key Laboratory of Complex System Modeling and Simulation Technology; Institute of Software, Chinese Academy of Sciences; University of Chinese Academy of Sciences, Beijing |
| Venue | ACL 2026 (long), ACL Anthology 2026.acl-long.912 |
| arXiv | [2604.22708](https://arxiv.org/abs/2604.22708) |
| Paper HTML | https://arxiv.org/html/2604.22708 |
| Code | https://github.com/TraceElephant/TraceElephant (agent-system code, LLM-API middleware used to record traces, `trace_locate` attribution code) |
| Data | https://huggingface.co/datasets/TraceElephant/TraceElephant (single `data.zip`, 597 MB) |
| License | CC BY 4.0 (HF card + GitHub LICENSE). Upstream tasks keep their own licenses (GAIA, AssistantBench, SWE-Bench Verified). |
| Availability | **Downloaded in full**, ungated. Only the 220 *failed* traces are released; the 160 successful runs mentioned in the paper are not in the zip. |
| On-disk size | 597 MB zip + 799 MB extracted (440 JSON files + 2 070 PNG screenshots); code repo clone ~ small |
| Local path | `/dataDisk/home/thanhdo/failure-attribution-datasets/data/traceelephant/extracted/data/<system-run-dir>/<run_id>/{trace_metadata.json, step_records.json, images/}`; code at `data/traceelephant/code_TraceElephant/` (not executed). |

## Description

**Purpose.** Failure attribution (responsible agent + decisive step) under *full execution observability*: unlike Who&When, which stores only agent outputs, every step here records the complete LLM-API call — the full input context (system prompt, all prior messages, tool results, screenshots), the raw model output, token usage, and tool-call logs — plus system metadata and runnable agent code. The paper's central claim: full traces raise attribution accuracy by up to 76 % (relative, step-level) over output-only observation.

**Construction.**
- Systems: **Captain-Agent** (AG2, dynamic team assembly: Orchestrator + generated `_Expert` agents + `Computer_terminal`), **Magentic-One** (AutoGen: Orchestrator + WebSurfer/FileSurfer/Coder/ComputerTerminal), **SWE-Agent** (single LLM agent whose "agents" are its tools `str_replace_editor`, `bash`, `submit`).
- Tasks: GAIA and AssistantBench validation sets for the two MAS; SWE-Bench Verified for SWE-Agent. Backbone GPT-4o, temperature 0.3, multiple trials, natural failure distribution preserved.
- Paper counts (Table): Captain-Agent GAIA 126 runs / 73 failed, AssistantBench 21 / 12; Magentic-One GAIA 119 / 74, AssistantBench 30 / 17; SWE-Agent 84 / 44 → 380 runs, 220 failed, 160 successful. The release contains exactly the 220 failed traces.
- Failures are **natural** (no injection). Traces were recorded with a non-intrusive LLM-API middleware (the code is released).
- **Annotation.** Three annotators with ≥ 1 year MAS development/debugging experience. Round 1 independent with confidence flags; uncertain cases resolved by discussion to consensus; final cross-review. Round-1 Krippendorff's α = 0.72 (agent) and 0.64 (step). Labels: `mistake_agent`, `mistake_step` (1-based LLM-call index), `mistake_reason` (free text). No failure-category taxonomy.
- Decisive step definition: earliest step after which failure becomes inevitable, with a role-aware/recoverability-aware adjustment (e.g. an orchestrator that could still recover is not blamed for a specialist's mistake).

**Task formulation & metrics.** Predict (agent, step) from the trace; agent-level accuracy and step-level accuracy (a tolerance-δ variant mentioned). Two settings: *static* (trace only) and *dynamic* (trace + replayable environment, allowing re-execution/intervention). Results averaged over 3 runs.

**Baselines (paper, GPT-4o backbone, all-system average, agent / step accuracy %).**

| Method | With ground-truth answer | Without ground-truth answer |
|---|---|---|
| All-at-Once | 62.2 / 28.1 | 58.0 / 22.7 |
| Binary Search | 38.9 / 12.9 | 37.4 / 9.1 |
| Step-by-Step | 60.9 / 16.7 | 54.0 / 12.5 |
| Static Agentic (theirs) | 65.9 / 30.3 | 59.1 / 26.1 |
| Dynamic Agentic (theirs) | 66.7 / 33.3 | 60.6 / 27.6 |

Ablation (Table 3): removing inputs + metadata from All-at-Once drops step accuracy from 0.28 to 0.16 (≈ 75 % relative) and agent accuracy by ≈ 22 %. Other backbones (GPT-4o-mini, Claude-4.5-Sonnet, DeepSeek-R1, Qwen3-32B, GPT-OSS-20B) are shown only in a radar chart; Claude-4.5-Sonnet, DeepSeek-R1 and GPT-4o are the strongest. o1 is not evaluated.

## Schema

Directory per run: `data/{captain-runs-gaia, captain-runs-assistantbench, magentic-runs-gaia, magentic-runs-assistant-bench, swe-agent-runs-swe-bench}/<run_id>/`.

`trace_metadata.json`

| Field | Meaning |
|---|---|
| `task_id` | Source task id (GAIA UUID, AssistantBench id, SWE-Bench instance id). |
| `task_instruction` | Full task prompt. |
| `ground_truth` | Expected answer (GAIA/AssistantBench only; absent for SWE-Bench where `tests_status` holds FAIL_TO_PASS / PASS_TO_PASS results). |
| `system_name` | `magentic-one` / `captain-agent` / `swe-agent`. |
| `agent_configuration` | Dict agent-name → import path (Magentic-One) or system prompt / `retrieved_tools` (Captain-Agent); empty for SWE-Agent. |
| `agent_system_intro` | Markdown description of the system's architecture (used as context for attribution). |
| `run_id` | Directory name. |
| `mistake_agent` | Label: responsible agent name. |
| `mistake_step` | Label: 1-based `step_id` of the decisive step (string). Two irregular values: `'none'` (assistant_bench_task_26: no single decisive step) and `'Step 36'`. |
| `mistake_reason` | Label: free-text explanation. |

`step_records.json` — list of steps, one per LLM invocation:

| Field | Meaning |
|---|---|
| `step_id` | 1-based sequential index. |
| `agent_id`, `agent_name` | Which agent made the call (SWE-Agent: name of the tool it invoked, i.e. `str_replace_editor`, `bash`, `submit`). |
| `input` | The full chat-completion request: `messages` (system prompt + prior conversation + tool results; screenshots as image parts), `model`, sampling params. |
| `output` | The raw chat-completion response (`choices[0].message.content`, `tool_calls`, `usage` tokens). |
| `tool_logs` | Tool-call records for that step (function name, arguments), or `null`. |

`images/step_<k>_image_<j>.png` — screenshots attached to the inputs of Magentic-One WebSurfer steps (2 070 files total; none for Captain-Agent/SWE-Agent).

## Statistics (computed from the data)

| Statistic | Overall | captain-agent | magentic-one | swe-agent |
|---|---|---|---|---|
| # released trajectories (all failed) | 220 | 85 | 91 | 44 |
| source benchmark | {'AssistantBench': 29, 'GAIA': 147, 'SWE-Bench Verified': 44} | {'AssistantBench': 12, 'GAIA': 73} | {'AssistantBench': 17, 'GAIA': 74} | {'SWE-Bench Verified': 44} |
| steps (LLM calls) per trajectory | mean 27.09, median 21.0, min 5, max 94 | mean 20.54, median 13, min 5, max 59 | mean 29.26, median 28, min 6, max 50 | mean 35.25, median 23.5, min 14, max 94 |
| steps histogram | 0-4: 0, 5-9: 30, 10-19: 67, 20-29: 45, 30-49: 56, 50-99: 22, >=100: 0 | 0-4: 0, 5-9: 20, 10-19: 37, 20-29: 10, 30-49: 7, 50-99: 11, >=100: 0 | 0-4: 0, 5-9: 10, 10-19: 18, 20-29: 20, 30-49: 42, 50-99: 1, >=100: 0 | 0-4: 0, 5-9: 0, 10-19: 12, 20-29: 15, 30-49: 7, 50-99: 10, >=100: 0 |
| distinct agent names per trajectory | mean 2.5, median 2.0, min 2, max 4 | mean 2.72, median 3, min 2, max 4 | mean 2.13, median 2, min 2, max 3 | mean 2.86, median 3.0, min 2, max 4 |
| annotated error step (1-based step_id) | mean 11.03, median 8, min 1, max 70 | mean 7.02, median 7, min 1, max 23 | mean 12.93, median 8.0, min 1, max 47 | mean 14.89, median 10.0, min 3, max 70 |
| relative position (step/len) | mean 0.47, median 0.4667, min 0.0172, max 1.0 | mean 0.46, median 0.4666666666666667, min 0.017241379310344827, max 0.92 | mean 0.49, median 0.45993589743589747, min 0.02564102564102564, max 1.0 | mean 0.45, median 0.47058823529411764, min 0.04819277108433735, max 0.9206349206349206 |
| output characters per trajectory (agent outputs + tool calls only) | mean 15089.49, median 9526.0, min 2224, max 45991 | mean 9673.46, median 7814, min 2680, max 42099 | mean 24002.66, median 22609, min 5360, max 45991 | mean 7118.23, median 5763.0, min 2224, max 18161 |
| total LLM tokens per trajectory (sum of usage.total_tokens; 0 where not logged) | mean 149358.17, median 55159.0, min 0, max 996647 | mean 109701.86, median 45554, min 6644, max 569060 | mean 258616.91, median 214127, min 10868, max 996647 | mean 0, median 0.0, min 0, max 0 |
| traces with non-numeric mistake_step ('none' / 'Step N') | 1 (magentic-runs-assistant-bench/assistant_bench_task_26_gpt_4o_r6uatbdru2pa) | | | |
| screenshots (png) per trajectory | mean 9.41, median 0.0, min 0, max 45 | mean 0, median 0, min 0, max 0 | mean 22.75, median 23, min 0, max 45 | mean 0, median 0.0, min 0, max 0 |

**Faulty agent distribution by system:**

*captain-agent*

| mistake_agent | count | % |
|---|---|---|
| WebServing_Expert | 28 | 32.9 |
| InformationExtraction_Expert | 25 | 29.4 |
| Orchestrator | 15 | 17.6 |
| DataVerification_Expert | 9 | 10.6 |
| Verification_Expert | 5 | 5.9 |
| CSVHandling_Expert | 2 | 2.4 |
| PythonProgramming_Expert | 1 | 1.2 |

*magentic-one*

| mistake_agent | count | % |
|---|---|---|
| WebSurfer | 57 | 62.6 |
| Orchestrator | 27 | 29.7 |
| FileSurfer | 5 | 5.5 |
| Coder | 2 | 2.2 |

*swe-agent*

| mistake_agent | count | % |
|---|---|---|
| str_replace_editor | 35 | 79.5 |
| bash | 8 | 18.2 |
| Orchestrator | 1 | 2.3 |



## Example trajectory

Run `captain-runs-gaia/gaia_task_9_gpt-4o_0su143t5rrfs` (system captain-agent, source GAIA), 5 steps (LLM calls), 2 distinct agents, 2680 output characters.

**Task:** Here's a fun riddle that I think you'll enjoy.

You have been selected to play the final round of the hit new game show "Pick That Ping-Pong". In this round, you will be competing for a large cash prize. Your job will be to pick one of several different numbered ping-pong balls, and then the game will commence. The host describes how the game works.

A device consisting of a winding clear ramp and a series of pistons controls the outcome of the game. The ramp feeds balls onto a platform. The platform has room for three ping-pong balls at a time. The three balls on the platform are each aligned with one of three pistons. At each stage of the game, one of the three pistons will randomly fire, ejecting the ball it strikes. If the piston ejects the ball in the first position on the platform the balls in the second and third position on the platform each advance one space, and the next ball on the ramp advances to the third position. If the piston ejects the ball in the second position, the ball in the first position is released and rolls away, the ball in the third position advances two spaces to occupy the first position, and the next two balls on the ramp advance to occupy the second and third positions on the platform. If the piston ejects the ball in the third position, the ball in the first position is released and rolls away, the ball in the second position advances one space to occupy the first position, and the next two balls on the ramp advance to occupy the second and t

**Ground-truth answer:** 3

Each step below shows the agent's *output* (plus tool calls) and, where present, the tool *observation* that was fed into the next step's input. The full per-step input context (system prompt + all prior messages) is in the raw record.

**Step 1 — Orchestrator**

> ```json
> {
>     "Retrieval specialist skilled at web search, browsing and summarizing evidence": "WebServing_Expert: A helpful assistant with access to a web browser. Ask them to perform web searches, open pages, navigate to Wikipedia, answer questions from pages, and or generate summaries.",
>     "Python coder who can read local files (csv, xlsx, pdf, image, audio) and verify answers with code": "CSVHandling_Expert: CSVHandling_Expert is a data analysis specialist proficient in handling CSV files  […]

**Step 2 — Orchestrator**

> CSVHandling_Expert

**Step 3 — CSVHandling_Expert**  **⟵ ANNOTATED ERROR STEP**

> ## ANSWER
> 1
> 
> ## REASON
> The first ball on the platform, which is initially ball number 1, is always in the position to be ejected first by the pistons. Given the mechanics of the game, the first ball has the highest probability of being ejected because it is always in the firing line of the pistons. Therefore, choosing ball number 1 maximizes the odds of winning the grand prize. 
> 
> TERMINATE

**Step 4 — Orchestrator**

> ## Task
> The task was to determine which numbered ping-pong ball a participant should choose in a game show to maximize the odds of winning a cash prize. The participant needed to select a ball that had the highest probability of being ejected by one of the pistons in a random sequence.
> 
> ## Results
> The conversation concluded with the recommendation to choose ball number 1.
> 
> ## Reason for the results
> The reasoning behind choosing ball number 1 is based on the mechanics of the game. The first ball  […]

**Step 5 — Orchestrator**

> ## ANSWER
> 1
> 
> ## REASON
> Ball number 1 should be chosen because it is always in the position to be ejected first by the pistons. This gives it the highest probability of being ejected, maximizing the chances of winning the prize.
> 
> TERMINATE


**Annotation:** mistake_agent = `CSVHandling_Expert`, mistake_step = `3` (1-based step_id), mistake_reason = "The mistake was assuming ball number 1 was most likely to be ejected, ignoring that all balls have equal chances due to random piston firing and changing positions.".


(normalised example written to /dataDisk/home/thanhdo/failure-attribution-datasets/notes/traceelephant_example_norm.json, 18.6 KB)


## Notes for the report

- **Step = one LLM invocation.** A "step" is an API call, not a message: for Magentic-One the orchestrator's plan, ledger update and speaker-selection calls are separate steps (hence ~29 steps/trace), and specialist tool actions appear as tool calls/observations inside the calls. For SWE-Agent (single agent), the `agent_name` is the *tool* the agent chose at that step (`str_replace_editor`, `bash`, `submit`), so "agent-level" attribution there is really tool-level attribution — 80 % of SWE-Agent labels blame `str_replace_editor`.
- **Full observability.** Each step stores the whole request context (`input.messages`, often tens of thousands of tokens: Magentic-One traces sum to ~259k prompt+completion tokens on average, max ~1M) and the raw response. Screenshots are stored as PNGs for Magentic-One WebSurfer steps (mean 23 per trace) and referenced from the inputs. SWE-Agent `usage` fields are all zero (token counts not logged), and Captain-Agent/SWE-Agent traces have no images.
- **Only failed traces are released** (220 = 85 Captain-Agent + 91 Magentic-One + 44 SWE-Agent); the 160 successful runs from the paper's 380 are not included, so success-vs-failure classification cannot be studied with this release.
- **Label quirks.** `mistake_step` is a string; one trace has `'none'` (annotators found no single decisive step) and one has `'Step 36'`. Blamed agents: Magentic-One → WebSurfer 63 %, Orchestrator 30 %; Captain-Agent → WebServing_Expert 33 %, InformationExtraction_Expert 29 %, Orchestrator 18 %. The decisive step lies on average at 47 % of the trace (median 47 %), similar to Who&When.
- **Comparison with Who&When.** Same two MAS and same benchmarks (GAIA, AssistantBench) but freshly collected runs (Dec 2025 timestamps, GPT-4o), a third system (SWE-Agent/SWE-Bench), developer-facing full traces, and reproducible agent-system code enabling *dynamic* attribution (re-execution from a step, counterfactual intervention). Step-level accuracies are correspondingly higher (28–33 % vs 5–25 %).
- **Reasons are short** (one or two sentences, e.g. "The PDF of the book is not displaying properly…"); no failure taxonomy. Inter-annotator agreement (α 0.72 agent / 0.64 step) is the only reported reliability figure among the four datasets besides MP-Bench's consensus rates.
- **Practical.** `data.zip` extracts to 799 MB; the per-step inputs are highly redundant (each step repeats the full conversation so far), so a renderer that shows only outputs + new tool observations (as done in the example above) is needed to fit a trace into a prompt.
