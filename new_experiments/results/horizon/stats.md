## 1. Environment verdict vs judge (result_2)

| group | n | both pass | both fail | env pass / judge FAIL | env fail / judge SUCCESS | disagree % |
|---|---|---|---|---|---|---|
| domain=database | 180 | 66 | 113 | 0 | 1 | 0.6 |
| domain=os | 2735 | 697 | 1637 | 174 | 227 | 14.7 |
| domain=web | 597 | 146 | 401 | 26 | 24 | 8.4 |
| model=claude | 1907 | 534 | 1101 | 146 | 126 | 14.3 |
| model=gpt | 1605 | 375 | 1050 | 54 | 126 | 11.2 |

OS by level (env pass/judge fail = EPJF, env fail/judge success = EFJS):
| level | n | EPJF | EFJS | disagree % |
|---|---|---|---|---|
| 0 | 918 | 63 | 78 | 15.4 |
| 1 | 914 | 54 | 80 | 14.7 |
| 2 | 903 | 57 | 69 | 14.0 |

Judge failure_type given to env-PASS runs (web+os+db):
{'Planning Error': 74, 'Environment': 12, 'Instruction': 97, 'False Assumption': 4, 'Catastrophic Forgetting': 12, 'History Error Accumulation': 1}

## 2. Judge self-consistency: result_2 vs result_3

| group | n | exact label agree % | pass/fail agree % |
|---|---|---|---|
| domain=database | 180 | 98.3 | 100.0 |
| domain=embodied | 270 | 70.0 | 74.1 |
| domain=os | 2735 | 74.6 | 95.1 |
| domain=web | 597 | 87.6 | 98.5 |
| env=None | 270 | 70.0 | 74.1 |
| env=fail | 2403 | 73.0 | 97.7 |
| env=pass | 1109 | 88.9 | 92.1 |
| len=1-5 | 826 | 85.2 | 88.9 |
| len=16-30 | 579 | 67.0 | 95.7 |
| len=6-15 | 2178 | 77.2 | 95.5 |
| len=>30 | 199 | 78.4 | 100.0 |
| level=database: | 180 | 98.3 | 100.0 |
| level=embodied: | 270 | 70.0 | 74.1 |
| level=os:0 | 918 | 73.7 | 93.9 |
| level=os:1 | 914 | 74.1 | 95.6 |
| level=os:2 | 903 | 76.0 | 95.7 |
| level=web:1 | 130 | 89.2 | 93.8 |
| level=web:2 | 130 | 91.5 | 100.0 |
| level=web:3 | 116 | 85.3 | 99.1 |
| level=web:4 | 116 | 84.5 | 100.0 |
| level=web:5 | 105 | 86.7 | 100.0 |
| model=claude | 2042 | 78.3 | 94.1 |
| model=gpt | 1740 | 76.4 | 94.6 |

Top label confusions (r2 -> r3):
[(('Catastrophic Forgetting', 'Planning Error'), 204), (('Instruction', 'Planning Error'), 109), (('Planning Error', 'Instruction'), 104), (('Planning Error', 'Catastrophic Forgetting'), 98), (('Success', 'Planning Error'), 68), (('Planning Error', 'Success'), 60), (('Instruction', 'Success'), 39), (('Instruction', 'Catastrophic Forgetting'), 35), (('Success', 'Instruction'), 31), (('False Assumption', 'Planning Error'), 22), (('Environment', 'Planning Error'), 18), (('Catastrophic Forgetting', 'Instruction'), 14)]

r2/r3 pass-fail splits, who matches env: {'r2 matches env': 57, 'r3 matches env': 87}
r2 disagrees with env: 452; of these r3 ALSO disagrees with env: 365 (80.8%) -> stable judge-vs-env disagreement
result_1 overlaps result_2 on 450 ids; exact agree r1-r2 84.7%, pass/fail agree 86.7%
result_5 overlaps result_2 on 147 ids; exact agree 85.0%, pass/fail 95.9%

## 3. Where the judge puts failure_step_number (result_5, web/GPT)

