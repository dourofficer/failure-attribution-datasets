# SearchAuditBench — SearchAuditor

## Identity

- **Full title:** *SearchAuditor: Auditing and Attributing Failures in Long-Horizon Search Agents*. Dataset: **SearchAuditBench**.
- **Authors / affiliation:** Zhixiang Liang, Yifei Liu, Yidan Huang, Haozhe Zhao, Beichen Huang, Jiaqi Wang, Nan Duan, Qiong Cao (affiliation not given on the arXiv abstract page; the HTML lists no institutional footer we could extract — Nan Duan / Qiong Cao are industry research leads).
- **Venue:** arXiv preprint **2608.05212** (v1, 5 Aug 2026, cs.AI); no venue stated.
- **Links:** paper https://arxiv.org/abs/2608.05212 · code + data https://github.com/lzzzx666/SearchAuditor (the benchmark is shipped inside the repo as `SearchAuditBench/SearchAuditBench.zip`, a PPMd-compressed ZIP that standard `unzip`/Python `zipfile` cannot read — extracted with the official 7-Zip 24.09 Linux binary).
- **License:** **none stated** (no LICENSE file in the repo; arXiv perpetual non-exclusive license for the paper). Trajectories contain full web-search/visit returns from five third-party benchmarks (BrowseComp, BrowseComp-ZH, DeepSearchQA, Seal-0/SEALQA, xBench-DeepSearch) whose own licenses apply.
- **Availability:** **downloaded** — 1,243 records, complete.
- **On-disk size:** 390 MB total — `extracted/benchmark_data_1243.jsonl` 313 MB (the only data file), `repo_SearchAuditor/` 46 MB (zip + method code + prompts), `SearchAuditor-main.tar.gz` 46 MB (download archive).
- **Local path:** `/dataDisk/home/thanhdo/failure-attribution-datasets/data/searchauditbench/` (`extracted/benchmark_data_1243.jsonl`, `repo_SearchAuditor/`).

## Description

