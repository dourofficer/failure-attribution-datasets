# MemTrace / MemTraceBench

## Identity

| Field | Value |
|---|---|
| Full title | **MemTrace: Tracing and Attributing Errors in Large Language Model Memory Systems** |
| Authors | Xinle Deng, Ruobin Zhong, Hujin Peng, Xiaoben Lu, Yanzhe Wu, Guang Li, Buqiang Xu, Yunzhi Yao, Jizhan Fang, Haoliang Cao, Junjie Guo, Yuan Yuan, Ziqing Ma, Yuanqiang Yu, Rui Hu, Baohua Dong, Hangcheng Zhu, Ningyu Zhang — Zhejiang University (ZJUNLP) with industry co-authors (affiliations not on the abstract page) |
| Venue | arXiv preprint, marked "Ongoing work" (v1 27 May 2026, v4 8 Oct 2026) |
| arXiv id | 2605.28732 |
| Paper | https://arxiv.org/abs/2605.28732 (HTML: https://arxiv.org/html/2605.28732) |
| Code | https://github.com/zjunlp/MemTrace (MIT); graph-generation code: https://github.com/zjunlp/MemBase (`examples/trace_memory_lifecycle_with_membase`); graph format: https://github.com/zjunlp/smartcomment |
| Data | https://huggingface.co/datasets/zjunlp/MemTraceBench (MIT, not gated, last modified 2026-10-08) |
| License | MIT (dataset card and paper) |
| Availability | **Released, downloaded in full** (`hf download zjunlp/MemTraceBench`). |
| On-disk size | **6.0 GB** — 103 JSON execution graphs (rag 299 MB / mem0 353 MB / long_context 2.2 GB / evermemos 2.9 GB; single files from 6.6 MB up to 532 MB) |
| Local path | `/dataDisk/home/thanhdo/failure-attribution-datasets/data/memtrace/{rag,mem0,evermemos,long_context}/*.json` (+ `README.md`, `annotation_overview.png`) |

Caveat on counts: the task brief says "160 traces"; the release contains **103 execution graphs** carrying **238 failure annotations**, of which **160 are memory-system failures** (40 per memory system) — the remaining 75 are *Annotation Error* (67 unique queries after de-duplication across systems) and 3 are *LLM-as-a-Judge Error*. The paper's README table (rag 56 / mem0 66 / evermemos 54 / long_context 62 annotations) matches our count exactly. The README says 30/19/20/34 graphs; we find 30/19/20/34 (=103).

## Description

**Purpose.** MemTrace targets failure attribution inside *LLM memory systems* rather than inside a planner/tool loop. A memory pipeline (extraction → update/delete → retrieval → answer generation) is instrumented so that every run becomes an *execution graph* ("memory evolution graph"): a directed acyclic bipartite graph of **variable nodes** (messages, extracted facts, memory units, retrieved results, prompts, predictions) and **operation nodes** (extraction, update, deletion, retrieval, filtering, judging, answer generation), connected by information-flow edges. Given a failed query (prediction ≠ gold), the task is to find the *earliest decisive faulty operation* o* and its error type.

**How it was built.**
- *Memory systems (4):* Long-Context (whole history in the prompt), Naive RAG, Mem0, EverMemOS — all run with **GPT-4.1-mini** for memory construction and answering; Qwen3-Embedding-4B / Qwen3-Reranker-4B for embedding/reranking (EverMemOS); **Claude Opus 4.5** as LLM-as-a-Judge for answer correctness.
- *Source benchmarks (3 multi-session conversational memory QA sets):* LoCoMo, LongMemEval, RealMem (file names `locomo_*`, `longmemeval_*`, `realmem_*`).
- *Failures are natural:* the instrumented systems were run on the conversations; 1,514 judged-wrong answers were collected (RAG 467, Long-Context 279, Mem0 466, EverMemOS 302 over 138/132/87/80 graphs) and then annotated until 40 system-caused failures per system were confirmed.
- *Annotation protocol:* five annotators from the author team (all familiar with the four systems), >10-page guideline, Streamlit annotation UI. Stage 1: each system's cases assigned to three annotators independently until 40 system-related errors per system; Stage 2: fill in missing labels so every case has three labels; Stage 3: majority vote + group discussion. Annotators first rule out *annotation errors* (gold answer not supported by the conversation) and *judge errors* (answer actually acceptable), then identify the earliest decisive faulty operation, its cause and error type. Pairwise disagreement 3–46 %; no kappa reported. The released `reason` text is the human reasons aggregated and polished by GPT-5.5.
- *Output:* 160 memory-failure cases (+75 annotation-error, +3 judge-error cases kept in the files).

