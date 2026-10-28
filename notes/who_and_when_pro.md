# Who&When Pro — dataset notes

## Identity

| Field | Value |
|---|---|
| Full title | *Who&When Pro: Can LLMs Really Attribute Failures in AI Agents?* |
| Authors / affiliation | Jiale Liu, Huajun Xi, Shaokun Zhang, Yifan Zeng, Tianwei Yue, Chi Wang, Jian Kang, Qingyun Wu, Huazheng Wang — Penn State University / AG2AI, Oregon State University, Google DeepMind and collaborators (same core group as Who&When) |
| Venue | ICML 2026 (also listed on the NeurIPS 2026 virtual site as a poster) |
| arXiv | [2607.09996](https://arxiv.org/abs/2607.09996) (v1 10 Jul 2026, v2 9 Oct 2026); arXiv license CC BY-NC-SA 4.0 |
| Paper HTML | https://arxiv.org/html/2607.09996 |
| Project page | https://whowhenpro.github.io |
| Code | https://github.com/ag2ai/whowhen_pro (evaluation harness `whowhen_eval`: per-framework renderers, LiteLLM runner, scorer, leaderboard; the README's "whowhenpro/whowhen_pro" URL is a 404). Data-generation pipeline not yet released (roadmap). |
| Data | https://huggingface.co/datasets/Leoxx/whowhen_pro (official, linked from project page and README). 21.7 GB: `data/text.jsonl` 75.6 MB (6 257 rows), `data/video.jsonl` 21.3 MB (916 rows), `data/image.jsonl` 6.79 GB, `data/image_gui.jsonl` 11.19 GB (images base64-embedded), `video_assets/` (21 850 JPEG frames), `taxonomy.yaml`. An earlier anonymous release `tmpxv7/who-when-pro` (3.5 GB tar, May 2026, "13,500+ traces", 18-mode taxonomy) and a re-upload of the text split (`00myeongsu/whowhen-pro-text`) also exist. |
| License | CC BY 4.0 (HF dataset card). Upstream benchmark assets under their own licenses. |
| Availability | Ungated. **Partially downloaded** (representative subset, as instructed): `text.jsonl` and `video.jsonl` in full, `taxonomy.yaml`, README, and byte-range samples of the first ~1 GB of `image.jsonl` and of `image_gui.jsonl` (file names `*.PARTIAL_first1GB.jsonl`; the truncated last line is ignored by the analysis script). Video frame assets were not downloaded. |
| On-disk size | see end of the Statistics section (≈ 0.1 GB complete splits + ≈ 1–2 GB of image samples) |
| Local path | `/dataDisk/home/thanhdo/failure-attribution-datasets/data/who_and_when_pro/{data/,taxonomy.yaml,code_ag2ai_whowhen_pro/}` |

## Description

**Purpose.** Large-scale successor of Who&When: a benchmark for automated failure attribution in *single- and multi-agent* systems across text, image (incl. GUI) and video modalities, with ground-truth labels for **who** (agent), **when** (step) and **what** (error mode) obtained *by construction* rather than by human annotation.

**Construction (counterfactual replay + failure injection).**
- Base agents are run on each (framework, benchmark) pair; only *successful* trajectories are used as seeds (natural failures are only used to build the taxonomy).
- For a chosen step *t*, the successful prefix up to *t−1* is replayed exactly — static tool calls (search, page fetch) are served from a SHA-256-keyed cache, stateful environments (browsers, OSWorld, ALFWorld) are re-executed with fidelity checks that abort on divergence (`ReplayFidelityError`); then an erroneous action is substituted at *t* and the agent continues on-policy. The erroneous action is produced by the base agent itself under an injection prompt written by a frontier model (so the error is in-distribution), targeting one of the taxonomy modes.
- Only continuations that end in task failure are kept; traces that leak construction artifacts, or where the correct answer is already salient before *t*, are filtered.
- Result: 12 326 failed traces, 26 source benchmarks in 9 task categories, 15 frameworks (7 single-agent: smolagents, ALF-Agent/ReAct, EVA, DVD, AgentOccam, OpenAI-CUA, Gemini/WebVoyager; 8 multi-agent: Multi-Agent Debate, DyLAN, MacNet, MetaGPT, MathChat, Magentic-One, PixelCraft, CoAct-1), 3 modalities; avg 7.5 / max 50 steps, avg 1 139 words per trace, 152 words per step, 1.3 images per multimodal trace (paper figures).
- **Taxonomy.** 6 families — Perception (P.1 visual misidentification, P.2 spatial/grounding), Reasoning (R.1 hallucination, R.2 reasoning error, R.3 numerical error, R.4 task misunderstanding), Planning (PL.1 ineffective planning, PL.2 goal drift), Action (A.1 tool parameter error, A.2 output-format error, A.3 premature termination, A.4 looping), Verification (V.1 context loss, V.2 inadequate verification), Coordination (C.1 delegation error, C.2 communication failure, C.3 over-reliance on other agents). The paper says 18 modes; the released `taxonomy.yaml` has 17 (the paper's separate "hallucinated tool/action" mode is folded in).
- **Validation.** Three annotators reviewed 100 stratified traces: 94 % of step labels and 90 % of agent/error-family labels approved, Fleiss' κ = 0.73, 2 % judged to have no clear decisive error. Review was done by the authors ("Ph.D.-level human-in-the-loop"), not crowd-sourced.

**Task formulation & metrics.** Given the rendered trajectory (with images for multimodal splits), predict agent, step coordinate and error mode. Metrics: *Agent* accuracy (multi-agent traces only, averaged per framework), *Step* exact-match accuracy (per-framework average; Step@k tolerance variants in the appendix), *Error* macro-F1 over modes, *Joint* = all three correct. Protocols: All-at-Once, Step-by-Step, Binary-Search.

**Baselines (paper, All-at-Once; Agent / Step / Error / Joint, %).**

| Model | Text | Image | Video |
|---|---|---|---|
| GPT-5.4 | 55.7 / 72.3 / 15.3 / 21.3 | 67.7 / 65.2 / 26.5 / 30.2 | 85.1 / 60.5 / 33.8 / 21.6 |
| Claude Sonnet 4.6 | 54.9 / 69.8 / 19.1 / 22.4 | 67.5 / 63.8 / 29.5 / 29.6 | 79.8 / 64.4 / 37.4 / 26.4 |
| Gemini 3 Flash | 52.1 / 71.2 / 16.2 / 17.3 | 62.5 / 63.9 / 26.0 / 29.6 | 74.4 / 59.8 / 40.0 / 23.0 |

Best open-weight text results: Qwen3.5-122B Step 73.9; GLM-5 Joint 25.3. Step@0→Step@1 tolerance adds +13.9 pp (text), +16.9 (image), +28.1 (video). Key finding: models detect *symptoms* but mis-locate *root causes* (low Error/Joint), worst on multimodal and long traces. o-series models are not evaluated.

## Schema

`data/<split>.jsonl`, one row per trace; `task`, `trajectory`, `ground_truth`, `extras` are JSON-encoded strings.

| Field | Meaning |
|---|---|
| `id` | Trace id, `<benchmark>_<framework>_<nnnn>`. |
| `framework` | Agent framework (text: smolagents, mathchat, magentic-one, debate, alfagent, macnet, dylan, metagpt; image: smolagents, pixelcraft, debate; image_gui: coact, openai_cua, agentoccam, gemini; video: eva, dvd). |
| `benchmark` | Source benchmark (26 total; e.g. gaia, simpleqa_verified, tablebench, dsqa, databench, dabench, dacode, kramabench, math, scibench, mmlu_pro, gpqa, bigcodebench, livecodebench_pro, humaneval, alfworld, browsecomp_vl, mmsearch(+plus), chartqapro, charxiv, evochart, mmmu_pro, webvoyager, osworld, lvbench). |
| `task` | `{query, answer, options?, images?}` — the task, reference answer, inputs. |
| `trajectory` | The full rollout in a **framework-specific** shape (see below). |
| `ground_truth` | `{mode, agent | agents, step | round(+position) | stage, accepted_predictions?}` — the injected error. `agent` is `null` for single-agent frameworks. |
| `extras` | Framework metadata: `agents` roster `[{id, role}]`, `final_answer`, `termination`, `topology`, `eval_status`, `video_context`, `post_injection_turns` … |

Trajectory shapes and step coordinates (as rendered/scored by the official harness):

| framework | trajectory entries | step coordinate | GT fields |
|---|---|---|---|
| smolagents | `user`, optional `planning{plan}`, `action{step_number, reasoning, code, observation, observation_images, error, is_final_answer}` | flat cursor over non-framing entries (0 if a planning step exists, else 1) | `step` |
| alfagent | `user`, `action{step_number, reasoning, action, observation}` | `step_number` (1-based) | `step` |
| mathchat | `user`, turns `{agent_id, round, position, output, is_injected, is_replayed}`, `final_answer` | `2·round+position` (bootstrap user_proxy turn unnumbered) | `round`, `position` |
| magentic-one | `user`, `agent{agent, role, round, position, output, ledger?, tool_actions?, phase}` | `"R.P"` (P=0 orchestrator, P=1 specialist) | `step` (string "R.P") |
| debate / dylan | `user`, `round{round, turns[{agent_id, role?, position?, output}]}`, `final_answer` | `"R.P"`; scored on round only | `agents` (list), `round` |
| macnet | `user`, author/critic/rewriter/sink turns `{agent_id, role, stage, output}` , `final_answer` | 0.0 / 1.0 / 1.1 / 2.0 | `round`, `position` (+`accepted_predictions`) |
| metagpt | `user`, architect/engineer/reviewer `{agent_id, role, stage, output}`, `final_answer` | `stage` 0/1/2 | `stage` |
| dvd / eva (video) | `system`, `user`, `assistant{content, tool_calls, injected}`, `tool{tool_name, content, frames}` | dvd: native index − 2; eva: (index − 2)//2 | `step` (native index) |
| image_gui (coact, openai_cua, agentoccam, gemini) | per-step screenshots | 1-based `step_number` | `step` |

Entries that were injected are flagged in the trajectory itself (`is_injected: true`, `injected: true`, or `phase` containing `"injected"`; replayed prefix entries carry `is_replayed`/`"replayed"`). This leaks the label and must be stripped before evaluation (the official renderers drop these fields).

## Statistics (computed from the downloaded data)

Rows analysed: 7457 (text 6257 + video 916 complete; image 166 + image_gui 118 from ~1 GB samples of each file). Paper total: 12,326.

| Statistic | All analysed rows | text | video | image (sample) | image_gui (sample) |
|---|---|---|---|---|---|
| # trajectories (all failed by construction) | 7457 | 6257 | 916 | 166 | 118 |
| scorable steps per trajectory | mean 5.69, median 4, min 1, max 79 | mean 6.1, median 4, min 1, max 31 | mean 3.06, median 2.0, min 2, max 49 | mean 3.77, median 4.0, min 1, max 12 | mean 7.07, median 4.0, min 1, max 79 |
| steps histogram | 0-2: 1471, 3-4: 3033, 5-9: 2129, 10-19: 464, 20-29: 43, 30-49: 316, >=50: 1 | 0-2: 679, 3-4: 2839, 5-9: 1977, 10-19: 423, 20-29: 27, 30-49: 312, >=50: 0 | 0-2: 729, 3-4: 78, 5-9: 73, 10-19: 26, 20-29: 6, 30-49: 4, >=50: 0 | 0-2: 26, 3-4: 93, 5-9: 45, 10-19: 2, 20-29: 0, 30-49: 0, >=50: 0 | 0-2: 37, 3-4: 23, 5-9: 34, 10-19: 13, 20-29: 10, 30-49: 0, >=50: 1 |
| relative position of injected step ((idx+1)/len) | mean 0.74, median 0.8333, min 0.0253, max 1.0 | mean 0.73, median 0.8, min 0.03333333333333333, max 1.0 | mean 0.79, median 1.0, min 0.09375, max 1.0 | mean 0.84, median 1.0, min 0.14285714285714285, max 1.0 | mean 0.56, median 0.5, min 0.02531645569620253, max 1.0 |
| characters per trajectory (step contents, images excluded) | mean 9431.79, median 4663, min 197, max 292024 | mean 8630.8, median 5053, min 197, max 83572 | mean 15378.81, median 1309.0, min 739, max 292024 | mean 8977.45, median 8297.0, min 560, max 31570 | mean 6378.68, median 2964.0, min 365, max 64421 |
| agents per trajectory (roster size; 1 for single-agent) | mean 1.87, median 1, min 1, max 5 | | | | |
| single- vs multi-agent rows | {'single': 4617, 'multi': 2840} | | | | |
| rows whose GT step could not be matched to a rendered step | 0 | | | | |

**Rows per framework (with benchmark, steps, agents, error position):**

| framework | n | benchmarks | steps (mean/med/min/max) | agents | err. rel. pos. mean | top faulty agent |
|---|---|---|---|---|---|---|
| smolagents | 3442 | tablebench:913, dsqa:830, databench:818, dabench:327, dacode:306, browsecomp_vl:166, kramabench:82 | 4.52/4.0/1/22 | 1 | 0.83 | (single-agent) (3442) |
| mathchat | 920 | mmlu_pro:315, math:304, scibench:301 | 3.62/3.0/3/29 | 2 | 0.85 | assistant (920) |
| magentic-one | 811 | simpleqa_verified:509, gaia:302 | 6.1/5/1/31 | 5 | 0.77 | orchestrator (636) |
| eva | 748 | lvbench:748 | 2.03/2.0/2/4 | 1 | 0.77 | (single-agent) (748) |
| debate | 445 | scibench:171, math:144, gpqa:74, mmlu_pro:56 | 6/6/6/6 | 3 | 0.4 | agent_2 (127) |
| alfagent | 311 | alfworld:311 | 30/30/30/30 | 1 | 0.3 | (single-agent) (311) |
| macnet | 261 | bigcodebench:170, livecodebench_pro:73, humaneval:18 | 4/4/4/4 | 3 | 0.35 | node_0 (152) |
| dvd | 168 | lvbench:168 | 7.64/5.0/3/49 | 2.89 | 0.91 | orchestrator (151) |
| dylan | 152 | scibench:83, gpqa:69 | 10.79/11.0/9/11 | 3.89 | 0.3 | agent_3 (42) |
| agentoccam | 116 | webvoyager:116 | 6.3/4.0/1/20 | 1 | 0.57 | (single-agent) (116) |
| metagpt | 81 | livecodebench_pro:56, bigcodebench:25 | 3/3/3/3 | 3 | 0.39 | architect (67) |
| coact | 2 | osworld:2 | 51.5/51.5/24/79 | 3 | 0.08 | coder (2) |

**Error-mode distribution (ground_truth.mode):**

| mode | count | % |
|---|---|---|
| R.4 Task misunderstanding | 1417 | 19.0 |
| R.2 Reasoning error | 1412 | 18.9 |
| A.3 Premature termination | 1254 | 16.8 |
| R.1 Hallucination | 822 | 11.0 |
| R.3 Numerical/calculation error | 745 | 10.0 |
| V.2 Inadequate or incorrect verification | 522 | 7.0 |
| C.3 Over-reliance on other agents | 346 | 4.6 |
| A.2 Output format/syntax error | 289 | 3.9 |
| P.1 Visual misidentification | 218 | 2.9 |
| V.1 Context/memory loss | 137 | 1.8 |
| PL.1 Ineffective Planning | 105 | 1.4 |
| A.4 Repetitive/looping behavior | 53 | 0.7 |
| PL.2 Goal drift | 46 | 0.6 |
| C.2 Communication failure | 33 | 0.4 |
| A.1 Tool parameter/invocation error | 31 | 0.4 |
| C.1 Delegation/orchestration error | 27 | 0.4 |

**Error-mode family:**

| family | count | % |
|---|---|---|
| R | 4396 | 59.0 |
| A | 1627 | 21.8 |
| V | 659 | 8.8 |
| C | 406 | 5.4 |
| P | 218 | 2.9 |
| PL | 151 | 2.0 |

**Source benchmark distribution:**

| benchmark | count | % |
|---|---|---|
| lvbench | 916 | 12.3 |
| tablebench | 913 | 12.2 |
| dsqa | 830 | 11.1 |
| databench | 818 | 11.0 |
| scibench | 555 | 7.4 |
| simpleqa_verified | 509 | 6.8 |
| math | 448 | 6.0 |
| mmlu_pro | 371 | 5.0 |
| dabench | 327 | 4.4 |
| alfworld | 311 | 4.2 |
| dacode | 306 | 4.1 |
| gaia | 302 | 4.0 |
| bigcodebench | 195 | 2.6 |
| browsecomp_vl | 166 | 2.2 |
| gpqa | 143 | 1.9 |
| livecodebench_pro | 129 | 1.7 |
| webvoyager | 116 | 1.6 |
| kramabench | 82 | 1.1 |
| humaneval | 18 | 0.2 |
| osworld | 2 | 0.0 |

**Faulty agent (multi-agent frameworks only; framework/agent):**

| framework/agent | count | % |
|---|---|---|
| mathchat/assistant | 920 | 32.4 |
| magentic-one/orchestrator | 636 | 22.4 |
| macnet/node_0 | 152 | 5.4 |
| dvd/orchestrator | 151 | 5.3 |
| debate/agent_2 | 127 | 4.5 |
| macnet/node_1 | 109 | 3.8 |
| magentic-one/websurfer | 93 | 3.3 |
| debate/agent_1 | 70 | 2.5 |
| magentic-one/coder | 69 | 2.4 |
| metagpt/architect | 67 | 2.4 |
| debate/agent_0 | 44 | 1.5 |
| dylan/agent_3 | 42 | 1.5 |
| debate/agent_0,agent_2 | 41 | 1.4 |
| dylan/agent_2 | 40 | 1.4 |
| debate/agent_2,agent_0 | 38 | 1.3 |
| dylan/agent_1 | 36 | 1.3 |
| debate/agent_0,agent_1 | 35 | 1.2 |
| debate/agent_2,agent_1 | 34 | 1.2 |
| dylan/agent_0 | 32 | 1.1 |
| debate/agent_1,agent_2 | 31 | 1.1 |
| debate/agent_1,agent_0 | 25 | 0.9 |
| dvd/frame_inspect_agent | 17 | 0.6 |
| metagpt/engineer | 14 | 0.5 |
| magentic-one/computerterminal | 8 | 0.3 |
| magentic-one/filesurfer | 5 | 0.2 |


## Example trajectory

Row id `gaia_magentic-one_0044` (framework magentic-one, benchmark gaia, split text), 7 scorable steps, 1922 characters, agents: ['orchestrator', 'websurfer', 'coder', 'filesurfer', 'computerterminal'].

**Task:** Take the gender split from the 2011 Bulgarian census about those who have completed tertiary education. Subtract the smaller number from the larger number, then return the difference in thousands of women. So if there were 30.1 thousand more men, you'd give "30.1"

Provide a concise, precise answer. State your final answer on the last line, prefixed with "FINAL ANSWER: "

**Ground-truth answer:** 234.9

**System's final answer:** 204.9

**Step 0.0 — orchestrator**

> Search for the official 2011 Bulgarian census data on educational attainment, specifically the number of men and women who have completed tertiary education. Extract the relevant numbers.

**Step 0.1 — websurfer**  **⟵ ANNOTATED ERROR STEP**

> I typed '2011 POPULATION CENSUS Main Results tertiary education men women 2011 Bulgaria' into the search bar.  
> The web browser is open to the page [2011 Bulgarian census educational attainment tertiary education numbers by gender - Search](https://www.bing.com/search?q=2011+Bulgarian+census+educational+attainment+tertiary+education+numbers+by+gender&form=QBLH&sp=-1&lq=0&pq=&sc=0-0&qs=n&sk=&cvid=0A81DC5DB135488789B8CEA69382C803).  
> The viewport shows 54% of the webpage.  
> The following text is v […]

**Step 1.0 — orchestrator**

> Subtract 586.9 from 791.8 to get the difference in thousands of women who completed tertiary education according to the 2011 Bulgarian census. Output the answer as: 'FINAL ANSWER: [number]'

**Step 1.1 — coder**

> ```python
> women = 791.8
> men = 586.9
> difference = women - men
> print(f"FINAL ANSWER: {difference:.1f}")
> ```

**Step 2.0 — orchestrator**

> Run the provided Python code to output the final answer.

**Step 2.1 — computerterminal**

> FINAL ANSWER: 204.9
> 

**Step 3.0 — orchestrator**

> According to the 2011 Bulgarian census, 791.8 thousand women and 586.9 thousand men had completed tertiary education. The difference between these numbers is 204.9 thousand, with more women than men.
> 
> FINAL ANSWER: 204.9


**Annotation (ground_truth):** `{"agent": "websurfer", "step": "0.1", "mode": "R.1"}` → faulty agent = `websurfer`, faulty step coordinate = `0.1`, error mode = `R.1` (Hallucination). No free-text reason is provided (labels are by construction). Trajectory entries flagged as injected: [2].


(normalised example written to /dataDisk/home/thanhdo/failure-attribution-datasets/notes/who_and_when_pro_example_norm.json, 3.8 KB)


Downloaded files: `text.jsonl` 75.6 MB (6 257 rows, complete), `video.jsonl` 21.3 MB (916 rows, complete), `image.PARTIAL_first1GB.jsonl` 473 MB (first 166 complete rows of 6.79 GB), `image_gui.PARTIAL_first1GB.jsonl` 791 MB (first 118 complete rows of 11.19 GB); total on disk 1.36 GB (+ eval-harness clone). Because the image files are ordered by benchmark, the samples cover only the first benchmarks in each file (browsecomp_vl for `image`, webvoyager/agentoccam and two osworld/coact rows for `image_gui`) and are **not** a random sample of the image modality; per-split statistics for those two columns should be read as indicative only. The paper's full-dataset figures are 12 326 traces, avg 7.5 steps (max 50), avg 1 139 words/trace.

## Notes for the report

- **Labels by construction, not annotation.** Every trace is a *successful* run into which one error was injected at a known step, so (agent, step, mode) are exact and there is no free-text reason. The trade-off is that failures are synthetic and *on-policy-but-prompted*: the error is written by the base agent under an adversarial instruction, and only continuations that ended in failure are kept. The injection step is typically late: mean relative position 0.74 (median 0.83) in our data — the paper reports 64 % of injections in the 40–80 % range — whereas natural-failure datasets (Who&When 0.46, TraceElephant 0.47, MP-Bench 0.40) put the decisive error near the middle. This is because the replayed prefix must be a correct prefix of a *successful* run.
- **Mostly single-agent and short.** 62 % of analysed rows are single-agent (smolagents 46 %, EVA, ALF-Agent, GUI agents); the "agent" axis is scored only on the 38 % multi-agent rows, where in several frameworks the responsible agent is nearly constant (MathChat: `assistant` 100 %; Magentic-One: `orchestrator` 78 %; MetaGPT: `architect` 83 %). Median trajectory length is 4 scorable steps; Debate (always 6 = 2 rounds × 3 agents), MacNet (4), MetaGPT (3) and ALF-Agent (always 30, i.e. hitting the step budget) have fixed lengths. Only Magentic-One (GAIA, SimpleQA-Verified) resembles the Who&When/TraceElephant setting.
- **Framework-specific trajectory schemas.** There is no common step format: 8 different `trajectory` shapes and 5 step-coordinate conventions (flat 1-based, flat 0-based with planning, `R.P` round.position, stage index, native index minus offset). The official harness's renderers/scorer must be reproduced exactly for comparable numbers; our stats follow it. Debate/DyLAN labels are round-level only (any turn in the round counts) and list *several* agents in `agents` (C.3 over-reliance), and 109 MacNet rows carry `accepted_predictions` alternates — i.e. even this benchmark concedes multiple acceptable answers for some traces.
- **Label leakage in the raw data.** Injected/replayed turns are marked in the trajectory (`is_injected`, `injected`, `phase: ["injected"]`, `is_replayed`); any evaluation must strip these fields (the harness does).
- **Taxonomy mismatch.** Paper: 18 modes (incl. "hallucinated tool/action"); released `taxonomy.yaml`: 17 modes with slightly different names (A.2 = output-format error, A.3 = premature termination, A.4 = looping). Mode distribution is dominated by Reasoning (59 %) and Action (22 %); Coordination modes are rare (5.6 %) and Perception/Planning very rare in the text split.
- **Overlap.** Same group as Who&When; Magentic-One + GAIA is the only overlap in (framework, benchmark) with Who&When/TraceElephant/MP-Bench, but the runs are new. 26 source benchmarks (19 seen in our subset) span QA, math, data analysis, code, embodied, web/GUI and video.
- **Practical.** Image and GUI rows embed base64 screenshots (6.8 + 11.2 GB); text + video splits are small (97 MB) and sufficient for text-only attribution experiments. Video rows reference frame JPEGs under `video_assets/` (not downloaded). Evaluation harness (`whowhen_eval`) needs LiteLLM, PyYAML, Pillow only.
