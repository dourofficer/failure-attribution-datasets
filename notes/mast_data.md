# MAST-Data / MAD (Why Do Multi-Agent LLM Systems Fail?)

## Identity

| Field | Value |
|---|---|
| Full title | **Why Do Multi-Agent LLM Systems Fail?** — introduces the **MAST** taxonomy (Multi-Agent System failure Taxonomy) and the **MAD** dataset (Multi-Agent system traces Dataset; HF name *MAST-Data*) |
| Authors / affiliation | Mert Cemri, Melissa Z. Pan, Shuyi Yang, Lakshya A. Agrawal, Bhavya Chopra, Rishabh Tiwari, Kurt Keutzer, Aditya Parameswaran, Dan Klein, Kannan Ramchandran, Matei Zaharia, Joseph E. Gonzalez, Ion Stoica — UC Berkeley (Stoica also Intesa Sanpaolo) |
| Venue | NeurIPS 2025 (BibTeX in the dataset card); arXiv v3 26 Oct 2025 |
| arXiv | [2503.13657](https://arxiv.org/abs/2503.13657) |
| Links | Paper HTML: https://arxiv.org/html/2503.13657 · Code/taxonomy/annotator: https://github.com/multi-agent-systems-failure-taxonomy/MAST · Data: https://huggingface.co/datasets/mcemri/MAST-Data |
| License | Dataset: CC-BY-4.0 (HF card). Paper: CC BY-NC-ND 4.0. |
| Availability | **Public, downloaded** (not gated). The HF repo `mcemri/MAST-Data` contains both files; there is **no separate `mcemri/MAST-Data-human` repo** (hf download of that name returns 404) — the human-labelled set is the `human_labelled` config (`MAD_human_labelled_dataset.json`) of the same repo (the GitHub README refers to the same HF repo under the alias `mcemri/MAD`). **GitHub repo not cloned**: three `git clone` attempts (HTTP/2, HTTP/1.1 + blob filter) aborted with transport errors/timeouts — the repo is very large (13,920 tree entries, of which 13,903 are raw trace files and attachments); its file tree and README were fetched via the GitHub API instead (`MAST_github_meta/`). |
| On-disk size | `MAD_full_dataset.json` 190 MB + `MAD_human_labelled_dataset.json` 2.9 MB (≈193 MB); GitHub metadata (tree.json + README) ≈ 3 MB |
| Local path | `/dataDisk/home/thanhdo/failure-attribution-datasets/data/mast_data/MAST-Data/{MAD_full_dataset.json,MAD_human_labelled_dataset.json}`; GitHub tree/README: `/dataDisk/home/thanhdo/failure-attribution-datasets/data/mast_data/MAST_github_meta/` |

## Description

**Purpose.** MAST is an empirically grounded *taxonomy* of why LLM-based MAS fail (14 failure modes in 3 categories), built with grounded-theory analysis of real traces. MAD / MAST-Data is the companion corpus of execution traces, each labelled with a **binary vector over the 14 modes** (trace-level: does this failure mode occur anywhere in the trace?). It is a failure-*taxonomy* dataset, not a step-attribution dataset: there is **no faulty-step, no faulty-agent, no reason text, and no task-success label** in the release.

**Source MAS, LLMs, benchmarks (computed from the data).** 7 frameworks: AG2 (MathChat / captain-agent style 3-agent group chat), MetaGPT (SimpleCoder/SimpleTester/SimpleReviewer), ChatDev (CEO/CPO/CTO/Programmer/Code Reviewer/Counselor/Test Engineer), Magentic-One (Orchestrator + WebSurfer/FileSurfer/Assistant/ComputerTerminal), AppWorld (Supervisor + per-app agents), HyperAgent (Planner/Navigator/Editor/Executor + inner assistants), OpenManus (single `Manus` agent with planning flow). 5 LLM labels: GPT-4o, Claude (3.7 Sonnet), GPT-4o-mini, Qwen (2.5-Coder-32B), CodeLlama (7B). 8 benchmarks: ProgramDev, ProgramDev-v2, GSM(-Plus), Olympiad(Bench), GAIA, MMLU, Test-C (AppWorld), SWE-Bench-Lite.

**How failures were obtained — natural.** Traces are ordinary runs of the frameworks; no injection. The paper reports 41–86.7 % task-failure rates across the systems, but the per-trace outcome is not in the release.

**Annotation protocol.** (1) Taxonomy building: 150+ traces from five MAS (HyperAgent, AppWorld, AG2, ChatDev, MetaGPT) open-coded by 6 experts (>20 h each), theoretical saturation, then iterative refinement across three inter-annotator rounds (taxonomy sizes 18 → 17 → 17 → final 14 modes). (2) **Human-labelled set**: 3 annotators; final Cohen's κ = **0.88**; out-of-domain generalisation round (OpenManus, Magentic-One on MMLU/GAIA) κ = **0.79**. The paper speaks of 21 traces × 3 experts; the released file holds **19 traces** (5+5+5 per round + 4 generalisation). (3) **Full set (1,642 traces)**: annotated by an **LLM-as-a-judge (OpenAI o1, few-shot)** validated against the human labels: accuracy 0.94, precision 0.833, recall 0.77, F1 0.80, κ = 0.77 (zero-shot: acc 0.89, κ 0.58). The GitHub repo ships the judge ("MAST Annotator").

**The 14 failure modes / 3 categories (paper frequencies over the human-annotated study; data share of all LLM-judge flags in parentheses):**

| Category | Mode | Paper % | Data share of flags | Data: traces flagged |
|---|---|---|---|---|
| FC1 Specification issues (paper ≈ 44%) | FM-1.1 Disobey task specification | 11.8 | 11.5 | 591 |
| | FM-1.2 Disobey role specification | 1.5 | 1.8 | 91 |
| | FM-1.3 Step repetition | 15.7 | 12.9 | 664 |
| | FM-1.4 Loss of conversation history | 2.8 | 2.3 | 117 |
| | FM-1.5 Unaware of termination conditions | 12.4 | 8.5 | 436 |
| FC2 Inter-agent misalignment (paper ≈ 32%) | FM-2.1 Conversation reset | 2.2 | 1.6 | 80 |
| | FM-2.2 Fail to ask for clarification | 6.8 | 5.2 | 265 |
| | FM-2.3 Task derailment | 7.4 | 6.9 | 353 |
| | FM-2.4 Information withholding | 0.85 | 0.5 | 24 |
| | FM-2.5 Ignored other agent's input | 1.9 | 7.2 | 370 |
| | FM-2.6 Reasoning-action mismatch | 13.2 | 11.9 | 610 |
| FC3 Task verification (paper ≈ 24%) | FM-3.1 Premature termination | 6.2 | 5.3 | 274 |
| | FM-3.2 No or incomplete verification | 8.2 | 11.8 | 608 |
| | FM-3.3 Incorrect verification | 9.1 | 12.8 | 658 |

(Category totals are sums of the paper's mode percentages; the paper gives them only in Figure 1.)

**Task formulation & metrics.** The paper is diagnostic; the "task" on MAD is multi-label trace classification (14 binary labels). Reported numbers: LLM-judge vs. human — accuracy 0.94 / F1 0.80 / κ 0.77 (o1 few-shot). Intervention case studies: ChatDev + role/workflow fix +9.4 % task success (GPT-4o), ChatDev + verification step +15.6 % on ProgramDev. Framework comparisons (paper): MetaGPT 60–68 % fewer FC1/FC2 failures than ChatDev but 1.56× more FC3; GPT-4o 39 % fewer FC1 failures than Claude-3.7 within MetaGPT.

## Schema

`MAD_full_dataset.json` — JSON list of 1,642 records:

| Field | Type | Meaning |
|---|---|---|
| `mas_name` | str | AG2, MetaGPT, ChatDev, Magentic, AppWorld, HyperAgent, OpenManus |
| `llm_name` | str | GPT-4o, Claude, GPT-4o-mini, Qwen, CodeLlama |
| `benchmark_name` | str | ProgramDev, ProgramDev-v2, GSM, Olympiad, GAIA, MMLU, Test-C, SWE-Bench-Lite |
| `trace_id` | int | running index within the file (0…1641) |
| `trace` | dict | `{key: "<MAS>_<benchmark>_<LLM>", index: int, trajectory: str}` — **one raw log string** per trace (format differs per framework: ChatDev/MetaGPT/OpenManus logs, AG2 printed message dicts, Magentic console transcript, AppWorld REPL transcript, HyperAgent logger lines) |
| `mast_annotation` | dict | 14 keys `"1.1"…"3.3"` → 1 / 0 / null (4 traces have all-null annotations) |

`MAD_human_labelled_dataset.json` — list of 19 records: `round` ("Round 1/2/3", "Generlazability"), `mas_name`, `benchmark_name`, `trace_id`, `trace` (str), `annotations`: list of `{ "failure mode": "<code> <name>\n\n<definition>", annotator_1, annotator_2, annotator_3: bool }`. The mode list differs per round (18 / 17 / 17 / 14 modes) and codes are **not comparable across rounds**; in the generalisation round `mas_name`/`benchmark_name` are swapped for the two GAIA rows.

GitHub repo (from the API tree listing; not cloned): `README.md`; `llm_judge_pipeline.ipynb` (the o1 LLM-as-a-judge annotation pipeline); `taxonomy_definitions_examples/{definitions.txt, examples.txt}` (the 14-mode definitions and few-shot examples used by the judge); `inter_annotator_agreement_annotations/` (4 PDFs: rounds 1–3 and "new benchmarks"); `assets/` (taxonomy figures); `traces/` with the **raw per-run artefacts** grouped as `AG2/`, `AppWorld/`, `HyperAgent/` (incl. `raw_trajs/*.log`), `MagenticOne_GAIA/gaia_validation_level_{1,2}__MagenticOne/<task-id>/…` (console logs, screenshots, downloaded PDFs/audio), `OpenManus_GAIA/`, `math_interventions/`, `mmlu/`, `programdev/` — i.e. the unflattened sources of the HF `trajectory` strings plus intervention runs. Nothing from it was executed.

## Statistics (computed from the data; `mast_data_stats.json`)

| Statistic | Value |
|---|---|
| Traces | **1,642** (config `default`, split `train`) + **19** human-labelled |
| Frameworks | AG2 597 · MetaGPT 430 · ChatDev 330 · Magentic 195 · OpenManus 30 · AppWorld 30 · HyperAgent 30 |
| LLMs | GPT-4o 751 · Claude 323 · Qwen 200 · CodeLlama 200 · GPT-4o-mini 168 |
| Benchmarks | ProgramDev-v2 400 · ProgramDev 390 · GSM 223 · Olympiad 206 · GAIA 195 · MMLU 168 · Test-C 30 · SWE-Bench-Lite 30 |
| (MAS, benchmark, LLM) cells | 15 (e.g. AG2/GSM/Claude 193, AG2/Olympiad/GPT-4o 206, AG2/MMLU/GPT-4o-mini 168, Magentic/GAIA/GPT-4o 195, ChatDev/ProgramDev/GPT-4o 130, ChatDev/ProgramDev-v2/{Qwen,CodeLlama} 100 each, MetaGPT/ProgramDev/{GPT-4o 130, Claude 100}, MetaGPT/ProgramDev-v2/{Qwen,CodeLlama} 100 each, AG2/GSM/GPT-4o 30, AppWorld/Test-C/GPT-4o 30, HyperAgent/SWE-Bench-Lite/Claude 30, OpenManus/ProgramDev/GPT-4o 30) |
| Success vs failure | **no task-outcome label**. Traces with ≥1 flagged mode: 1,237 (75.5 %); none flagged: 401; all-null: 4 |
| Flagged modes per trace | mean 3.14 · median 2 · max 14; hist 0:401 · 1:189 · 2:237 · 3:208 · 4:153 · 5:133 · 6:85 · 7:76 · 8:45 · 9:30 · 10:24 · 11:29 · 12:20 · 13:6 · 14:2 |
| Traces with any mode in FC1 / FC2 / FC3 | 954 / 876 / 907 |
| Any-failure rate by framework | OpenManus 96.7 % · AppWorld 96.7 % · MetaGPT 94.9 % · ChatDev 92.4 % · HyperAgent 90.0 % · Magentic 78.5 % · AG2 47.9 % |
| Most common mode combinations | none 401 · 1.3+1.5 54 · 1.1 46 · 3.2 34 · 1.3 33 · 3.3 29 · 2.6+3.3 20 · 2.6 20 · 2.6+3.2+3.3 20 |
| Characters per trace | mean 115.9 k · median 9.7 k · min 1.3 k · max 2.0 M; hist ≤5k: 384 · 5–20k: 566 · 20–50k: 221 · 50–200k: 137 · 200–500k: 177 · >500k: 157 (ChatDev traces are 170 k–2 M chars) |
| Steps per trace (**heuristic** regex split, 1,610 parsed; 32 AG2/HyperAgent parse failures) | mean 20.1 · median 6 · min 2 · max 513; hist 1–5: 340 · 6–10: 692 · 11–20: 87 · 21–40: 198 · 41–80: 280 · >80: 13 |
| Steps by framework (median) | AG2 4 · MetaGPT 6 · Magentic 19 · OpenManus 23 · AppWorld 23.5 · HyperAgent 50.5 · ChatDev 66 |
| Distinct agents per trace (heuristic) | mean 3.9 · median 4 · min 1 (OpenManus) · max 7 (HyperAgent/ChatDev); AG2 2–4, MetaGPT 4 (incl. Human), Magentic 2–6, AppWorld 2–3 |
| Error step position / faulty agent | not available (trace-level labels only) |
| Human-labelled set agreement (computed) | Round 1 (5 traces, 18 modes): pairwise agreement 1.00, κ 1.00 · Round 2 (5, 17 modes): 1.00 / 1.00 · Round 3 (5, 17 modes): agreement 0.91–1.00, κ 0.72–1.00 · Generalisation (4, 14 modes): agreement 0.86–0.96, κ 0.38–0.88; positive-label rate 8–27 % of cells |

Caveat: our κ on the released human file is per-round over trace×mode cells and is not the same computation as the paper's κ = 0.88 (the released rounds 1–2 show perfect agreement, suggesting the file contains post-discussion consolidated labels).

## Example trajectory

Chosen: AG2 (MathChat-style `mathproxyagent` ↔ `assistant`) on GSM-Plus with Claude, `trace_id` 124, 6 messages, 4.8 k chars, LLM-judge flags **FM-2.6 Reasoning-action mismatch** only. Raw record: `mast_data_example.json`; normalised: `mast_data_example_norm.json` (steps obtained by parsing the printed message list; the dataset itself has no step structure or step label — hence no "⟵ ANNOTATED ERROR" marker; the mismatch is visible at step 1, where the assistant's code prints $302 but it states "The answer is \boxed{$254}", then at step 3 silently switches to $302).

**Source id:** `AG2_GSM_Plus_Claude#124 (trace_id=124)`  
**Task:** Let's use Python to solve a math problem.

Query requirements:
You should always use the 'print' function for the output and use fractions/radical forms instead of decimals.
You can use packages like sympy to help you.
You must follow the formats below to write your code:
```python
# your code
```

First state the key idea to solve the problem. You may choose from three ways to solve the problem:
Case 1: If the problem can be solved with Python code directly, please write a program to solve it. You can enumerate all possible arrangements if needed.
Case  […] but Leah got a 10% discount on the total vaccine cost, and the kitten broke 4 vases that cost $12 each. How much has the kitten cost so far?  
**Ground truth:** —  
**Final output:** Great! The calculations are now correct.

# Final Solution
Let's summarize the costs:

1. Spaying cost: $200
2. Vaccines: 3 vaccines at $20 each = $60 subtotal, with 10% discount = $54
3. Broken vases: 4 vases at $12 each = $48

Adding all these up: $200 + $54 + $48 = $302

The answer is \boxed{$302}

**Step 0 — mathproxyagent**
> Let's use Python to solve a math problem.
> 
> Query requirements:
> You should always use the 'print' function for the output and use fractions/radical forms instead of decimals.
> You can use packages like sympy to help you.
> You must follow the formats below to write your code:
> ```python
> # your code
> ```
> 
> First state the key idea to solve the problem. You may choose from three ways to solve the problem:
>  […]  vaccine cost, and the kitten broke 4 vases that cost $12 each. How much has the kitten cost so far?

**Step 1 — assistant**
> # Key Idea
> I'll solve this problem directly with Python code. We need to calculate the total cost which includes:
> 1. Spaying cost: $200
> 2. Vaccines cost: 3 vaccines at $20 each with a 10% discount
> 3. Broken vases: 4 vases at $12 each
> 
> ```python
> from fractions import Fraction
> 
> # Calculate the costs
> spaying_cost = 200
> vaccine_cost_per_unit = 20
> number_of_vaccines = 3
> vaccine_discount = Fraction(10,  […] of broken vases: ${vase_cost}")
> print(f"Total cost: ${total_cost}")
> ```
> 
> The answer is \boxed{$254}.

**Step 2 — mathproxyagent**
> Spaying cost: $200
> Vaccine cost (with discount): $54
> Cost of broken vases: $48
> Total cost: $302

**Step 3 — assistant**
> I need to review my calculations as the output shows a discrepancy. Let me recalculate:
> 
> # Key Idea
> I'll solve this problem directly with Python code but with corrected calculations. Let me carefully check each part:
> 
> ```python
> from fractions import Fraction
> 
> # Calculate the costs
> spaying_cost = 200
> 
> # Vaccine calculations - 3 vaccines at $20 each, then 10% discount on the total
> vaccine_cost_per_u […] n vases: 4 vases at $12 each = $48
> 
> Total cost: $200 + $54 + $48 = $302
> 
> The answer is \boxed{$302}.

**Step 4 — mathproxyagent**
> Spaying cost: $200
> Vaccine subtotal: $60
> Vaccine cost (with discount): $54
> Cost of broken vases: $48
> Total cost: $302

**Step 5 — assistant**
> Great! The calculations are now correct.
> 
> # Final Solution
> Let's summarize the costs:
> 
> 1. Spaying cost: $200
> 2. Vaccines: 3 vaccines at $20 each = $60 subtotal, with 10% discount = $54
> 3. Broken vases: 4 vases at $12 each = $48
> 
> Adding all these up: $200 + $54 + $48 = $302
> 
> The answer is \boxed{$302}

**Annotation**

- faulty agent: `None`
- faulty step: `None`
- category: `['FM-2.6 Reasoning-action mismatch (FC2 Inter-agent misalignment)']`
- reason: (none provided)
- mast_annotation: {"1.1": 0, "1.2": 0, "1.3": 0, "1.4": 0, "1.5": 0, "2.1": 0, "2.2": 0, "2.3": 0, "2.4": 0, "2.5": 0, "2.6": 1, "3.1": 0, "3.2": 0, "3.3": 0}
- mas_name: AG2
- llm_name: Claude
- benchmark_name: GSM
- annotator: LLM judge (OpenAI o1, few-shot) — trace-level binary labels only
- step_split: heuristic: AG2 message list parsed with ast.literal_eval; agent = message `name`

## Notes for the report

- **Taxonomy dataset, not attribution dataset**: labels are trace-level binary flags for 14 modes; no step, no agent, no reason, no outcome label. Use it for failure-mode classification / taxonomy statistics, not for localisation metrics.
- **Only 19 (paper: 21) traces are human-labelled**; the 1,642-trace corpus is labelled by o1 (κ 0.77 vs. humans). Frequencies in the paper (Fig. 1) come from the human grounded-theory study (150+ traces), not from this corpus; the corpus shares differ noticeably for FM-2.5 (7.2 % vs 1.9 %) and FM-3.2/3.3.
- **Highly heterogeneous raw formats** (seven different log layouts, 1 k–2 M chars); any step-level use requires framework-specific parsers (our heuristic splits are in `scripts/analyze_mast.py`). ChatDev traces are far too long for most judge contexts; 334 traces exceed 200 k chars.
- Strong **framework × benchmark × LLM confounding**: most cells are a single LLM per framework (e.g. all HyperAgent runs are Claude on SWE-Bench-Lite), so cross-framework comparisons are not controlled.
- Quirks: 4 all-null annotations; 30 AG2 traces not parseable as printed Python dicts; the human file swaps `mas_name`/`benchmark_name` for its two GAIA rows and uses the misspelt round name "Generlazability"; HF `MAST-Data-human` does not exist as a separate repo.
- Overlaps: GAIA (Magentic-One) traces overlap in *task source* with Who&When, TRAIL and CORRECT-Error (all use GAIA); SWE-Bench-Lite overlaps with TRAIL / AgentErrata; the MAST taxonomy is the reference taxonomy that AgentErrata's and several other 2025–26 datasets' modes map onto.
