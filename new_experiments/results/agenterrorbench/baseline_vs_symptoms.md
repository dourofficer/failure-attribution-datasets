# Baseline and prefix probe vs symptom turns

## All-at-once (n=60)

| count | n |
|---|---|
| exact | 17 |
| exact & gold == first malformed/inadmissible/Nothing turn | 1 |
| miss | 43 |
| miss & pred == first malformed/inadmissible/Nothing turn | 4 |
| miss & pred earlier than gold | 27 |
| miss & pred earlier & run has >=5 Nothing turns | 7 |

| env | n | exact | pred earlier (turns) | pred later | within ±1 turn |
|---|---|---|---|---|---|
| alfworld | 25 | 6 | 11 | 8 | 13 |
| webshop | 17 | 5 | 12 | 0 | 6 |
| gaia | 18 | 6 | 4 | 8 | 9 |

| id | env | gold turn | pred turn | pred-gold | label type | pred == symptom turn | #Nothing | #malformed |
|---|---|---|---|---|---|---|---|---|
| GPT-4o_021_alfworld_task_0 | alfworld | 30 | 3 | -27 | system.step_limit | first malformed,first Nothing | 7 | 7 |
| GPT-4o_002_alfworld_task_0 | alfworld | 24 | 13 | -11 | memory.over_simplification | - | 7 | 6 |
| Qwen3-8B_007_id_7___chat_b | alfworld | 30 | 26 | -4 | system.step_limit | - | 0 | 0 |
| Llama3.3-70B-Turbo_006_006 | alfworld | 7 | 3 | -4 | planning. | first inadmissible | 14 | 4 |
| GPT-4o_009_alfworld_task_0 | alfworld | 10 | 7 | -3 | planning.impossible_action | - | 10 | 10 |
| Llama3.3-70B-Turbo_012_012 | alfworld | 24 | 22 | -2 | planning. | - | 9 | 7 |
| GPT-4o_039_alfworld_task_0 | alfworld | 4 | 3 | -1 | memory.over_simplification | - | 11 | 11 |
| Qwen3-8B_027_id_27___chat_ | alfworld | 23 | 22 | -1 | reflection. | - | 0 | 0 |
| Qwen3-8B_023_id_23___chat_ | alfworld | 4 | 3 | -1 | planning.inefficient_plan | - | 0 | 0 |
| Llama3.3-70B-Turbo_013_013 | alfworld | 4 | 3 | -1 | action. | first malformed,first Nothing | 17 | 13 |
| Qwen3-8B_002_id_2___chat_b | alfworld | 5 | 4 | -1 | planning.inefficient_plan | - | 0 | 0 |
| GPT-4o_047_alfworld_task_0 | alfworld | 10 | 10 | 0 | memory.over_simplification | - | 4 | 4 |
| GPT-4o_049_alfworld_task_0 | alfworld | 9 | 9 | 0 | memory.over_simplification | - | 5 | 5 |
| GPT-4o_019_alfworld_task_0 | alfworld | 7 | 7 | 0 | action.misalignment | - | 12 | 4 |
| Qwen3-8B_018_id_18___chat_ | alfworld | 4 | 4 | 0 | reflection.causal_misattribution | - | 0 | 0 |
| Llama3.3-70B-Turbo_003_003 | alfworld | 4 | 4 | 0 | planning. | first malformed,first Nothing | 26 | 22 |
| GPT-4o_048_alfworld_task_0 | alfworld | 26 | 26 | 0 | reflection.progress_misjudge | - | 9 | 9 |
| GPT-4o_010_alfworld_task_0 | alfworld | 4 | 5 | 1 | reflection.progress_misjudge | first malformed,first Nothing | 7 | 5 |
| Llama3.3-70B-Turbo_017_044 | alfworld | 4 | 5 | 1 | planning. | - | 18 | 7 |
| Llama3.3-70B-Turbo_020_057 | alfworld | 2 | 9 | 7 | action. | - | 12 | 1 |
| GPT-4o_022_alfworld_task_0 | alfworld | 9 | 23 | 14 | planning.inefficient_plan | - | 6 | 6 |
| GPT-4o_056_alfworld_task_0 | alfworld | 4 | 19 | 15 | planning.impossible_action | - | 3 | 2 |
| Qwen3-8B_014_id_14___chat_ | alfworld | 11 | 30 | 19 | planning.inefficient_plan | - | 0 | 0 |
| Llama3.3-70B-Turbo_018_045 | alfworld | 1 | 22 | 21 | action. | - | 17 | 13 |
| Qwen3-8B_006_id_6___chat_b | alfworld | 1 | 29 | 28 | planning.inefficient_plan | - | 0 | 0 |
| Llama3.3-70B-Turbo_001_mem | gaia | 6 | 1 | -5 | planning.inefficient_plan | - | 0 | 0 |
| GPT-4o_012_memory_b001_t00 | gaia | 5 | 2 | -3 | action.Parameter_error | - | 0 | 0 |
| GPT-4o_002_memory_b000_t00 | gaia | 3 | 1 | -2 | action.misalignment | - | 0 | 0 |
| GPT-4o_008_memory_b000_t00 | gaia | 5 | 4 | -1 | planning.impossible_action | - | 0 | 0 |
| Qwen3-8B_006_memory_b000_t | gaia | 1 | 1 | 0 | system.llm_limit | - | 0 | 0 |
| Llama3.3-70B-Turbo_007_mem | gaia | 1 | 1 | 0 | action.parameter_error | - | 0 | 0 |
| GPT-4o_006_memory_b000_t00 | gaia | 3 | 3 | 0 | memory.over_simplification | - | 0 | 0 |
| Qwen3-8B_015_memory_b001_t | gaia | 2 | 2 | 0 | reflection.outcome_misinterpretation | - | 0 | 0 |
| Qwen3-8B_013_memory_b001_t | gaia | 4 | 4 | 0 | reflection.outcome_misinterpretation | - | 0 | 0 |
| Qwen3-8B_011_memory_b001_t | gaia | 5 | 5 | 0 | system.tool_execution_error | - | 0 | 0 |
| Qwen3-8B_007_memory_b000_t | gaia | 2 | 3 | 1 | planning.inefficient_plan | - | 0 | 0 |
| Qwen3-8B_017_memory_b001_t | gaia | 2 | 3 | 1 | planning.inefficient_plan | - | 0 | 0 |
| Llama3.3-70B-Turbo_002_mem | gaia | 10 | 14 | 4 | planning.inefficient_plan | - | 0 | 0 |
| GPT-4o_010_memory_b001_t00 | gaia | 4 | 8 | 4 | planning.impossible_action | - | 0 | 0 |
| Llama3.3-70B-Turbo_009_mem | gaia | 4 | 9 | 5 | memory.hallucination | - | 0 | 0 |
| GPT-4o_011_memory_b001_t00 | gaia | 3 | 12 | 9 | memory.over_simplification | - | 0 | 0 |
| GPT-4o_001_memory_b000_t00 | gaia | 5 | 30 | 25 | planning.inefficient_plan | - | 0 | 0 |
| Llama3.3-70B-Turbo_005_mem | gaia | 1 | 30 | 29 | system.tool_execution_error  | - | 0 | 0 |
| GPT-4o_011_chat_b000_t00_e | webshop | 21 | 1 | -20 | planning.inefficient_plan | - | 0 | 0 |
| Qwen3-8B_011_chat_b000_t00 | webshop | 12 | 1 | -11 | planning.inefficient_plan | - | 0 | 0 |
| GPT-4o_007_chat_b000_t00_e | webshop | 11 | 4 | -7 | reflection.progress_misjudge | - | 0 | 0 |
| Qwen3-8B_008_chat_b000_t00 | webshop | 7 | 1 | -6 | planning.inefficient_plan | - | 0 | 0 |
| Qwen3-8B_006_chat_b000_t00 | webshop | 7 | 1 | -6 | planning.inefficient_plan | - | 0 | 0 |
| Qwen3-8B_003_chat_b000_t00 | webshop | 7 | 1 | -6 | planning.constraint_ignorance | - | 0 | 0 |
| Llama3.3-70B-Turbo_018_web | webshop | 6 | 1 | -5 | planning.plan_inefficient | - | 0 | 0 |
| GPT-4o_009_chat_b000_t00_e | webshop | 5 | 1 | -4 | planning.inefficient_plan | - | 0 | 0 |
| Llama3.3-70B-Turbo_015_web | webshop | 6 | 2 | -4 | reflection.causal_misattribution | - | 0 | 0 |
| Llama3.3-70B-Turbo_006_web | webshop | 6 | 2 | -4 | memory.over_simplification | - | 0 | 0 |
| Llama3.3-70B-Turbo_011_web | webshop | 4 | 1 | -3 | planning.plan_inefficient | - | 0 | 0 |
| Llama3.3-70B-Turbo_017_web | webshop | 6 | 5 | -1 | memory.hallucination | - | 0 | 0 |
| Llama3.3-70B-Turbo_014_web | webshop | 2 | 2 | 0 | memory.over_simplification | - | 0 | 0 |
| GPT-4o_004_chat_b000_t00_e | webshop | 2 | 2 | 0 | reflection.progress_misjudge | - | 0 | 0 |
| Llama3.3-70B-Turbo_005_web | webshop | 1 | 1 | 0 | system.environment_error | - | 0 | 0 |
| GPT-4o_013_chat_b000_t00_e | webshop | 2 | 2 | 0 | memory.hallucination | - | 0 | 0 |
| Qwen3-8B_005_chat_b000_t00 | webshop | 1 | 1 | 0 | system.environment_error | - | 0 | 0 |

