
## T1. What kind of step is the gold step? (hallucinated runs, by category)
| category | n | has tool call | tool error in its response | is ask_human | is last step | is step 0 | is handoff | is final-answer step |
|---|---|---|---|---|---|---|---|---|
| Human-Interaction | 73 | 100% | 0% | 100% | 0% | 37% | 0% | 0% |
| Planning | 67 | 0% | 0% | 3% | 0% | 96% | 0% | 3% |
| Reasoning | 118 | 67% | 8% | 0% | 16% | 10% | 3% | 14% |
| Retrieval | 82 | 100% | 11% | 0% | 0% | 0% | 0% | 0% |
| Tool-Use | 103 | 91% | 35% | 0% | 3% | 9% | 0% | 0% |

## T2. Tool-error steps (regex on tool responses) relative to the gold step; clean runs as control
| class | framework | n | runs with >=1 tool-error step | tool-error steps / all steps | err before / at / after gold (hallucinated) |
|---|---|---|---|---|---|
| hallucinated | BFCL | 103 | 68% | 10.4% | 30% / 35% / 17% |
| hallucinated | Camel | 57 | 53% | 11.9% | 25% / 4% / 32% |
| hallucinated | Magentic_One | 54 | 7% | 1.8% | 4% / 2% / 4% |
| hallucinated | Octotools | 30 | 43% | 16.6% | 23% / 17% / 17% |
| hallucinated | OpenDeepSearch | 58 | 33% | 9.0% | 21% / 9% / 14% |
| hallucinated | OpenManus | 84 | 20% | 7.3% | 15% / 0% / 6% |
| hallucinated | SmolAgents | 57 | 46% | 14.2% | 16% / 9% / 26% |
| clean | BFCL | 61 | 46% | 7.8% | - |
| clean | Camel | 36 | 50% | 13.3% | - |
| clean | Magentic_One | 40 | 18% | 2.7% | - |
| clean | Octotools | 17 | 24% | 8.1% | - |
| clean | OpenDeepSearch | 42 | 7% | 1.6% | - |
| clean | OpenManus | 20 | 30% | 6.9% | - |
| clean | SmolAgents | 34 | 53% | 12.7% | - |

clean runs with >=1 tool-error step (recovered-error proxy): 84/250 = 33.6%; hallucinated: 179/443

## T3. Is the correct answer visible in the trajectory of hallucinated runs? (exact normalised GT string, GT <= 40 chars, non-BFCL)
| category | n evaluable | GT visible before gold | at gold | after gold | never |
|---|---|---|---|---|---|
| ALL | 245 | 15 (6%) | 10 (4%) | 15 (6%) | 205 (84%) |
| Human-Interaction | 55 | 3 (5%) | 4 (7%) | 2 (4%) | 46 (84%) |
| Planning | 48 | 0 (0%) | 2 (4%) | 8 (17%) | 38 (79%) |
| Reasoning | 75 | 2 (3%) | 1 (1%) | 2 (3%) | 70 (93%) |
| Retrieval | 67 | 10 (15%) | 3 (4%) | 3 (4%) | 51 (76%) |
ids GT visible before gold: Camel/029.json, Camel/037.json, Magentic_One/008.json, Magentic_One/037.json, Magentic_One/042.json, OpenDeepSearch/007.json, OpenDeepSearch/013.json, OpenDeepSearch/025.json, OpenDeepSearch/069.json, OpenManus/002.json, OpenManus/005.json, OpenManus/058.json, SmolAgents/026.json, SmolAgents/059.json, SmolAgents/068.json
ids GT visible at gold: Camel/049.json, Camel/067.json, Octotools/027.json, Octotools/043.json, OpenDeepSearch/019.json, OpenDeepSearch/091.json, OpenManus/053.json, OpenManus/056.json, OpenManus/064.json, SmolAgents/058.json
clean runs (same filter): GT visible in trajectory {'never': 42, 'visible': 101}