- **Purpose.** *Trajectory auditing* for deep-search (web research) agents. Given a query `q`, the agent's wrong final answer `â` and the frozen trajectory `τ`, an auditor must (1) localise the **critical error step** (a decision step = assistant message), (2) classify the **root cause** into a six-way search-specific taxonomy, and (3) write a **repair directive** that is graded against 3–5 expert atomic rubrics. Auditing is strictly offline (no gold answer, no web access).
- **Construction (natural failures).** Eight open-weight models with exposed reasoning — GLM-5.2, Kimi-K2.6, DeepSeek-V4-Pro, Qwen3.5-397B-A17B (general) and OpenSeeker, OpenResearcher, Quest-35B, Tongyi-DeepResearch-30B-A3B (deep-research specialists) — run under one unified scaffold adapted from Tongyi DeepResearch with two tools (`search`, `visit`), on query pools from five deep-search benchmarks (BrowseComp, BrowseComp-ZH, DeepSearchQA, Seal-0, xBench-DeepSearch). 3,500 raw runs → 3,288 gradable → 1,674 judged incorrect by an LLM evaluator → after discarding non-auditable cases (evaluator false negatives, flawed benchmark items, truncated traces, environment-caused failures, no single critical step) → **1,243 annotated failed trajectories**, 125–175 per model.
- **Annotation.** Four annotators from the author team (>1 year agent research each), each case labelled by **one** annotator (disjoint split, so no inter-annotator agreement is reported). Claude Opus 4.6 pre-screens candidate error regions with rationales; humans verify/relocate/relabel (all fields human-authored). The critical step is the earliest decision step at which the root-cause mechanism becomes established; a **tolerance span** `[ks, ke]` brackets equally defensible adjacent decisions. Exactly one primary root cause per trajectory. Rubrics must be case-specific, process-level and independently checkable; a DeepSeek-V4-Flash grader was validated against humans (Appendix D: 30/713 rubric false passes, 43/159 false fails).
- **Labels:** `critical_step.message_index` + span, `root_cause_primary` (6 classes), `rationale.failure_rationale` (free text), `repair_directive` (free text), `repair_rubrics` (3–5 `requirement` strings), plus `gold_answer` and `predicted_answer`. Single agent, so no agent-level label.
- **Root-cause taxonomy (6 classes, Appendix A):** *Candidate Mismanagement* (premature lock-in / wrong rejection / failure to update or converge on candidates), *Search Coverage Gap* (decisive evidence path never searched/inspected), *Constraint Neglect* (accepts a candidate violating a hard query constraint that was visible), *Unverified Source Reliance* (trusts snippet/secondary/inaccessible source without verification), *Entity–Relation Misbinding* (correct fact bound to the wrong entity/relation/time/slot), *Unsupported Answer* (residual: guess/memory answer with no evidence chain).
- **Metrics (paper §5 / README):** CS-Strict (exact critical message), CS-Loose (inside tolerance span), RC-Acc / RC-F1 (6-way), Diag = RC correct ∧ CS-Loose, Rep@Diag (all rubrics pass, conditioned on Diag), **FPS** = Diag × Rep@Diag (end-to-end). Baselines: All-at-Once, Step-by-Step, Binary Search (Who&When-style prompting), AgentRx; backbones GPT-5.5, Gemini-3.1-Pro, Claude-Opus-4.8.
- **Reported results (Table 2, selected):** with GPT-5.5, SearchAuditor reaches CS-Strict 44.89 / CS-Loose 58.73 / FPS 32.26 vs. strongest baseline 39.02 / 51.89 / 26.55. Claude-Opus-4.8 block (CS-Strict | CS-Loose, RC-Acc, RC-F1, Diag, Rep@Diag, FPS): All-at-Once 32.10 | 47.06, 47.63, 45.43, 28.24, 71.51, 20.19; Step-by-Step 23.09 | 37.65, 37.49, 36.15, 18.91, 68.94, 13.03; Binary Search 32.82 | 47.06, 43.36, 41.55, 25.34, 70.48, 17.86; AgentRx 35.40 | 49.72, 42.96, 40.92, 26.71, 46.39, 12.39; **SearchAuditor 39.90 | 54.79, 50.68, 47.05, 33.71, 73.03, 24.62**. Resuming failed LiveBrowseComp runs with SearchAuditor repairs raises accuracy (Table 4).

## Schema

Single JSONL file `benchmark_data_1243.jsonl`, one object per failed run:

- `index` (int) — stable example id (0–1242, not contiguous order in file).
- `model` (str) — generating agent (8 values, see stats).
- `dataset` (str) — source benchmark (`BrowseComp`, `BrowseComp English`, `BrowseComp-ZH`, `DeepSearchQA`, `SEALQA`, `XBench-DeepSearch`; note `BrowseComp English` is a separate tag used only for GLM-5.2).
- `query` (str) — the search question (English or Chinese).
- `predicted_answer` (str) — the agent's wrong final answer (often with `<answer>` tags / markdown).
- `gold_answer` (str) — reference answer (only for QC; auditors must not see it).
- `trajectory` (list) — OpenAI-style messages: `message_index` (0-based), `role` (`system`/`user`/`assistant`/`tool`), `content` (str or null), `reasoning_content` (assistant chain-of-thought), `tool_calls` (list of `{tool_name, tool_arguments, tool_call_id}`; `search` takes a list of queries, `visit` a list of URLs + `goal`), `name` (tool name on tool messages), `tool_call_id`, `finish_reason`, `answer_block_normalized`.
- `critical_step` (obj) — `message_index`, `span_start_message_index`, `span_end_message_index` (always an assistant message; span may include intervening tool messages).
- `root_cause_primary` (str) — one of the 6 taxonomy labels.
- `rationale.failure_rationale` (str) — evidence-grounded explanation of the critical step.
- `repair_directive` (str) — process-level repair from the critical step onward.
- `repair_rubrics` (list of `{requirement}`) — 3–5 atomic grading criteria.