**Label types.** Per failed query: `final_error_type` (7-way), `final_op_id` (operation-level root cause = "step" and "agent/component" at once), `reason` (free text), `source_evidence(_ids)` (gold evidence messages), `golden_answers`, `prediction`. There is no agent-role label; the *operation category* (extraction / update / retrieval / evaluation …) plays the role of the faulty component.

**Error taxonomy (7 types; definitions from Appendix D.5):**

| Error type | Definition | n (all 238) |
|---|---|---|
| Annotation Error | gold answer not supported by the evidence / wrong gold | 75 (67 unique queries) |
| LLM-as-a-Judge Error | answer acceptable but judged wrong | 3 |
| Extraction Error | critical information never enters any memory unit | 19 |
| Update Error | a later update removes or degrades critical information already stored | 31 |
| Deletion Error | a memory unit holding critical information is explicitly deleted | 0 (none observed; Mem0 deletes are 1 % of ops) |
| Retrieval Error | information is in the store but retrieval leaves it out of the final context | 76 |
| Response Error | the retrieved context contains all evidence but the answer LLM still fails | 34 |

**Task formulation and metrics.** Input: a failed execution graph G for question q plus the golden answer. Output: o* = argmin over decisive faulty operations of time t_o (singleton setting; a "Decisive Error Set" generalisation is discussed in App. F but not implemented) and the error type. Metrics: **ETA** (error-type accuracy) and **OIA** (operation-identification accuracy), plus token cost and runtime. The proposed MemTrace attributor walks operation sub-graphs backwards from the prediction (MemTrace-OBS = observation-only variant).

**Baselines (paper Table 1, accuracy %, overall over the 160 cases):**

| Backbone | Method | Overall ETA | Overall OIA | LC OIA | RAG OIA | Mem0 OIA | EverMemOS OIA |
|---|---|---|---|---|---|---|---|
| GPT-4.1-mini | All-at-Once | 31.9 | 13.1 | 5.0 | 27.5 | 7.5 | 12.5 |
| GPT-4.1-mini | MemTrace-OBS | 20.0 | 9.4 | 3.3 | 17.5 | 16.7 | 0.0 |
| GPT-4.1-mini | MemTrace | 36.5 | 14.2 | 4.2 | 26.7 | 23.3 | 2.5 |
| GPT-5.4 | All-at-Once | 51.9 | 18.8 | 0.0 | 52.5 | 5.0 | 17.5 |
| GPT-5.4 | MemTrace-OBS | 53.8 | **46.3** | 7.5 | 87.5 | 55.0 | 35.0 |
| GPT-5.4 | MemTrace | **54.4** | 38.1 | 20.0 | 65.8 | 59.2 | 7.5 |

Downstream use: attribution signals used to rewrite Mem0 prompts improved LoCoMo end-task accuracy by up to 7.62 points.

## Schema

Layout: `<split>/<source>_<conversation-id>.json`, one file per (memory system, conversation) = one serialised `smartcomment` execution graph. Splits = memory systems (`rag`, `mem0`, `evermemos`, `long_context`); the HF `configs` map each split to `split/*.json`.

Top level: `graph_id`, `user_id` (conversation id), `project_id` (e.g. `TracedMem0`), `storage_path`, `strict`, `driver_type`, `created_at`, `metadata` (`memtracebench_system`, `memtracebench_dataset_source` ∈ {LoCoMo, LongMemEval, RealMem}, `layer_type`, save dirs), `data`.

`data` has five lists:

