#!/usr/bin/env python3
"""Figures from notes/<slug>_stats.json. Cross-dataset figures -> report/2_overview/figures/fig_*.pdf;
per-dataset bar charts -> report/<group>/<slug>/figures/{cat,agent,bench,fw}.pdf (see report_layout.py).

Usage: python3 make_figures.py ../notes ../report
"""
import json, os, sys, glob, statistics as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_layout import GROUP, OVERVIEW_FIGURES  # noqa: E402
NOTES, REPORT = sys.argv[1], sys.argv[2]
FIGS = os.path.join(REPORT, OVERVIEW_FIGURES)
os.makedirs(FIGS, exist_ok=True)


def dataset_fig_dir(slug):
    d = os.path.join(REPORT, GROUP[slug], slug, "figures")
    os.makedirs(d, exist_ok=True)
    return d

# --- fonts (TeX Gyre Termes = Times, from TinyTeX, to match the report's newtx body font) ---
fira = glob.glob(os.path.expanduser("~/.TinyTeX/texmf-dist/fonts/opentype/public/tex-gyre/texgyretermes-*.otf"))
for f in fira:
    try:
        font_manager.fontManager.addfont(f)
    except Exception:
        pass
plt.rcParams.update({
    "font.family": "TeX Gyre Termes" if fira else "DejaVu Serif",
    "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5, "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#8a8984", "axes.linewidth": 0.5, "xtick.color": "#52514e", "ytick.color": "#52514e",
    "axes.labelcolor": "#52514e", "text.color": "#0b0b0b", "grid.color": "#e6e5e0", "grid.linewidth": 0.5,
    "pdf.fonttype": 42, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})
# dataviz reference palette
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"
INK2, INK3 = "#52514e", "#8a8984"
KIND_COLOR = {"natural": BLUE, "injected": ORANGE, "taxonomy": AQUA, "related": VIOLET}

# slug -> (label, group, failure source kind)
META = {
    "who_and_when": ("Who&When", 1, "natural"),
    "traceelephant": ("TraceElephant", 1, "natural"),
    "mp_bench": ("MP-Bench", 1, "natural"),
    "who_and_when_pro": ("Who&When Pro", 1, "injected"),
    "longrca": ("LongRCA", 1, "natural"),
    "agentrx": ("AgentRx", 1, "natural"),
    "symtrace": ("SymFail", 1, "natural"),
    "tracertraj": ("TracerTraj", 2, "injected"),
    "aegis": ("Aegis", 2, "injected"),
    "correct_error": ("CORRECT-Error", 2, "injected"),
    "agenterrata": ("AgentErrata", 2, "injected"),
    "mast_data": ("MAST-Data", 3, "taxonomy"),
    "trail": ("TRAIL", 3, "taxonomy"),
    "agenterrorbench": ("AgentErrorBench", 4, "related"),
    "searchauditbench": ("SearchAuditBench", 4, "related"),
    "failure_as_process": ("Failure-as-a-Process", 4, "related"),
    "trajerrbench": ("TrajErrBench", 4, "related"),
    "agenthallu": ("AgentHallu", 4, "related"),
    "memtrace": ("MemTrace", 4, "related"),
    "horizon": ("HORIZON", 4, "related"),
    "megarca_mix": ("MegaRCA-Mix", 4, "related"),
}

stats = {}
for slug in META:
    p = os.path.join(NOTES, f"{slug}_stats.json")
    if os.path.exists(p):
        try:
            stats[slug] = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            print("bad json", slug, e)


def steps_of(slug):
    d = stats.get(slug, {})
    v = d.get("steps_per_traj_failed") or d.get("steps_per_traj") or []
    return [int(x) for x in v if isinstance(x, (int, float)) and x > 0]


def relpos_of(slug):
    d = stats.get(slug, {})
    v = d.get("error_step_rel_pos") or []
    return [float(x) for x in v if isinstance(x, (int, float)) and 0 <= x <= 1.0001]


# ---------- Fig 1: steps per trajectory (box plots, log x) ----------
rows = [(s, steps_of(s)) for s in META if len(steps_of(s)) >= 5]
rows.sort(key=lambda r: st.median(r[1]))
fig, ax = plt.subplots(figsize=(3.5, 0.2 * len(rows) + 0.75))
labels = [META[s][0] for s, _ in rows]
data = [v for _, v in rows]
bp = ax.boxplot(data, vert=False, widths=0.55, showfliers=True, patch_artist=True,
                flierprops=dict(marker=".", markersize=2, markerfacecolor=INK3, markeredgecolor="none", alpha=0.5),
                medianprops=dict(color="white", linewidth=1.2), whiskerprops=dict(color=INK3, linewidth=0.6),
                capprops=dict(color=INK3, linewidth=0.6), boxprops=dict(linewidth=0))
for patch, (s, _) in zip(bp["boxes"], rows):
    patch.set_facecolor(KIND_COLOR[META[s][2]])
ax.set_yticks(range(1, len(rows) + 1)); ax.set_yticklabels(labels)
ax.set_xscale("log"); ax.set_xlabel("steps per trajectory (log scale)")
ax.grid(axis="x"); ax.set_axisbelow(True)
for i, (s, v) in enumerate(rows):
    ax.text(max(v) * 1.3, i + 1, f"n={len(v):,} / med {int(st.median(v))}", va="center", fontsize=5.6, color=INK2)
ax.set_xlim(right=max(max(v) for v in data) * 12)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=KIND_COLOR[k], label=l) for k, l in
                   [("natural", "natural failures, human-labelled"), ("injected", "fault injection"),
                    ("taxonomy", "failure-mode taxonomy"), ("related", "related / single-domain")]],
          loc="upper center", bbox_to_anchor=(0.45, -0.2), frameon=False, ncol=2, handlelength=1.2, columnspacing=1.0)