labelled records: 294; in-range: 294
| statistic | n | % |
|---|---|---|
| label == last step | 8 | 2.7 |
| label within last 5 steps | 123 | 41.8 |
| label in first 5 steps | 134 | 45.6 |
| label == 1 | 1 | 0.3 |
| run has a consecutive identical-action loop | 215 | 73.1 |
|   label == first loop step (2nd identical action) | 1 |  |
|   label == loop step - 1 (first of the pair) | 91 |  |
|   label before loop start-1 | 104 |  |
|   label after loop start | 19 |  |
| run has any repeated action | 254 |  |
|   label <= first repeat | 201 |  |
| run has an empty/none action | 202 |  |
|   label == first none action | 80 |  |
| run ends with stop[...] | 294 |  |
|   label == stop step | 8 |  |
| judge window (steps field) non-empty | 294 |  |
|   window = 5 steps | 274 |  |
|   window ends at last step | 15 |  |
|   window centred on label (fail at pos 3 of 5) | 269 |  |
|   window first step == label (fail at pos 1) | 1 |  |

fail position inside window: Counter({2: 269, 1: 12, None: 10, 3: 2, 0: 1})
rel position (fs/last) deciles: Counter({0: 49, 5: 36, 1: 35, 6: 33, 8: 27, 2: 26, 7: 25, 3: 24, 4: 24, 9: 15})
label step action type: [('click', 123), ('none', 88), ('type', 50), ('goto', 20), ('stop', 8), ('new_tab', 5)]
failure_type x (label==last): Counter({('Planning Error', False): 249, ('Environment', False): 17, ('False Assumption', False): 6, ('History Error Accumulation', False): 5, ('Memory Limitation', False): 5, ('Instruction', True): 4, ('Instruction', False): 4, ('Planning Error', True): 3, ('False Assumption', True): 1})
score of labelled records: Counter({'0.0': 282, '1.0': 12})

## 4. OS runs: visible error signs vs judge label

| env | judge | n | runs with >=1 error-looking OS response % | runs with repeated command % | runs with answer() % | mean agent turns | mean error responses |
|---|---|---|---|---|---|---|---|
| fail | Catastrophic Forgetting | 710 | 36 | 16 | 98 | 11.5 | 0.5 |
| fail | Environment | 26 | 27 | 50 | 73 | 20.2 | 0.4 |
| fail | False Assumption | 8 | 12 | 25 | 88 | 11.4 | 0.1 |
| fail | Instruction | 406 | 31 | 27 | 27 | 18.7 | 0.5 |
| fail | Planning Error | 487 | 34 | 14 | 53 | 15.3 | 0.5 |
| fail | Success | 227 | 10 | 9 | 86 | 10.0 | 0.1 |
| pass | Catastrophic Forgetting | 7 | 29 | 57 | 100 | 14.6 | 0.4 |
| pass | Environment | 8 | 12 | 38 | 100 | 12.2 | 0.1 |
| pass | False Assumption | 3 | 0 | 0 | 100 | 3.3 | 0.0 |
| pass | History Error Accumulation | 1 | 0 | 0 | 100 | 11.0 | 0.0 |
| pass | Instruction | 97 | 18 | 11 | 95 | 13.6 | 0.2 |
| pass | Planning Error | 58 | 29 | 2 | 97 | 10.8 | 0.4 |
| pass | Success | 697 | 15 | 8 | 99 | 9.4 | 0.2 |

Catastrophic Forgetting rate by OS level and by length bin (judge r2, failed-by-judge runs only):
| group | n judged-fail | CF % |
|---|---|---|
| len=1-5 | 47 | 25.5 |
| len=11-20 | 996 | 39.2 |
| len=6-10 | 502 | 58.4 |
| len=>20 | 266 | 8.3 |
| level=00 | 606 | 37.6 |
| level=01 | 608 | 39.3 |
| level=02 | 597 | 41.9 |
| model=claude | 874 | 8.9 |
| model=gpt | 937 | 68.2 |

Judge reason keyword rates for CF labels (os):
  forgot: 29%
  forget: 45%
  ignored: 0%
  never: 1%
  did not: 0%
  skipped: 0%
  loop: 0%
  repeat: 0%
  answer: 71%