# AgentErrorBench targeted statistics

### 1. Action-validity signature per env x backbone (turn counts summed over runs)

| env | backbone | runs | turns | valid | malformed (right action, wrong surface form) | inadmissible | obs 'Nothing happens' | runs with >=1 malformed | runs with >=50% Nothing |
|---|---|---|---|---|---|---|---|---|---|
| alfworld | GPT-4o | 50 | 1500 | 970 | 493 | 37 | 517 | 49 | 12 |
| alfworld | Llama3.3-70B-Turbo | 23 | 690 | 359 | 156 | 175 | 317 | 22 | 11 |
| alfworld | Qwen3-8B | 27 | 810 | 801 | 0 | 9 | 9 | 0 | 0 |
| gaia | GPT-4o | 16 | 291 | 0 | 0 | 0 | 0 | 0 | 0 |
| gaia | Llama3.3-70B-Turbo | 17 | 339 | 0 | 0 | 0 | 0 | 0 | 0 |
| gaia | Qwen3-8B | 17 | 87 | 0 | 0 | 0 | 0 | 0 | 0 |
| webshop | GPT-4o | 15 | 426 | 421 | 0 | 0 | 0 | 0 | 0 |
| webshop | Llama3.3-70B-Turbo | 17 | 510 | 435 | 0 | 0 | 0 | 0 | 0 |
| webshop | Qwen3-8B | 18 | 360 | 360 | 0 | 0 | 0 | 0 | 0 |

### 2. ALFWorld: label turn vs first malformed action / first inadmissible action / first "Nothing happens"

| relation | vs first malformed | vs first inadmissible | vs first Nothing |
|---|---|---|---|
| none | 29 | 59 | 23 |
| label<first | 14 | 22 | 14 |
| label==first | 6 | 5 | 9 |
| label>first | 51 | 14 | 54 |

### 2b. ALFWorld: is the labelled turn itself a malformed / inadmissible / Nothing-happens turn, by module

| module | n | gold malformed | gold inadmissible | gold -> 'Nothing happens' | obs before gold = 'Nothing happens' | median Nothing count in run |
|---|---|---|---|---|---|---|
| action | 14 | 5 | 3 | 8 | 2 | 12.0 |
| memory | 18 | 5 | 1 | 6 | 7 | 9.0 |
| planning | 33 | 7 | 4 | 11 | 8 | 6 |
| reflection | 22 | 7 | 0 | 7 | 6 | 8.5 |
| system | 13 | 2 | 0 | 1 | 2 | 0 |

### 3. Repetition before vs after the labelled turn (means over runs; cap runs only, n_turns=30)

| env | runs | repeat-action frac before | after | bigram repeat before | after | novel-obs frac before | after | 'Nothing' per turn before | after | median max consecutive identical action |
|---|---|---|---|---|---|---|---|---|---|---|
| alfworld | 86 | 0.11 | 0.42 | 0.02 | 0.19 | 0.83 | 0.54 | 0.25 | 0.30 | 2.0 |
| webshop | 34 | 0.30 | 0.64 | 0.26 | 0.45 | 0.87 | 0.60 | 0.00 | 0.00 | 6.0 |
| gaia | 15 | 0.01 | 0.58 | 0.00 | 0.36 | 0.91 | 0.31 | 0.00 | 0.00 | 2 |

### 3b. Distinct-action fraction and tail stagnation per env (all runs)

| env | runs | median distinct-action frac | runs with distinct frac < 0.5 | runs whose last 10 turns contain <=3 distinct actions | runs with >=5 consecutive identical actions |
|---|---|---|---|---|---|
| alfworld | 100 | 0.6 | 35 | 8 | 1 |
| webshop | 50 | 0.3466666666666667 | 36 | 12 | 26 |
| gaia | 50 | 0.9375 | 9 | 6 | 7 |

### 4. How runs end, per env (answer / buy / step cap / other) and tool-error observations

| env | runs | answer | buy now | cap (30 turns) | other | runs with >=1 error-like observation | label at last turn |
|---|---|---|---|---|---|---|---|
| alfworld | 100 | 0 | 0 | 100 | 0 | 0 | 10 |
| webshop | 50 | 0 | 11 | 39 | 0 | 0 | 7 |
| gaia | 50 | 47 | 0 | 0 | 3 | 24 | 12 |

### 4b. Module of the label by how the run ended

| ended | n | planning | reflection | memory | action | system |
|---|---|---|---|---|---|---|
| answer | 47 | 24 | 9 | 5 | 6 | 3 |
| buy | 11 | 0 | 6 | 4 | 1 | 0 |
| cap | 139 | 52 | 25 | 29 | 15 | 18 |
| other | 3 | 2 | 0 | 0 | 0 | 1 |

### 5. Label-text consistency

| check | count |
|---|---|
| records with empty failure_type | 27 |
| records with no reason text | 43 |
| reason mentions step numbers, none equal to the label turn | 2 |
| label = last turn (30) with category system.step_limit | 8 |
| label = last turn, other category | 21 |
| ALFWorld runs with >=1 malformed action but label module != action | 58 |
| ALFWorld runs with >=10 malformed actions | 30 |
| ALFWorld runs with >=10 malformed actions whose label module != action | 26 |

reason/label step mismatches: alfworld/Qwen3-8B_023_id_23___chat_b013_t00_e00-d3248f80 label 4 reason [3]; webshop/GPT-4o_015_chat_b000_t00_e14-1d03d2d8 label 2 reason [3]