fig.savefig(os.path.join(FIGS, "fig_steps.pdf")); plt.close(fig)

# ---------- Fig 2: relative position of the labelled error step ----------
rows = [(s, relpos_of(s)) for s in META if len(relpos_of(s)) >= 20]
n = len(rows); cols = 6; r = (n + cols - 1) // cols
fig, axes = plt.subplots(r, cols, figsize=(6.8, 1.0 * r + 0.3), sharex=True)
axes = axes.ravel()
for ax, (s, v) in zip(axes, rows):
    ax.hist(v, bins=10, range=(0, 1), color=KIND_COLOR[META[s][2]], edgecolor="white", linewidth=0.4)
    ax.set_title(f"{META[s][0]}\nn={len(v):,}, mean={st.mean(v):.2f}", fontsize=6.4, loc="left", pad=2, color=INK2)
    ax.set_yticks([]); ax.spines["left"].set_visible(False)
    ax.set_xticks([0, 0.5, 1]); ax.set_xticklabels(["start", "mid", "end"], fontsize=6)
for ax in axes[len(rows):]:
    ax.axis("off")
fig.subplots_adjust(hspace=1.0, wspace=0.15)
fig.savefig(os.path.join(FIGS, "fig_errpos.pdf")); plt.close(fig)

# ---------- Fig 3: dataset sizes (labelled failed trajectories) ----------
SIZES = {  # paper-reported sizes (labelled failed trajectories); used where data is partial/unavailable
    "who_and_when": 184, "traceelephant": 220, "mp_bench": None, "who_and_when_pro": 12326, "longrca": 1140,
    "agentrx": 115, "symtrace": 536, "tracertraj": 3998, "aegis": 9533, "correct_error": 2226, "agenterrata": 303,
    "mast_data": 1642, "trail": 148, "agenterrorbench": 200, "searchauditbench": 1243,
    "failure_as_process": 1184, "trajerrbench": 486, "agenthallu": 693, "memtrace": 160, "horizon": 2498,
    "megarca_mix": 50,
}
for s in META:
    if s in stats and isinstance(stats[s].get("n_trajectories"), int) and (SIZES.get(s) is None):
        SIZES[s] = stats[s]["n_trajectories"]
rows = [(s, SIZES[s]) for s in META if SIZES.get(s)]
rows.sort(key=lambda r: r[1])
fig, ax = plt.subplots(figsize=(3.5, 0.185 * len(rows) + 0.6))
ax.barh([META[s][0] for s, _ in rows], [v for _, v in rows], color=[KIND_COLOR[META[s][2]] for s, _ in rows], height=0.62)
ax.set_xscale("log"); ax.set_xlabel("labelled trajectories (log scale)"); ax.grid(axis="x"); ax.set_axisbelow(True)
for i, (s, v) in enumerate(rows):
    ax.text(v * 1.15, i, f"{v:,}", va="center", fontsize=6.5, color=INK2)
ax.set_xlim(right=max(v for _, v in rows) * 4)
fig.savefig(os.path.join(FIGS, "fig_sizes.pdf")); plt.close(fig)


# ---------- per-dataset small category / agent bar charts ----------
def small_bar(slug, key, title, fname, topk=10, color=BLUE):
    d = stats.get(slug, {}).get(key) or {}
    items = [(k, v) for k, v in d.items() if isinstance(v, (int, float))]
    if not items:
        return False
    items.sort(key=lambda kv: -kv[1])
    other = sum(v for _, v in items[topk:])
    items = items[:topk]
    if other > 0:
        items.append(("Other", other))
    labels = [str(k)[:34] for k, _ in items][::-1]; vals = [v for _, v in items][::-1]
    # fixed 3.4in width with the label gutter inside the figure, so the PDF is placed at true size
    # (a tight bbox around long labels used to widen the file and shrink the fonts when scaled to the column)
    W, H = 3.4, 0.19 * len(items) + 0.5
    left = min(0.08 + 0.049 * max(len(l) for l in labels), 0.55 * W)
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([left / W, 0.32 / H, 1 - left / W - 0.02, 1 - 0.32 / H - 0.2 / H])
    cols = [INK3 if l == "Other" else color for l in labels]
    ax.barh(labels, vals, color=cols, height=0.65)
    ax.set_title(title, loc="left", fontsize=8, color=INK2, pad=2)
    ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False)
    ax.grid(axis="x"); ax.set_axisbelow(True)
    for i, v in enumerate(vals):
        ax.text(v + max(vals) * 0.015, i, f"{int(v):,}", va="center", fontsize=6.5, color=INK2)
    ax.set_xlim(right=max(vals) * 1.22)
    fig.savefig(os.path.join(dataset_fig_dir(slug), fname)); plt.close(fig)
    return True


for slug in META:
    if slug not in stats:
        continue
    color = KIND_COLOR[META[slug][2]]
    small_bar(slug, "category_counts", "failure category / mode", "cat.pdf", color=color)
    small_bar(slug, "faulty_agent_counts", "labelled faulty agent / role", "agent.pdf", color=color)
    small_bar(slug, "source_benchmark_counts", "source benchmark", "bench.pdf", topk=8, color=color)
    small_bar(slug, "framework_counts", "agent framework", "fw.pdf", topk=8, color=color)

print("overview figures:", sorted(os.listdir(FIGS)))
print("dataset figure dirs:", sum(1 for s in META if os.path.isdir(os.path.join(REPORT, GROUP.get(s, ""), s, "figures"))))
