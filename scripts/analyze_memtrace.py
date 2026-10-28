"""Analyse MemTraceBench (zjunlp/MemTraceBench). Usage: python3 -I analyze_memtrace.py <data_root> <notes_dir> [example_selector]
Writes memtrace_stats.json and prints summary + candidate examples. The example_selector is '<split>/<file>::<query_id>'."""
import json, os, sys, glob, statistics, collections

root, notes = sys.argv[1], sys.argv[2]
selector = sys.argv[3] if len(sys.argv) > 3 else None
splits = ["rag", "mem0", "evermemos", "long_context"]

def backward_slice(pred_full_id, edges_by_target, max_nodes=200000):
    """Return set of op_ids and node ids that are ancestors of the prediction node."""
    seen_nodes, ops = set(), set()
    stack = [pred_full_id]
    while stack:
        nid = stack.pop()
        if nid in seen_nodes:
            continue
        seen_nodes.add(nid)
        for e in edges_by_target.get(nid, ()):
            ops.add(e["op_id"])
            s = e["source_full_node_id"]
            if s not in seen_nodes:
                stack.append(s)
        if len(seen_nodes) > max_nodes:
            break
    return ops, seen_nodes

per_graph = []
per_ann = []
example_payload = None
for sp in splits:
    for f in sorted(glob.glob(os.path.join(root, sp, "*.json"))):
        with open(f, encoding="utf-8") as fh:
            g = json.load(fh)
        D = g["data"]
        md = g.get("metadata", {})
        ops = D["operations"]
        ops_sorted = sorted(ops, key=lambda o: o["created_at"])
        op_index = {o["op_id"]: i for i, o in enumerate(ops_sorted)}
        op_by_id = {o["op_id"]: o for o in ops}
        opcat = collections.Counter(o.get("category") for o in ops)
        nodecat = collections.Counter(n.get("category") for n in D["nodes"])
        edges_by_target = collections.defaultdict(list)
        for e in D["edges"]:
            edges_by_target[e["target_full_node_id"]].append(e)
        node_by_id = {n["full_node_id"]: n for n in D["nodes"]}
        src_ds = md.get("memtracebench_dataset_source") or os.path.basename(f).split("_")[0]
        chars = sum(len(str(n.get("value", ""))) for n in D["nodes"])
        per_graph.append(dict(split=sp, file=os.path.basename(f), source=src_ds, n_nodes=len(D["nodes"]), n_edges=len(D["edges"]),
                              n_ops=len(ops), n_sessions=len(D["sessions"]), n_ann=len(D["annotations"]), op_categories=dict(opcat),
                              node_categories=dict(nodecat), chars=chars))
        for a in D["annotations"]:
            fo = a.get("final_op_id")
            o = op_by_id.get(fo)
            slice_ops, slice_nodes = backward_slice(a.get("prediction_id"), edges_by_target)
            slice_ops_sorted = sorted(slice_ops, key=lambda x: op_index.get(x, -1))
            pos_in_slice = slice_ops_sorted.index(fo) + 1 if fo in slice_ops else None
            rec = dict(split=sp, file=os.path.basename(f), source=src_ds, query_id=a.get("query_id"), error_type=a.get("final_error_type"),
                       final_op_id=fo, faulty_op_category=(o or {}).get("category"), faulty_op_name=(o or {}).get("op_name"),
                       faulty_op_pos_global=(op_index.get(fo, -1) + 1) if fo else None, n_ops_global=len(ops),
                       n_ops_slice=len(slice_ops), n_nodes_slice=len(slice_nodes), faulty_op_pos_slice=pos_in_slice,
                       slice_chars=sum(len(str(node_by_id.get(n, {}).get("value", ""))) for n in slice_nodes),
                       reason_len=len(a.get("reason") or ""))
            per_ann.append(rec)
            key = f"{sp}/{os.path.basename(f)}::{a.get('query_id')}"
            if selector and key == selector:
                # build example: steps = slice ops in chronological order
                steps = []
                edges_by_op = collections.defaultdict(list)
                for e in D["edges"]:
                    if e["op_id"] in slice_ops:
                        edges_by_op[e["op_id"]].append(e)
                for oid in slice_ops_sorted:
                    op = op_by_id[oid]
                    ins = sorted(set(e["source_full_node_id"] for e in edges_by_op[oid]))
                    outs = sorted(set(e["target_full_node_id"] for e in edges_by_op[oid]))
                    steps.append(dict(op_id=oid, op_name=op.get("op_name"), category=op.get("category"), comment=op.get("comment"),
                                      session_id=op.get("session_id"), created_at=op.get("created_at"), metadata=op.get("metadata"),
                                      inputs=[dict(id=i, category=node_by_id.get(i, {}).get("category"), name=node_by_id.get(i, {}).get("name"), value=node_by_id.get(i, {}).get("value")) for i in ins],
                                      outputs=[dict(id=i, category=node_by_id.get(i, {}).get("category"), name=node_by_id.get(i, {}).get("name"), value=node_by_id.get(i, {}).get("value")) for i in outs]))
                example_payload = dict(graph_file=f"{sp}/{os.path.basename(f)}", graph_id=g.get("graph_id"), metadata=md, annotation=a,
                                       graph_size=dict(nodes=len(D["nodes"]), edges=len(D["edges"]), operations=len(ops), sessions=len(D["sessions"])),
                                       prediction_backward_slice_steps=steps)
        print(f"{sp}/{os.path.basename(f)}: nodes={len(D['nodes'])} ops={len(ops)} ann={len(D['annotations'])}", file=sys.stderr)
        del g, D

