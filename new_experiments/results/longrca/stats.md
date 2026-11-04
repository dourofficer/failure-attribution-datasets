## 1. reason classification (heuristic)
| source | n | causal link | no link | redundant+link | redundant, no link | mentions hand-off | mentions verif. | mentions final answer |
|---|---|---|---|---|---|---|---|---|
| swe_bench_pro | 128 | 92 (72%) | 23 (18%) | 12 (9%) | 1 (1%) | 50% | 61% | 12% |
| terminal_bench_2 | 42 | 33 (79%) | 5 (12%) | 4 (10%) | 0 (0%) | 33% | 67% | 12% |
| travelplanner | 685 | 408 (60%) | 101 (15%) | 147 (21%) | 29 (4%) | 12% | 61% | 21% |
| vitabench | 108 | 64 (59%) | 34 (31%) | 10 (9%) | 0 (0%) | 10% | 26% | 3% |
| webarena_verified | 177 | 97 (55%) | 30 (17%) | 45 (25%) | 5 (3%) | 36% | 43% | 15% |
| ALL | 1140 | 694 (61%) | 193 (17%) | 218 (19%) | 35 (3%) | 21% | 55% | 17% |

## 2. root step type and blamed role afterwards
| source | n | root = hand-off/orchestration | root = tool call | root = final output | blamed role acts again | median #later msgs by blamed | root followed by tool error |
|---|---|---|---|---|---|---|---|
| swe_bench_pro | 128 | 59% | 95% | 2% | 98% | 13.5 | 12% |
| terminal_bench_2 | 42 | 40% | 93% | 2% | 98% | 18.5 | 0% |
| travelplanner | 685 | 0% | 39% | 8% | 89% | 6 | 2% |
| vitabench | 108 | 0% | 44% | 3% | 94% | 11.0 | 14% |
| webarena_verified | 177 | 10% | 0% | 0% | 80% | 2 | 0% |
| ALL | 1140 | 10% | 42% | 5% | 89% | 7.0 | 4% |

## 3. verifier / judge after the root
| source | n | any verifier msg after root | median # verifier msgs after | verifier says pass after root | verifier says fail after root | pass only (never fail) | last agent msg claims success |
|---|---|---|---|---|---|---|---|
| swe_bench_pro | 128 | 98% | 38.0 | 98% | 93% | 5% | 88% |
| terminal_bench_2 | 42 | 98% | 27.5 | 93% | 88% | 7% | 40% |
| travelplanner | 685 | 47% | 0 | 40% | 37% | 7% | 0% |
| vitabench | 108 | 0% | 0.0 | 0% | 0% | 0% | 0% |
| webarena_verified | 177 | 100% | 7 | 5% | 100% | 0% | 0% |
| ALL | 1140 | 59% | 3.0 | 39% | 51% | 5% | 11% |

## 4. visible error signs before vs after root (rates per step)
| source | tool-err before | tool-err after | retry-lang before | retry-lang after | dup tool calls before | dup after |
|---|---|---|---|---|---|---|
| swe_bench_pro | 24.1% | 26.7% | 9.0% | 12.8% | 40.7% | 20.7% |
| terminal_bench_2 | 15.3% | 15.9% | 15.4% | 12.9% | 21.9% | 19.3% |
| travelplanner | 4.6% | 5.5% | 7.4% | 7.0% | 3.7% | 3.5% |
| vitabench | 3.4% | 9.3% | 0.0% | 0.0% | 2.3% | 7.9% |
| webarena_verified | 0.4% | 5.5% | 39.7% | 38.4% | 0.0% | 0.0% |
| ALL | 7.6% | 14.6% | 10.4% | 11.3% | 7.0% | 9.2% |

## 5. Run finished texts (first 120 chars) most common per source
swe_bench_pro [('', 128)]
terminal_bench_2 [('', 42)]
travelplanner [("Run finished: Text 'TASK_COMPLETE' mentioned", 283), ('Run finished: Max rounds reached.', 88), ("Run finished: Missing or malformed 'is_request_satisfied' in", 18), ('Run finished: We have successfully gathered all required com', 14), ('Run finished: The verifier has confirmed all constraints are', 9)]
vitabench [('Run finished: agent_stop', 87), ('Run finished: too_many_errors', 14), ('Run finished: max_steps', 7)]
webarena_verified [('Run finished: Reached the multi-agent coordination budget wi', 95), ('Run finished: The task has been completed successfully. The ', 4), ("Run finished: The order history page clearly shows 'You have", 2), ('Run finished: The most recent post cannot be determined from', 1), ('Run finished: The WebSurfer encountered a network error on t', 1)]
