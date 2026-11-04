# Who&When Pro targeted statistics (G4)

## (a) Position priors: where is the injected step?

| framework | n | label = last agent step % | label = last step of its agent % | agent steps after label (mean) | no continuation % | >=3 continuation steps % |
|---|---|---|---|---|---|---|
| alfagent | 311 | 0.0 | 0.0 | 21.03 | 0.0 | 99.4 |
| debate | 445 | 32.4 | 45.8 | 2.11 | 32.4 | 54.2 |
| dylan | 152 | 0.0 | 14.5 | 6.09 | 0.0 | 100.0 |
| macnet | 261 | 0.0 | 58.2 | 2.58 | 0.0 | 58.2 |
| magentic-one | 811 | 56.0 | 69.5 | 1.92 | 56.0 | 26.9 |
| mathchat | 920 | 78.8 | 78.8 | 0.31 | 78.8 | 1.1 |
| metagpt | 81 | 0.0 | 100.0 | 1.83 | 0.0 | 0.0 |
| smolagents | 3276 | 52.1 | 52.1 | 1.11 | 52.1 | 13.6 |
| ALL | 6257 | 48.4 | 55.2 | 2.35 | 48.4 | 24.4 |

## (b) Construction check: does the final output actually disagree with the ground truth?

| framework | n | final == GT (lenient) | mismatch | no GT / no output | % match among comparable |
|---|---|---|---|---|---|
| alfagent | 311 | 0 | 0 | 311 | 0.0 |
| debate | 445 | 4 | 441 | 0 | 0.9 |
| dylan | 152 | 5 | 147 | 0 | 3.3 |
| macnet | 261 | 0 | 188 | 73 | 0.0 |
| magentic-one | 811 | 28 | 782 | 1 | 3.5 |
| mathchat | 920 | 9 | 911 | 0 | 1.0 |
| metagpt | 81 | 0 | 25 | 56 | 0.0 |
| smolagents | 3276 | 5 | 3262 | 9 | 0.2 |
| ALL | 6257 | 51 | 5756 | 450 | 0.9 |

examples of lenient matches (id, final, gt):
- debate: ('math_debate_0106', '998', '1997/2')
- debate: ('scibench_debate_0080', '556.5', '556')
- debate: ('scibench_debate_0099', '588313.25', '588313')
- debate: ('scibench_debate_0100', '1591', '1590')
- dylan: ('scibench_dylan_0022', '102964.41', '102965.21')
- dylan: ('scibench_dylan_0044', '102964.42', '102965.21')
- dylan: ('scibench_dylan_0051', '102964', '102965.21')
- dylan: ('scibench_dylan_0055', '-273.2', '-273')
- magentic-one: ('gaia_magentic-one_0010', '564.1', '563.9')
- magentic-one: ('gaia_magentic-one_0050', '563.7', '563.9')
- magentic-one: ('gaia_magentic-one_0253', '564.1', '563.9')
- magentic-one: ('simpleqa_verified_magentic-one_0032', 'niloufar bayani', 'niloufar bayan')
- mathchat: ('math_mathchat_0026', '0.3263888888888889', '47/144')
- mathchat: ('math_mathchat_0030', '0.9074074074', '49/54')
- mathchat: ('math_mathchat_0121', '0.9074074074074074', '49/54')
- mathchat: ('math_mathchat_0140', 'p - q - 1', 'p - q')
- smolagents: ('databench_smolagents_0198', 'execution logs:\nlast output from code snippet:\ntropical frui', 'fruits')
- smolagents: ('databench_smolagents_0211', 'execution logs:\nlast output from code snippet:\nemail phone p', 'photographer')
- smolagents: ('databench_smolagents_0394', 'execution logs:\nlast output from code snippet:\ntropical frui', 'fruits')
- smolagents: ('dsqa_smolagents_0435', 'execution logs:\nlast output from code snippet:\nboth national', 'applications of mathematics')

## (c) Style: injected turn vs the same agent's other turns in the same trajectory

| framework | n (agent has >=2 other turns) | z chars | z words | z hedge | z cert | z selfref | z digits | z newlines | injected is longest % | shortest % | argmax |z| (len,hedge,digits) % | chance % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alfagent | 311 | +1.64 | +1.50 | +0.21 | +0.14 | -0.00 | -0.81 | -1.51 | 14 | 0 | 13 | 3 |
| dylan | 112 | -1.49 | -1.34 | +0.16 | -2.09 | -1.35 | +0.28 | -1.57 | 16 | 57 | 83 | 33 |
| magentic-one | 376 | +1.77 | +1.75 | +0.23 | +1.08 | +0.08 | -0.05 | +1.45 | 53 | 6 | 62 | 25 |
| mathchat | 95 | -2.16 | -2.35 | +0.14 | +0.16 | -0.23 | -2.67 | -1.44 | 8 | 65 | 92 | 27 |
| smolagents | 2599 | -0.93 | -1.05 | +0.16 | +0.01 | +0.05 | -0.58 | -0.92 | 8 | 36 | 50 | 23 |
| ALL | 3493 | -0.46 | -0.57 | +0.17 | +0.07 | -0.01 | -0.57 | -0.75 |  |  |  |  |

