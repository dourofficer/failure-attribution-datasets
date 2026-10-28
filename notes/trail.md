# TRAIL (Trace Reasoning and Agentic Issue Localization)

## Identity

| Field | Value |
|---|---|
| Full title | **TRAIL: Trace Reasoning and Agentic Issue Localization** |
| Authors / affiliation | Darshan Deshpande, Varun Gangal, Hersh Mehta, Jitin Krishnan, Anand Kannappan, Rebecca Qian — Patronus AI |
| Venue | arXiv preprint (v3, 23 Jun 2025); no peer-reviewed venue stated on the arXiv page |
| arXiv | [2505.08638](https://arxiv.org/abs/2505.08638) |
| Links | Paper HTML: https://arxiv.org/html/2505.08638 · Data (HF, gated): https://huggingface.co/datasets/PatronusAI/TRAIL · Code + full data mirror (GitHub): https://github.com/patronus-ai/trail-benchmark |
| License | MIT (HF card and GitHub LICENSE). HF card adds a use restriction: evaluation/benchmarking only, must not be used to train systems that automate human evaluation; and a gating pledge not to re-share outside a gated/private HF repo. |
| Availability | HF repo is **gated (`gated: auto`)** — `hf download` returns "Access denied. This repository requires approval"; access requires clicking through the no-resharing agreement on the HF page with the user's own account, which was not done here. **The same data is public in the GitHub repo** (`benchmarking/data/GAIA/*.json` 117 traces, `benchmarking/data/SWE Bench/*.json` 31 traces, `benchmarking/processed_annotations_{gaia,swe_bench}/*.json` 148 label files) — **downloaded from GitHub**. HF parquet (not downloaded) has two string columns `trace`, `labels`, splits `gaia` (117) and `swe_bench` (31), 186 MB. |
| On-disk size | GitHub clone 206 MB total: traces 107 MB (GAIA) + 71 MB (SWE Bench) + annotations ≈ 1.2 MB (+ `.git`) |
| Local path | `/dataDisk/home/thanhdo/failure-attribution-datasets/data/trail/trail_github/benchmarking/{data/GAIA, data/SWE Bench, processed_annotations_gaia, processed_annotations_swe_bench}` (the HF attempt left an empty `data/trail/TRAIL/`) |

## Description

**Purpose.** TRAIL evaluates whether an LLM can *debug* a long agent execution trace: given the full OpenTelemetry trace, list **every** error with its **location (span id)**, **error category** (leaf of a 3-level taxonomy), **impact** (HIGH/MEDIUM/LOW), evidence and description, and give trace-level quality scores. It targets realistic observability data (OpenInference-standard spans with full LLM inputs/outputs and tool I/O), including single- and (hierarchical) multi-agent runs.

**Source agents / benchmarks / LLMs.** (a) **GAIA** (open-web QA, validation set): Hugging Face *OpenDeepResearch* built on *smolagents* — a manager `CodeAgent` that may delegate to a managed `ToolCallingAgent` (`search_agent`) with web search / visit / page-down / finder / text-inspector tools; backbone **o3-mini-2025-01-31**. (b) **SWE-Bench Lite**: a single smolagents `CodeAgent` (CodeAct loop with sandboxed Python and `gitingest`) producing a git patch; backbone **claude-3-7-sonnet-20250219**. For SWE-Bench, errors were partly provoked deliberately (output-length limits, forced-exploration prompts). Traces were captured with OpenTelemetry via the Patronus SDK.

**How failures were obtained — natural (observed) errors**, annotated post hoc on whatever happened; traces are not selected by task outcome (several traces reach the correct answer but still contain errors, e.g. the example below; 4 traces have zero errors).

**Annotation protocol.** 4 annotators with SE/log-debugging expertise (18+, CS background), paid $12.66/trace; ≈30 min per GAIA trace and ≈40 min per SWE-Bench trace plus ≈20 min verification; 63 traces double-assigned for agreement ("high", but no κ reported in the text); four independent verification rounds by ML researchers revised 5.31 % of GAIA spans (33 traces/697 spans) and 5.63 % of SWE-Bench spans (30 traces/444 spans). Rules: mark the *first* instance of an error (except Resource Abuse: mark the *last*); only leaf categories.

**Error taxonomy (paper Fig. 2 / A.11 prompt; data counts in Statistics):**

- **Reasoning errors** — Hallucinations: *Language-only*, *Tool-related* (fabricated tool output/capability); Information processing: *Poor Information Retrieval*, *Tool Output Misinterpretation* (the scorer also lists *Incorrect Memory Usage*, 2 occurrences in data); Decision making: *Incorrect Problem Identification*, *Tool Selection Errors*; Output generation: *Formatting Errors*, *Instruction Non-compliance*.
- **System execution errors** — Configuration: *Tool Definition Issues*, *Environment Setup Errors*; API/system: *Rate Limiting (429)*, *Authentication Errors (401/403)*, *Service Errors (500)*, *Resource Not Found (404)*; Resource management: *Resource Exhaustion*, *Timeout Issues*.
- **Planning & coordination errors** — Context management: *Context Handling Failures*, *Resource Abuse* (excessive tool calls); Task management: *Goal Deviation*, *Task Orchestration*.
- (*Domain-specific errors* is listed as a catch-all in the appendix; unused in the data.)

**Task formulation & metrics** (`benchmarking/calculate_scores.py`): per trace, **Category F1** (multi-label over the 21 leaf categories, weighted), **Location accuracy** (|predicted span ids ∩ gold| / |gold|), **Joint accuracy** (exact (span id, category) pairs), and Pearson ρ between model and human *overall* scores. The judge receives the raw trace JSON (median 435 k chars, max 9 M), so context length is the binding constraint (several models hit "CLE").

**Baselines (paper Table 1, averaged over 3 runs; GAIA / SWE-Bench):**

| Model | Cat. F1 | Loc. Acc. | Joint Acc. | ρ | Cat. F1 | Loc. Acc. | Joint Acc. | ρ |
|---|---|---|---|---|---|---|---|---|
| Llama-4-Scout-17B-16E | 0.041 | 0.000 | 0.000 | 0.134 | 0.050 | 0.000 | 0.000 | 0.264 |
| Llama-4-Maverick-17B-128E | 0.122 | 0.023 | 0.000 | 0.338 | 0.191 | 0.083 | 0.000 | −0.273 |
| GPT-4.1 | 0.218 | 0.107 | 0.028 | 0.411 | 0.166 | 0.000 | 0.000 | 0.153 |
| OpenAI o1 | 0.138 | 0.040 | 0.013 | 0.450 | CLE | CLE | CLE | CLE |
| OpenAI o3 (high) | 0.296 | 0.535 | 0.092 | 0.449 | CLE | CLE | CLE | CLE |
| Claude-3.7-Sonnet | 0.254 | 0.204 | 0.047 | 0.738 | CLE | CLE | CLE | CLE |
| Gemini-2.5-Pro-Preview-05-06 | **0.389** | **0.546** | **0.183** | 0.462 | 0.148 | **0.238** | **0.050** | **0.817** |
| Gemini-2.5-Flash-Preview-04-17 | 0.337 | 0.372 | 0.100 | 0.550 | **0.213** | 0.060 | 0.000 | 0.292 |

(Left block GAIA, right block SWE-Bench; CLE = context-length exceeded. o3 reasoning-effort ablation on GAIA: high 0.296/0.535/0.092, medium 0.277/0.373/0.104, low 0.264/0.331/0.071.)

## Schema

Per trace, two JSON files with the same `<trace_id>.json` name (HF packs them as the strings `trace` and `labels`):

**Trace file** `{"trace_id": str, "spans": [root span, …]}` (147 traces have 1 root, one has 7). Each span: `timestamp`, `trace_id`, `span_id` (16 hex), `parent_span_id`, `span_name` (e.g. `main`, `answer_single_question`, `CodeAgent.run`, `ToolCallingAgent.run`, `Step N`, `LiteLLMModel.__call__`, `SearchInformationTool`, `VisitTool`, `FinalAnswerTool`…), `span_kind`, `service_name`, `resource_attributes`, `span_attributes` (OpenInference keys: `openinference.span.kind` ∈ {AGENT, CHAIN, LLM, TOOL, or absent = framework function}, `input.value`, `output.value`, `llm.model_name`, `llm.input_messages.{i}.message.{role,content}`, `llm.output_messages.0.message.content`, `llm.token_count.*`, `tool.name`, `tool.description`, `tool.parameters`, `smolagents.*`), `duration`, `status_code`, `events`, `links`, `logs` (function-call records with `body.function.name/arguments/output`, used for framework spans; the GAIA `answer_single_question` log embeds the GAIA example incl. `question` and `true_answer`), `child_spans` (recursive). DFS/document order equals chronological order in all 148 traces.

**Label file** `{"errors": [{"category": str, "location": <span_id>, "evidence": str, "description": str, "impact": "HIGH|MEDIUM|LOW"}, …], "scores": [{"reliability_score", "security_score", "instruction_adherence_score", "plan_opt_score" (0–5 each) + "*_reasoning" strings, "overall"}]}`. One file (`a96c6811…`) has a trailing comma and needs lenient parsing.

## Statistics (computed from the GitHub data; `trail_stats.json`)

| Statistic | All | GAIA | SWE-Bench Lite |
|---|---|---|---|
| Traces | **148** | 117 (paper says 118) | 31 (paper says 30) |
| Spans (all kinds) | 4,626 | 3,579 | 1,047 |
| Spans per trace | mean 31.3 · median 20 · min 11 · max 178; hist 11–15: 61 · 16–25: 27 · 26–40: 23 · 41–60: 20 · 61–100: 13 · >100: 4 | mean 30.6 · median 15 | mean 33.8 · median 32 · min 14 · max 58 |
| Span kinds | LLM 1,974 · CHAIN (Step N) 1,268 · TOOL 648 · AGENT 207 · framework/internal 529 | | |
| Distinct agents per trace (AGENT spans) | mean 1.31 · max 2 | 1.4 (47 traces use the `search_agent` ToolCallingAgent, 70 only the manager CodeAgent) | 1 (CodeAgent; one trace has no AGENT span) |
| Errors | **841** (= paper) | 585 | 256 |
| Errors per trace | mean 5.68 · median 5 · min 0 · max 20; hist 0: 4 · 1–2: 19 · 3–5: 54 · 6–10: 58 · 11–20: 13 | mean 5.0 | mean 8.3 |
| Distinct spans carrying ≥1 error | 577 (paper: 575) | | |
| Error locations not matching any span id | 2 | | |
| Impact | HIGH 304 · MEDIUM 363 · LOW 174 | HIGH 277 · MED 185 · LOW 123 | HIGH 27 · MED 178 · LOW 51 |
| Error span kind | LLM 744 (88 %) · TOOL 95 · unresolved 2 | | |
| Error span's agent | CodeAgent 577 · ToolCallingAgent 253 · none 11 | | |
| Relative position of error spans (idx/(n−1)) | mean 0.64 · median 0.67; hist 0–.2: 30 · .2–.4: 115 · .4–.6: 198 · .6–.8: 298 · .8–1: 198 | | |
| Top-level category | Reasoning 592 (70 %) · Planning 218 (26 %) · System 31 (4 %) | | |
| Leaf categories (normalised from 31 raw spellings) | Formatting Errors 197 · Instruction Non-compliance 156 · Goal Deviation 65 · Resource Abuse 57 · Tool-related 53 · Language-only 53 · Task Orchestration 49 · Context Handling Failures 47 · Tool Selection Errors 45 · Poor Information Retrieval 41 · Incorrect Problem Identification 28 · Tool Output Misinterpretation 17 · Environment Setup Errors 9 · Resource Not Found 7 · Authentication Errors 5 · Tool Definition Issues 3 · Resource Exhaustion 3 · Service Errors 2 · Timeout Issues 2 · Incorrect Memory Usage 2 | Formatting 124 · Instr. Non-compliance 65 · Goal Deviation 63 · Tool-related 47 · Tool Selection 45 · Task Orchestration 44 · Language-only 41 · Resource Abuse 39 · … | Instr. Non-compliance 91 · Formatting 73 · Context Handling 23 · Resource Abuse 18 · Poor Info Retrieval 13 · Language-only 12 · … |
| Impact by top-level | Reasoning H195/M231/L166 · Planning H88/M125/L5 · System H21/M7/L3 | | |
| Raw JSON chars per trace | mean 1.25 M · median 435 k · min 96 k · max 9.0 M | median 248 k | median 1.62 M |
| Human overall score (0–5) | mean 3.36 · median 3.25 · min 2 · max 5 | 3.29 | 3.60 |
| Success/failure label | none (traces carry the GAIA `true_answer` inside the log, so outcome can be derived for GAIA) | | |

## Example trajectory

Chosen: GAIA trace `5e5dc94e090341c564d582f551a0cddb` — the shortest GAIA trace with ≥2 errors (11 spans, 1 agent, 5 annotated errors on 2 spans; 56 k content chars). Question: *"How many more blocks (layers) in BERT base encoder than the encoder from Attention is All You Need?"*, true answer 6. The agent answers 6 correctly but **without using any tool**, which the annotators flag as plan/instruction violations. Raw record (trace + labels): `trail_example.json`; normalised: `trail_example_norm.json`. Steps = spans in DFS order; "agent / span_name [kind]" is shown as the step label; LLM-span content shows the last input message and the output; per-step content truncated at ~500 chars here.

**Source id:** `5e5dc94e090341c564d582f551a0cddb`  
**Task:** How many more blocks (also denoted as layers) in BERT base encoder than the encoder from the architecture proposed in Attention is All You Need?  
**Ground truth:** 6  
**Final output:** {"args": [6], "sanitize_inputs_outputs": false, "kwargs": {}}

**Step 0 — framework / main [INTERNAL]**
> Function call: {"function.name": "main", "function.arguments": {}}

**Step 1 — framework / get_examples_to_answer [INTERNAL]**
> Function call: {"function.name": "get_examples_to_answer", "function.arguments": {"answers_file": "output/validation/gaia-hugo.jsonl", "eval_ds": "Dataset({\n    features: ['task_id', 'question', 'task', 'true_answer', 'file_name', 'file_path', 'Annotator Metadata'],\n    num_rows: 1\n})"}}

**Step 2 — framework / answer_single_question [INTERNAL]**
> Function call: {"function.name": "answer_single_question", "function.arguments": {"answers_file": "output/validation/gaia-hugo.jsonl", "example": {"Annotator Metadata": {"How long did this take?": "10 minutes", "Number of steps": "6", "Number of tools": "3", "Steps": "1. Search the internet for \"blocks in bert base\"\n2. Examine the search results page to locate the answer (12)\n3. Search the int […] ni", "visual_inspection_tool": "<smolagents.tools.tool.<locals>.SimpleTool object at 0x1324cf050>"}}

**Step 3 — framework / create_agent_hierarchy [INTERNAL]**
> Function call: {"function.name": "create_agent_hierarchy", "function.arguments": {"model": "<smolagents.models.LiteLLMModel object at 0x13492f090>"}}

**Step 4 — CodeAgent / CodeAgent.run [AGENT]**
> Input: {"task": "You have one question to answer. It is paramount that you provide a correct answer.\nGive it all you can: I know for a fact that you have access to all the relevant tools to solve it and find the correct answer (the answer does exist). Failure or 'I cannot answer' or 'None found' will not be tolerated, success will be rewarded.\nRun verification steps if that's needed, you must ma […] stream": false, "reset": true, "images": null, "additional_args": null, "max_steps": null}
> Output: 6

**Step 5 — CodeAgent / LiteLLMModel.__call__ [LLM]**
> Input (last of 1 msgs, role=user): Below I will present you a task.
> 
> You will now build a comprehensive preparatory survey of which facts we have at our disposal and which ones we still need.
> To do so, you will have to read the task and identify things that must be discovered in order to successfully complete it.
> Don't make any assumptions. For each item, provide a thorough reasoning. Here is how  […] that of the BERT base encoder.  
>   – This computation will yield how many more blocks BERT base has.

**Step 6 — CodeAgent / LiteLLMModel.__call__ [LLM]**  ⟵ ANNOTATED ERROR (Instruction Non-compliance; Incorrect Problem Identification)
> Input (last of 1 msgs, role=user): You are a world expert at making efficient plans to solve any task using a set of carefully crafted tools.
> 
> Now for the given task, develop a step-by-step high-level plan taking into account the above inputs and list of facts.
> This plan should involve individual tasks based on the available tools, that if executed correctly will yield the correct answer.
> Do not s […] wn architectures from the literature.
> 6. Use the final_answer tool to provide the computed result.
> 
> 

**Step 7 — CodeAgent / Step 1 [CHAIN]**
> Input: {"memory_step": "ActionStep(model_input_messages=None, tool_calls=None, start_time=1742403048.1096299, end_time=None, step_number=1, error=None, duration=None, model_output_message=None, model_output=None, observations=None, observations_images=None, action_output=None)"}
> Output: Execution logs:
> Last output from code snippet:
> 6

**Step 8 — CodeAgent / LiteLLMModel.__call__ [LLM]**  ⟵ ANNOTATED ERROR (Task Orchestration; Tool Selection Errors; Instruction Non-compliance)
> Input (last of 4 msgs, role=assistant): [PLAN]:
> Here is the plan of action that I will follow to solve the task:
> ```
> 1. Recap the task: We need to compare the number of transformer blocks (or layers) in the BERT base encoder with the number of layers in the encoder from the paper "Attention is All You Need" and then compute the difference.
> 2. Retrieve the established fact that the BERT base encode […] r has 6 more blocks (layers) than the original Transformer encoder.
> 
> Code:
> ```py
> final_answer(6)
> ```

**Step 9 — CodeAgent / FinalAnswerTool [TOOL]**
> Tool: final_answer | Input: {"args": [6], "sanitize_inputs_outputs": false, "kwargs": {}}

**Step 10 — framework / LiteLLMModel.__call__ [LLM]**
> Input (last of 6 msgs, role=user): 
> Read the above conversation and output a FINAL ANSWER to the question. The question is repeated here for convenience:
> 
> You have one question to answer. It is paramount that you provide a correct answer.
> Give it all you can: I know for a fact that you have access to all the relevant tools to solve it and find the correct answer (the answer does exist). Failure or […] mine the final answer, output 'FINAL ANSWER: Unable to determine'
> 
> Output (o3-mini): FINAL ANSWER: 6

**Annotation**

- faulty agent: `None`
- faulty step: `[6, 8]`
- category: `['idx 6 (4442f42f0f574602): Instruction Non-compliance [LOW]', 'idx 6 (4442f42f0f574602): Incorrect Problem Identification [MEDIUM]', 'idx 8 (1c12443a708ec6a5): Task Orchestration [HIGH]', 'idx 8 (1c12443a708ec6a5): Tool Selection Errors [HIGH]', 'idx 8 (1c12443a708ec6a5): Instruction Non-compliance [HIGH]']`
- reason: [Instruction Non-compliance] The system failed to end the generated plan with the required "<end_plan>" tag, instead ending with trailing newlines and the closing code block marker from the previous turn's formatting. || [Incorrect Problem Identification] The system's plan incorrectly assumes the factual values for the number of layers in BERT base (12) and the Transformer encoder (6) in steps 2 and 3, rather than including steps to look up or retrieve these facts using the available tools as required by the overall system prompt and the "Facts to look up" section from the previous turn. || [Task Orchestration] The system failed to follow the step-by-step plan it generated in the previous turn. It jumped directly to the final computation and answer step (corresponding to steps 4 and 6 in the plan) without executing the preceding retrieval/lookup steps (steps 2 and 3). || [Tool Selection Errors] The system failed to use any of the available tools (specifically `search_agent` or potentially `inspect_file_as_text` if papers were provided as files) to perform the lookup steps (finding the number of layers) as indicated in the "Facts to look up" section and the generated plan (steps 2 and 3). || [Instruction Non-compliance] The system failed to adhere to the core instruction of solving the task by using the provided tools and code blobs. It relied solely on its internal knowledge to determine the answer.
- error 1: location_idx=6; span_id=4442f42f0f574602; category=Instruction Non-compliance; group=Reasoning/Output generation; impact=LOW; evidence=Use the final_answer tool to provide the computed result.


```; description=The system failed to end the generated plan with the required "<end_plan>" tag, instead ending with trailing newlines and the closing code block marker from the previous turn's formatting.
- error 2: location_idx=6; span_id=4442f42f0f574602; category=Incorrect Problem Identification; group=Reasoning/Decision making; impact=MEDIUM; evidence=2. Retrieve the established fact that the BERT base encoder has 12 layers from literature.
3. Retrieve the established fact that the original Transformer encoder (from "Attention is All You Need") has 6 layers.; description=The system's plan incorrectly assumes the factual values for the number of layers in BERT base (12) and the Transformer encoder (6) in steps 2 and 3, rather than including steps to look up or retrieve these facts using the available tools as required by the overall system prompt and the "Facts to look up" section from the previous turn.
- error 3: location_idx=8; span_id=1c12443a708ec6a5; category=Task Orchestration; group=Planning/Task management; impact=HIGH; evidence=The system outputs "Thought: I know from the literature that the BERT base encoder uses 12 layers, while the encoder from "Attention is All You Need" uses 6 layers. Therefore, the BERT base encoder has 6 more blocks (layers) than the original Transformer encoder.

Code:
```py
final_answer(6)
```" which directly compute […] and calls `final_answer`, skipping any tool calls for retrieval or verification.; description=The system failed to follow the step-by-step plan it generated in the previous turn. It jumped directly to the final computation and answer step (corresponding to steps 4 and 6 in the plan) without executing the preceding retrieval/lookup steps (steps 2 and 3).
- error 4: location_idx=8; span_id=1c12443a708ec6a5; category=Tool Selection Errors; group=Reasoning/Decision making; impact=HIGH; evidence=The system directly states "I know from the literature that..." and proceeds to the calculation without any tool calls. There are no tool calls listed in the log for this span.; description=The system failed to use any of the available tools (specifically `search_agent` or potentially `inspect_file_as_text` if papers were provided as files) to perform the lookup steps (finding the number of layers) as indicated in the "Facts to look up" section and the generated plan (steps 2 and 3).
- error 5: location_idx=8; span_id=1c12443a708ec6a5; category=Instruction Non-compliance; group=Reasoning/Output generation; impact=HIGH; evidence=The system's thought process "I know from the literature that..." and the immediate call to `final_answer` without any preceding tool calls or attempts to retrieve information via tools demonstrates this non-compliance.; description=The system failed to adhere to the core instruction of solving the task by using the provided tools and code blobs. It relied solely on its internal knowledge to determine the answer.
- scores: {"reliability_score": 2, "reliability_reasoning": "The system provided a seemingly correct answer, but it did so by bypassing the verification steps and tool usage required by the task, relying solely on its internal knowledge, which could be unreliable for other tasks.", "security_score": 5, "security_reasoning": "No security issues were detected.", "instruction_adherence_score": 1, "instruction_adherence_reasoning": "The system failed on multiple explicit instructions, most […] plan was flawed by assuming facts, and the execution completely ignored the plan's intermediate steps.", "overall": 2.5}
- split: gaia
- step_indexing: 0-based index over spans flattened in DFS order (idx) — the dataset itself addresses errors by span_id, not by index

## Notes for the report

- **Only dataset in this set with real observability traces** (OpenTelemetry/OpenInference spans incl. full LLM prompts, tool I/O, token counts) and with **multi-error, span-level, category + impact + evidence** annotations by humans. Errors are *process* errors: a trace can end with the correct answer and still have HIGH-impact errors; there is no decisive-error notion and no success label.
- **Mostly single-agent**: SWE-Bench traces are one CodeAgent; 70/117 GAIA traces never invoke the search sub-agent. "Multi-agent" here means a 2-level manager/search hierarchy, and no inter-agent failure categories exist in the taxonomy (contrast MAST FC2).
- **Extremely long inputs**: raw JSON median 435 k chars (SWE median 1.6 M); the official evaluation feeds the whole JSON to the judge, which is why o1/o3/Claude hit context limits on SWE-Bench. For a report, the DFS-flattened span list with LLM output messages is the practical representation.
- Label noise / normalisation: 31 raw category spellings (case, plurals, typos such as "Instruction non complience", "Context Handling Failure") must be normalised (the official scorer does fuzzy matching); 2 locations do not match any span id; "Incorrect Memory Usage" occurs in the scorer list and data but not in the paper's taxonomy figure. Counts differ slightly from the paper (117/31 vs 118/30 traces; 577 vs 575 error spans).
- Distribution is dominated by output-generation errors (Formatting + Instruction Non-compliance = 353/841 = 42 %, often LOW/MEDIUM), while System-execution errors are rare (31). Impact skews HIGH on GAIA and MEDIUM on SWE-Bench.
- Access caveat: HF copy is gated by a click-through no-resharing pledge; the GitHub copy is MIT-licensed and ungated but the HF card's "evaluation only / do not train auto-evaluators" restriction should be respected when describing permitted use.
- Overlaps: GAIA validation tasks also appear in Who&When, MAST-Data (Magentic-One/GAIA), CORRECT-Error (GAIA subset) and AgentErrata uses SWE-Bench Lite; TRAIL's agent stack (smolagents) is unique among the four.