## Statistics (computed from the data; 1,243 trajectories, all failed)

| quantity | n | mean | median | min | max | p10 | p90 |
|---|---|---|---|---|---|---|---|
| messages per trajectory (system+user+assistant+tool) | 1243 | 73.11 | 43 | 8 | 404 | 11 | 164 |
| assistant decision steps per trajectory | 1243 | 34.31 | 20 | 3 | 201 | 5 | 81 |
| tool-return messages per trajectory | 1243 | 36.72 | 21 | 3 | 201 | 4 | 80 |
| critical message index (0-based) | 1243 | 38.19 | 16 | 2 | 392 | 4 | 104 |
| critical rel. position (idx / last idx) | 1243 | 0.58 | 0.5833 | 0.0064 | 1.0 | 0.12 | 1.0 |
| critical rel. position among assistant steps (rank/n) | 1243 | 0.58 | 0.5909 | 0.0064 | 1.0 | 0.1235 | 1.0 |
| tolerance span length (messages) | 1243 | 4.3 | 4 | 1 | 12 | 1 | 7 |
| repair rubrics per instance | 1243 | 4.37 | 4 | 3 | 5 | 4 | 5 |
| characters per trajectory (content+reasoning+tool_calls) | 1243 | 208534.93 | 122832 | 7450 | 1854156 | 36733 | 537512 |
| query length (chars) | 1243 | 259.17 | 146 | 21 | 1547 | 59 | 590 |
| predicted answer length (chars) | 1243 | 1463.26 | 669 | 17 | 27658 | 22 | 4177 |

Histogram of messages per trajectory:

| messages | n | % |
|---|---|---|
| 0-19 | 350 | 28.2 |
| 20-39 | 245 | 19.7 |
| 40-59 | 139 | 11.2 |
| 60-79 | 91 | 7.3 |
| 80-99 | 77 | 6.2 |
| 100-149 | 139 | 11.2 |
| 150-199 | 129 | 10.4 |
| 200-299 | 44 | 3.5 |
| >=300 | 29 | 2.3 |

Histogram of critical-step relative position (message index / last index):

| rel. position | n | % |
|---|---|---|
| 0.0-0.2 | 198 | 15.9 |
| 0.2-0.4 | 221 | 17.8 |
| 0.4-0.6 | 227 | 18.3 |
| 0.6-0.8 | 192 | 15.4 |
| 0.8-1.0 | 420 | 33.8 |

Root-cause distribution (one primary label per trajectory):

| root cause | n | % |
|---|---|---|
| Candidate Mismanagement | 338 | 27.2 |
| Search Coverage Gap | 284 | 22.8 |
| Constraint Neglect | 238 | 19.1 |
| Unverified Source Reliance | 205 | 16.5 |
| Entity–Relation Misbinding | 141 | 11.3 |
| Unsupported Answer | 37 | 3.0 |

Source benchmark:

| benchmark | n | % |
|---|---|---|
| DeepSearchQA | 255 | 20.5 |
| BrowseComp | 251 | 20.2 |
| BrowseComp-ZH | 236 | 19.0 |
| XBench-DeepSearch | 234 | 18.8 |
| SEALQA | 217 | 17.5 |
| BrowseComp English | 50 | 4.0 |

Generating agent (model):

| model | n | % |
|---|---|---|
| GLM-5.2 | 175 | 14.1 |
| Kimi-K2.6 | 164 | 13.2 |
| OpenSeeker | 160 | 12.9 |
| OpenResearcher | 159 | 12.8 |
| DeepSeek-V4-Pro | 158 | 12.7 |
| Quest-35B | 156 | 12.6 |
| Tongyi-DeepResearch-30B-A3B | 146 | 11.7 |
| Qwen3.5-397B-A17B | 125 | 10.1 |

Model × benchmark:

