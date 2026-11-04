"""Visualise the bipartite execution-graph structure of MemTraceBench (zjunlp/MemTraceBench).

Usage: python3 -I visualize_memtrace.py <data_root> <out_dir> [--workers N]

MemTrace stores each run as variable-to-variable edges tagged with the operation that produced them.
We render the bipartite form  variable --(input)--> operation --(output)--> variable.
Variables that an operation both consumes and produces (intermediate prompts / responses inside one
call) are drawn as outputs only, which keeps the drawing acyclic.

Outputs (PNG, 200 dpi):
  schema_<system>.png          type-level bipartite graph over all graphs of one memory system
                               (variable category <-> operation name, edge width ~ log count)
  slice_<system>_<query>.png   instance-level bipartite DAG of one failed query: every operation and
                               variable in the backward slice of the prediction, x = chronological
                               operation order, one lane per variable category / operation name;
                               faulty operation and gold-evidence messages are marked
  example_mem0_f8c5f88b.png    the report's worked example, labelled with memory-unit texts
  schema_counts.json           cached type-level counts (re-used on later runs)
"""
import json, os, sys, glob, math, collections, textwrap
from concurrent.futures import ProcessPoolExecutor

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from matplotlib.lines import Line2D
import networkx as nx

SPLITS = ["rag", "mem0", "evermemos", "long_context"]
SYSTEM_NAME = {"rag": "Naive RAG", "mem0": "Mem0", "evermemos": "EverMemOS", "long_context": "Long-Context"}
MEMORY_ERRORS = {"ExtractionError", "UpdateError", "DeletionError", "RetrievalError", "ResponseError"}

# Fixed categorical order (validated default palette, slots 1-6); one hue per operation category.
OP_COLOR = {
    "extraction": "#2a78d6",          # blue
    "update": "#eb6834",              # orange
    "retrieval": "#1baf7a",           # aqua
    "evaluation": "#eda100",          # yellow
    "boundary_detection": "#e87ba4",  # magenta
    "initialization": "#008300",      # green
}
OP_COLOR_DEFAULT = "#6250d6"
VAR_FILL, VAR_EDGE = "#e4e3dc", "#7a7970"
INK, INK2, MUTED, GRID = "#1f1f1e", "#52514b", "#8a897f", "#ecebe6"
MARK = "#1f1f1e"  # faulty-op ring: ink, not a series hue (identity carried by the text label)
EVID = "#6250d6"  # gold-evidence ring (violet, slot 7, not used by any op category)

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": "white", "axes.facecolor": "white"})


# ----------------------------------------------------------------------------- graph helpers
def op_io(edges):
    """Group edges per op -> (inputs, outputs). Inputs exclude variables the op itself produced."""
    ins, outs = collections.defaultdict(set), collections.defaultdict(set)
    for e in edges:
        ins[e["op_id"]].add(e["source_full_node_id"])
        outs[e["op_id"]].add(e["target_full_node_id"])
    return {o: (ins[o] - outs[o], outs[o]) for o in outs}


def backward_slice(pred, edges_by_target):
    seen, ops, stack = set(), set(), [pred]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        for e in edges_by_target.get(n, ()):
            ops.add(e["op_id"])
            stack.append(e["source_full_node_id"])
    return ops, seen


def schema_counts_for_file(path):
    """Type-level bipartite edge counts for one graph file."""
    with open(path, encoding="utf-8") as fh:
        D = json.load(fh)["data"]
    ncat = {n["full_node_id"]: n.get("category") or "?" for n in D["nodes"]}
    ops = {o["op_id"]: o for o in D["operations"]}
    cnt = collections.Counter()
    opcat = {}
    for oid, (ins, outs) in op_io(D["edges"]).items():
        name = ops.get(oid, {}).get("op_name", "?")
        opcat[name] = ops.get(oid, {}).get("category", "?")
        for v in ins:
            cnt[("v:" + ncat.get(v, "?"), "o:" + name)] += 1
        for v in outs:
            cnt[("o:" + name, "v:" + ncat.get(v, "?"))] += 1
    opn = collections.Counter("o:" + ops[o].get("op_name", "?") for o in ops)
    varn = collections.Counter("v:" + c for c in ncat.values())
    return {"edges": [[a, b, c] for (a, b), c in cnt.items()], "opcat": opcat,
            "nodes": dict(opn + varn)}