## (d) Continuation symptoms per agent step: after the labelled step, WWP (injected) vs Who&When (natural)

| set | marker | records | steps before | % before | labelled steps | % at label | steps after | % after |
|---|---|---|---|---|---|---|---|---|
| WWP smolagents | tool_error | 3276 | 8013 | 1.0 | 3276 | 3.3 | 3649 | 11.6 |
| WWP smolagents | self_correct | 3276 | 8013 | 1.5 | 3276 | 0.9 | 3649 | 4.9 |
| WWP smolagents | uncertainty | 3276 | 8013 | 1.9 | 3276 | 1.9 | 3649 | 10.4 |
| WWP smolagents | loop_marker | 3276 | 8013 | 1.5 | 3276 | 0.6 | 3649 | 3.5 |
| WWP smolagents | repeat | 3276 | 8013 | 0.0 | 3276 | 0.0 | 3649 | 0.0 |
| WWP magentic-one | tool_error | 811 | 2577 | 1.9 | 811 | 1.0 | 1559 | 1.3 |
| WWP magentic-one | self_correct | 811 | 2577 | 1.4 | 811 | 0.7 | 1559 | 0.8 |
| WWP magentic-one | uncertainty | 811 | 2577 | 1.2 | 811 | 0.6 | 1559 | 0.9 |
| WWP magentic-one | loop_marker | 811 | 2577 | 2.2 | 811 | 1.4 | 1559 | 2.1 |
| WWP magentic-one | repeat | 811 | 2577 | 0.6 | 811 | 0.0 | 1559 | 1.2 |
| WWP mathchat | tool_error | 920 | 1840 | 1.5 | 920 | 0.2 | 568 | 1.8 |
| WWP mathchat | self_correct | 920 | 1840 | 2.1 | 920 | 2.5 | 568 | 9.5 |
| WWP mathchat | uncertainty | 920 | 1840 | 0.0 | 920 | 0.1 | 568 | 0.5 |
| WWP mathchat | loop_marker | 920 | 1840 | 0.8 | 920 | 0.7 | 568 | 3.3 |
| WWP mathchat | repeat | 920 | 1840 | 9.7 | 920 | 0.0 | 568 | 7.9 |
| WWP alfagent | tool_error | 311 | 2479 | 0.0 | 311 | 0.0 | 6540 | 0.0 |
| WWP alfagent | self_correct | 311 | 2479 | 0.5 | 311 | 0.6 | 6540 | 0.0 |
| WWP alfagent | uncertainty | 311 | 2479 | 2.7 | 311 | 0.0 | 6540 | 0.0 |
| WWP alfagent | loop_marker | 311 | 2479 | 3.9 | 311 | 17.7 | 6540 | 0.0 |
| WWP alfagent | repeat | 311 | 2479 | 0.0 | 311 | 0.0 | 6540 | 26.0 |
| WWP all | tool_error | 6257 | 16593 | 1.2 | 6257 | 2.8 | 15290 | 4.7 |
| WWP all | self_correct | 6257 | 16593 | 2.7 | 6257 | 3.5 | 15290 | 7.4 |
| WWP all | uncertainty | 6257 | 16593 | 1.6 | 6257 | 1.3 | 15290 | 3.1 |
| WWP all | loop_marker | 6257 | 16593 | 2.4 | 6257 | 3.0 | 15290 | 2.5 |
| WWP all | repeat | 6257 | 16593 | 1.2 | 6257 | 0.0 | 15290 | 13.3 |
| WW hand-crafted | tool_error | 58 | 821 | 0.5 | 58 | 12.1 | 2056 | 1.3 |
| WW hand-crafted | self_correct | 58 | 821 | 10.1 | 58 | 22.4 | 2056 | 7.0 |
| WW hand-crafted | uncertainty | 58 | 821 | 1.7 | 58 | 3.4 | 2056 | 3.2 |
| WW hand-crafted | loop_marker | 58 | 821 | 15.8 | 58 | 3.4 | 2056 | 13.9 |
| WW hand-crafted | repeat | 58 | 821 | 13.5 | 58 | 0.0 | 2056 | 22.9 |
| WW alg-generated | tool_error | 126 | 378 | 10.3 | 126 | 6.3 | 595 | 11.3 |
| WW alg-generated | self_correct | 126 | 378 | 6.3 | 126 | 6.3 | 595 | 3.9 |
| WW alg-generated | uncertainty | 126 | 378 | 4.2 | 126 | 7.1 | 595 | 4.9 |
| WW alg-generated | loop_marker | 126 | 378 | 4.0 | 126 | 5.6 | 595 | 4.9 |
| WW alg-generated | repeat | 126 | 378 | 3.2 | 126 | 0.0 | 595 | 3.9 |
| WW all | tool_error | 184 | 1199 | 3.6 | 184 | 8.2 | 2651 | 3.5 |
| WW all | self_correct | 184 | 1199 | 8.9 | 184 | 11.4 | 2651 | 6.3 |
| WW all | uncertainty | 184 | 1199 | 2.5 | 184 | 6.0 | 2651 | 3.6 |
| WW all | loop_marker | 184 | 1199 | 12.1 | 184 | 4.9 | 2651 | 11.9 |
| WW all | repeat | 184 | 1199 | 10.3 | 184 | 0.0 | 2651 | 18.6 |

