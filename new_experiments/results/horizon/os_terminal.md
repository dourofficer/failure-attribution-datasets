## Terminal action: finish without answer

| model | env | n | ends with finish | task asks for an answer (strict regex) | finish & task asks answer | finish & asks & a number in the final Think |
|---|---|---|---|---|---|---|
| claude | fail | 852 | 549 | 542 | 321 | 290 |
| claude | pass | 517 | 13 | 328 | 0 | 0 |
| gpt | fail | 1012 | 17 | 652 | 2 | 2 |
| gpt | pass | 354 | 2 | 216 | 0 | 0 |

## Drift to the /etc one-shot example: precursors

gpt: n=836; drift turn index mean 8.6 of 10.7 turns; turns after drift mean 2.2; empty-output share before drift 71%; runs with >=1 repeated command before drift 14%; last 3 turns before drift all empty-output 22%
   turns-after-drift distribution: [(2, 810), (3, 3), (4, 2), (5, 1), (6, 20)]
claude: n=103; drift turn index mean 11.8 of 18.8 turns; turns after drift mean 7.0; empty-output share before drift 78%; runs with >=1 repeated command before drift 17%; last 3 turns before drift all empty-output 55%
   turns-after-drift distribution: [(2, 50), (3, 6), (4, 3), (5, 6), (6, 38)]

GPT OS: overall empty-output share 67% (all runs)