def build_schema(root, out_dir, workers):
    cache = os.path.join(out_dir, "schema_counts.json")
    if os.path.exists(cache):
        with open(cache) as fh:
            return json.load(fh)
    res = {}
    for sp in SPLITS:
        files = sorted(glob.glob(os.path.join(root, sp, "*.json")))
        with ProcessPoolExecutor(max_workers=min(workers, len(files))) as ex:
            parts = list(ex.map(schema_counts_for_file, files))
        E, N, C = collections.Counter(), collections.Counter(), {}
        for p in parts:
            for a, b, c in p["edges"]:
                E[(a, b)] += c
            N.update(p["nodes"])
            C.update(p["opcat"])
        res[sp] = {"edges": [[a, b, c] for (a, b), c in E.items()], "nodes": dict(N), "opcat": C,
                   "n_graphs": len(files)}
        print(f"schema {sp}: {len(files)} graphs, {len(N)} types, {len(E)} type edges", flush=True)
    with open(cache, "w") as fh:
        json.dump(res, fh, indent=1)
    return res


# ----------------------------------------------------------------------------- layered layout
def layered_layout(G, roots_first=None):
    """Sugiyama-lite: break cycles by DFS, longest-path layers, barycenter ordering. Returns
    (layer_of, order_in_layer, back_edges)."""
    order = sorted(G.nodes, key=lambda n: (G.in_degree(n) > 0, roots_first(n) if roots_first else 0, n))
    color, back = {}, set()

    def dfs(u):
        color[u] = 1
        for v in sorted(G.successors(u)):
            if color.get(v) == 1:
                back.add((u, v))
            elif v not in color:
                dfs(v)
        color[u] = 2

    sys.setrecursionlimit(10000)
    for n in order:
        if n not in color:
            dfs(n)
    H = nx.DiGraph()
    H.add_nodes_from(G.nodes)
    H.add_edges_from(e for e in G.edges if e not in back and e[0] != e[1])
    layer = {}
    for n in nx.topological_sort(H):
        preds = list(H.predecessors(n))
        layer[n] = 1 + max((layer[p] for p in preds), default=-1)
    L = collections.defaultdict(list)
    for n, l in layer.items():
        L[l].append(n)
    pos = {}
    for l in sorted(L):
        L[l].sort(key=lambda n: (n[0], n))
        for i, n in enumerate(L[l]):
            pos[n] = i
    for _ in range(8):  # barycenter sweeps down and up
        for l in sorted(L)[1:]:
            L[l].sort(key=lambda n: (sum(pos[p] for p in H.predecessors(n)) / max(1, H.in_degree(n))
                                     if H.in_degree(n) else pos[n]))
            for i, n in enumerate(L[l]):
                pos[n] = i
        for l in sorted(L, reverse=True)[1:]:
            L[l].sort(key=lambda n: (sum(pos[s] for s in H.successors(n)) / max(1, H.out_degree(n))
                                     if H.out_degree(n) else pos[n]))
            for i, n in enumerate(L[l]):
                pos[n] = i
    return layer, pos, L, back


def short_op(name):
    return name.replace("memory_system.", "").replace("evermemos.", "")


