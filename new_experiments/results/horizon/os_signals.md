## OS environment quirk: commands that should print something return "output is empty"

pwd calls: 148, of which empty: 128 (86%)
commands matching ls/cat/echo/wc/find/grep/...: 19992, empty: 11002 (55%)
runs with >=1 such swallowed output: 2497 / 2735

## Signals by env verdict x judge label (OS)

| env | judge | n | turns | same cmd >=3x % | consecutive repeat % | swallowed output % | error resp % | ends finish % | ends answer % | answer format mismatch % (of checkable) | truncated output % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| fail | Catastrophic Forgetting | 710 | 11.5 | 2 | 1 | 87 | 36 | 2 | 98 | 93 | 22 |
| fail | Environment | 26 | 20.2 | 8 | 8 | 92 | 27 | 19 | 73 | 44 | 19 |
| fail | False Assumption | 8 | 11.4 | 0 | 0 | 88 | 12 | 12 | 88 | 0 | 12 |
| fail | Instruction | 406 | 18.7 | 8 | 1 | 98 | 31 | 71 | 27 | 45 | 33 |
| fail | Planning Error | 487 | 15.3 | 4 | 1 | 95 | 34 | 46 | 53 | 69 | 24 |
| fail | Success | 227 | 10.0 | 2 | 0 | 93 | 10 | 14 | 86 | 5 | 7 |
| pass | Catastrophic Forgetting | 7 | 14.6 | 14 | 0 | 100 | 29 | 0 | 100 | 0 | 0 |
| pass | Environment | 8 | 12.2 | 12 | 0 | 100 | 12 | 0 | 100 | 0 | 12 |
| pass | False Assumption | 3 | 3.3 | 0 | 0 | 67 | 0 | 0 | 100 | 50 | 0 |
| pass | History Error Accumulation | 1 | 11.0 | 0 | 0 | 100 | 0 | 0 | 100 | 0 | 0 |
| pass | Instruction | 97 | 13.6 | 3 | 0 | 92 | 18 | 5 | 95 | 3 | 13 |
| pass | Planning Error | 58 | 10.8 | 0 | 0 | 83 | 29 | 3 | 97 | 3 | 16 |
| pass | Success | 697 | 9.4 | 1 | 1 | 89 | 15 | 1 | 99 | 6 | 5 |

## By model: env pass vs fail

| model | env | n | turns | same cmd >=3x % | consec repeat % | swallowed % | error % | ends finish % | fmt mismatch % |
|---|---|---|---|---|---|---|---|---|---|
| gpt | pass | 354 | 8.1 | 1 | 1 | 84 | 13 | 1 | 7 |
| gpt | fail | 1012 | 10.3 | 1 | 1 | 87 | 33 | 2 | 81 |
| claude | pass | 517 | 11.3 | 2 | 0 | 93 | 18 | 3 | 5 |
| claude | fail | 852 | 18.4 | 7 | 1 | 98 | 29 | 64 | 33 |

## AUROC of cheap whole-trajectory features for env FAIL (P6: do failures deviate from a normal flow?)

| model | n fail | n pass | AUROC n_turns | max repeat | consec repeat | n error resp | n empty resp | cf level | ends finish | fmt mismatch |
|---|---|---|---|---|---|---|---|---|---|---|
| gpt | 1012 | 354 | 0.708 | 0.530 | 0.499 | 0.603 | 0.576 | 0.727 | 0.506 | 0.718 |
| claude | 852 | 517 | 0.800 | 0.567 | 0.506 | 0.554 | 0.742 | 0.652 | 0.810 | 0.518 |
| all | 1864 | 871 | 0.692 | 0.545 | 0.503 | 0.576 | 0.636 | 0.683 | 0.643 | 0.627 |

## What the judge calls Catastrophic Forgetting on GPT vs Claude (env-fail runs): feature means

| model | judge label | n | turns | same cmd>=3x % | ends answer % | ends finish % | fmt mismatch % | mean cf level |
|---|---|---|---|---|---|---|---|---|
| gpt | Catastrophic Forgetting | 635 | 10.6 | 1 | 100 | 0 | 94 | 6.5 |
| gpt | Planning Error | 224 | 10.6 | 1 | 100 | 0 | 77 | 6.6 |
| gpt | Instruction | 15 | 9.5 | 0 | 87 | 13 | 92 | 4.9 |
| claude | Catastrophic Forgetting | 75 | 19.1 | 9 | 80 | 19 | 84 | 7.2 |
| claude | Planning Error | 263 | 19.4 | 6 | 12 | 86 | 6 | 6.2 |
| claude | Instruction | 391 | 19.1 | 9 | 25 | 74 | 36 | 6.5 |