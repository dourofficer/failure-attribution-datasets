## Web: pass vs fail cheap features (env score)

| model | n fail | n pass | steps fail/pass | has none-action % f/p | early stop % f/p | consecutive repeat % f/p | AUROC n | AUROC none | AUROC consec | AUROC maxrep |
|---|---|---|---|---|---|---|---|---|---|---|
| gpt | 104 | 45 | 36.4 / 6.2 | 61 / 58 | 93 / 24 | 100 / 89 | 0.867 | 0.551 | 0.847 | 0.870 |
| claude | 321 | 127 | 29.4 / 4.3 | 43 / 3 | 87 / 8 | 99 / 83 | 0.913 | 0.695 | 0.902 | 0.904 |
| all | 425 | 172 | 31.1 / 4.8 | 47 / 17 | 89 / 12 | 99 / 84 | 0.898 | 0.657 | 0.886 | 0.894 |

Early-stop / stop strings in failed web runs: [('stop [Early stop]', 377), ('stop ', 48)]
Fail runs by (early-stop-by-parse, loop): Counter({('other-stop', 'consec-loop'): 269, ('parse-early-stop', 'consec-loop'): 153, ('other-stop', 'no-loop'): 3})

## Shared action prefix: passing run at a lower level vs failing run at a higher level (same model, same task_id)

pairs: 223
mean LCP 2.00; LCP >= pass_n-1 (fail run reproduces the whole passing run): 204 (91%); LCP==0: 4
pairs with a judge step label on the failing run: 20; label <= LCP (judge blames a step the passing run also took): 0; label == LCP+1 (first divergent step): 2; label > LCP+1: 18
LCP distribution: [(0, 4), (1, 2), (2, 209), (3, 7), (4, 1)]

## Label-step signatures (result_5)

| signature of the labelled step | n | % |
|---|---|---|
| Action: none (parse failure) at the label | 88 | 29.9 |
| label is first of an identical-action pair (loop start) | 118 | 40.1 |
| label repeats an earlier action | 160 | 54.4 |
| label is the stop action | 8 | 2.7 |
| none of the above (needs semantics) | 20 | 6.8 |