# ----------------------------------------------------------------------------- schema figure
def draw_schema(sp, S, out_dir):
    G = nx.DiGraph()
    for a, b, c in S["edges"]:
        G.add_edge(a, b, w=c)
    layer, pos, L, back = layered_layout(G, roots_first=lambda n: n != "v:message")
    nlay = max(L) + 1
    height = max(len(v) for v in L.values())
    fig_w = max(10, 2.15 * nlay + 1.5)
    fig_h = max(4.5, 1.25 * height + 2.2)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    xy = {}
    for l, ns in L.items():
        off = (height - len(ns)) / 2
        for i, n in enumerate(ns):
            xy[n] = (l * 2.0, -(off + i) * 1.35)
    maxw = max(c for _, _, c in S["edges"])
    for a, b, c in sorted(S["edges"], key=lambda t: t[2]):
        lw = 0.6 + 3.4 * math.log1p(c) / math.log1p(maxw)
        isback = (a, b) in back
        rad = 0.35 if isback else 0.0
        arr = FancyArrowPatch(xy[a], xy[b], arrowstyle="-|>", mutation_scale=9, lw=lw,
                              color=MUTED if not isback else "#b5b4ab", alpha=0.75,
                              linestyle="--" if isback else "-",
                              connectionstyle=f"arc3,rad={rad}", shrinkA=11, shrinkB=11, zorder=1)
        ax.add_patch(arr)
        if not isback and len(S["edges"]) <= 30:
            mx, my = (xy[a][0] + xy[b][0]) / 2, (xy[a][1] + xy[b][1]) / 2
            ax.text(mx, my + 0.09, f"{c:,}", fontsize=6.5, color=INK2, ha="center", va="bottom", zorder=4,
                    bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))
    for n, (x, y) in xy.items():
        if n.startswith("o:"):
            name = n[2:]
            col = OP_COLOR.get(S["opcat"].get(name), OP_COLOR_DEFAULT)
            ax.scatter([x], [y], s=260, marker="s", c=col, edgecolors="white", linewidths=2, zorder=3)
            ax.text(x, y - 0.27, short_op(name), ha="center", va="top", fontsize=7.6, color=INK,
                    fontweight="bold", zorder=5)
            ax.text(x, y - 0.5, f"×{S['nodes'].get(n, 0):,}", ha="center", va="top", fontsize=6.5,
                    color=MUTED, zorder=5)
        else:
            ax.scatter([x], [y], s=200, marker="o", c=VAR_FILL, edgecolors=VAR_EDGE, linewidths=1.2, zorder=3)
            ax.text(x, y - 0.27, n[2:], ha="center", va="top", fontsize=7.6, color=INK, style="italic", zorder=5)
            ax.text(x, y - 0.5, f"×{S['nodes'].get(n, 0):,}", ha="center", va="top", fontsize=6.5,
                    color=MUTED, zorder=5)
    xs = [p[0] for p in xy.values()]
    ys = [p[1] for p in xy.values()]
    ax.set_xlim(min(xs) - 1.1, max(xs) + 1.1)
    ax.set_ylim(min(ys) - 0.9, max(ys) + 0.6)
    ax.axis("off")
    cats = sorted({S["opcat"].get(n[2:]) for n in G.nodes if n.startswith("o:")},
                  key=lambda c: list(OP_COLOR).index(c) if c in OP_COLOR else 99)
    handles = [Line2D([], [], marker="o", ls="", mfc=VAR_FILL, mec=VAR_EDGE, ms=9, label="variable node (category)")]
    handles += [Line2D([], [], marker="s", ls="", mfc=OP_COLOR.get(c, OP_COLOR_DEFAULT), mec="white", ms=10,
                       label=f"operation: {c}") for c in cats]
    handles += [Line2D([], [], color=MUTED, lw=2, label="information flow (width ~ log edge count)"),
                Line2D([], [], color="#b5b4ab", lw=1.5, ls="--", label="edge drawn backwards (same variable type reused at an earlier stage)")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=min(4, len(handles)),
              frameon=False, fontsize=8)
    ax.set_title(f"MemTrace execution-graph schema: {SYSTEM_NAME[sp]}  "
                 f"({S['n_graphs']} graphs; nodes = variable categories and operation names, ×n = instances, "
                 f"edge labels = instance edges)", loc="left", fontsize=11, color=INK, fontweight="bold")
    fig.tight_layout()
    p = os.path.join(out_dir, f"schema_{sp}.png")
    fig.savefig(p, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", p, flush=True)
    return layer, pos


# ----------------------------------------------------------------------------- slice figure
def snippet(val, n=48):
    s = val if isinstance(val, str) else json.dumps(val)
    try:
        j = json.loads(s)
        if isinstance(j, dict):
            s = j.get("memory") or j.get("content") or j.get("text") or s
    except Exception:
        pass
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 1] + "…"