| model | BrowseComp | BrowseComp English | BrowseComp-ZH | DeepSearchQA | SEALQA | XBench-DeepSearch | total |
|---|---|---|---|---|---|---|---|
| DeepSeek-V4-Pro | 39 | 0 | 30 | 32 | 26 | 31 | 158 |
| GLM-5.2 | 0 | 50 | 38 | 33 | 23 | 31 | 175 |
| Kimi-K2.6 | 40 | 0 | 32 | 31 | 29 | 32 | 164 |
| OpenResearcher | 29 | 0 | 30 | 33 | 33 | 34 | 159 |
| OpenSeeker | 33 | 0 | 29 | 32 | 32 | 34 | 160 |
| Quest-35B | 39 | 0 | 25 | 33 | 29 | 30 | 156 |
| Qwen3.5-397B-A17B | 33 | 0 | 20 | 31 | 19 | 22 | 125 |
| Tongyi-DeepResearch-30B-A3B | 38 | 0 | 32 | 30 | 26 | 20 | 146 |

Root cause × median relative position:

| root cause | n | median rel. pos | share in final third |
|---|---|---|---|
| Candidate Mismanagement | 338 | 0.5 | 38.8% |
| Search Coverage Gap | 284 | 0.4 | 29.9% |
| Constraint Neglect | 238 | 0.846 | 66.0% |
| Unverified Source Reliance | 205 | 0.591 | 45.4% |
| Entity–Relation Misbinding | 141 | 0.619 | 49.6% |
| Unsupported Answer | 37 | 1.0 | 91.9% |

Critical step attached to: {'False': 1033, 'True': 210} (True = the final-answer assistant message). Critical-step role counts: {'assistant': 1243}. Tool-call names: {'search': 32013, 'visit': 13608, '.../': 1, 'booksearch': 2, 'Visit': 3, 'qwen_internal_search': 1, 'web_search': 7, 'query': 1, 'investigative_questions': 1, 'download': 1}.

Paper-reported (Table 5–7) for comparison: 73.1 messages and 65.1 K tokens per trajectory on average (median 39.4 K, P90 152 K; tool returns 49.1 K vs. reasoning 15.3 K), 36.7 tool calls (57.3 atomic operations), median critical position 58.3 %, 45.9 % of critical steps in the final third, mean span 4.30 messages, 4.37 rubrics per repair, 83.1 % of critical steps on a tool-calling turn and 16.9 % on the final answer — all consistent with our counts.

## Example trajectory

Chosen: index `546` (GLM-5.2 on XBench-DeepSearch), 8 messages (3 assistant decision steps), 9058 characters; shortest English-benchmark trajectory with ≤15 messages whose critical step is not the final answer. Step index = `message_index` (0-based; system and user prompt are steps 0–1).

**Source id:** `546`  
**Task:** IShowSpeed在YouTube上发布过一条关于物理挑战的播放量过亿的短视频（截至2025年5月18日），请问视频是在哪拍摄的？

**[step 0] system**

```text
Content: You are a deep research assistant. Your core function is to conduct thorough, multi-source investigations into any topic. You must handle both broad, open-domain inquiries and queries within specialized academic fields. For every request, synthesize information from credible, diverse sources to deliver a comprehensive, accurate, and objective response. When you have gathered sufficient in […] t enclose the entire final answer within <answer></answer> tags.

Current date: 2026-06-23
```

**[step 1] user**

```text
Content: IShowSpeed在YouTube上发布过一条关于物理挑战的播放量过亿的短视频（截至2025年5月18日），请问视频是在哪拍摄的？
```

**[step 2] assistant**

```text
Thought: The user is asking about an IShowSpeed YouTube short video about a physical challenge that has over 100 million views (as of May 18, 2025), and where it was filmed. Let me search for this.
Action (tool_calls): [{"tool_name": "search", "tool_arguments": {"query": "IShowSpeed YouTube short 100 million views physical challenge"}, "tool_call_id": "chatcmpl-tool-8a2b15e24f33c7c4"}, {"tool_name […] {"query": "IShowSpeed 播放量过亿 短视频 物理挑战"}, "tool_call_id": "chatcmpl-tool-aec006d5a75e3a55"}]
```

