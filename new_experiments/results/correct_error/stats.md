# CORRECT-Error targeted statistics (G4)

## (a) Position / agent priors

| benchmark | n | steps | label = last step % | label = last agent step % | last step is Planner % | label agent Planner % | labelled step contains FINAL ANSWER/TERMINATE % | label at user msg | agent/step mismatch % | steps after label (mean) |
|---|---|---|---|---|---|---|---|---|---|---|
| arc | 304 | 5.3 | 81.6 | 81.6 | 88.8 | 87.8 | 84.2 | 11 | 7.9 | 2.2 |
| gaia | 50 | 10.9 | 64.0 | 64.0 | 84.0 | 62.0 | 64.0 | 0 | 10.0 | 2.2 |
| hotpot | 578 | 12.8 | 41.7 | 41.7 | 58.3 | 73.2 | 48.8 | 8 | 6.7 | 6.7 |
| math500 | 157 | 6.3 | 65.0 | 65.0 | 96.8 | 60.5 | 65.6 | 3 | 30.6 | 2.0 |
| mmlu_pro | 92 | 6.1 | 71.7 | 71.7 | 87.0 | 83.7 | 71.7 | 6 | 12.0 | 3.1 |
| musique | 312 | 14.7 | 36.5 | 36.5 | 50.0 | 74.4 | 50.0 | 6 | 5.8 | 7.6 |
| wikimqa | 733 | 14.5 | 42.2 | 42.2 | 56.2 | 70.1 | 49.1 | 9 | 5.6 | 6.8 |
| ALL | 2226 | 11.8 | 50.0 | 50.0 | 65.1 | 73.6 | 56.4 | 43 | 8.4 | 5.6 |

"last step + its agent" prior: step exact 50.0%, step+agent 47.9%
steps between label and end (capped 6): 0: 50.0%, 1: 7.3%, 2: 0.1%, 3: 3.2%, 4: 0.5%, 5: 1.2%, 6: 37.6%

agent/step mismatches (step agent -> label agent): WebSurfer->Planner: 55, user->Unknown: 42, Planner->WebSurfer: 32, Planner->Orchestrator: 17, Planner->Coder: 12, CodeExecutor->Planner: 6, Planner->ComputerTerminal: 3, CodeExecutor->Coder: 3, Planner->Solver: 3, Planner->CodeExecutor: 2, Planner->MathSolver: 2, Planner->Calculator/Analysis Agent: 1
for mismatched rows, nearest step by the labelled agent at offset: {'none': 89, -1: 92, 2: 1, 1: 1, -2: 3}

questions with >1 injected variant: 599 (rows 1385); variants with identical step count: 165; identical prefix up to min label: 68
label steps across variants (first 10): [3, 0, 2]; [2, 2]; [5, 3]; [2, 2]; [3, 5]; [2, 2]; [5, 3, 5]; [0, 4]; [2, 2]; [0, 2]

## (b) Loop structure after the label (G4 addendum)

- long (>=21 steps): n=809; label last 0%; Planner->Planner adjacency right after label 56.5% (any adjacency in run 59.3%); Planner 'Updated Understanding' blocks after the label that verbatim repeat an earlier one: 144/5598 (3%); first Planner turn whose Updated-Understanding changes == label: 13.1% (within 1: 35.6%)
- mid (5-20): n=807; label last 70%; Planner->Planner adjacency right after label 10.4% (any adjacency in run 10.7%); Planner 'Updated Understanding' blocks after the label that verbatim repeat an earlier one: 0/542 (0%); first Planner turn whose Updated-Understanding changes == label: 7.1% (within 1: 20.4%)
- short (<=4): n=610; label last 90%; Planner->Planner adjacency right after label 0.2% (any adjacency in run 0.7%); Planner 'Updated Understanding' blocks after the label that verbatim repeat an earlier one: 0/63 (0%); first Planner turn whose Updated-Understanding changes == label: 27.9% (within 1: 32.6%)

- Rule 'first Planner->Planner adjacency else last step' over ALL 2226 rows: exact 74.0%, within 1 81.0% (last-step rule alone 50.0%); rows with an adjacency 570 of which first adjacency == label 94.6%, within 1 95.8%. Same-agent adjacency for any agent: exact 74.0%.

## (c) Agent/index mismatches excluding Unknown (G4 addendum): n=144; labelled agent is named inside the indexed turn 21%; previous turn is by the labelled agent 64%; next turn is by the labelled agent 43%