## T4. ask_human steps: where they occur and whether the gold step is one
| class | n | runs with ask_human | ask_human per such run | gold is ask_human step | gold is FIRST ask_human | frameworks |
|---|---|---|---|---|---|---|
| HI (hallucinated) | 73 | 73 | 1.33 | 73 | 65 | [('OpenManus', 42), ('Camel', 31)] |
| other hallucinated | 370 | 10 | 1.30 | 2 | 2 | [('OpenManus', 7), ('Camel', 3)] |
| clean | 250 | 23 | 1.35 | 0 | 0 | [('Camel', 18), ('OpenManus', 5)] |
non-HI hallucinated runs containing ask_human: ['Camel/055.json', 'Camel/072.json', 'Camel/075.json', 'OpenManus/038.json', 'OpenManus/070.json', 'OpenManus/071.json', 'OpenManus/072.json', 'OpenManus/073.json', 'OpenManus/081.json', 'OpenManus/091.json']
clean runs containing ask_human: ['Camel/035.json', 'Camel/036.json', 'Camel/040.json', 'Camel/041.json', 'Camel/042.json', 'Camel/043.json', 'Camel/047.json', 'Camel/048.json', 'Camel/061.json', 'Camel/062.json', 'Camel/064.json', 'Camel/068.json', 'Camel/069.json', 'Camel/076.json', 'Camel/080.json', 'Camel/081.json', 'Camel/082.json', 'Camel/083.json', 'OpenManus/048.json', 'OpenManus/049.json', 'OpenManus/061.json', 'OpenManus/069.json', 'OpenManus/099.json']
HI runs where a number from the human reply reappears in the final answer: 25/73

## T5. BFCL (Tool-Use): turn structure, gold step type, silent tool responses
| subcategory | n | gold is a tool-call step | gold response has error | gold response silent (None) | gold in first / last turn | user turns (task) | detected turns |
|---|---|---|---|---|---|---|---|
| Incorrect Tool Arguments | 36 | 97% | 19% | 8% | 8% / 33% | 0.0 | 4.1 |
| Missing Required Call | 32 | 75% | 56% | 12% | 22% / 22% | 0.0 | 3.6 |
| Parallel Call Conflict | 12 | 100% | 50% | 17% | 25% / 50% | 0.0 | 3.2 |
| Unnecessary Tool Call | 23 | 100% | 22% | 22% | 43% / 30% | 0.0 | 3.4 |
BFCL hallucinated: tool-error steps 106/1022 = 10.4%; runs with >=1 error 70/103
BFCL clean: tool-error steps 49/631 = 7.8%; runs with >=1 error 28/61

## T6. Step number quoted in hallucination_reason vs hallucination_step label (1-based)
reason quotes a step: 442/443; agrees with label: 439; disagrees: 3; no step quoted: 1
disagreements (id, reason step, label step, n_steps): [('BFCL/110.json', 1, 7, 8), ('Magentic_One/093.json', 3, 18, 18), ('SmolAgents/009.json', 2, 5, 5)]

## T7. gold == step 0 (112 runs): who is step 0 and what category
| framework | agent at step 0 | category | n |
|---|---|---|---|
| OpenManus | assistant | Human-Interaction | 27 |
| SmolAgents | assistant | Planning | 25 |
| Magentic_One | MagenticOneOrchestrator | Planning | 17 |
| OpenDeepSearch | assistant | Planning | 16 |
| OpenManus | assistant | Reasoning | 12 |
| BFCL | assistant | Tool-Use | 9 |
| Camel | Planner | Planning | 5 |
| Octotools | assistant | Planning | 1 |
gold==0 share by framework: {'BFCL': '9/103', 'Camel': '5/57', 'Magentic_One': '17/54', 'Octotools': '1/30', 'OpenDeepSearch': '16/58', 'OpenManus': '39/84', 'SmolAgents': '25/57'}

## T8. Multi-agent frameworks: is the gold step a WebSurfer/Search fetch step whose RESPONSE carries the wrong fact (fetch) vs an agent assertion (adopt)?
| framework | n | gold = search/browse tool-call step | gold = orchestrator/planner step | agent at gold |
|---|---|---|---|---|
| Magentic_One | 54 | 11 | 25 | {'Coder': 14, 'WebSurfer': 15, 'MagenticOneOrchestrator': 25} |
| Camel | 57 | 31 | 5 | {'Developer Agent': 19, 'Multi-Modal Processing Agent': 1, 'None': 1, 'Search Agent': 31, 'Planner': 5} |