**[step 3] tool (search)**

```text
Observation (tool return): A Google search for 'IShowSpeed YouTube short 100 million views physical challenge' found 10 results:

## Web Results
1. [$100000 WIPEOUT with MrBeast and KSI - IShowSpeed - YouTube](https://www.youtube.com/watch?v=iitET2IZ0rE)
Date published: Jun 4, 2024
for tips/donations text to speech is here : https://streamlabs.com/ishowspeed/tip Media request for your video to pop […] eamer surprised his fans by doing 50 push-ups in front of the camera, just to disprove ...
```

**[step 4] tool (search)**

```text
Observation (tool return): A Google search for 'IShowSpeed 播放量过亿 短视频 物理挑战' found 10 results:

## Web Results
1. [IShowSpeed亿级视频拍摄地揭秘- U深搜 - UniFuncs](https://unifuncs.com/s/PSEtt1XB)
IShowSpeed在YouTube上发布的物理挑战视频拍摄于中国河北省邯郸市永年区洺珠小镇的八卦坑。该视频拍摄于2025年4月初，内容为IShowSpeed在一个彩色锥形坑中通过螺旋奔跑 ...

2. [ishowspeed youtube 物理挑战播放量过亿短视频拍摄地点的相關文章](https://www.juksy.com/tag/ishowspeed%20youtube%20%E7%89%A9%E7%90%86%E6% […] 頂繩飛身重擊Logan Paul 砸穿播報桌！ WWE 摔角狂熱42（WrestleMania 42）於2026 年4 月18 日在拉斯維加斯忠實體育場（Allegiant ...
```

**[step 5] assistant  ⟵ ANNOTATED ERROR STEP**

```text
Thought: The first search result from UniFuncs seems to have the answer. Let me visit that page to confirm.
Action (tool_calls): [{"tool_name": "visit", "tool_arguments": {"goal": "确认IShowSpeed物理挑战短视频的拍摄地点", "url": ["https://unifuncs.com/s/PSEtt1XB"]}, "tool_call_id": "chatcmpl-tool-ab2de3fc9ef44113"}]
```

**[step 6] tool (visit)**

```text
Observation (tool return): The useful information in https://unifuncs.com/s/PSEtt1XB for user goal 确认IShowSpeed物理挑战短视频的拍摄地点 as follows: 

Evidence in page: 
根据多个可靠来源的交叉验证，IShowSpeed在YouTube上发布的物理挑战视频拍摄地点是：

### 具体位置

**河北省邯郸市永年区洺珠小镇的八卦坑** （也称"太极八卦坑"或"洺珠八卦坑"）

### 详细地址信息

*   **国家** ：中国
*   **省份** ：河北省
*   **城市** ：邯郸市
*   **区县** ：永年区
*   **具体地点** ：洺珠小镇（洺珠酷跳健身园）
*   **景点名称** ：八卦坑 / 太极八卦坑

### 视频内容背景 […] 坑）。该视频拍摄于2025年4月，内容为挑战从彩色锥形坑底部利用离心力螺旋奔跑至顶部。此结论得到了Instagram、抖音、TikTok等多个独立来源的一致确认，信息可靠性高。


```

**[step 7] assistant**

```text
Thought: 我已经得到了答案。
Content: <answer>

IShowSpeed 在 YouTube 上发布的那条播放量过亿的物理挑战短视频，拍摄地点是**中国河北省邯郸市永年区洺珠小镇的"八卦坑"**（也称"太极八卦坑"）。

**具体信息：**

- **地点**：河北省邯郸市永年区洺珠小镇（洺珠酷跳健身园）内的八卦坑景点
- **拍摄时间**：2025 年 4 月初（IShowSpeed 中国行期间）
- **视频内容**：IShowSpeed 在一个彩色锥形坑中，通过螺旋奔跑的方式利用离心力从坑底上升到顶部，完成"物理挑战"逃脱。这是一个网红打卡游乐项目，难度较高。

该结论得到了 Instagram、抖音、TikTok 等多个独立来源的交叉验证。

</answer>
```

