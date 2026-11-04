# Worklog

- 2026-11-01: infrastructure written (common/, loaders/who_and_when.py, baseline/all_at_once.py); smoke test on 6 Who&When
  records OK (Qwen3.8-27B, thinking on; one record hit the 8k completion cap, default raised to 16k).
- 2026-11-01: workflow launched: 19 dataset-inspection agents + 5 literature agents.
- 2026-11-01: loader agent delivered 18 loaders (loaders/STATUS.md; 34,828 records). error_step() now prefers the dataset's
  primary index stored in labels.extra. Literature agent delivered lit/known_phenomena.md (phenomena P1–P8).
- 2026-11-01: baseline/run_all.sh launched (3 chains, results/<slug>/DONE markers); four group agents launched
  (G1 output-only MAS, G2 full-trace/long, G3 single-agent natural, G4 injected/taxonomy) writing findings/datasets/<slug>.md
  and findings/groups/<g>.md.
- 2026-11-01: vLLM on :8210 saturated (16 running / 80 queued). Second Qwen3.8-27B instance started on GPU 3 port 8211
  (vllm/serve_second.sh, mpmath shim in vllm/pyshim); common/llm.py now routes each request to the least-loaded server.
- 2026-11-01 10:12: baseline runner restarted on the load-balanced client (old jobs only used :8210; cached calls are kept).
- 2026-11-01 11:45: group syntheses g1, g2, g4 in; G3 resumed after an API error (403) to write g3. Fixed render.py for
  list-valued fields (AgentHallu BFCL) and relaunched that baseline. Wrote findings/hypotheses.md draft v1 (12 phenomena,
  12 ranked hypotheses, P1–P8 verdicts, experiment programme); PENDING rows listed in its §8. Cross-dataset tables:
  inspect/summarize_baselines.py, inspect/summarize_probes.py.
- 2026-11-01 11:50: runner ALL_DONE except SearchAuditBench and MemTrace (400: prompt over 200k; approx_tokens tightened to
  chars/2.6, 400s no longer retried, chat_json returns an error row; both relaunched with --budget-tokens 110000).
  Appended §4b baseline sections to mp_bench, symtrace, agentrx, longrca, horizon, agenthallu. hypotheses.md §1 table filled
  (LongRCA is the only set where the judge's misses skew late: 30/48, median |offset| 28). Verified FaP annotator-B jitter and
  TrajErrBench zh goal leakage on the raw files; both recorded in hypotheses.md §4.
- 2026-11-01 12:00: SearchAuditBench (40% exact, misses earlier 14/6) and MemTrace (30%, 3 overflow rows) baselines done; hypotheses.md §1/§8 final; §4b appended to both dataset files. Round complete.
- 2026-11-01 13:00: ML-principles mapping: lit/ml_principles/{00_brief,A_causation_credit,B_labels_abstention,C_shift_shortcuts_structure,README}.md; hypotheses.md §5b points to it.