def load_slice(path, qid):
    with open(path, encoding="utf-8") as fh:
        D = json.load(fh)["data"]
    ann = next(a for a in D["annotations"] if a["query_id"] == qid)
    by_t = collections.defaultdict(list)
    for e in D["edges"]:
        by_t[e["target_full_node_id"]].append(e)
    sops, snodes = backward_slice(ann["prediction_id"], by_t)
    edges = [e for e in D["edges"] if e["op_id"] in sops and e["target_full_node_id"] in snodes]
    ops = {o["op_id"]: o for o in D["operations"] if o["op_id"] in sops}
    nodes = {n["full_node_id"]: n for n in D["nodes"] if n["full_node_id"] in snodes}
    faulty = next((o for o in D["operations"] if o["op_id"] == ann.get("final_op_id")), None)
    return ann, ops, nodes, edges, faulty


def draw_slice(sp, path, qid, schema_layer, schema_pos, out_dir, fname, labelled=False):
    ann, ops, nodes, edges, faulty = load_slice(path, qid)
    io = op_io(edges)
    rank = {o: i for i, o in enumerate(sorted(ops, key=lambda o: (ops[o]["created_at"], o)))}
    producer = {}
    for o, (ins, outs) in io.items():  # earliest producer (retrieval re-emits stored memory units)
        for v in outs:
            if v not in producer or rank[o] < rank[producer[v]]:
                producer[v] = o
    consumers = collections.defaultdict(list)
    for o, (ins, outs) in io.items():
        for v in ins:
            consumers[v].append(o)

    def vtype(v):
        return "v:" + (nodes.get(v, {}).get("category") or "?")

    def otype(o):
        return "o:" + ops[o]["op_name"]

    # x positions first, then lanes ordered by first appearance (pipeline reads top to bottom)
    xpos, kind = {}, {}
    for o in ops:
        xpos[("o", o)] = rank[o]
    for v in nodes:
        if v in producer:
            xpos[("v", v)] = rank[producer[v]] + 0.38
        elif consumers.get(v):
            xpos[("v", v)] = min(rank[c] for c in consumers[v]) - 0.38
    tof = {k: (otype(k[1]) if k[0] == "o" else vtype(k[1])) for k in xpos}
    first = collections.defaultdict(lambda: 1e9)
    for k, x in xpos.items():
        first[tof[k]] = min(first[tof[k]], x)
    lanes = sorted(first, key=lambda t: (round(first[t], 2), schema_layer.get(t, 99), schema_pos.get(t, 0), t))
    lane_y = {t: -i for i, t in enumerate(lanes)}
    # spread variables that share (x, lane) inside the lane band
    groups = collections.defaultdict(list)
    for k, x in xpos.items():
        groups[(round(x, 3), tof[k])].append(k)
    xy = {}
    for (x, t), ks in groups.items():
        ks.sort(key=lambda k: k[1])
        n = len(ks)
        for j, k in enumerate(ks):
            dy = 0.0 if n == 1 else 0.34 * (2 * j / (n - 1) - 1)
            xy[k] = (xpos[k], lane_y[t] + dy)
    nops = len(ops)
    big = nops > 60
    span = nops + 1
    fig_h = max(4.2, 0.42 * len(lanes) + 2.4) if not labelled else max(6.5, 0.62 * len(lanes) + 2.6)
    if labelled:
        fig = plt.figure(figsize=(17, fig_h))
        gsp = fig.add_gridspec(1, 2, width_ratios=[2.15, 1], wspace=0.02)
        ax, axl = fig.add_subplot(gsp[0]), fig.add_subplot(gsp[1])
    else:
        fig, ax = plt.subplots(figsize=(13 if not big else 16, fig_h))
    for t, y in lane_y.items():
        ax.axhline(y, color=GRID, lw=(14 if labelled else 6) if not big else 4, zorder=0, solid_capstyle="butt")
    lw, al = (0.7, 0.55) if not big else (0.25, 0.35)
    for o, (ins, outs) in io.items():
        ox, oy = xy[("o", o)]
        for v in list(ins) + list(outs):
            if ("v", v) in xy:
                vx, vy = xy[("v", v)]
                ax.plot([vx, ox], [vy, oy], color=MUTED, lw=lw, alpha=al, zorder=1)
    vs = [k for k in xy if k[0] == "v"]
    os_ = [k for k in xy if k[0] == "o"]
    ms_v, ms_o = (34, 60) if not big else (7, 12)
    ax.scatter([xy[k][0] for k in vs], [xy[k][1] for k in vs], s=ms_v, marker="o", c=VAR_FILL,
               edgecolors=VAR_EDGE, linewidths=0.6 if not big else 0.3, zorder=2)
    ax.scatter([xy[k][0] for k in os_], [xy[k][1] for k in os_], s=ms_o, marker="s",
               c=[OP_COLOR.get(ops[k[1]].get("category"), OP_COLOR_DEFAULT) for k in os_],
               edgecolors="white", linewidths=0.6 if not big else 0.2, zorder=3)
    ytop = 0.7
    ev = [("v", v) for v in ann.get("source_evidence_ids") or [] if ("v", v) in xy]
    for k in ev:
        ax.scatter(*xy[k], s=ms_v * 6 if not big else 160, facecolors="none", edgecolors=EVID, linewidths=1.8, zorder=4)
    fo = ann.get("final_op_id")
    fault_note = ""
    if ("o", fo) in xy:
        fx, fy = xy[("o", fo)]
        ax.scatter([fx], [fy], s=ms_o * 6 if not big else 260, facecolors="none", edgecolors=MARK, linewidths=2.2, zorder=5)
        ax.annotate(f"annotated faulty op: {short_op(faulty['op_name'])} ({ann['final_error_type']})",
                    xy=(fx, fy), xytext=(fx - 0.05 * span, fy + 0.62), fontsize=8.5, color=INK,
                    ha="right", va="bottom", arrowprops=dict(arrowstyle="-|>", color=INK, lw=1), zorder=6,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.9))
        ytop = max(ytop, fy + 1.1)
    else:
        fault_note = (f"  [faulty op {short_op(faulty['op_name']) if faulty else '?'} lies outside the slice: "
                      f"its output never reaches the answer]")
    if ev:
        ex, ey = xy[ev[0]]
        ax.annotate("gold evidence message", xy=(ex, ey), xytext=(ex + 0.04 * span, ey - 0.62),
                    fontsize=8.5, color=EVID, ha="left", va="top",
                    arrowprops=dict(arrowstyle="-|>", color=EVID, lw=1), zorder=6,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.9))
    if labelled:
        fin, fout = io.get(fo, (set(), set()))
        mem = sorted([k for k in vs if nodes[k[1]].get("category") == "memory_entry"], key=lambda k: (xy[k][0], -xy[k][1]))
        lines = []
        for i, k in enumerate(mem, 1):
            x, y = xy[k]
            ax.text(x + 0.12, y, f"M{i}", fontsize=7, color=INK, va="center", ha="left", zorder=6, fontweight="bold")
            role = []
            if k[1] in fin:
                role.append("input to faulty op")
            if k[1] in fout:
                role.append("output of faulty op")
            if any(k[1] in io[o][0] for o in io if ops[o]["op_name"] == "question-answering"):
                role.append("in answer context")
            lines.append((f"M{i}", snippet(nodes[k[1]].get("value"), 62), ", ".join(role)))
        axl.axis("off")
        axl.text(0, 1.0, "Memory units in the slice (M = memory_entry node)", fontsize=9.5, fontweight="bold",
                 color=INK, va="top", transform=axl.transAxes)
        step = min(0.06, 0.92 / max(1, len(lines)))
        for i, (m, txt, role) in enumerate(lines):
            y = 0.95 - i * step
            hot = "faulty" in role
            axl.text(0, y, m, fontsize=8, fontweight="bold", color=INK, va="top", transform=axl.transAxes)
            axl.text(0.07, y, txt, fontsize=8, color=INK if hot else INK2, va="top", transform=axl.transAxes,
                     fontweight="bold" if hot else "normal")
            if role:
                axl.text(0.07, y - step * 0.45, role, fontsize=7, color=MUTED, style="italic", va="top",
                         transform=axl.transAxes)
    ax.set_yticks(list(lane_y.values()))
    labels = []
    for t in lane_y:
        if t.startswith("o:"):
            cat = next((ops[o].get("category") for o in ops if otype(o) == t), None)
            labels.append(f"{short_op(t[2:])}  [{cat}]")
        else:
            labels.append(t[2:])
    ax.set_yticklabels(labels, fontsize=8)
    for lab, t in zip(ax.get_yticklabels(), lane_y):
        lab.set_fontweight("bold" if t.startswith("o:") else "normal")
        lab.set_style("normal" if t.startswith("o:") else "italic")
        lab.set_color(INK if t.startswith("o:") else INK2)
    if not big:
        ax.set_xticks(range(nops))
        ax.set_xticklabels([str(i + 1) for i in range(nops)], fontsize=7.5)
    else:
        from matplotlib.ticker import FuncFormatter
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(round(v)) + 1}"))
    ax.set_xlim(-1, nops + 0.2)
    ax.set_ylim(min(lane_y.values()) - 0.7, ytop)
    ax.set_xlabel("operation order in the slice (chronological, 1-based; each variable sits just right of the "
                  "operation that produced it)")
    for s_ in ("top", "right", "left"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="y", length=0)
    pred = snippet(nodes.get(ann["prediction_id"], {}).get("value", ann.get("prediction", "")), 120)
    gold = ann.get("golden_answers")
    gold = gold[0] if isinstance(gold, list) and gold else gold
    title = (f"{SYSTEM_NAME[sp]}: bipartite backward slice of one failed answer  "
             f"({nops} operations, {len(nodes)} variables){fault_note}")
    sub = (f"Q: {snippet(ann['query'], 100)}    gold: {snippet(str(gold), 60)}\n"
           f"prediction: {pred}\nsource: {sp}/{os.path.basename(path)} :: {qid}")
    ax.annotate(title, xy=(0, 1), xycoords="axes fraction", xytext=(0, 48), textcoords="offset points",
                fontsize=11, color=INK, fontweight="bold", va="bottom", ha="left")
    ax.annotate(sub, xy=(0, 1), xycoords="axes fraction", xytext=(0, 8), textcoords="offset points",
                fontsize=7.8, color=INK2, va="bottom", ha="left")
    cats = sorted({ops[o].get("category") for o in ops}, key=lambda c: list(OP_COLOR).index(c) if c in OP_COLOR else 99)
    handles = [Line2D([], [], marker="o", ls="", mfc=VAR_FILL, mec=VAR_EDGE, ms=7, label="variable node")]
    handles += [Line2D([], [], marker="s", ls="", mfc=OP_COLOR.get(c, OP_COLOR_DEFAULT), mec="white", ms=8,
                       label=f"operation: {c}") for c in cats]
    handles += [Line2D([], [], marker="o", ls="", mfc="none", mec=MARK, mew=2, ms=11, label="annotated faulty operation"),
                Line2D([], [], marker="o", ls="", mfc="none", mec=EVID, mew=2, ms=11, label="gold evidence message")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=min(4, len(handles)),
              frameon=False, fontsize=8)
    p = os.path.join(out_dir, fname)
    fig.savefig(p, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", p, flush=True)


# ----------------------------------------------------------------------------- main
SLICES = {  # smallest memory-failure slice per system whose faulty op lies inside the slice
    "rag": ("longmemeval_longmemeval-6613b389.json", "query:6613b389@1"),
    "mem0": ("longmemeval_longmemeval-2ce6a0f2.json", "query:2ce6a0f2@1"),
    "evermemos": ("longmemeval_longmemeval-ef66a6e5.json", "query:ef66a6e5@1"),
    "long_context": ("longmemeval_longmemeval-5a7937c8.json", "query:5a7937c8@1"),
}
EXAMPLE = ("mem0", "longmemeval_longmemeval-f8c5f88b.json", "query:f8c5f88b@1")


def main():
    root, out_dir = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 16
    os.makedirs(out_dir, exist_ok=True)
    schema = build_schema(root, out_dir, workers)
    lay = {}
    for sp in SPLITS:
        lay[sp] = draw_schema(sp, schema[sp], out_dir)
    for sp, (f, q) in SLICES.items():
        draw_slice(sp, os.path.join(root, sp, f), q, *lay[sp], out_dir,
                   f"slice_{sp}_{q.split(':')[1].split('@')[0]}.png")
    sp, f, q = EXAMPLE
    draw_slice(sp, os.path.join(root, sp, f), q, *lay[sp], out_dir,
               "example_mem0_f8c5f88b.png", labelled=True)


if __name__ == "__main__":
    main()
