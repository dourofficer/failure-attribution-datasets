# AEGIS targeted statistics (G4)

records 9533; with is_injected markers 2359; frameworks [('agentverse', 2449), ('llm_debate', 2404), ('macnet', 2359), ('dylan', 1567), ('smoagents', 481), ('magentic_one', 273)]

## (a) Mode x framework and the structural-agent prior

| framework | n | turns | pairs/traj | top faulty agents | top modes | strategies |
|---|---|---|---|---|---|---|
| agentverse | 2449 | 12.4 | 2.99 | Solver 31%, Evaluator 26%, RoleAssigner 24% | FM-2.1 9%, FM-3.2 9%, FM-1.1 9% | {'response_corruption': 4172, 'prompt_injection': 3154} |
| dylan | 1567 | 11.0 | 2.60 | Assistant4 14%, Assistant1 12%, Assistant3 10% | FM-2.6 9%, FM-1.5 9%, FM-3.3 9% | {'response_corruption': 2181, 'prompt_injection': 1894} |
| llm_debate | 2404 | 12.0 | 1.97 | Assistant1 35%, Assistant3 34%, Assistant2 30% | FM-1.5 11%, FM-2.3 10%, FM-1.1 9% | {'response_corruption': 2343, 'prompt_injection': 2385} |
| macnet | 2359 | 10.0 | 2.47 | Node0 44%, Node3 31%, Node1 25% | FM-1.1 11%, FM-2.2 9%, FM-2.3 9% | {'prompt_injection': 2550, 'response_corruption': 3268} |
| magentic_one | 273 | 16.3 | 1.00 | MagenticOneOrchestrator 47%, WebSurfer 27%, Coder 18% | FM-1.1 19%, FM-2.6 14%, FM-2.2 12% | {'prompt': 273} |
| smoagents | 481 | 18.3 | 1.00 | Manager 56%, Searcher 44% | FM-1.1 12%, FM-2.3 9%, FM-1.2 7% | {'prompt_injection': 481} |

constant-agent prior (most frequent faulty agent of the framework) hits a faulty agent in 72.4% of records
mean distinct speaking agents 4.37; mean faulty agents 2.32; fraction of speaking agents that are faulty 0.54

## (b) MacNet is_injected markers: every turn of an injected agent?

MacNet records 2359: every turn of the faulty agents marked in 48.7%; marked turns always by faulty agents 48.7%; marked turns per record 5.70 of 10.0 turns; first marked = first turn of the agent 72.1%
=> the marker is an agent flag, not a step label; the "error_steps" of the loader is simply the first turn of the first injected agent.

## (c) Surface cues: turns of injected agents vs clean agents in the same trajectory (all frameworks, using faulty_agents)

| framework | n | d chars (inj-clean) | d hedge (inj-clean) | d cert (inj-clean) | d selfref (inj-clean) | d digits (inj-clean) | loop_words % inj/clean | terminate % inj/clean | ignore % inj/clean | hedge_refuse % inj/clean | wrong_arith % inj/clean |
|---|---|---|---|---|---|---|---|---|---|---|---|
| agentverse | 2188 | +370 | +1.52 | -1.04 | -0.622 | +0.00572 | 4/1 | 23/27 | 8/1 | 4/3 | 11/5 |
| dylan | 1138 | -104 | +0.436 | -0.268 | +0.3 | -0.00507 | 4/3 | 7/10 | 4/3 | 2/1 | 14/17 |
| llm_debate | 2277 | +163 | +1.65 | +0.0142 | +1.36 | -0.00651 | 8/4 | 19/15 | 10/2 | 5/2 | 25/28 |
| macnet | 2359 | +175 | +1.11 | -0.137 | +0.965 | -0.00674 | 5/2 | 14/12 | 14/5 | 5/3 | 14/17 |
| magentic_one | 206 | -94 | -0.37 | -0.163 | -0.975 | +0.0145 | 3/2 | 3/2 | 3/3 | 5/3 | 1/0 |
| smoagents | 481 | -3.21e+03 | -0.113 | -0.417 | +0.058 | -0.000608 | 8/24 | 22/31 | 1/2 | 7/20 | 0/0 |