**Annotation**

- Faulty agent: `assistant (single search agent)`
- Faulty step: `5`
- Category: `Unverified Source Reliance`
- Reason / root cause: The decisive error occurs at message 5, where the agent treats a UniFuncs aggregation page as the confirming evidence after seeing a direct YouTube short result and the IShowSpeed channel in search results. The trajectory never opens or verifies the exact IShowSpeed YouTube short, does not check the dated view-count threshold, and does not prove that the location evidence belongs to the same qualifying video rather than a repost or similar physics challenge clip. The final location therefore depends on an unverified secondary summary rather than primary or reliably corroborated evidence.
- tolerance_span: [5, 7]
- repair_directive: Return to source verification. Open or reliably archive the exact IShowSpeed YouTube short or channel result, verify that it is the physical-challenge video and that it met the requested view threshold by the specified date, then corroborate the filming location for that same video using primary metadata, original description, credible reporting, or verifiable visual/location evidence. Do not accept an aggregation page or social snippet unless it is independently tied to the exact qualifying video.
- repair_rubrics: [{"requirement": "A valid repair must verify the exact YouTube short or channel posting rather than relying on an aggregation page."}, {"requirement": "A valid repair must check that the same video satisfies the physical-challenge description and the dated view-count threshold."}, {"requirement": "A valid repair must bind filming-location evidence to the exact qualifying video, not to a similar clip, repost, or general trip content."}, {"requirement": "A valid repair must use primary metadata, credible reporting, or independently verifiable visual/location evidence before finalizing the location."}]
- model: GLM-5.2
- source_benchmark: XBench-DeepSearch
- Ground truth: 长沙
- Produced answer / final output: <answer>

IShowSpeed 在 YouTube 上发布的那条播放量过亿的物理挑战短视频，拍摄地点是**中国河北省邯郸市永年区洺珠小镇的"八卦坑"**（也称"太极八卦坑"）。

**具体信息：**

- **地点**：河北省邯郸市永年区洺珠小镇（洺珠酷跳健身园）内的八卦坑景点
- **拍摄时间**：2025 年 4 月初（IShowSpeed 中国行期间）
- **视频内容**：IShowSpeed 在一个彩色锥形坑中，通过螺旋奔跑的方式利用离心力从坑底上升到顶部，完成"物理挑战"逃脱。这是一个网红打卡游乐项目，难度较高。

该结论得到了 Instagram、抖音、TikTok 等多个独立来源的交叉验证。

</answer>

## Notes for the report

- **Richest label set of the four:** critical step **with tolerance span**, root cause, rationale, repair directive *and* executable rubrics — it is the only dataset here that evaluates "how to fix" (diagnosis-gated repair grading), making it a natural testbed for attribution → repair pipelines.
- **Long and evidence-heavy:** median 43 messages but P90 164 and max 404 messages; median 123 k characters (max 1.85 M) because tool returns (search snippets, visited pages) are stored verbatim. Multilingual: BrowseComp-ZH queries and several models reason in Chinese even on English benchmarks (the example above is a Chinese-language xBench query answered by GLM-5.2).
- **Single annotator per case, author-team annotators, LLM pre-screening (Claude Opus 4.6)** — no IAA; the authors argue the pre-screening model is not among the evaluated auditors to avoid label/generator overlap.
- **Positional skew:** one third of critical steps lie in the last 20 % of the trajectory (Constraint Neglect and Unsupported Answer are late by construction), so "predict the last assistant step" is a non-trivial baseline for CS-Loose.
- **Single-agent, single scaffold:** all eight models share one Tongyi-DeepResearch-style ReAct scaffold with `search`/`visit`; failures are natural, not injected. No official train/test split.
- **Tooling caveat:** the ZIP uses PPMd; `7z` is required (the README says so). Data is also redistributed with no explicit license.
