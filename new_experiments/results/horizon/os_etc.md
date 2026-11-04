System prompt excerpt around the one-shot example:
If you think you should execute some bash code, take bash action, and you should print like this: |  | Think: put your thought here. |  | Act: bash |  | ```bash | # put your bash code here | ``` |  | 2. If you think you have finished the task, take finish action, and you should print like this: |  | Think: put your thought here. |  | Act: finish |  | 3. If you think you have got the answer to the question, take answer action, and you should print like this: |  | Think: put your thought here. |  | Act: answer(Your answer to the question should be put in this pair of parentheses) |  | If the output is too long, I will truncate it. The truncated output is not complete. You have to deal with the truncating problem by yourself. Attention, your bash code should not contain any input operation. Once again, you should take only exact one of the three actions in each turn. |  | Now, my problem is: |  | tell me how many files are in the directory "/etc"?

## /etc drift in runs whose task does not mention /etc

| model | env | n | task w/o /etc | final answer mentions /etc | % | any /etc command | % |
|---|---|---|---|---|---|---|---|
| claude | fail | 852 | 819 | 59 | 7.2 | 99 | 12.1 |
| claude | pass | 517 | 493 | 0 | 0.0 | 4 | 0.8 |
| gpt | fail | 1012 | 972 | 786 | 80.9 | 828 | 85.2 |
| gpt | pass | 354 | 337 | 5 | 1.5 | 8 | 2.4 |

Judge label (r2) of drifted runs (answer mentions /etc, task does not):
[(('gpt', 'Catastrophic Forgetting'), 594), (('gpt', 'Planning Error'), 168), (('claude', 'Catastrophic Forgetting'), 44), (('claude', 'Instruction'), 5), (('claude', 'Environment'), 4), (('gpt', 'Environment'), 3), (('gpt', 'False Assumption'), 3), (('gpt', 'Success'), 1)]
r3 label of the same runs: [(('gpt', 'Catastrophic Forgetting'), 485), (('gpt', 'Planning Error'), 282), (('claude', 'Catastrophic Forgetting'), 41), (('claude', 'Environment'), 7), (('claude', 'Planning Error'), 3), (('claude', 'Instruction'), 2)]

When does the first /etc command appear (relative position in run) for drifted runs:
n=939, mean rel 0.86, share in last third 94%, share at turn 1 1%

Share of all GPT env-fail runs explained by /etc drift (answer mentions /etc while task does not): 764 / 1012
Share of GPT Catastrophic-Forgetting labels that are /etc drift: 594 / 639