def q(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return {}
    return dict(mean=round(statistics.mean(xs), 2), median=statistics.median(xs), min=xs[0], max=xs[-1])

mem_types = {"ExtractionError", "UpdateError", "DeletionError", "RetrievalError", "ResponseError"}
err_types = collections.Counter(a["error_type"] for a in per_ann)
sys_err = {sp: collections.Counter(a["error_type"] for a in per_ann if a["split"] == sp) for sp in splits}
src_cnt = collections.Counter(a["source"] for a in per_ann)
src_graph = collections.Counter(g["source"] for g in per_graph)
is_mem = lambda a: a["error_type"] in mem_types
mem_anns = [a for a in per_ann if is_mem(a)]
uniq_q = set(a["query_id"] for a in per_ann)
uniq_ann_err = set(a["query_id"] for a in per_ann if a["error_type"] == "AnnotationError")
summary = dict(
    n_graphs=len(per_graph), graphs_per_split=collections.Counter(g["split"] for g in per_graph), graphs_per_source=dict(src_graph),
    n_annotations=len(per_ann), n_unique_query_ids=len(uniq_q), n_unique_annotation_error_queries=len(uniq_ann_err),
    n_memory_system_failures=len(mem_anns), ann_per_split=collections.Counter(a["split"] for a in per_ann),
    mem_failures_per_split=collections.Counter(a["split"] for a in mem_anns),
    error_type_counts=dict(err_types), error_type_by_split={k: dict(v) for k, v in sys_err.items()},
    source_counts_ann=dict(src_cnt), source_counts_mem=dict(collections.Counter(a["source"] for a in mem_anns)),
    faulty_op_category_counts=dict(collections.Counter(a["faulty_op_category"] for a in mem_anns)),
    faulty_op_name_counts=dict(collections.Counter(a["faulty_op_name"] for a in mem_anns)),
    ops_per_graph=q([g["n_ops"] for g in per_graph]), nodes_per_graph=q([g["n_nodes"] for g in per_graph]), edges_per_graph=q([g["n_edges"] for g in per_graph]),
    chars_per_graph=q([g["chars"] for g in per_graph]),
    ops_per_graph_by_split={sp: q([g["n_ops"] for g in per_graph if g["split"] == sp]) for sp in splits},
    slice_ops_per_failure=q([a["n_ops_slice"] for a in mem_anns]), slice_ops_by_split={sp: q([a["n_ops_slice"] for a in mem_anns if a["split"] == sp]) for sp in splits},
    slice_chars_per_failure=q([a["slice_chars"] for a in mem_anns]),
    faulty_pos_rel_global=q([a["faulty_op_pos_global"] / a["n_ops_global"] for a in mem_anns if a["faulty_op_pos_global"]]),
    faulty_pos_rel_slice=q([a["faulty_op_pos_slice"] / a["n_ops_slice"] for a in mem_anns if a["faulty_op_pos_slice"]]),
    faulty_op_in_slice=sum(1 for a in mem_anns if a["faulty_op_pos_slice"]), reason_len=q([a["reason_len"] for a in per_ann]),
    op_category_totals=dict(sum((collections.Counter(g["op_categories"]) for g in per_graph), collections.Counter())),
)
print(json.dumps(summary, indent=1, default=dict))
stats = dict(
    n_trajectories=len(mem_anns), n_graphs=len(per_graph), n_annotations_total=len(per_ann),
    steps_per_traj=[a["n_ops_slice"] for a in mem_anns],
    steps_per_graph=[g["n_ops"] for g in per_graph],
    error_step_rel_pos=[a["faulty_op_pos_slice"] / a["n_ops_slice"] for a in mem_anns if a["faulty_op_pos_slice"]],
    error_step_rel_pos_global=[a["faulty_op_pos_global"] / a["n_ops_global"] for a in mem_anns if a["faulty_op_pos_global"]],
    agents_per_traj=[len(g["op_categories"]) for g in per_graph],
    faulty_agent_counts=dict(collections.Counter(a["faulty_op_category"] for a in mem_anns)),
    category_counts=dict(err_types), category_counts_memory_only=dict(collections.Counter(a["error_type"] for a in mem_anns)),
    source_benchmark_counts=dict(src_cnt),
    splits={sp: dict(graphs=sum(1 for g in per_graph if g["split"] == sp), annotations=sum(1 for a in per_ann if a["split"] == sp), memory_failures=sum(1 for a in mem_anns if a["split"] == sp)) for sp in splits},
    summary=json.loads(json.dumps(summary, default=dict)), per_graph=per_graph, per_annotation=per_ann,
)
with open(os.path.join(notes, "memtrace_stats.json"), "w") as fh:
    json.dump(stats, fh, indent=1)
if example_payload:
    with open(os.path.join(notes, "memtrace_example.json"), "w", encoding="utf-8") as fh:
        json.dump(example_payload, fh, indent=1, ensure_ascii=False)
    print("example written: steps", len(example_payload["prediction_backward_slice_steps"]))
print("\nCANDIDATES (memory failures, smallest slices):")
for a in sorted(mem_anns, key=lambda a: (a["n_ops_slice"], a["slice_chars"]))[:25]:
    print(a["split"], a["file"], a["query_id"], a["error_type"], a["faulty_op_category"], "slice_ops", a["n_ops_slice"], "chars", a["slice_chars"], "pos", a["faulty_op_pos_slice"])
