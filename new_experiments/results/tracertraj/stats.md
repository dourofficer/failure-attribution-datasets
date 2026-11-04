# TracerTraj targeted statistics (G4)

## (a) Label position and continuation by domain / label source

| domain/source | n | steps mean/median | rel pos | label = last agent step % | agent steps after | no continuation % | >=3 after % | labelled step chars |
|---|---|---|---|---|---|---|---|---|
| agentic/Diagnosis Error | 278 | 10.7/9.0 | 0.69 | 47.8 | 3.4 | 47.8 | 34.5 | 3140 |
| agentic/Injection Error | 1822 | 9.1/7.0 | 0.53 | 12.8 | 4.0 | 12.8 | 59.1 | 3840 |
| coding/n/a | 1268 | 20.9/14.0 | 0.46 | 3.7 | 11.5 | 3.7 | 93.0 | 1770 |
| math/n/a | 630 | 6.3/7.0 | 0.54 | 9.0 | 2.7 | 9.0 | 40.3 | 1691 |

## (b) Agentic rows: content type of the labelled step by source

| source | n | tool call % | final answer % | mentions error/wrong % | <200 chars % |
|---|---|---|---|---|---|
| agentic/Injection Error | 1822 | 6.3 | 12.9 | 9.3 | 0.4 |
| agentic/Diagnosis Error | 278 | 7.2 | 28.4 | 14.7 | 0.4 |
coding: mistake_reason written from an injector's perspective (regex 'by changing/instead of/this step is critical because'): 56.6% of 1268; starts with 'This step is critical': 51.7%
math: mistake_reason written from an injector's perspective (regex 'by changing/instead of/this step is critical because'): 7.5% of 630; starts with 'This step is critical': 0.0%

error_source values: Counter({None: 1898, 'Injection Error': 1822, 'Diagnosis Error': 278})
mistake_reason non-empty by domain: Counter({('agentic', False): 2100, ('coding', True): 1268, ('math', True): 630})

## (c) Symptom markers per step before / at / after the label by label source

| group | marker | steps before | % before | % at label | steps after | % after |
|---|---|---|---|---|---|---|
| agentic/Diagnosis Error | tool_error | 1764 | 3.7 | 5.8 | 939 | 4.2 |
| agentic/Diagnosis Error | self_correct | 1764 | 15.8 | 15.5 | 939 | 23.7 |
| agentic/Diagnosis Error | uncertainty | 1764 | 6.9 | 6.1 | 939 | 13.6 |
| agentic/Diagnosis Error | repeat | 1764 | 0.3 | 0.0 | 939 | 0.6 |
| agentic/Injection Error | tool_error | 7520 | 5.7 | 4.3 | 7311 | 5.2 |
| agentic/Injection Error | self_correct | 7520 | 13.0 | 6.5 | 7311 | 20.3 |
| agentic/Injection Error | uncertainty | 7520 | 3.6 | 3.8 | 7311 | 6.4 |
| agentic/Injection Error | repeat | 7520 | 0.5 | 0.0 | 7311 | 0.5 |
| coding/n/a | tool_error | 10572 | 1.4 | 1.3 | 14617 | 3.5 |
| coding/n/a | self_correct | 10572 | 0.5 | 0.6 | 14617 | 2.3 |
| coding/n/a | uncertainty | 10572 | 2.0 | 1.5 | 14617 | 1.2 |
| coding/n/a | repeat | 10572 | 28.8 | 0.0 | 14617 | 33.6 |
| math/n/a | tool_error | 1612 | 0.0 | 0.2 | 1704 | 0.4 |
| math/n/a | self_correct | 1612 | 1.2 | 3.5 | 1704 | 4.8 |
| math/n/a | uncertainty | 1612 | 0.0 | 0.0 | 1704 | 0.1 |
| math/n/a | repeat | 1612 | 0.0 | 0.0 | 1704 | 0.0 |

## (d) Coding rows: length and label placement

