## fix window t_lock - t_err {'n': 1184, 'mean': 6.639, 'median': 1.0, 'min': 0, 'max': 197, 'p10': 0, 'p90': 20}
zero window 463 / 1184 (39.1%)  >=3 520  >10 239
## t_obs - t_lock (n with t_obs) {'n': 852, 'mean': 2.312, 'median': 1.0, 'min': -130, 'max': 528, 'p10': -9, 'p90': 14}
negative (symptom before lock-in) 241  zero 149  >=5 214
## t_obs - t_err {'n': 852, 'mean': 10.088, 'median': 4.0, 'min': 0, 'max': 528, 'p10': 0, 'p90': 26}
silent (no t_obs) 332 / 1184
## t_err rel position {'n': 1184, 'mean': 0.377, 'median': 0.3125, 'min': 0.005, 'max': 1.0, 'p10': 0.0851063829787234, 'p90': 0.7807017543859649}
## t_lock rel position {'n': 1184, 'mean': 0.555, 'median': 0.5714285714285714, 'min': 0.00528169014084507, 'max': 1.0, 'p10': 0.15384615384615385, 'p90': 0.9347826086956522}
## steps after lock-in (m - t_lock) {'n': 1184, 'mean': 23.162, 'median': 9.0, 'min': 0, 'max': 1155, 'p10': 1, 'p90': 49} share of run after lock-in 0.445

## by trigger mechanism: n, median fix window, % zero window, % silent, median t_err rel, % forewarning
| trigger | n | med fix win | % win=0 | % silent | med t_err rel | % forewarn | % never aware | % fabric |
|---|---|---|---|---|---|---|---|---|
| false_premise | 364 | 2.0 | 36 | 31 | 0.29 | 64 | 56 | 37 |
| knowledge_gap | 284 | 1.0 | 42 | 24 | 0.3 | 60 | 51 | 15 |
| spec_neglect | 176 | 1.0 | 44 | 44 | 0.3 | 39 | 86 | 14 |
| capability_limit | 104 | 1.0 | 48 | 21 | 0.39 | 48 | 55 | 14 |
| environment_obstacle_mishandled | 104 | 2.5 | 39 | 13 | 0.38 | 90 | 44 | 50 |
| misread_output | 52 | 2.0 | 29 | 21 | 0.37 | 81 | 69 | 25 |
| ignored_signal | 49 | 2 | 22 | 16 | 0.48 | 88 | 55 | 18 |
| premature_action | 44 | 3.0 | 32 | 32 | 0.33 | 70 | 52 | 23 |
| other | 7 | 0 | 86 | 57 | 1.0 | 14 | 100 | 43 |

## awareness x tail behaviour
| awareness | cosmetic_progress | fabrication | immediate_claim | new_wrong_direction | thrash_repeat | verification_theater | n |
|---|---|---|---|---|---|---|---|
| aware_abandoned | 8 | 11 | 6 | 6 | 16 | 4 | 51 |
| aware_too_late | 5 | 3 | 2 | 1 | 8 | 6 | 25 |
| aware_wrong_fix | 26 | 65 | 13 | 75 | 170 | 64 | 413 |
| never_aware | 51 | 100 | 195 | 22 | 74 | 253 | 695 |
recovery attempts per failed run {'n': 1184, 'mean': 2.519, 'median': 1.0, 'min': 0, 'max': 122, 'p10': 0, 'p90': 7} ; runs with >=1 attempt 637
verification_ever Counter({True: 936, False: 248}) ; verification step after lock-in 647
awareness x silent: {'aware_abandoned': (4, 51), 'aware_too_late': (0, 25), 'aware_wrong_fix': (19, 413), 'never_aware': (309, 695)}
tail x silent: {'cosmetic_progress': (35, 90), 'fabrication': (34, 179), 'immediate_claim': (109, 216), 'new_wrong_direction': (4, 104), 'thrash_repeat': (20, 268), 'verification_theater': (130, 327)}
fabrication onset - t_lock {'n': 304, 'mean': 7.438, 'median': 0.0, 'min': -26, 'max': 270, 'p10': -2, 'p90': 22} fabrication at last step 35
forewarning present 732 / 1184 ; forewarning_first_step < t_err 370 == t_err 120 > t_err 242
forewarning types Counter({'empty_or_unexpected_output': 456, 'command_error': 415, 'repeated_command': 180, 'contradictory_evidence': 109, 'self_doubt_language': 48, 'misread_output': 2, 'ignored_signal': 1})