| List | Key fields (one line each) |
|---|---|
| `nodes` (variables) | `full_node_id` (= `name@version`), `name`, `version`, `category` (message, memory_entry, llm_response, prompt, similar_memories, memory_context, prediction, golden_answers, query …), `value` (the payload, often JSON-as-string), `comment` (human-readable meaning of the variable), `session_id`, `created_at`, `filename`/`lineno`/`trigger_point` (source location that produced it), `metadata` |
| `operations` | `op_id`, `op_name` (e.g. `memory_system.extract_facts`, `memory_system.update_memory_decision`, `memory_system.search_vector_store`, `memory_system.retrieve`, `memory_system.agentic_final_rerank`, `question-answering`), `category` ∈ {initialization, boundary_detection, extraction, update, retrieval, evaluation}, `comment`, `session_id`, `created_at`, `metadata` (e.g. `llm_model`) |
| `edges` | `edge_id`, `op_id` (operation that produced the edge), `source_full_node_id` → `target_full_node_id`, `category`, `comment`, `created_at` |
| `sessions` | `session_id`, `category` (memory_construction / answering), `comment` ("It is the k-th conversational session") |
| `annotations` | `query_id`, `query`, `golden_answers`, `golden_answers_id`, `prediction`, `prediction_id`, `source_evidence`, `source_evidence_ids`, `final_error_type`, `final_op_id`, `reason` |

A "trajectory" for one failed query is not stored explicitly; it is the backward dependency slice of `prediction_id` through `edges` (we materialise it in `scripts/analyze_memtrace.py`).

## Statistics

Computed from the data (`scripts/analyze_memtrace.py`; machine-readable: `notes/memtrace_stats.json`, which also includes per-graph and per-annotation records).

| Statistic | Value |
|---|---|
| Execution graphs | **103** (rag 30, mem0 19, evermemos 20, long_context 34); by source: LongMemEval 75, LoCoMo 16, RealMem 12 |
| Failure annotations | **238** total = **160 memory-system failures** (40 per system) + 75 Annotation Error (67 unique) + 3 LLM-as-a-Judge Error; 214 unique query ids |
| Memory failures by source | LongMemEval 70, LoCoMo 58, RealMem 32 |
| Error types (memory failures) | Retrieval 76 · Response 34 · Update 31 · Extraction 19 · Deletion 0 |
| Error types by system | rag: Retrieval 37, Response 3 · mem0: Extraction 18, Retrieval 14, Update 7, Response 1 · evermemos: Retrieval 25, Response 14, Extraction 1 · long_context: Update 24, Response 16 |
| Faulty operation category ("faulty agent") | retrieval 76, evaluation (question-answering) 34, update 31, extraction 19 |
| Faulty operation name | `memory_system.retrieve` 37, `question-answering` 34, `memory_system.memory_update` 24, `memory_system.agentic_final_rerank` 22, `extract_facts` 18, `search_vector_store` 14, `update_memory_decision` 7, `agentic_round2_bundle` 3, `extract_memory` 1 |
| Operations per graph | mean 1,111, median 743, min 422, max 4,571 (rag 630 / mem0 1,009 / evermemos 1,407 / long_context 498 medians) |
| Nodes / edges per graph | nodes mean 3,010 (median 1,488, max 17,753); edges mean 5,322 (median 2,828, max 32,616) |
| Operation categories (all graphs) | update 68,534 · extraction 15,094 · boundary_detection 12,628 · evaluation 9,054 · retrieval 6,161 · initialization 2,920 |
| **Steps per failed trajectory** = operations in the backward slice of the prediction | mean 805, median 497, min 12, max 3,661 (rag median 495; mem0 81; evermemos 1,447; long_context 497) |
| Steps histogram (slice size) | 12–99: 22 · 100–299: 20 · 300–599: 52 · 600–999: 20 · 1000–1999: 31 · ≥2000: 15 (from `steps_per_traj`) |
| Faulty op inside the slice | 140 / 160 (the 20 misses are mostly mem0 *Extraction* errors: the information never became a memory unit, so no edge connects the faulty extraction to the prediction) |
| Relative position of faulty op in slice (chronological) | mean 0.79, median 0.90, min 0.10 |
| Relative position of faulty op among *all* operations of the graph | mean 0.69, median 0.68, min 0.03, max 0.999 |
| Characters per graph (sum of node values) | mean 48.5 M, median 20.9 M, min 3.0 M, max 439 M; per failed slice: median 7.6 M chars (mem0 slices ≈ 0.1–0.3 M) |
| Reason text length | mean 578 chars |

Note that the "step" granularity here is an *operation* (an LLM call, a vector search, a filter), far finer than a ReAct turn; a single LongMemEval conversation yields ~500–1,500 operations.

## Example trajectory

