"""AgentErrata is not released; build example/stat files from the paper + the Who&When case file it cites.
Usage: python3 -I make_agenterrata_files.py <whoandwhen_handcrafted_2.json> <notes_dir> <scratch_dir>
"""
import sys, os, json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import *

src, notes_dir, scratch = sys.argv[1:4]
d = json.load(open(src))
dump(d, os.path.join(notes_dir, "agenterrata_example.json"))

steps = []
for i, m in enumerate(d["history"]):
    txt, tr = trim_long(m.get("content", ""))
    st = {"idx": i, "agent": m.get("name") or m.get("role"), "content": txt}
    if tr:
        st["trimmed"] = True
    steps.append(st)
ms = int(d["mistake_step"])
norm = {
    "dataset": "agenterrata",
    "from_paper": True,
    "note": ("AgentErrata itself is NOT publicly released (as of 2026-10-16). The AGENTSCOPE paper (arXiv 2609.02371) "
             "shows no AgentErrata trajectory; its only worked example (Appendix C) is this Who&When Hand-Crafted trace "
             "(Zhang et al. 2025, https://github.com/ag2ai/Agents_Failure_Attribution/blob/main/Who%26When/Hand-Crafted/2.json), "
             "which the paper uses to argue that the annotated step (4) is the earliest issue while the decisive failure is the "
             "later stagnation loop (steps 11, 15, ...). Steps/annotation below come from that file; the paper's own reading is in annotation.extra."),
    "source_id": "Who&When/Hand-Crafted/2.json (question_ID=" + d["question_ID"] + ")",
    "task": d["question"],
    "ground_truth": d["ground_truth"],
    "final_output": d["history"][-1]["content"],
    "steps": steps,
    "annotation": {
        "faulty_agent": d["mistake_agent"],
        "faulty_step": ms,
        "category": None,
        "reason": d["mistake_reason"],
        "extra": {
            "is_corrected": d["is_corrected"],
            "step_indexing": "0-based index into `history` (index 0 = human query); history[4] is a WebSurfer step, matching mistake_agent",
            "paper_appendix_C_reading": ("Step 4 (annotated): WebSurfer retrieves only a search-results page without extracting structured information. "
                                          "Steps 11 and 15 (and later): WebSurfer repeats the same click / sees an identical viewport -> stagnation loop "
                                          "(flagged by the system as is_in_loop: true), persisting despite refined Orchestrator instructions; "
                                          "run ends with a content-filter (ResponsibleAI) BadRequestError in the ledger update, not with an answer."),
            "agentscope_failure_modes_that_would_apply": ["SL Step Loop (Control-flow)", "IC Insufficient Context (Reasoning)", "EF Execution Failure (Action)"],
        },
    },
}
dump(norm, os.path.join(notes_dir, "agenterrata_example_norm.json"))
with open(os.path.join(scratch, "agenterrata_example.md"), "w") as f:
    f.write(render_example_md(norm, step_limit=350))

stats = {
    "n_trajectories": 303,
    "source": "ALL numbers from the paper (arXiv 2609.02371v1, Sec. 4.1 / Appendix B / Fig. 6-7); dataset not released, nothing computed from data.",
    "steps_per_traj": [],
    "error_step_rel_pos": [],
    "agents_per_traj": [],
    "faulty_agent_counts": {},
    "category_counts": {"Reasoning (IC, WC, IU, CM)": "36.0% (Fig. 6; the four modes sum to 33.1% in Fig. 7)",
                        "Control-flow (TM, PT, SL)": "31.0%", "Action (AM, II, EF)": "36.0%"},
    "mode_share_pct": {"IC Insufficient Context": 9.6, "WC Wrong Context": 8.3, "IU Instruction Unfollowing": 9.9,
                       "CM Context Miss": 5.3, "TM Termination Miss": 9.6, "PT Premature Termination": 12.5,
                       "SL Step Loop": 8.9, "AM Action Mismatch": 13.2, "II Invocation Issue": 7.9, "EF Execution Failure": 14.9},
    "mode_counts_est_from_pct_x303": {k: round(v * 303 / 100) for k, v in {
        "IC": 9.6, "WC": 8.3, "IU": 9.9, "CM": 5.3, "TM": 9.6, "PT": 12.5, "SL": 8.9, "AM": 13.2, "II": 7.9, "EF": 14.9}.items()},
    "source_benchmark_counts": {"BrowseComp": "n/a (not reported)", "SWE-Bench Lite": "n/a", "WebArena": "n/a"},
    "framework_counts": {"OpenManus": "n/a (not reported)", "OWL": "n/a", "Mini SWE Agent": "n/a"},
    "splits": {"all": 303},
    "all_failed": True,
    "labels": ["failing step (single decisive injected error)", "failure mode (1 of 10) / category (1 of 3)"],
    "metrics": ["SLA step-level accuracy", "SLAT step-level accuracy with tolerance ±1/±3", "CA failure-mode classification accuracy"],
    "baselines_pct": {
        "GPT-4o": {"W&W All-at-once SLA T±0/±1/±3 w/ solution": [2.14, 6.05, 21.00], "W&W Step-by-step": [10.56, 14.52, 25.74],
                   "AgentScope": [28.38, 34.98, 48.51], "LLM-as-Judge CA w/o solution": 20.63, "AgentScope CA w/o solution": 43.56},
        "GPT-5.1": {"W&W All-at-once": [2.64, 5.61, 18.81], "W&W Step-by-step": [1.65, 4.62, 12.21], "AgentScope": [29.70, 34.65, 50.50],
                    "LLM-as-Judge CA w/o solution": 18.15, "AgentScope CA w/o solution": 45.87},
        "DeepSeek-V3.2": {"All-at-once SLA w/o,w/": [0.66, 0.99], "Step-by-step SLA": [17.82, 17.82], "AgentScope SLA": [34.98, 33.33], "AgentScope CA": [45.21, 44.22]},
    },
}
dump(stats, os.path.join(notes_dir, "agenterrata_stats.json"))
print("ok", len(steps), "steps; norm size", os.path.getsize(os.path.join(notes_dir, "agenterrata_example_norm.json")))
