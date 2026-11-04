# First-symptom heuristics vs human label (turn units)

| env | heuristic | n | exact | ±1 | ±3 | undefined (counted as miss) |
|---|---|---|---|---|---|---|
| alfworld | turn 1 | 100 | 4% | 10% | 36% | 0 |
| alfworld | last turn | 100 | 10% | 10% | 10% | 0 |
| alfworld | first malformed/inadmissible | 100 | 9% | 20% | 34% | 23 |
| alfworld | first 'Nothing happens' | 100 | 9% | 21% | 35% | 23 |
| alfworld | first repeated action | 100 | 13% | 28% | 53% | 13 |
| alfworld | first repeated observation | 100 | 11% | 33% | 49% | 14 |
| alfworld | first error-like tool result | 100 | 0% | 0% | 0% | 100 |
| alfworld | start of longest identical-action run | 100 | 3% | 12% | 22% | 40 |
| alfworld | first anomaly (min of the above symptom turns) | 100 | 17% | 31% | 47% | 11 |
| webshop | turn 1 | 50 | 10% | 28% | 42% | 0 |
| webshop | last turn | 50 | 14% | 16% | 18% | 0 |
| webshop | first malformed/inadmissible | 50 | 0% | 0% | 0% | 50 |
| webshop | first 'Nothing happens' | 50 | 0% | 0% | 0% | 50 |
| webshop | first repeated action | 50 | 6% | 32% | 50% | 2 |
| webshop | first repeated observation | 50 | 12% | 26% | 54% | 0 |
| webshop | first error-like tool result | 50 | 0% | 0% | 0% | 50 |
| webshop | start of longest identical-action run | 50 | 16% | 24% | 34% | 3 |
| webshop | first anomaly (min of the above symptom turns) | 50 | 14% | 32% | 52% | 0 |
| gaia | turn 1 | 49 | 18% | 45% | 76% | 0 |
| gaia | last turn | 49 | 24% | 31% | 43% | 0 |
| gaia | first malformed/inadmissible | 49 | 0% | 0% | 0% | 49 |
| gaia | first 'Nothing happens' | 49 | 0% | 0% | 0% | 49 |
| gaia | first repeated action | 49 | 4% | 10% | 33% | 24 |
| gaia | first repeated observation | 49 | 12% | 29% | 59% | 17 |
| gaia | first error-like tool result | 49 | 12% | 18% | 31% | 26 |
| gaia | start of longest identical-action run | 49 | 0% | 2% | 12% | 32 |
| gaia | first anomaly (min of the above symptom turns) | 49 | 20% | 33% | 61% | 14 |