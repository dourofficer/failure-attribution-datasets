## (a) structural-rule exact hit rates (and within 5) per source

| rule | swe_bench_pro | terminal_bench_2 | travelplanner | vitabench | webarena_verified |
|---|---|---|---|---|---|
| first DiagnostAgent->ActionAgent delegation | 45% / 51% (fires 100%) | 14% / 21% (fires 100%) | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) |
| last DiagnostAgent->ActionAgent delegation | 24% / 27% (fires 100%) | 10% / 14% (fires 100%) | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) |
| first file edit (str_replace/create) | 11% / 25% (fires 100%) | 12% / 31% (fires 95%) | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) |
| final itinerary JSON write | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) | 7% / 13% (fires 51%) | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) |
| first Task_Planner delegation (step 2) | 0% / 1% (fires 100%) | 0% / 17% (fires 100%) | 2% / 6% (fires 100%) | 6% / 19% (fires 100%) | 3% / 10% (fires 100%) |
| first accommodation_search call | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) | 0% / 14% (fires 89%) | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) |
| first Verification_Expert turn | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) | 3% / 12% (fires 100%) |
| last Action_Expert turn | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) | 3% / 6% (fires 100%) | 20% / 29% (fires 100%) |
| first Action_Expert turn | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) | 0% / 15% (fires 100%) | 4% / 15% (fires 100%) |
| last agent step | 0% / 0% (fires 100%) | 0% / 2% (fires 100%) | 0% / 23% (fires 100%) | 3% / 6% (fires 100%) | 0% / 27% (fires 100%) |
| first order/pay tool call (vita) | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) | 6% / 29% (fires 82%) | 0% / 0% (fires 0%) |
| last agent turn before an user complaint (vita) | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) | 0% / 0% (fires 0%) |
| uniform over agent steps (expected exact) | 0.9% | 1.1% | 1.2% | 4.5% | 2.1% |

## (b) TravelPlanner verifier behaviour

TP runs: no verifier conclusion at all 79/685; verifier conclusions all passed:true 286; at least one passed:false 320; of those, run still terminated as complete 217

## (c) TravelPlanner final-write inconsistencies

TP runs with a final JSON: 347; duplicate meal names across the plan 146 (42%); some named item absent from the blackboard snapshot 42 (12%); either 173
runs whose root IS the final JSON write: 48; of those with a detectable inconsistency (dup or absent): 27
