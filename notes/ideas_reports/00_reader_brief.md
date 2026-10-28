# Brief: mine a batch of papers for ideas transferable to LLM-agent failure attribution

You are one of several readers. Each reader gets a batch of plain-text extractions of PDFs (in
`/tmp/claude-1007/-dataDisk-home-thanhdo-failure-attribution-datasets/db7f457e-98ed-4be7-b325-7c9c3167a7b5/scratchpad/papers_txt/`).
Read each paper in your batch END TO END (method, experiments, limitations, appendix if useful). If the text
extraction of a figure/table is garbled and matters, you may open the original PDF under
`/dataDisk/home/thanhdo/sharonish/papers/` with the Read tool (pages parameter). Do not run any code from the papers.
Do not read other readers' batches. Do not web-search; everything you need is local.

## The target problem (what the ideas must serve)

**Failure attribution for LLM agent / multi-agent systems.** A system (single agent or several roles: orchestrator,
web-surfer, coder, verifier...) runs on a task and produces a trajectory τ = (s_1..s_T); each step s_t is an agent output
(message / tool call / code) plus the observation it produced (tool result, page, test log). The run FAILS (answer wrong,
tests fail). The task: find
- **when**: the decisive error step t* = the earliest step such that, had it been correct, the run would have succeeded
  (counterfactual definition); variants: the set of all error steps, the lock-in point after which no single-step repair
  recovers the run, three timestamps t_err / t_lock / t_obs (first observable symptom);
- **who**: the agent/role that emitted t* (multi-agent only);
- **what**: a failure category (taxonomies of 9–20 modes: planning, reasoning, tool misuse, verification, coordination...).
Metrics: exact-step accuracy, step accuracy within ±k, agent accuracy, set-F1 over error steps, nDCG over a ranked list of
candidate steps, category accuracy; also calibration of P(fail | prefix) and lead time for online monitors.

**Why it is hard.** Errors propagate: the visible crash is dozens of steps after the subtle cause. Best prompted LLMs
reach ~55% agent / 10–30% step accuracy on natural failures; humans themselves agree on the exact step only 40–90% of the
time depending on dataset. Trajectories are long (median 10–150 steps, 7k–260k tokens). Step labels are scarce and
expensive; outcome labels (success/fail) are free wherever the task has a verifier.

**Data available (already downloaded and analysed; a 68-page survey exists).**
- Human-labelled natural failures with (agent, step): Who&When (184, GAIA/AssistantBench MAS), TraceElephant (220, full
  LLM-call traces incl. inputs/screenshots, replayable), MP-Bench (289, THREE annotators per log, set-valued votes),
  LongRCA (1,140, median 145 steps), AgentRx (73 public, every failure event + root cause + 9 categories), SymFail
  (536, replayable event graphs), TrajErrBench (486, τ²-bench + SWE-Bench Pro, κ 0.91/0.67), AgentErrorBench (200,
  ALFWorld/WebShop/GAIA single agent, module+type), AgentHallu (693 runs of which 443 hallucinated and 250 CLEAN, step +
  cause), SearchAuditBench (1,243 deep-search runs, step + tolerance span + root cause + repair rubric), MemTrace (160
  memory-system failures as execution graphs), Failure-as-a-Process (1,184 FAIL + 610 PASS CLI-coding runs, annotations
  only, t_err/t_lock/t_obs).
- Injected (synthetic) failures, labels exact by construction, large: Who&When Pro (12k, 15 frameworks, mode label),
  Aegis (9.5k, (agent, MAST mode) sets, no step), TracerTraj (4k), CORRECT-Error (2.2k). Their error POSITION distribution
  is skewed (near the end or near the start), unlike natural failures.
- Taxonomy-only (trace-level mode flags, LLM-judge labelled): MAST-Data (1,642), HORIZON (3,782 incl. 1,284 successes).
- Most natural-failure sets release failures ONLY; successes exist in AgentHallu, HORIZON, TRAIL, Failure-as-a-Process.
- Grey/white-box access: for self-collected runs we can log token log-probs and hidden states of open models; released
  datasets are text logs only (TraceElephant/SymFail/MemTrace have full per-call requests/responses).

**Two research proposals already drafted (so you can say whether an idea is new, complementary, or a duplicate):**
1. *Interventional definition + perturbation screen*: define attribution as the step-level repair-effect profile
   φ(τ,k,δ) = P(success | replay prefix, apply fix δ at k) − P(success | replay prefix as is), estimated by N rollouts in
   replayable environments; the decisive step, error set, lock-in and responsible agent are summary statistics of that
   profile. Tasks: learn a surrogate f(prefix, step, δ) ≈ effect without executing; compare effect-based labels to human
   labels; fragility curves on successful runs (inject at k, measure recovery probability vs position). Analogy to
   Perturb-seq / GEARS in biology.
2. *Label-free attribution from the flow of trajectories*: a step-hazard survival model h_t = P(step t is the first
   unrecovered error | prefix); P(success)=∏(1−h_t); fit by maximum likelihood on ALL trajectories using only the outcome
   label (L1), optionally plus rollouts of the same prefix (L1+); fully unsupervised change-point mixture when even the
   outcome is unknown (L0). Positions itself against OAT (one-class model of successful trajectories with a neural CDE).

**Supervision levels used in the proposals**: L2 = step labels; L1+ = outcomes of several continuations of the same
prefix; L1 = outcome only; L0 = raw logs.

## What to produce

For EACH paper in your batch, in this order:

1. **Paper** — short name, venue/year, 3–5 sentence description of the actual mechanism (not the abstract's claims):
   what signal it uses, what it learns, what supervision it needs, what it is evaluated on, key numbers.
2. **Transferable ideas** — 0 to 4 idea cards. It is fine to return ZERO ideas for a paper that genuinely has none
   (say why in one line). Do NOT pad. Each card:
   - **Idea name** (≤ 10 words)
   - **Mechanism in the paper** (with section/figure/equation reference and a short verbatim quote if useful)
   - **Mapping to failure attribution**: what plays the role of the paper's object (what is the "sample", what is the
     "step", what signal is read), which output it yields (when / who / what / P(fail|prefix) / repair), which supervision
     level it needs (L0/L1/L1+/L2), grey-box or text-only
   - **Which of the datasets above it could be run on**, and what baseline it would be compared against
   - **Relation to the two existing proposals**: new / strengthens proposal 1 or 2 (how) / duplicate
   - **Main risk** (one or two lines: why it might not transfer)
   - **Plausibility 1–5** (5 = I would start this next week; 1 = far-fetched) and **Effort S/M/L**
3. **Quotable facts** — up to 5 numbers or sentences from the paper worth citing (with page/section).
4. **Code/data released?** — one line.

At the end of your report add a **Batch ranking**: your top 5 ideas across the batch, one line each, with plausibility.

Style: dense, concrete, no marketing language. Prefer mechanisms over slogans. If an idea is only "use hidden states",
say exactly which hidden states, from which model, aggregated how, and what the paper showed about that choice.
Write the full report as your final message (it is the only thing the coordinator sees). Also save a copy to
`/tmp/claude-1007/-dataDisk-home-thanhdo-failure-attribution-datasets/db7f457e-98ed-4be7-b325-7c9c3167a7b5/scratchpad/reports/<batch-letter>.md`.