coding rows: 1268; >=100 steps: 13; >=200: 1
- coding/train/642_Apps_1145_I: n=304, label idx 4 (Engineer), rel 0.01; agents [('Engineer', 294), ('Team Leader', 10)]; reason: This step is critical because initializing the dp array with None instead of 0 will cause the algorithm to misinterpret unvisited cells. The algorithm relies on the dp array to store the minimum costs
- coding/train/919_Taco_56314_I: n=192, label idx 3 (Engineer), rel 0.02; agents [('Engineer', 184), ('Team Leader', 8)]; reason: This step is critical because modifying the return statement to include .replace('  ', ' ') will alter the output by removing any unintended double spaces at the end of the transformed string. This co
- coding/test/106_Codeforces_7286_I: n=151, label idx 4 (Engineer), rel 0.03; agents [('Engineer', 146), ('Team Leader', 5)]; reason: The Engineer implemented the unobstructed_buildings function such that it only checks if the current building is strictly taller than the maximum height to its right. However, the problem statement re
- coding/train/767_Algorithm_20066_I: n=149, label idx 4 (Product Manager), rel 0.03; agents [('Product Manager', 128), ('Team Leader', 12), ('Architect', 9)]; reason: This step is critical because sorting by start time instead of end time will lead to incorrect task scheduling, potentially allowing overlapping tasks to be counted as non-overlapping, thus failing to
- coding/train/101_Data_Structure_6103_I: n=137, label idx 3 (Engineer), rel 0.02; agents [('Engineer', 128), ('Team Leader', 9)]; reason: This step is critical because it directly affects the logic of determining if B is a substring of the repeated A. By changing the condition to check for the absence of B, the function will incorrectly
- coding/train/817_Leetcode_33109_I: n=136, label idx 4 (Engineer), rel 0.03; agents [('Engineer', 130), ('Team Leader', 6)]; reason: This step is critical because the choice of pairing strategy directly affects the output of the function. By changing the pairing strategy, the function will produce incorrect results, especially for 
- coding/test/35_Filter_56113_I: n=125, label idx 5 (Engineer), rel 0.04; agents [('Engineer', 116), ('Team Leader', 9)]; reason: This step is critical because it directly affects the ranking of elements above the threshold. By sorting in ascending order, the function will produce incorrect rankings, leading to an incorrect fina
- coding/train/181_Code_Contests_18143_I: n=122, label idx 4 (Engineer), rel 0.03; agents [('Engineer', 116), ('Team Leader', 6)]; reason: This step is critical because it initializes the first row of the DP table. If the first row is incorrectly initialized, it will propagate errors throughout the DP table, leading to an incorrect final

blamed agent by domain: {'coding': [('Engineer', 935), ('Product Manager', 155), ('Team Leader', 125), ('Architect', 46), ('Data Analyst', 7)], 'math': [('Custom', 400), ('reasoning expert', 171), ('BestMAS_GSM8K', 55), ('AnswerGenerate', 2), ('QualityDiversity', 1)]}

question_IDs with >1 row: 118 (Counter({'math': 118})); labels across variants (first 8): [3, 2]; [6, 3]; [6, 1]; [2, 1]; [5, 1]; [1, 2]; [5, 2]; [1, 5]

## (e) Hidden injection in coding / math (G4 addendum)

- coding: 679/1,268 rows (53.5%) carry the string `*_attacked_solution.py` in the task message (step 0) -- the injected rows leak the fact in the trajectory; 655 of them have a mistake_reason starting "This step is critical because ... By changing X ..." (the injector's rationale), the other 589 rows have diagnosis-style reasons ("In Step 6, the Engineer implemented ... However ...") and no leak. Injected coding rows: median 13 steps, label rel. pos 0.34, never at the last step; diagnosed coding rows: median 15 steps, rel. pos 0.59, 8.0% at the last step.
- math: 99.4% of mistake_reason mention "inject" ("Step 5 is the most decisive because ... Injecting at this step ensures ..."): ALL math rows are injected and the reason is the injector's plan, written before the injection. 12.2% of labelled math steps are a refusal ("I'm sorry, but I can't comply with that request") -- the injection prompt triggered a refusal and the refusal was kept as the error step.
- agentic: label-source split is explicit (error_source). Diagnosed labels sit on the final-answer step in 42.1% (vs 13.0% injected) and on a `crawl_page` call in 28.8% (the tool fails with "crawl4ai is not installed" in 9.7% of diagnosed rows).
- agentic shell-style injected rows (316): 18.0% of labelled steps contain a `| sed "s/.../.../"` substitution appended to the command (the perturbation operator rewrites the observation in-line); 2.5% of diagnosed.

## (f) Text-free rules on agentic rows (G4 addendum)

- Diagnosis Error (n=278): final-answer step 47.5%, first crawl_page call 19.1%, last agent step 47.8%, combo (first crawl_page if the run has an install error, else final-answer step) 47.8%
- Injection Error (n=1822): final-answer step 12.1%, first crawl_page call 24.9%, last agent step 12.8%, combo (first crawl_page if the run has an install error, else final-answer step) 13.5%
