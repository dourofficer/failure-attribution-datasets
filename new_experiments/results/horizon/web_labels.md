## Web pass vs fail (score), id-stripped actions

| model | n fail | n pass | consecutive identical action % f/p | same action >=3x % f/p | has none % f/p | AUROC n_steps | AUROC consec | AUROC maxrep | AUROC none |
|---|---|---|---|---|---|---|---|---|---|
| gpt | 104 | 45 | 40 / 2 | 73 / 7 | 61 / 58 | 0.867 | 0.686 | 0.879 | 0.551 |
| claude | 321 | 127 | 29 / 2 | 64 / 8 | 43 / 3 | 0.913 | 0.631 | 0.835 | 0.695 |
| all | 425 | 172 | 32 / 2 | 66 / 8 | 47 / 17 | 0.898 | 0.645 | 0.845 | 0.657 |

stop type x outcome:
Counter({('max-steps-early-stop', 'fail'): 224, ('parse-early-stop', 'fail'): 153, ('stop[answer]', 'pass'): 151, ('stop[answer]', 'fail'): 48, ('parse-early-stop', 'pass'): 13, ('max-steps-early-stop', 'pass'): 8})

## Label-step signatures (result_5, 294 labels), id-stripped actions

| signature of the labelled step | n | % |
|---|---|---|
| Action: none (unparseable action) | 88 | 29.9 |
| first of two identical consecutive actions (loop start) | 29 | 9.9 |
| repeats an action taken earlier (non-consecutive) | 91 | 31.0 |
| is the stop action | 8 | 2.7 |
| none of these (needs semantics) | 78 | 26.5 |

Label vs first syntactic anomaly (earliest of: start of first identical-consecutive pair, first none):
| relation | n | % |
|---|---|---|
| no syntactic anomaly in run | 47 | 16.0 |
| label == first anomaly | 80 | 27.2 |
| label BEFORE first anomaly (judge earlier than syntax) | 92 | 31.3 |
| label 1-3 after first anomaly | 37 | 12.6 |
| label >3 after first anomaly | 38 | 12.9 |
d_anom distribution (label - first anomaly): [(-107, 1), (-71, 1), (-65, 1), (-63, 1), (-58, 1), (-57, 1), (-54, 1), (-53, 2), (-48, 1), (-46, 1), (-45, 2), (-42, 1), (-41, 1), (-36, 1), (-34, 1), (-31, 2), (-30, 1), (-29, 1), (-27, 2), (-26, 2), (-25, 1), (-24, 2), (-23, 1), (-22, 1), (-21, 1), (-19, 1), (-18, 1), (-16, 6), (-14, 3), (-13, 1), (-12, 1), (-11, 3), (-9, 1), (-8, 4), (-7, 2), (-6, 4), (-5, 4), (-4, 4), (-3, 6), (-2, 8), (-1, 12), (0, 80), (1, 19), (2, 12), (3, 6), (4, 6), (5, 5), (6, 7), (7, 1), (8, 6), (12, 1), (14, 2), (15, 1), (16, 1), (18, 2), (20, 1), (24, 1), (26, 1), (37, 1), (40, 2), (None, 47)]
by failure_type: label==first anomaly: {'History Error Accumulation': '0/5', 'False Assumption': '1/7', 'Memory Limitation': '0/5', 'Environment': '10/17', 'Planning Error': '69/252', 'Instruction': '0/8'}