## (d) The same (agent, mode) label: how much does the malicious_action_description vary?

- FM-1.1: 2166 pairs, 10 distinct descriptions; top: "" (1404) | "Node 3 injected with response_corruption" (216)
- FM-1.2: 1746 pairs, 10 distinct descriptions; top: "" (1210) | "Node 1 injected with prompt_injection" (130)
- FM-1.3: 1424 pairs, 10 distinct descriptions; top: "" (976) | "Node 0 injected with response_corruption" (109)
- FM-1.4: 1596 pairs, 11 distinct descriptions; top: "" (1091) | "Node 0 injected with prompt_injection" (121)
- FM-1.5: 1964 pairs, 12 distinct descriptions; top: "" (1355) | "Node 3 injected with response_corruption" (162)
- FM-2.1: 1668 pairs, 10 distinct descriptions; top: "" (1257) | "Node 0 injected with prompt_injection" (121)
- FM-2.2: 1656 pairs, 10 distinct descriptions; top: "" (1050) | "Node 3 injected with response_corruption" (164)
- FM-2.3: 1762 pairs, 10 distinct descriptions; top: "" (1148) | "Node 0 injected with prompt_injection" (192)
- FM-2.4: 1449 pairs, 10 distinct descriptions; top: "" (1018) | "Node 0 injected with prompt_injection" (144)
- FM-2.5: 1422 pairs, 9 distinct descriptions; top: "" (1000) | "Node 3 injected with response_corruption" (100)
- FM-2.6: 1369 pairs, 9 distinct descriptions; top: "" (905) | "Node 0 injected with response_corruption" (154)
- FM-3.1: 1356 pairs, 11 distinct descriptions; top: "" (835) | "Node 0 injected with response_corruption" (166)
- FM-3.2: 1677 pairs, 11 distinct descriptions; top: "" (1175) | "Node 0 injected with prompt_injection" (92)
- FM-3.3: 1446 pairs, 9 distinct descriptions; top: "" (1040) | "Node 0 injected with prompt_injection" (97)

## (e) Self-announcing cues in turns of faulty vs clean agents (regex: incorrectly / miscalculate / again for emphasis / disregard / prematurely / Incorrect Answer ...)

| framework | n | % faulty-agent turns with cue | % clean-agent turns with cue | records where some agent has a cue | cue-argmax agent is faulty % | constant-agent prior % |
|---|---|---|---|---|---|---|
| agentverse | 2449 | 38.6 | 44.8 | 2118 (86%) | 77.2 | 93.1 |
| dylan | 1567 | 41.1 | 29.6 | 1271 (81%) | 58.5 | 35.4 |
| llm_debate | 2404 | 27.4 | 7.0 | 1455 (61%) | 91.1 | 69.5 |
| macnet | 2359 | 48.4 | 29.9 | 2349 (100%) | 66.5 | 84.8 |
| magentic_one | 273 | 14.2 | 21.7 | 123 (45%) | 32.5 | 47.3 |
| smoagents | 481 | 1.2 | 1.6 | 75 (16%) | 42.7 | 55.7 |
| ALL | 9533 | 36.5 | 25.6 | 7391 (78%) | 72.3 | 72.4 |

per mode (faulty agent turns with a cue):
FM-1.1 38%, FM-1.2 35%, FM-1.3 56%, FM-1.4 32%, FM-1.5 34%, FM-2.1 35%, FM-2.2 43%, FM-2.3 34%, FM-2.4 30%, FM-2.5 36%, FM-2.6 33%, FM-3.1 35%, FM-3.2 34%, FM-3.3 36%
