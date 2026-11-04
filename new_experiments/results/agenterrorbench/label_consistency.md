# Label-text consistency

records with reason text: 157; records whose reason contains >=2 content words absent from the whole trajectory and >=25% of its content words absent: 102

| id | env | missing words | reason (head) |
|---|---|---|---|
| alfworld/Qwen3-8B_003_id_3___chat_b001_t00_e01-5b8f974f | alfworld | although, began, eventually, inefficient, kind, obviously, prioritizing, risk | After finding the desk lamp on sidetable 1, instead of prioritizing the inspection of other side tables (2-5), I began t |
| alfworld/Qwen3-8B_006_id_6___chat_b004_t00_e03-d2034edc | alfworld | concentrating, consecutive, high-cost, higher, ignoring, leads, linear, much | Concentrating the search too much on consecutive cabinet openings and ignoring higher prior countertops leads to high-co |
| alfworld/Qwen3-8B_008_id_8___chat_b005_t00_e00-d3248f80 | alfworld | abandoned, bread, concluded, fridge, lettuce, misunderstanding, reasonable, resulting | After opening fridge 1, the Agent saw bread and concluded that there was no lettuce, misunderstanding the observation re |
| alfworld/Qwen3-8B_010_id_10___chat_b005_t00_e04-7e3c13ba | alfworld | cabinet-only, committed, despite, exhaustive, higher-probability, low-cost | At step 13, the plan explicitly committed to an exhaustive cabinet-only search (cabinets 8→23) despite multiple prior em |
| alfworld/Qwen3-8B_012_id_12___chat_b006_t00_e02-1e119842 | alfworld | enters, judged, meaningless, point, regarded, repetitive | When the task is fulfilled in Step 7 (cooling the mug and placing it in the sidetable), it should be judged as completed |
| alfworld/Qwen3-8B_014_id_14___chat_b007_t00_e02-1e119842 | alfworld | follow-up, idling, known, repeated, triggering, updated | Start invalid follow-up visits to sinkbasin; The search strategy was not updated based on known observations, triggering |
| alfworld/Qwen3-8B_015_id_15___chat_b008_t00_e00-d3248f80 | alfworld | although, closed-loop, perform | Although Step 30 found butterknife, it did not perform the complete closed-loop action of take → clean → put, and the ta |
| alfworld/Qwen3-8B_016_id_16___chat_b008_t00_e03-d2034edc | alfworld | abandonment, ignored, interpreted, judged, resulting, wrongly | After the Agent only saw tomato in the refrigerator, it wrongly interpreted it as there were no eggs in the refrigerator |
| alfworld/Qwen3-8B_017_id_17___chat_b009_t00_e01-5b8f974f | alfworld | basically, interpreted, judged, objective, obtained, sub-objective, triggered | The ladle 1 obtained from cabinet 2 is directly interpreted as having been cleaned. Based on this, it is judged that the |
| alfworld/Qwen3-8B_018_id_18___chat_b009_t00_e03-d2034edc | alfworld | assumed, located', stubbornly | Stubbornly assumed 'desk is where the desklamp is likely located' |
| alfworld/Qwen3-8B_019_id_19___chat_b012_t00_e00-d3248f80 | alfworld | completion, constraint, ignoring, misdirected, preventing | The agent incorrectly assumed that a pot could substitute for the required kettle, ignoring the explicit task constraint |
| alfworld/Qwen3-8B_021_id_21___chat_b012_t00_e02-1e119842 | alfworld | continuously, eventually, extremely, failed, fell, giving, inefficient, mechanical | Starting from step 5, the Agent fell into a mechanical strategy of opening each cabinet one by one for search, without g |
| alfworld/Qwen3-8B_022_id_22___chat_b012_t00_e04-7e3c13ba | alfworld | assumed, located', stubbornly | Stubbornly assumed 'desk 1 is where the desklamp is likely located' |
| alfworld/Qwen3-8B_023_id_23___chat_b013_t00_e00-d3248f80 | alfworld | brute-force, cabinet-by-cabinet, confirming, defaulted, environmental, failing, food-related, ignored | After confirming in Step 3 that the fridge contained no tomato, the agent defaulted to brute-force cabinet-by-cabinet se |
| alfworld/Qwen3-8B_025_id_25___chat_b013_t00_e03-d2034edc | alfworld | back-and-forth, constant, neglects, obtained, performed, resulting, target, truly | soapbar 1 was observed in step 25, but in step 26, the necessary 'take soapbar 1' action was not performed and the sinkb |
| alfworld/Qwen3-8B_026_id_26___chat_b014_t00_e04-7e3c13ba | alfworld | enumerates, high-probability, large, maximizing | The initial search strategy exhaustively enumerates from a large number of cabinets without maximizing the priority of t |
| alfworld/GPT-4o_001_alfworld_task_001 | alfworld | caused, dropping, future, later, oversimplified, revisit | At step 16, the model oversimplified its memory by dropping all the locations it had already explored, which later cause |
| alfworld/GPT-4o_002_alfworld_task_002 | alfworld | chose, failed, oversimplified, previously, remember, repeated, searches, visited | At step 24, the model oversimplified its memory. It was already at and had examined countertop 4, but failed to remember |
| alfworld/GPT-4o_003_alfworld_task_003 | alfworld | caused, confusion, issued, prevented, proceeding, returned, system | In the previous step, the agent had already found the plate and brought it to the sink. It then issued the correct admis |
| alfworld/GPT-4o_005_alfworld_task_005 | alfworld | causing, conducted, decided, series | It only notes that we went to sidetable 1 and found a desklamp, without indicating that (1) there is no box and (2) we a |
| alfworld/GPT-4o_006_alfworld_task_006 | alfworld | emphasized, insists, repeatedly | In Step 4, the system has repeatedly emphasized that nothing happened, but in Step 5, the agent still insists on going t |
| alfworld/GPT-4o_007_alfworld_task_007 | alfworld | aciton, action'go, actually, fridge', happens' | The model misinterpreted the aciton result because the feedback of module observation was 'nothing happens',but actually |
| alfworld/GPT-4o_009_alfworld_task_009 | alfworld | affordances, agent's, available, entered, fundamentally, generated, heat', impossible | At step 10, the planning module generated a plan to 'heat the tomato using the microwave.' However, the admissible actio |
| alfworld/GPT-4o_010_alfworld_task_010 | alfworld | assumed, cleaning, fundamental, ignoring, misjudged, ultimately | After taking the cup, the agent misjudged its progress by ignoring the required step of cleaning it. Instead, it assumed |
| alfworld/GPT-4o_012_alfworld_task_012 | alfworld | continuing, goes, ignores, therefore | This memory ignores all the other places that have already been explored and why they were explored. Therefore, the agen |
| alfworld/GPT-4o_013_alfworld_task_013 | alfworld | acceptable, assuming, explicitly, hallucinated, required | The task explicitly required a spraybottle, but the reflection hallucinated by assuming a soapbottle was also acceptable |
| alfworld/GPT-4o_015_alfworld_task_015 | alfworld | agent's, entire, fundamentally, impossible, interactable, listed, never, outset | The environment never presented a pillow as an observable or interactable object in any observation, nor did it provide  |
| alfworld/GPT-4o_018_alfworld_task_018 | alfworld | agent's, already-visited, containers, diverged, earliest, impossible, leading, loop | At step 4, the agent's plan was to 'explore other drawers or furniture where the keychain might be located,' which would |
| alfworld/GPT-4o_019_alfworld_task_019 | alfworld | clearly, misalignment, stated | The plan clearly stated to determine if it was clean, but the action was to take it directly. This misalignment led to f |
| alfworld/GPT-4o_020_alfworld_task_020 | alfworld | fridge1', happens', manifested | The agent took action 'go to fridge1' and observation manifested 'nothing happens',then the agent misinterpreted the act |
| alfworld/GPT-4o_021_alfworld_task_021 | alfworld | finished, gone, limit, nearly | The agent nearly finished the task—it had already found the newspaper and gone to the sofa, but the step limit ran out. |
| alfworld/GPT-4o_022_alfworld_task_022 | alfworld | chose, porcess, recheck, reexamine, repeatedly, serach, subsequent, thought | The agent thought the initial serach might miss the lettuce,so chose to reexamine the fridge,and in the subsequent porce |
| alfworld/GPT-4o_023_alfworld_task_023 | alfworld | forgotten, went | In the memory of step 8, agent has already forgotten that in step 7, it went to cabinet 1. |
| alfworld/GPT-4o_024_alfworld_task_024 | alfworld | ignoring, misjudged | The agent misjudged its progress by ignoring the need to cool the pot before placing it on the countertop. |
| alfworld/GPT-4o_026_alfworld_task_026 | alfworld | happens', thought, tried | The agent tried to go to fridge 1 but it thought the action was not executed on the observation module 'nothing happens' |
| alfworld/GPT-4o_027_alfworld_task_027 | alfworld | actual, adapt, agent's, began, cascade, caused, dooming, ignore | At step 3 the memory module began to oversimplify the agent's exploration history by summarizing the result of moving to |
| alfworld/GPT-4o_028_alfworld_task_028 | alfworld | actually, agent's, alone, both, cabinet', continued, doomed, endlessly | At step 4 the agent planned to 'explore another location that might contain a dishsponge such as a cabinet' and executed |
| alfworld/GPT-4o_030_alfworld_task_030 | alfworld | checking, ignores, mentions, section | While the reflection mentions that the goal is to put the clean butterknife on the dining table, the plan section ignore |
| alfworld/GPT-4o_031_alfworld_task_031 | alfworld | affordances, became, both, cascade, environment's, ever, fundamental, futile | At step 10 the agent planned to 'clean soapbar 1 with sinkbasin 1' while holding the soapbar but the environment require |
| alfworld/GPT-4o_033_alfworld_task_033 | alfworld | hallucinated, returning, stating, though | The agent had already looked in the fridge, which contained only a tomato and no egg. However, it hallucinated by statin |
| alfworld/GPT-4o_034_alfworld_task_034 | alfworld | agent's, became, cascade, continued, depositing, despite, earlier, fixated | At step 14 the planning module generated a plan to 'move to garbagecan 1 to be ready to deposit a soapbottle' despite th |
| alfworld/GPT-4o_035_alfworld_task_035 | alfworld | ignoring, misjudged, stating | The model misjudged its progress by ignoring the need to clean the ladle and directly stating that the next step was to  |
| alfworld/GPT-4o_036_alfworld_task_036 | alfworld | adapted, checking, clear, considering, dooming, entered, evidence, fundamentally | At step 10 the agent planned to 'go to microwave 1' and then 'open microwave 1' but after arriving at the microwave repe |
| alfworld/GPT-4o_037_alfworld_task_037 | alfworld | accurately, assumption, causing, ever, false, forced, futile, hallucinated | At step 2 the memory module hallucinated the presence of a desklamp at desk 1 stating: 'the desklamp is likely located a |
| alfworld/GPT-4o_038_alfworld_task_038 | alfworld | agent's, alfworld, assuming, cascade, chasing, consumed, described, diverted | At step 22 the agent planned to 'take the box from the armchair to see if it contains the laptop or leads to further dis |
| alfworld/GPT-4o_039_alfworld_task_039 | alfworld | agent's, alert, began, causing, critical, described, dooming, fact | At step 4 the memory module began oversimplifying the agent's recent experience by failing to accurately recall and summ |
| alfworld/GPT-4o_040_alfworld_task_040 | alfworld | attempting, dooming, entered, environment's, feasible, generated, include, ineffective | At step 7, the planning module generated a plan to 'examine or search the contents of drawer 1,' but the admissible acti |
| alfworld/GPT-4o_041_alfworld_task_041 | alfworld | access, actually, agent's, cascade, contained, critically, detailed, entered | At step 4, the memory module critically oversimplified the agent's experience by failing to retain and utilize the detai |
| alfworld/GPT-4o_043_alfworld_task_043 | alfworld | acceptable, clearly, concluded, misjudged | The task clearly states that we should use a kettle, but the LLM reflection misjudged the progress by suggesting that a  |
| alfworld/GPT-4o_047_alfworld_task_047 | alfworld | causing, following, ignoring, misled, oversimplified | The memory was oversimplified, ignoring that no desklamp or alarmclock was found. This misled the following actions, cau |
| alfworld/GPT-4o_048_alfworld_task_048 | alfworld | assumed, ignoring, misjudged | The reflection misjudged the progress by ignoring that we haven't checked if the ladle is clean, and assumed the next st |
| alfworld/GPT-4o_049_alfworld_task_049 | alfworld | clearly, kept, memories, switching, throughout, trajectory, whole | The memories in this whole trajectory clearly failed to indicate that desk 1 / desk 2 had already been explored and that |
| alfworld/GPT-4o_052_alfworld_task_052 | alfworld | sends, wasting | already confirming at steps 3-4 that fridge 1 contains no tomato, the plan again sends the agent back there, wasting mov |
| alfworld/GPT-4o_053_alfworld_task_053 | alfworld | completely, misunderstood | agent completely misunderstood the outcome |
| alfworld/GPT-4o_054_alfworld_task_054 | alfworld | confirming, sends, wasting | already confirming at shelf 2 contains no credit card now, the plan again sends the agent back there, wasting moves. |
| alfworld/GPT-4o_056_alfworld_task_056 | alfworld | cannot, despite, having, intended, reached | Plan expects to examine the bowl with the desklamp despite not having located or reached any desklamp, so the intended a |
| gaia/GPT-4o_001_memory_b000_t00_e00-7743eba0 | gaia | inefficient, redo | Inefficient plan by redo similar stuffs |
| gaia/GPT-4o_003_memory_b000_t00_e03-21a3a421 | gaia | inefficient, redo, similar, stuffs | Inefficient plan by redo similar stuffs |
| gaia/GPT-4o_004_memory_b000_t00_e04-5e8c1dcf | gaia | constraint_ignorance, required | constraint_ignorance by not including all required elements |
| gaia/GPT-4o_005_memory_b000_t00_e05-c9015705 | gaia | inefficient, starting | Inefficient plan by starting with a bad query |
| gaia/GPT-4o_006_memory_b000_t00_e06-71f77595 | gaia | actually, details, enumerate, extraction, store, summarized | At step 3, the memory module summarized the outcome of the world box office URL extraction as 'The top 10 highest-grossi |
| gaia/GPT-4o_007_memory_b000_t00_e08-f572f2ad | gaia | grossly, oversimplified, providing, summarizing | At step 2, the memory module grossly oversimplified the search results by summarizing them as providing no significant p |
| gaia/GPT-4o_009_memory_b001_t00_e01-7ab08a46 | gaia | inefficient, redo, stuffs | Inefficient plan by redo similar stuffs |
| gaia/GPT-4o_014_memory_b001_t00_e06-71f77595 | gaia | inefficient, redo, stuffs | Inefficient plan by redo similar stuffs |
| gaia/GPT-4o_016_memory_b001_t00_e08-f572f2ad | gaia | inefficient, won't | Inefficient plan that won't help |
| gaia/Llama3.3-70B-Turbo_001_memory_b000_t00_e00-7743eba0 | gaia | efficient, repeat | Make an low efficient plan that not success, repeat the similar action that not success |
| gaia/Llama3.3-70B-Turbo_002_memory_b000_t00_e01-7ab08a46 | gaia | efficient, make | Make an low efficient plan that not success, to do a not so relevant task |
| gaia/Llama3.3-70B-Turbo_003_memory_b000_t00_e02-8d639e26 | gaia | agent's, astley's, discover, dqw4w9wgxcq', however, on-screen, unrelated | At step 2, the agent's plan was to find and access the first episode of Game Grumps' Sonic the Hedgehog (2006) Let's Pla |
| gaia/Llama3.3-70B-Turbo_004_memory_b000_t00_e03-21a3a421 | gaia | constraint, enough | Not enough reasoning based on the constraint |
| gaia/Llama3.3-70B-Turbo_006_memory_b000_t00_e05-c9015705 | gaia | claiming, progress_misjudge | progress_misjudge by claiming that the agent has completed the task goal |
| gaia/Llama3.3-70B-Turbo_011_memory_b001_t00_e02-8d639e26 | gaia | inefficient, redo | Inefficient plan by redo similar stuffs |
| gaia/Llama3.3-70B-Turbo_013_memory_b001_t00_e04-5e8c1dcf | gaia | claiming, completed, progress_misjudge | Progress_misjudge by claiming that the agent has completed the task goal |
| gaia/Llama3.3-70B-Turbo_016_memory_b001_t00_e07-f5b5d66a | gaia | inefficient, redo, stuffs | Inefficient plan by redo similar stuffs |
| gaia/Llama3.3-70B-Turbo_017_memory_b001_t00_e08-f572f2ad | gaia | inefficient, redo, stuffs | Inefficient plan by redo similar stuffs |
| gaia/Qwen3-8B_001_memory_b000_t00_e00-7743eba0 | gaia | acquire, built, choice, critical, ensured, eventual, fulfill, generic | URL extractor can not extract video content, description, or transcript from a YouTube page, and only returns generic si |
| gaia/Qwen3-8B_002_memory_b000_t00_e01-7ab08a46 | gaia | exhausted, finding, plausible, strategies | The agent had not yet exhausted all plausible strategies for finding the Tropicos ID |
| gaia/Qwen3-8B_004_memory_b000_t00_e04-5e8c1dcf | gaia | constraint, fully, satisfy | Not fully satisfy the constraint |
| gaia/Qwen3-8B_005_memory_b000_t00_e05-c9015705 | gaia | constraint, fully, satisfy | Not fully satisfy the constraint |
| gaia/Qwen3-8B_010_memory_b001_t00_e00-7743eba0 | gaia | constraint, match | Provide new information that not match the constraint |
| webshop/GPT-4o_001_chat_b000_t00_e00-d3248f80 | webshop | almost, beginning, direction, identical, inefficient, loops, very | This plan loops back to the very beginning, moving in the wrong direction, and results in an inefficient search query th |
| webshop/GPT-4o_003_chat_b000_t00_e02-1e119842 | webshop | produce, unlikely, woman | The terms ‘man’ and ‘woman’ are conflicting in this context, making the search unlikely to produce relevant results. |
| webshop/GPT-4o_005_chat_b000_t00_e04-7e3c13ba | webshop | caused, essentially, produced, rather | The plan produced a query that was essentially the same as the initial one. This caused repeated results rather than new |
| webshop/GPT-4o_006_chat_b000_t00_e05-996588dc | webshop | caused, essentially, produced, rather, repeated | The plan produced a query that was essentially the same as the initial one. This caused repeated results rather than new |
| webshop/GPT-4o_007_chat_b000_t00_e06-a15c0dc2 | webshop | parameters, prevented, refining, repeated, suggested | The agent had already found a suitable option, but instead of selecting it, the reflection suggested exploring more opti |
| webshop/GPT-4o_008_chat_b000_t00_e07-d50ae81f | webshop | almost, caused, identical, meaningful, produced, rather, repeated | Instead of refining the query in a meaningful way, the plan produced a search that was almost identical to the initial o |
| webshop/GPT-4o_009_chat_b000_t00_e08-6a7bac22 | webshop | essentially, meaningful, resulting | The plan made no meaningful adjustments, resulting in a query that was essentially the same as the initial one. |
| webshop/GPT-4o_010_chat_b000_t00_e09-f0557a9f | webshop | checking, concluded, example, simply, very, worth | There are products that look very relevant and worth further checking — for example, B09KLQLLT2 - Long Sleeve Superhero  |
| webshop/GPT-4o_011_chat_b000_t00_e10-69d80a84 | webshop | inefficiency, produces, queries, resulting, similar | The plan produces queries that are too similar to previous ones, resulting in inefficiency and repeated results. |
| webshop/GPT-4o_012_chat_b000_t00_e11-1cc61441 | webshop | apparel, changed, diverging, entirely, every, maintaining, objective, reformulated | At step 13, the planning module failed by diverging from the initial objective. Instead of maintaining the focus on ‘men |
| webshop/GPT-4o_015_chat_b000_t00_e14-1d03d2d8 | webshop | absence, adjusting, brute-force, complex, criterion, decisions, evaluation, evidence | At step 3, the memory module oversimplified the complex search context by stating, 'I found some relevant products like  |
| webshop/Qwen3-8B_002_chat_b000_t00_e01-7ab08a46 | webshop | asked, henley' | task asked for henley, but the product is a t-shirt. The plan should have been to refine the search query to include 'he |
| webshop/Qwen3-8B_003_chat_b000_t00_e02-1e119842 | webshop | began, dooming, fundamental, ignored, inconsistent, logically, misunderstanding, path | At step 7, the agent's plan explicitly ignored a key constraint in the user task: the user requested 'men's dress shirts |
| webshop/Qwen3-8B_004_chat_b000_t00_e03-d2034edc | webshop | concise, realized, very, working | The refined search query is very similar to the previous one, and the agent should have realized that the previous searc |
| webshop/Qwen3-8B_007_chat_b000_t00_e07-d50ae81f | webshop | altered, approval, clarification, deciding, diverged, explanation, fundamentally, gracefully | At step 8, the agent planned to 'Refine the search query by replacing 'zest' with a broader color term (e.g., 'yellow')  |
| webshop/Qwen3-8B_008_chat_b000_t00_e08-6a7bac22 | webshop | realized, very, working | The new search query is very similar to the previous one, and the agent should have realized that the previous search qu |
| webshop/Qwen3-8B_010_chat_b000_t00_e10-69d80a84 | webshop | clarified, continued, decomposing, endless, fundamentally, graceful, inconsistent, informative | At step 4, the agent recognized that the initial search query was not yielding relevant results (mostly t-shirts and hoo |
| webshop/Qwen3-8B_011_chat_b000_t00_e11-1cc61441 | webshop | realized, very, working | The new search query is very similar to the previous one, and the agent should have realized that the previous search qu |
| webshop/Qwen3-8B_012_chat_b000_t00_e12-f27d2887 | webshop | clothes, trying | The task request men's clothes but the planning module is trying to search for women fit. And the search query is too lo |
| webshop/Qwen3-8B_013_chat_b000_t00_e13-eb20423f | webshop | matached, recognize | The color is matached but the rubber outsole requirement is not met. The reflection is not able to recognize this correc |
| webshop/Qwen3-8B_016_chat_b000_t00_e16-3c6f739f | webshop | conclusion, confirming, constraints, dooming, failed, judged, meeting, premature | At step 4, the agent incorrectly judged that it had found a product meeting all user constraints (women's sweater, relax |
| webshop/Qwen3-8B_017_chat_b000_t00_e17-fbe4c42d | webshop | hallucinated, never | The size was never checked. The memory is hallucinated. It should check the product details to see if the size is met. |
| webshop/Qwen3-8B_018_chat_b000_t00_e18-5d01dff2 | webshop | checked, hallucinated, never | The  material (polyester&spandex) is never checked. The memory is hallucinated. It should check the product details to s |

## module / failure_type spellings as shipped
| module (raw) | failure_type | n |
|---|---|---|
| action |  | 10 |
| action | Parameter_error | 1 |
| action | invalid_action | 1 |
| action | misalignment | 7 |
| action | parameter_error | 3 |
| memory |  | 4 |
| memory | hallucination | 12 |
| memory | memory_retrieval_failure | 2 |
| memory | over_simplification | 20 |
| plan |  | 9 |
| plan | constraint_ignorance | 9 |
| plan | impossible_action | 3 |
| plan | inefficient_plan | 25 |
| plan | plan_inefficient | 3 |
| planning | constraint_ignorance | 4 |
| planning | impossible_action | 7 |
| planning | inefficient_plan | 18 |
| reflection |  | 2 |
| reflection | causal_misattribution | 5 |
| reflection | hallucination | 1 |
| reflection | outcome_misinterpretation | 12 |
| reflection | progress_misjudge | 20 |
| system |  | 2 |
| system | environment_error | 7 |
| system | llm_limit | 1 |
| system | step_limit | 8 |
| system | tool_execution_error | 3 |
| system | tool_execution_error  | 1 |
## ALFWorld: reason mentions an object/receptacle name that never appears in the run (object vocabulary of 82 names)

- alfworld/Qwen3-8B_008_id_8___chat_b005_t00_e00-d3248f80 task='put a newspaper in sofa.' label turn 3 cats=reflection.outcome_misinterpretation: objects in reason absent from run: ['bread', 'fridge', 'lettuce']; reason: after opening fridge 1, the agent saw bread and concluded that there was no lettuce, misunderstanding the observation result. without examin

1 of 74 ALFWorld reasons mention objects absent from the run

duplicated reason texts (used for >1 record): [('Inefficient plan by redo similar stuffs', 7), ('Not fully satisfy the constraint', 2), ('Make an low efficient plan that not success', 3), ('Get the wrong information for the answer think it is success', 2), ('The plan produced a query that was essentially the same as the initial', 2), ('The new search query is very similar to the previous one, and the agen', 3)]