median signed offset (turns) per env: {'alfworld': 0, 'webshop': -4, 'gaia': 0.0}

## Prefix probe (window ±6 idx around gold, n=20 records)

| group | records | gold flagged | earliest flagged == gold | flag rate before gold | flag rate after gold | gold turn is a null-obs/malformed turn |
|---|---|---|---|---|---|---|
| alfworld | 9 | 2 | 0 | 3/27 | 15/24 | 1 |
| module=memory | 5 | 3 | 1 | 3/13 | 9/15 | 1 |
| module=reflection | 2 | 0 | 0 | 0/6 | 2/6 | 0 |
| webshop | 6 | 3 | 3 | 0/16 | 8/18 | 0 |
| module=planning | 9 | 3 | 2 | 1/25 | 14/25 | 0 |
| gaia | 5 | 3 | 2 | 1/7 | 6/10 | 0 |
| module=system | 3 | 2 | 2 | 0/3 | 3/3 | 0 |
| module=action | 1 | 0 | 0 | 0/3 | 1/3 | 0 |

| gold-turn kind | flagged | not flagged |
|---|---|---|
| gold is null-obs/malformed | 0 | 2 |
| gold is a semantic decision | 8 | 10 |

per-record probe: GPT-4o_047_alfworld_ta gold 10 flagged=True earliest=7 what='It returns to desk 1 despite repeated observations that the desk lacks a desklam'; GPT-4o_010_alfworld_ta gold 4 flagged=False earliest=6 what='Taking the cup from the countertop is a valid necessary step; it can be cleaned '; Llama3.3-70B-Turbo_011 gold 4 flagged=False earliest=None what='Clicking next is a valid exploration step, though refining the search may be mor'; Qwen3-8B_006_memory_b0 gold 1 flagged=True earliest=1 what='It prematurely provides a final answer without waiting for or using the search r'; GPT-4o_009_alfworld_ta gold 10 flagged=False earliest=11 what='The action is correct because the previous close failed, so closing the microwav'; Llama3.3-70B-Turbo_002 gold 10 flagged=True earliest=7 what='It attempts to compute the ISBN-10 check digit without having found or supplied '; Qwen3-8B_007_memory_b0 gold 2 flagged=False earliest=None what='Using Google search after a failed Wikipedia lookup is a reasonable next step to'; GPT-4o_011_chat_b000_t gold 21 flagged=True earliest=21 what='Clicking next on Page 5 of 50 total results is unjustified because there are lik'; GPT-4o_039_alfworld_ta gold 4 flagged=False earliest=None what='Going to the dresser is a valid admissible action and a plausible place to searc'; Qwen3-8B_007_id_7___ch gold 30 flagged=False earliest=None what='The action is a logical continuation of the systematic search for the newspaper.'; GPT-4o_009_chat_b000_t gold 5 flagged=False earliest=None what='Clicking next page is a reasonable way to continue browsing the 50 search result'; GPT-4o_049_alfworld_ta gold 9 flagged=True earliest=6 what='Returning to desk 1 is unjustified because desk 1 was already examined and showe'; GPT-4o_001_memory_b000 gold 5 flagged=False earliest=6 what='The step is a reasonable, though not optimal, search for community discussion ab'; Llama3.3-70B-Turbo_017 gold 6 flagged=True earliest=6 what='It ignores the confirmed matching product and returns to search instead of going'; GPT-4o_019_alfworld_ta gold 7 flagged=False earliest=9 what='Taking a ladle from the countertop is a valid progress step; if it is dirty it c'; Llama3.3-70B-Turbo_005 gold 1 flagged=True earliest=1 what='The python_code_generator query omits the actual table entries, so the tool lack'; Llama3.3-70B-Turbo_018 gold 6 flagged=True earliest=6 what='Repeats the same unsuccessful search query instead of refining it as planned.'; Qwen3-8B_027_id_27___c gold 23 flagged=False earliest=26 what='Going to shelf 1 with the bowl is a valid next step to place it; no clear eviden'; GPT-4o_056_alfworld_ta gold 4 flagged=False earliest=5 what='Taking the bowl is a reasonable step toward examining it with the desklamp and d'; Llama3.3-70B-Turbo_014 gold 2 flagged=False earliest=5 what='Clicking next is a valid browsing action, though inspecting the plausible candid'