## (e) Mode distribution per framework and the constant-agent prior

| framework | n | top modes | top labelled agents |
|---|---|---|---|
| alfagent | 311 | R.4 19%, V.2 19%, R.2 19%, A.4 17% | None 100% |
| debate | 445 | C.3 46%, R.1 17%, R.4 14%, R.2 14% | agent_2 29%, agent_1 16%, agent_0 10% |
| dylan | 152 | R.2 32%, R.1 28%, R.4 19%, R.3 17% | agent_3 28%, agent_2 26%, agent_1 24% |
| macnet | 261 | C.3 42%, R.4 26%, A.1 9%, R.2 9% | node_0 58%, node_1 42% |
| magentic-one | 811 | R.1 31%, V.2 30%, R.4 12%, R.2 9% | orchestrator 78%, websurfer 11%, coder 9% |
| mathchat | 920 | R.2 32%, R.3 31%, R.4 29%, R.1 9% | assistant 100% |
| metagpt | 81 | R.4 32%, R.2 30%, PL.1 21%, A.1 10% | architect 83%, engineer 17% |
| smolagents | 3276 | A.3 35%, R.4 16%, R.2 16%, R.3 11% | None 100% |

## (f) Scheduling seam check (G4 addendum): is the injected turn followed by a turn of the SAME agent more often than other turns are?

- magentic-one: injected turn followed by same agent 0.0% (of 357 with a next turn) vs base rate 0.0% over other pairs
- mathchat: injected turn followed by same agent 100.0% (of 195 with a next turn) vs base rate 100.0% over other pairs
- debate: injected turn followed by same agent 0.0% (of 445 with a next turn) vs base rate 0.0% over other pairs
- dylan: injected turn followed by same agent 0.0% (of 152 with a next turn) vs base rate 0.5% over other pairs
- macnet: injected turn followed by same agent 41.8% (of 261 with a next turn) vs base rate 29.1% over other pairs
- metagpt: injected turn followed by same agent 0.0% (of 81 with a next turn) vs base rate 0.0% over other pairs

## (g) Style argmax restricted to rows where the injected step is NOT the last turn of its agent (G4 addendum)

- smolagents: n=1569 (injected not last turn of agent): argmax|z| picks injected 28% vs chance 19%
- magentic-one: n=219 (injected not last turn of agent): argmax|z| picks injected 50% vs chance 23%
- mathchat: n=52 (injected not last turn of agent): argmax|z| picks injected 85% vs chance 31%
- dylan: n=112 (injected not last turn of agent): argmax|z| picks injected 83% vs chance 33%
- alfagent: n=311 (injected not last turn of agent): argmax|z| picks injected 13% vs chance 3%

## (h) Magentic-One injection_via (G4 addendum)

- client_patch: n=128; injected step is final answer 0%; has tool Action 56%; [('agent_websurfer', 59), ('agent_coder', 41), ('mode_R.1', 38), ('mode_R.2', 23), ('mode_V.2', 18), ('mode_C.3', 18)]
- direct_chat_completion: n=619; injected step is final answer 58%; has tool Action 0%; [('agent_orchestrator', 100), ('mode_V.2', 35), ('mode_R.1', 31), ('mode_R.4', 14), ('mode_A.3', 10), ('mode_R.2', 4)]
