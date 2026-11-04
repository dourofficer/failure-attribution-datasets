"""MemTraceBench (zjunlp/MemTraceBench): data/memtrace/{rag,mem0,evermemos,long_context}/<source>_<conv>.json, one
serialised execution graph per (memory system, conversation) (40-530 MB each; files are loaded one at a time and
released). One record per annotation (data.annotations[]) whose final_error_type is a memory-system failure
(ExtractionError / UpdateError / DeletionError / RetrievalError / ResponseError); other annotations (AnnotationError, ...)
are skipped unless all_types=True. The trajectory = operations in the backward dependency slice of the annotation's
prediction node (through edges, target -> source), ordered chronologically by created_at. Step content = op_name,
category, description, and the op's input / output variables (each value truncated to 10k chars; prompt templates
are summarised). native_step = op_id. labels.error_steps = [index of final_op_id in the slice] or [] when the faulty
operation is not in the slice (meta['op_in_slice'] = False). load(systems=['mem0','rag']) restricts the systems."""
import collections
import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # for python3 -I
from common.schema import make_record, make_step
from common.util import DATA

ROOT = os.path.join(DATA, 'memtrace')
SYSTEMS = ('rag', 'mem0', 'evermemos', 'long_context')
MEMORY_ERRORS = {'ExtractionError', 'UpdateError', 'DeletionError', 'RetrievalError', 'ResponseError'}
VALUE_LIMIT = 10000
AGENT_CATS = {'extraction', 'update', 'retrieval', 'evaluation', 'response', 'deletion'}


def backward_slice(pred, edges_by_target, max_nodes=500000):
    seen, ops, stack = set(), set(), [pred]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        for e in edges_by_target.get(n, ()):
            ops.add(e['op_id'])
            s = e['source_full_node_id']
            if s not in seen:
                stack.append(s)
        if len(seen) > max_nodes:
            break
    return ops, seen


def val(v, lim=VALUE_LIMIT):
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return s if len(s) <= lim else s[:lim] + f' […{len(s) - lim} more chars]'


def render_op(op, ins, outs, node_by_id):
    lines = [f"Operation: {op.get('op_name')} [{op.get('category')}] (op_id {op.get('op_id')}, session {op.get('session_id')}, {op.get('created_at')})"]
    if op.get('comment'):
        lines.append('Description: ' + str(op['comment']).strip())
    for title, ids in (('Inputs', ins), ('Outputs', outs)):
        rows = []
        for nid in ids:
            n = node_by_id.get(nid, {})
            cat = n.get('category')
            if cat == 'prompt':
                rows.append(f"  - [{cat}] {n.get('name')} (prompt template, {len(str(n.get('value', '')))} chars, omitted)")
            else:
                rows.append(f"  - [{cat}] {n.get('name')}: {val(n.get('value', ''))}")
        lines.append(f'{title}:\n' + ('\n'.join(rows) if rows else '  (none)'))
    return '\n'.join(lines)


def _graph_files(systems):
    out = []
    for sp in systems:
        out += sorted(glob.glob(os.path.join(ROOT, sp, '*.json')))
    return out


def load(limit=None, systems=SYSTEMS, all_types=False, files=None):
    recs = []
    for f in files or _graph_files(systems):
        sp = os.path.basename(os.path.dirname(f))
        with open(f, encoding='utf-8') as fh:
            g = json.load(fh)
        D = g['data']
        md = g.get('metadata') or {}
        ops_sorted = sorted(D['operations'], key=lambda o: o['created_at'])
        op_index = {o['op_id']: i for i, o in enumerate(ops_sorted)}
        op_by_id = {o['op_id']: o for o in D['operations']}
        node_by_id = {n['full_node_id']: n for n in D['nodes']}
        edges_by_target = collections.defaultdict(list)
        edges_by_op = collections.defaultdict(list)
        for e in D['edges']:
            edges_by_target[e['target_full_node_id']].append(e)
            edges_by_op[e['op_id']].append(e)
        src = md.get('memtracebench_dataset_source') or os.path.basename(f).split('_')[0]
        for a in D['annotations']:
            et = a.get('final_error_type')
            if not all_types and et not in MEMORY_ERRORS:
                continue
            fo = a.get('final_op_id')
            slice_ops, slice_nodes = backward_slice(a.get('prediction_id'), edges_by_target)
            order = sorted(slice_ops, key=lambda x: op_index.get(x, -1))
            steps = []
            for i, oid in enumerate(order):
                op = op_by_id.get(oid, {'op_id': oid})
                ins = sorted({e['source_full_node_id'] for e in edges_by_op[oid]})
                outs = sorted({e['target_full_node_id'] for e in edges_by_op[oid]})
                ins = [x for x in ins if x not in set(outs)]
                cat = op.get('category') or 'op'
                steps.append(make_step(i, cat, 'agent' if cat in AGENT_CATS else 'env', render_op(op, ins, outs, node_by_id),
                                       native_step=oid, meta={'op_name': op.get('op_name'), 'category': cat, 'session_id': op.get('session_id'),
                                                              'created_at': op.get('created_at'), 'global_op_pos': op_index.get(oid),
                                                              'n_inputs': len(ins), 'n_outputs': len(outs)}))
            fidx = order.index(fo) if fo in slice_ops else None
            fop = op_by_id.get(fo) or {}
            recs.append(make_record('memtrace', f"{sp}/{os.path.basename(f)}::{a.get('query_id')}", a.get('query'), steps, subset=sp,
                                    ground_truth=json.dumps(a.get('golden_answers'), ensure_ascii=False) if not isinstance(a.get('golden_answers'), str) else a.get('golden_answers'),
                                    final_output=a.get('prediction'), outcome='fail', error_steps=[fidx] if fidx is not None else [],
                                    error_agent=fop.get('category'), categories=[et] if et else [], reason=a.get('reason'),
                                    extra={'final_op_id': fo, 'final_op_name': fop.get('op_name'), 'final_op_global_pos': op_index.get(fo),
                                           'query_id': a.get('query_id'), 'prediction_id': a.get('prediction_id'),
                                           'source_evidence': a.get('source_evidence'), 'source_evidence_ids': a.get('source_evidence_ids'),
                                           'golden_answers': a.get('golden_answers')},
                                    meta={'file': f, 'framework': sp, 'memory_system': md.get('memtracebench_system') or sp, 'benchmark': src,
                                          'op_in_slice': fidx is not None, 'graph_id': g.get('graph_id'),
                                          'graph_size': {'nodes': len(D['nodes']), 'edges': len(D['edges']), 'operations': len(D['operations']),
                                                         'sessions': len(D['sessions']), 'annotations': len(D['annotations'])},
                                          'slice_size': {'operations': len(slice_ops), 'nodes': len(slice_nodes)}}))
            if limit and len(recs) >= limit:
                del g, D
                return recs
        del g, D, node_by_id, edges_by_target, edges_by_op
    return recs


if __name__ == '__main__':
    systems = sys.argv[1].split(',') if len(sys.argv) > 1 else SYSTEMS
    rs = load(systems=systems)
    from collections import Counter
    print(len(rs), 'records;', sum(len(r['steps']) for r in rs), 'steps;', sum(1 for r in rs if r['labels']['error_steps']), 'with error_steps')
    print(Counter(r['subset'] for r in rs), Counter(r['labels']['categories'][0] for r in rs))
    print('op_in_slice', Counter(r['meta']['op_in_slice'] for r in rs))
    r = rs[0]
    print(r['id'], r['labels']['error_steps'], r['labels']['error_agent'], len(r['steps']), r['meta']['slice_size'])