## action code at t_err / t_lock / t_obs (E explore P plan W write X execute V verify C claim R repair O other)
t_err Counter({'W': 687, 'X': 241, 'E': 106, 'P': 72, 'V': 31, 'C': 19, 'R': 16, 'O': 12})
t_lock Counter({'W': 647, 'X': 313, 'V': 64, 'C': 54, 'E': 35, 'P': 34, 'R': 32, 'O': 5})
t_obs Counter({'X': 351, 'V': 347, 'W': 55, 'E': 35, 'C': 30, 'R': 25, 'O': 6, 'P': 3})
last step code FAIL Counter({'C': 832, 'V': 169, 'X': 55, 'R': 44, 'W': 31, 'E': 26, 'O': 24, 'P': 3})  PASS Counter({'C': 434, 'V': 137, 'X': 15, 'O': 11, 'W': 7, 'E': 4, 'R': 2})
t_err == first W step 482 ; t_err == first X step 115 ; t_err in first segment 104

## PASS runs: error events
error events {'n': 610, 'mean': 2.292, 'median': 1.0, 'min': 0, 'max': 29, 'p10': 0, 'p90': 5} share >=1 0.71
recoveries {'n': 610, 'mean': 1.825, 'median': 1.0, 'min': 0, 'max': 29, 'p10': 0, 'p90': 4} max detour {'n': 610, 'mean': 6.893, 'median': 3.0, 'min': 0, 'max': 170, 'p10': 0, 'p90': 15}
first_error_step rel {'n': 433, 'mean': 0.312, 'median': 0.27906976744186046, 'min': 0.008333333333333333, 'max': 0.9814814814814815, 'p10': 0.08108108108108109, 'p90': 0.6}
suspicious pass 39 Counter({'proxy_solution': 21, 'lucky_environment': 13, 'other': 5})
solution_directness Counter({'trial_and_error': 224, 'direct': 201, 'detour': 185})  verification_before_claim Counter({True: 586, False: 24})
near miss 52
pass error observability Counter({'observable': 320, None: 177, 'silent': 113})

## matched design: same task, FAIL t_err vs PASS first_error_step (absolute)
tasks with both 58 ; median over tasks of (median FAIL t_err) 7.0 vs (median PASS first error) 5.5
pass rate per task {'n': 89, 'mean': 0.333, 'median': 0.23809523809523808, 'min': 0.0, 'max': 1.0, 'p10': 0.0, 'p90': 0.8571428571428571} ; tasks with 0 pass 28 ; tasks all pass 2

## per system: n fail, pass rate, % silent, % fabrication, median fix window, % verification theatre
| system | n fail | pass% | % silent | % fabric | med fix win | % verif theatre | % never aware | med m |
|---|---|---|---|---|---|---|---|---|
| miniswe/claude | 58 | 35 | 26 | 40 | 3.5 | 31 | 59 | 21.5 |
| miniswe/deepseek-v3.2 | 65 | 27 | 20 | 26 | 2 | 22 | 49 | 17 |
| miniswe/devstral | 54 | 36 | 37 | 31 | 1.0 | 43 | 70 | 41.0 |
| miniswe/gemini | 69 | 19 | 30 | 26 | 1 | 20 | 49 | 20 |
| miniswe/gpt5 | 59 | 34 | 36 | 22 | 1 | 3 | 66 | 7 |
| miniswe/kimi | 60 | 33 | 25 | 37 | 2.5 | 45 | 62 | 26.0 |
| miniswe/qwen | 63 | 29 | 30 | 29 | 1 | 33 | 57 | 25 |
| openhands/claude | 58 | 35 | 26 | 29 | 2.0 | 28 | 50 | 36.5 |
| openhands/deepseek-v3.2 | 58 | 35 | 14 | 24 | 5.0 | 29 | 43 | 55.0 |
| openhands/devstral | 60 | 31 | 20 | 17 | 0.0 | 38 | 63 | 30.5 |
| openhands/gemini | 60 | 30 | 38 | 25 | 0.0 | 3 | 68 | 15.5 |
| openhands/gpt5 | 49 | 45 | 27 | 16 | 1 | 12 | 65 | 13 |
| openhands/kimi | 61 | 31 | 21 | 28 | 3 | 31 | 64 | 46 |
| openhands/qwen | 61 | 31 | 15 | 23 | 3 | 11 | 52 | 48 |
| terminus2/claude | 51 | 40 | 24 | 37 | 3 | 37 | 53 | 35 |
| terminus2/deepseek-v3.2 | 39 | 43 | 26 | 15 | 6 | 38 | 56 | 81 |
| terminus2/devstral | 51 | 41 | 35 | 24 | 2 | 39 | 71 | 34 |
| terminus2/gemini | 52 | 40 | 50 | 19 | 0.0 | 4 | 60 | 12.0 |
| terminus2/gpt5 | 41 | 39 | 32 | 20 | 2 | 34 | 49 | 33 |
| terminus2/kimi | 56 | 33 | 30 | 23 | 1.0 | 48 | 59 | 35.0 |
| terminus2/qwen | 59 | 29 | 32 | 22 | 2 | 36 | 68 | 30 |