Chosen record: `mem0/longmemeval_longmemeval-f8c5f88b.json`, annotation `query:f8c5f88b@1` (Mem0 on LongMemEval; **Update Error**; the decisive operation is #12 of the 16 operations in the prediction's backward slice; the full graph has 977 operations / 2,290 nodes). Raw record (annotation + metadata + the 16 slice operations with full input/output node values): `notes/memtrace_example.json`; normalised: `notes/memtrace_example_norm.json`. Prompt-template nodes (4–8 k chars each) are omitted from the rendering below.

**Source id:** `mem0/longmemeval_longmemeval-f8c5f88b.json::query:f8c5f88b@1`  
**Task:** 'Where did I buy my new tennis racket from?'  
**Ground truth:** ['the sports store downtown']  
**Final output of the system:** "The memories provided do not mention where you bought your new tennis racket from. Therefore, I don't have that information."  

Steps (16 total):

- **Step 1 — extraction operation (memory_system.extract_facts)**

  > Operation: memory_system.extract_facts [extraction] (op_id op-033d2905d9bf40fd89e86af67a91bb4f, session 1ede478b, 2026-04-27 01:00:46.385)
  > Description: Extract facts from a conversation snippet using an LLM. Please note that these extracted facts are initially without timestamps, which will be added later when the memory unit is created or updated.
  > Inputs:
  >   - [prompt] fact-extraction-system-prompt (prompt template, 4248 chars, omitted)
  >   - [llm_response] str:c4d3eefad6ce7d259347218d38832b914cd1dff9: '{"facts" : ["Planning to check out West Elm and Crate […]  West Elm and Crate & Barrel online", "Looking to buy new rugs for the living room", "Interested in stores with a wide selection of rugs"]}'

- **Step 2 — update operation (memory_system.update_memory_decision)**

  > Operation: memory_system.update_memory_decision [update] (op_id op-35263efef0ab46f3a35b16a39b81dc9b, session 1ede478b, 2026-04-27 01:00:47.464)
  > Description: Decide how to update the memory store using a large language model.
  > Inputs:
  >   - [similar_memories] str:3a82ed585fc1d5dae6573a915a7c5fc982cc2b24: 'Find 8 existing memories similar to the new extracted facts.'
  >   - [llm_response] str:c4d3eefad6ce7d259347218d38832b914cd1dff9: ['Planning to check out West Elm and Crate & Barrel online', 'Looking to buy new rugs for the living room', 'Interested in stores  […]            "text": "Planning to buy the Tab S8"         },         {             "event": "NONE",             "id": "4",             "te […]

- **Step 3 — extraction operation (memory_system.extract_facts)**

  > Operation: memory_system.extract_facts [extraction] (op_id op-34a8949827c94ee69a40754fcf28a700, session 66c23110_1, 2026-04-27 01:06:01.751)
  > Description: Extract facts from a conversation snippet using an LLM. Please note that these extracted facts are initially without timestamps, which will be added later when the memory unit is created or updated.
  > Inputs:
  >   - [prompt] fact-extraction-system-prompt (prompt template, 4248 chars, omitted)
  >   - [llm_response] str:29308fffce86ada19dac92c57e7c41c3554d3b29: '{"facts": ["Recently bought an eyeshadow palette at […] 6ada19dac92c57e7c41c3554d3b29: '{"facts": ["Recently bought an eyeshadow palette at Sephora", "Has 200 points in Sephora loyalty program"]}'

- **Step 4 — update operation (memory_system.update_memory_decision)**

  > Operation: memory_system.update_memory_decision [update] (op_id op-46e0d327c91d4e4b85f699f003f7e760, session 66c23110_1, 2026-04-27 01:06:02.721)
  > Description: Decide how to update the memory store using a large language model.
  > Inputs:
  >   - [similar_memories] str:d70b5f680e2b5fcaa09f935df5ebd0d3c31ac49a: 'Find 6 existing memories similar to the new extracted facts.'
  >   - [llm_response] str:29308fffce86ada19dac92c57e7c41c3554d3b29: ['Recently bought an eyeshadow palette at Sephora', 'Has 200 points in Sephora loyalty program']
  >   - [prompt] memory-update-deci […] iman Marcus about six weeks ago"         },         {             "event": "NONE",             "id": "4",             "text": "Open to t […]

- **Step 5 — extraction operation (memory_system.extract_facts)**

  > Operation: memory_system.extract_facts [extraction] (op_id op-21161dcfcdb74761af8361564a97a46b, session answer_c3567066, 2026-04-27 01:08:59.593)
  > Description: Extract facts from a conversation snippet using an LLM. Please note that these extracted facts are initially without timestamps, which will be added later when the memory unit is created or updated.
  > Inputs:
  >   - [prompt] fact-extraction-system-prompt (prompt template, 4248 chars, omitted)
  >   - [llm_response] str:738f1c9c10461810e7fd840a33e04a0fab59798f: '{"facts" : ["Plays tennis", "Has a new tennis  […] acket from a sports store downtown", "Feels the new tennis racket has improved their game", "Plans to do exercises before playing tennis"]}'

- **Step 6 — update operation (memory_system.update_memory_decision)**

  > Operation: memory_system.update_memory_decision [update] (op_id op-aa7aeb57455146c4965ef8be3f73a5d2, session answer_c3567066, 2026-04-27 01:09:00.594)
  > Description: Decide how to update the memory store using a large language model.
  > Inputs:
  >   - [similar_memories] str:70bc8a22ac4325bb28717881ebf51672a1c1c0f8: 'Find 13 existing memories similar to the new extracted facts.'
  >   - [llm_response] str:738f1c9c10461810e7fd840a33e04a0fab59798f: ['Plays tennis', 'Has a new tennis racket from a sports store downtown', 'Feels the new tennis racket has improved their g […]    "event": "NONE",             "id": "3",             "text": "Has a meeting at 7:30 AM"         },         {             "event": "NON […]

- **Step 7 — extraction operation (memory_system.extract_facts)**

  > Operation: memory_system.extract_facts [extraction] (op_id op-1469467aa52c41b9bc07e27acda865a2, session answer_c3567066, 2026-04-27 01:09:08.319)
  > Description: Extract facts from a conversation snippet using an LLM. Please note that these extracted facts are initially without timestamps, which will be added later when the memory unit is created or updated.
  > Inputs:
  >   - [prompt] fact-extraction-system-prompt (prompt template, 4248 chars, omitted)
  >   - [llm_response] str:3200421f4d4a3bea2c9baba6dd7a629cc78bb374: '{"facts" : ["Planning to buy new tennis balls  […] 3200421f4d4a3bea2c9baba6dd7a629cc78bb374: '{"facts" : ["Planning to buy new tennis balls this weekend", "Is a recreational tennis player"]}'

- **Step 8 — update operation (memory_system.update_memory_decision)**

  > Operation: memory_system.update_memory_decision [update] (op_id op-99c97880413a4eff81057aa93ebc6a81, session answer_c3567066, 2026-04-27 01:09:09.181)
  > Description: Decide how to update the memory store using a large language model.
  > Inputs:
  >   - [similar_memories] str:d70b5f680e2b5fcaa09f935df5ebd0d3c31ac49a: 'Find 6 existing memories similar to the new extracted facts.'
  >   - [llm_response] str:3200421f4d4a3bea2c9baba6dd7a629cc78bb374: ['Planning to buy new tennis balls this weekend', 'Is a recreational tennis player']
  >   - [memory_entry] memory-unit-190e1a1 […] tennis",             "text": "Plays tennis"         },         {             "event": "NONE",             "id": "4",             "text": […]

- **Step 9 — extraction operation (memory_system.extract_facts)**

  > Operation: memory_system.extract_facts [extraction] (op_id op-5d3029ffb1e749e5bba7b5682f17e7e3, session answer_c3567066, 2026-04-27 01:09:14.042)
  > Description: Extract facts from a conversation snippet using an LLM. Please note that these extracted facts are initially without timestamps, which will be added later when the memory unit is created or updated.
  > Inputs:
  >   - [prompt] fact-extraction-system-prompt (prompt template, 4248 chars, omitted)
  >   - [llm_response] str:4f1fe3d732d310c2444187e0546e729f86020aff: '{"facts": ["Considering getting a tennis ball  […]  - [llm_response] str:4f1fe3d732d310c2444187e0546e729f86020aff: '{"facts": ["Considering getting a tennis ball machine to practice shots"]}'

- **Step 10 — update operation (memory_system.update_memory_decision)**

  > Operation: memory_system.update_memory_decision [update] (op_id op-c3a40398534a4d0f9509c706c588b4c8, session answer_c3567066, 2026-04-27 01:09:14.843)
  > Description: Decide how to update the memory store using a large language model.
  > Inputs:
  >   - [similar_memories] str:1d11637d2cbbd050a008a89385183949c8a1650b: 'Find 5 existing memories similar to the new extracted facts.'
  >   - [llm_response] str:4f1fe3d732d310c2444187e0546e729f86020aff: ['Considering getting a tennis ball machine to practice shots']
  >   - [prompt] memory-update-decision-prompt (prompt template […] s to warm up before playing tennis"         },         {             "event": "NONE",             "id": "4",             "text": "Plays  […]

- **Step 11 — extraction operation (memory_system.extract_facts)**

  > Operation: memory_system.extract_facts [extraction] (op_id op-153ebf67780d461cba0edeb3af6e7524, session answer_c3567066, 2026-04-27 01:09:18.365)
  > Description: Extract facts from a conversation snippet using an LLM. Please note that these extracted facts are initially without timestamps, which will be added later when the memory unit is created or updated.
  > Inputs:
  >   - [prompt] fact-extraction-system-prompt (prompt template, 4248 chars, omitted)
  >   - [llm_response] str:afaa9ba60de546fd3ebb8fa59aaa7584f32b3be6: '{"facts" : ["Considering getting a tennis ball […] proving tennis game with a new racket", "Practices tennis with friends", "Interested in exercises to strengthen core and legs for tennis"]}'

- **Step 12 — update operation (memory_system.update_memory_decision)**  ⟵ ANNOTATED ERROR STEP

  > Operation: memory_system.update_memory_decision [update] (op_id op-439f2d5e63ed4e36a41befae415d9526, session answer_c3567066, 2026-04-27 01:09:19.622)
  > Description: Decide how to update the memory store using a large language model.
  > Inputs:
  >   - [similar_memories] str:7d4e99d6a16256cad6119529f75d541cfd99ac46: 'Find 9 existing memories similar to the new extracted facts.'
  >   - [llm_response] str:afaa9ba60de546fd3ebb8fa59aaa7584f32b3be6: ['Considering getting a tennis ball machine in the future', 'Currently focusing on improving tennis game with a new racket' […] ": "Currently focusing on improving tennis game with a new racket"         },         {             "event": "NONE",             "id": " […]

- **Step 13 — extraction operation (memory_system.extract_facts)**

  > Operation: memory_system.extract_facts [extraction] (op_id op-c69216285c7e40dbb9a6fa7ccf598123, session 15232887_1, 2026-04-27 01:14:00.243)
  > Description: Extract facts from a conversation snippet using an LLM. Please note that these extracted facts are initially without timestamps, which will be added later when the memory unit is created or updated.
  > Inputs:
  >   - [prompt] fact-extraction-system-prompt (prompt template, 4248 chars, omitted)
  >   - [llm_response] str:6bc4fb15773b200e3e2dccb8d521898a84709fc5: '{"facts" : ["Enjoys tennis lessons", "Wants tennis  […] {"facts" : ["Enjoys tennis lessons", "Wants tennis drills to improve serves and volleys", "Attended a swimming session on Sunday morning"]}'

- **Step 14 — update operation (memory_system.update_memory_decision)**

  > Operation: memory_system.update_memory_decision [update] (op_id op-3d51cd8caa4a4cf5a4b02e5da73d8650, session 15232887_1, 2026-04-27 01:14:02.053)
  > Description: Decide how to update the memory store using a large language model.
  > Inputs:
  >   - [similar_memories] str:51fe65b667286dfd3eced911f45431360b1365b2: 'Find 11 existing memories similar to the new extracted facts.'
  >   - [llm_response] str:6bc4fb15773b200e3e2dccb8d521898a84709fc5: ['Enjoys tennis lessons', 'Wants tennis drills to improve serves and volleys', 'Attended a swimming session on Sunday morning'] […]             "event": "UPDATE",             "id": "4",             "old_memory": "Includes tennis lessons, running, and cycling in workou […]

- **Step 15 — retrieval operation (memory_system.search_vector_store)**

  > Operation: memory_system.search_vector_store [retrieval] (op_id op-a90ea470bc05492eb6863a76e54b3af7, session session-0be59f88323243669f8831091324bf22, 2026-04-27 14:42:39.679)
  > Description: A task query searches the memory store for top-10 relevant memories.
  > Inputs:
  >   - [message & query] f8c5f88b: 'Where did I buy my new tennis racket from?'
  > Outputs:
  >   - [memory_entry] memory-unit-142e8f97-642e-4472-988a-f6bb2d890dc6: {     "id": "142e8f97-642e-4472-988a-f6bb2d890dc6",     "memory": "Wants tennis drills to improve serves and volleys",     "timestamp": "20 […] 946b8c3: {     "id": "f7b5184b-0ec3-41ea-be69-a5475946b8c3",     "memory": "Enjoys tennis lessons",     "timestamp": "2023-05-27T19:21:00" }

- **Step 16 — evaluation operation (question-answering)**

  > Operation: question-answering [evaluation] (op_id op-ea59e23d201444d4a4ee876879d4e811, session session-1bdc9fd4f46646bdb6d3ec41fc27c71d, 2026-04-27 15:07:41.993)
  > Description: The question-answering model generates an answer based on the question, the context retrieved from the memory system, and a question-answering prompt.
  > Inputs:
  >   - [memory_context] str:6f387573accd693da0390f35f8d83975da56256f: '### Memory 1:\nMemory: Feels the new tennis racket has improved their game\nTime: 2023-05-25T21:29:00\n\n### Memory 2:\nMemory: Planning to buy new tennis bal […] 083c74a1952b: "The memories provided do not mention where you bought your new tennis racket from. Therefore, I don't have that information."

**Annotation:**

- Faulty agent/component: `update operation (memory_system.update_memory_decision)`
- Faulty step: `12`
- Category: `UpdateError`
- Reason / root cause: The system incorrectly updated the memory about the user’s tennis racket. The original memory stated that the user had a new tennis racket from a sports store downtown, which included the purchase location needed to answer the query. It was changed to a more general memory about focusing on improving their tennis game with a new racket. This update removed the key detail that the racket came from the sports store downtown, causing the model to later claim the purchase location was unavailable.
- final_op_id: op-439f2d5e63ed4e36a41befae415d9526
- query_id: query:f8c5f88b@1
- prediction_id: prediction:str:afcbbf28d347f17f53052bf1e78c083c74a1952b@1
- source_evidence: ['{\n    "content": "I\'ll definitely do those exercises before playing tennis. By the way, I\'m really happy with my new tennis racket, which I got from a sports store downtown. It\'s been performing really well, and I feel like it\'s impr […] "role": "user",\n    "timestamp": "2023-05-25T21:29:00"\n}']
- source_evidence_ids: ['longmemeval-message-10-28-5@1']
- memory_system: mem0
- source_dataset: LongMemEval
- graph_size: {'nodes': 2290, 'edges': 3979, 'operations': 977, 'sessions': 49}
- note: Steps are the operations in the backward (dependency) slice of the prediction node, in chronological order; the full execution graph has many more operations (see graph_size) that do not feed into this prediction.

## Notes for the report

- **What is unique.** The only dataset in the survey where the "trajectory" is a *white-box execution graph* of a memory system (hundreds to thousands of operations, with every intermediate variable recorded) rather than a message log, and where the root-cause unit is an *operation id* in that graph. It is the natural testbed for "memory failure" categories that other taxonomies (MAST, HORIZON's Memory Limitation, Raj et al.'s model–memory edge) only name.
- **Component-level attribution.** No multi-agent roles; the four operation categories (extraction / update / retrieval / response) are the "agents". Deletion errors exist in the taxonomy but have zero instances.
- **Hard localisation, easy typing.** Best OIA 46.3 % vs ETA 54.4 % (GPT-5.4); long-context OIA ≤ 20 % because all information sits in one giant prompt and the "faulty operation" is an update/response op buried among hundreds.
- **Size and loading.** 6 GB for 103 graphs; a single EverMemOS graph can be 500 MB and 17 k nodes, so per-file `json.load` needs several GB of RAM. The README recommends the `smartcomment` package (`ExecNetwork.import_graph`) — we deliberately parsed the JSON directly instead of running shipped code.
- **Noise labels retained.** 75 Annotation-Error and 3 Judge-Error annotations are kept in the files; filter on `final_error_type` ∈ {Extraction, Update, Deletion, Retrieval, Response}Error to get the 160-case benchmark (names have no spaces in the data: `RetrievalError` etc.).
- **Agreement.** No kappa; pairwise disagreement 3–46 % and the authors note that all three source datasets contain annotation errors (RealMem's open-ended questions are the noisiest).
- **Overlaps.** Source conversations are the public LoCoMo / LongMemEval / RealMem sets (LLM-synthesised, no real users); no overlap with other failure-attribution datasets. The paper says "upon acceptance we will release…", but the data is already public on HF (MIT).