## dual annotation (docs/kappa_agreement/dual_annotations.csv): released == annotator A for t_err in 1184/1184
t_err n 1184 exact agree 144 (12.2%) B later 559 B earlier 481 |diff|>=3 7 |diff|>=10 7 diff dist [(1, 558), (-1, 474), (0, 144), (2, 1), (-83, 1), (-59, 1), (-74, 1), (-84, 1)] non-int 0
t_lock n 1184 exact agree 58 (4.9%) B later 680 B earlier 446 |diff|>=3 904 |diff|>=10 102 diff dist [(8, 83), (6, 76), (4, 73), (7, 72), (3, 70), (5, 69), (10, 68), (9, 60)] non-int 0
t_obs n 852 exact agree 211 (24.8%) B later 369 B earlier 272 |diff|>=3 504 |diff|>=10 56 diff dist [(0, 211), (7, 43), (6, 42), (2, 41), (-1, 41), (9, 39), (5, 37), (-6, 36)] non-int 0
t_err |A-B|>=3: {'n': 7, 'med_m': 114, 'med_fix': 0, 'silent': 0.29, 'long': 0.29, 'trig': [('knowledge_gap', 2), ('spec_neglect', 2), ('false_premise', 1), ('other', 1)], 'unc_terr': 0.29, 'conf': [('high', 6), ('medium', 1)]}
t_err |A-B|<3: {'n': 1177, 'med_m': 27, 'med_fix': 1, 'silent': 0.28, 'long': 0.05, 'trig': [('false_premise', 363), ('knowledge_gap', 282), ('spec_neglect', 174), ('capability_limit', 104)], 'unc_terr': 0.25, 'conf': [('high', 1045), ('medium', 132)]}
root_cause (trigger) disagree 165 / 1184 top confusions [(('false_premise', 'spec_neglect'), 10), (('knowledge_gap', 'environment_obstacle_mishandled'), 8), (('false_premise', 'ignored_signal'), 8), (('knowledge_gap', 'spec_neglect'), 8), (('false_premise', 'environment_obstacle_mishandled'), 7), (('false_premise', 'misread_output'), 7)]
awareness disagree 135 / 1184 top confusions [(('never_aware', 'aware_too_late'), 28), (('never_aware', 'aware_abandoned'), 24), (('aware_wrong_fix', 'aware_too_late'), 22), (('never_aware', 'aware_wrong_fix'), 21), (('aware_wrong_fix', 'never_aware'), 18), (('aware_wrong_fix', 'aware_abandoned'), 15)]
tail_behavior disagree 211 / 1184 top confusions [(('verification_theater', 'cosmetic_progress'), 14), (('thrash_repeat', 'cosmetic_progress'), 14), (('verification_theater', 'thrash_repeat'), 13), (('verification_theater', 'fabrication'), 13), (('verification_theater', 'immediate_claim'), 13), (('thrash_repeat', 'new_wrong_direction'), 11)]
fabrication_present disagree 46 / 1184 top confusions [(('False', 'True'), 34), (('True', 'False'), 12)]

uncertain_fields (FAIL) Counter({'t_err': 295, 't_commit': 183, 't_surface': 180, 'forewarning_first_step': 131, 'num_recovery_attempts': 51, 'tail_dominant_behavior': 29, 'forewarning_types': 28, 'forewarning_present': 24, 'contributing_failure_1_subtype': 22, 'trigger_mechanism': 18, 'action_segments': 12, 'timepoint_confidence': 11, 'awareness': 10, 'contributing_failure_1_layer': 9, 'fabrication_onset_step': 9, 'fabrication_type': 8, 'primary_failure_subtype': 5, 'first_relevant_verification_step': 5, 'contributing_failure_1_category': 4, 't_surface_evidence': 4, 'fabrication_present': 4, 'first_awareness_step': 4, 'primary_failure_layer': 2, 't_err: could also be placed at step 9 when agent sees products file is absent and does not immediately attempt git-lfs pull, but step 28 is the clearest decisive action': 1, 'num_recovery_attempts: counted steps 29-36 as 4 attempts to find products data (KDD Cup search, curl, cloning competitor repo, aicrowd-cli install) before giving up': 1, 'forewarning_evidence': 1, 'primary_failure_category': 1})  timepoint_confidence Counter({'high': 1051, 'medium': 133})
long_traj FAIL 57 PASS 7