#!/usr/bin/env python3
"""Analyse TrajErrBench (TrajDebug repo). Usage: python3 -I analyze_trajerrbench.py"""
import collections
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

SLUG = 'trajerrbench'
R = os.path.join(C.DATA, SLUG, 'repo_TrajDebug', 'data', 'trajerrbench')

recs = {}
ann_keys = collections.Counter()
for lang in ('en', 'zh'):
    for sub in ('tau2bench', 'swebenchpro'):
        for p in sorted(glob.glob(os.path.join(R, lang, sub, '*.json'))):
            d = json.load(open(p, encoding='utf-8'))
            md = d['metadata']
            ann = md['annotation']
            ann_keys.update(ann.keys())
            msgs = d['messages']
            k = ann['critical_error_step']
            names = collections.Counter((m['role'], m.get('name')) for m in msgs)
            chars = sum(len(m.get('content') or '') for m in msgs)
            tid = md['task_id']
            m = re.match(r'(airline|retail|telecom)?_?failed_([^:]+)::', tid)
            if sub == 'tau2bench':
                dom = tid.split('_failed_')[0]
                model = tid.split('_failed_')[1].split('::')[0]
            else:
                dom, model = 'swe', tid.split('_instance_')[0]
            recs[(lang, sub, tid)] = dict(lang=lang, sub=sub, tid=tid, file=os.path.relpath(p, R), n_msg=len(msgs),
                                          n_assist=sum(1 for x in msgs if x['role'] == 'assistant'),
                                          n_tool=sum(1 for x in msgs if x['role'] == 'tool'),
                                          n_user=sum(1 for x in msgs if x['role'] == 'user'),
                                          k=k, rel=(k / (len(msgs) - 1)) if k is not None and len(msgs) > 1 else None,
                                          etype=ann.get('critical_error_type'), module=(ann.get('critical_error_type') or 'None').split('.')[0],
                                          reward=md['reward'], chars=chars, dom=dom, model=model,
                                          crit_role=msgs[k]['role'] if k is not None else None,
                                          crit_name=msgs[k].get('name') if k is not None else None,
                                          names=dict(names), extra_keys=sorted(md.get('extra', {}).keys()),
                                          rationale=ann.get('human_rationale'))
print('loaded', len(recs), 'annotation keys', ann_keys)
en = [r for r in recs.values() if r['lang'] == 'en']
zh = [r for r in recs.values() if r['lang'] == 'zh']
# consistency en vs zh
mism = 0
for r in en:
    z = recs.get(('zh', r['sub'], r['tid']))
    if z and (z['k'] != r['k'] or z['etype'] != r['etype'] or z['n_msg'] != r['n_msg']):
        mism += 1
print('en records', len(en), 'zh', len(zh), 'en/zh label or length mismatches', mism)
print('extra keys', collections.Counter(tuple(r['extra_keys']) for r in en))
print('swe model sample', [r['model'] for r in en if r['sub'] == 'swebenchpro'][:5])
print('crit roles', collections.Counter(r['crit_role'] for r in en), collections.Counter(r['crit_name'] for r in en))
print('rewards', collections.Counter(r['reward'] for r in en))

# swe model: try to find from extra
sample_swe = next(r for r in en if r['sub'] == 'swebenchpro')
print('sample swe tid', sample_swe['tid'], sample_swe['extra_keys'])

by_sub = collections.defaultdict(list)
for r in en:
    by_sub[r['sub']].append(r)

stats = {
    'n_trajectories': len(en), 'n_failed': sum(1 for r in en if r['reward'] == 0), 'n_success': sum(1 for r in en if r['reward'] == 1),
    'edition_note': 'statistics computed on the English (en) edition; the zh edition is a 1:1 pair with identical labels and lengths (mismatches: %d)' % mism,
    'steps_per_traj': [r['n_msg'] for r in en],
    'assistant_steps_per_traj': [r['n_assist'] for r in en],
    'error_step_rel_pos': [round(r['rel'], 4) for r in en if r['rel'] is not None],
    'error_step_abs': [r['k'] for r in en],
    'agents_per_traj': [1] * len(en),
    'faulty_agent_counts': dict(collections.Counter(f"{r['crit_role']}" + (f" ({r['crit_name']})" if r['crit_name'] else '') for r in en)),
    'category_counts': dict(collections.Counter(str(r['etype']) for r in en)),
    'module_counts': dict(collections.Counter(r['module'] for r in en)),
    'source_benchmark_counts': dict(collections.Counter(r['sub'] for r in en)),
    'domain_counts': dict(collections.Counter(f"{r['sub']}/{r['dom']}" for r in en)),
    'model_counts': dict(collections.Counter(f"{r['sub']}/{r['model']}" for r in en)),
    'chars_per_traj': [r['chars'] for r in en],
    'role_counts_total': dict(sum((collections.Counter({f'{k[0]}' + (f'({k[1]})' if k[1] else ''): v for k, v in r['names'].items()}) for r in en), collections.Counter())),
    'splits': {'en/tau2bench': len(by_sub['tau2bench']), 'en/swebenchpro': len(by_sub['swebenchpro']),
               'zh/tau2bench': sum(1 for r in zh if r['sub'] == 'tau2bench'), 'zh/swebenchpro': sum(1 for r in zh if r['sub'] == 'swebenchpro')},
    'per_subset': {s: {'steps_per_traj': [r['n_msg'] for r in v], 'error_step_rel_pos': [round(r['rel'], 4) for r in v],
                       'category_counts': dict(collections.Counter(str(r['etype']) for r in v))} for s, v in by_sub.items()},
}
C.write_json(os.path.join(C.NOTES, f'{SLUG}_stats.json'), stats)

L = []
L.append(C.md_table(C.SUMM_HEADERS, [
    C.summ_row('messages per trajectory (all, en)', stats['steps_per_traj']),
    C.summ_row('messages per trajectory (τ²-Bench)', [r['n_msg'] for r in by_sub['tau2bench']]),
    C.summ_row('messages per trajectory (SWE-Bench Pro)', [r['n_msg'] for r in by_sub['swebenchpro']]),
    C.summ_row('assistant steps per trajectory (all)', stats['assistant_steps_per_traj']),
    C.summ_row('tool messages per trajectory (all)', [r['n_tool'] for r in en]),
    C.summ_row('critical step index (0-based message idx)', stats['error_step_abs']),
    C.summ_row('critical rel. position (idx / last idx), all', stats['error_step_rel_pos']),
    C.summ_row('critical rel. position, τ²-Bench', stats['per_subset']['tau2bench']['error_step_rel_pos']),
    C.summ_row('critical rel. position, SWE-Bench Pro', stats['per_subset']['swebenchpro']['error_step_rel_pos']),
    C.summ_row('characters per trajectory (all)', stats['chars_per_traj']),
    C.summ_row('characters per trajectory (τ²-Bench)', [r['chars'] for r in by_sub['tau2bench']]),
    C.summ_row('characters per trajectory (SWE-Bench Pro)', [r['chars'] for r in by_sub['swebenchpro']]),
]))
L.append('\nHistogram of messages per trajectory (en):\n')
L.append(C.hist_md(stats['steps_per_traj'], [0, 10, 20, 30, 40, 60, 80, 120, 200], 'messages'))
L.append('\nHistogram of critical-step relative position:\n')
rp = stats['error_step_rel_pos']
L.append(C.md_table(['rel. position', 'n', '%'], [[f'{a:.1f}-{a + 0.2:.1f}', c, f'{100 * c / len(rp):.1f}'] for a in [0.0, 0.2, 0.4, 0.6, 0.8] for c in [sum(1 for x in rp if a <= x < a + 0.2 or (a == 0.8 and x >= 1.0))]]))
L.append('\nSubset / domain / generating model:\n')
L.append(C.counts_md(collections.Counter(f"{r['sub']} / {r['dom']} / {r['model']}" for r in en), 'subset / domain / model'))
L.append('\nCritical-error type (module.subtype) — all en trajectories:\n')
L.append(C.counts_md(collections.Counter(str(r['etype']) for r in en), 'critical_error_type'))
L.append('\nCritical-error module (prefix of the type label):\n')
L.append(C.counts_md(collections.Counter(r['module'] for r in en), 'module'))
L.append('\nCritical-error type by subset:\n')
types = sorted(set(str(r['etype']) for r in en))
L.append(C.md_table(['type', 'τ²-Bench', 'SWE-Bench Pro'], [[t, sum(1 for r in by_sub['tau2bench'] if str(r['etype']) == t), sum(1 for r in by_sub['swebenchpro'] if str(r['etype']) == t)] for t in types]))
L.append(f"\nRole of the annotated critical message: {stats['faulty_agent_counts']}. Reward values: {dict(collections.Counter(r['reward'] for r in en))}.")
C.write_fragment(SLUG, 'stats', '\n'.join(L))

# ---------- example ----------
cands = sorted([r for r in en if r['sub'] == 'tau2bench'], key=lambda r: (r['n_msg'], r['chars']))
short = [r for r in cands if r['n_msg'] <= 15]
ex = (short or cands)[0]
# among the shortest few prefer one with a mid-trajectory critical step
pool = [r for r in cands if r['n_msg'] <= max(15, ex['n_msg'])]
pool.sort(key=lambda r: (r['n_msg'], r['chars']))
ex = pool[0]
print('example', ex['tid'], ex['n_msg'], ex['k'], ex['etype'], ex['chars'])
d = json.load(open(os.path.join(R, ex['file']), encoding='utf-8'))
C.write_json(os.path.join(C.NOTES, f'{SLUG}_example.json'), {'file': 'data/trajerrbench/' + ex['file'], 'record': d})
steps_norm = []
for m in d['messages']:
    c, trimmed = C.norm_content(m['content'])
    st = {'idx': m['step'], 'agent': m['role'] + (f" ({m['name']})" if m.get('name') and m['name'] != m['role'] else ''), 'content': c}
    if trimmed:
        st['trimmed'] = True
    steps_norm.append(st)
md = d['metadata']
final = next((m['content'] for m in reversed(d['messages']) if m['role'] == 'assistant'), None)
norm = {'dataset': SLUG, 'source_id': md['task_id'], 'task': md['task_description'], 'ground_truth': None, 'final_output': final,
        'steps': steps_norm,
        'annotation': {'faulty_agent': d['messages'][md['annotation']['critical_error_step']]['role'],
                       'faulty_step': md['annotation']['critical_error_step'], 'category': md['annotation']['critical_error_type'],
                       'reason': md['annotation'].get('human_rationale') or '(no free-text rationale is shipped in the release; label = earliest failure-responsible step under the Who&When decisive-error protocol)',
                       'extra': {'reward': md['reward'], 'source_benchmark': md['extra'].get('source_benchmark'), 'language': md['extra'].get('language'),
                                 'pair_id': md['extra'].get('pair_id'), 'agent_framework_description': md['extra'].get('agent_framework_description')}}}
C.write_json(os.path.join(C.NOTES, f'{SLUG}_example_norm.json'), norm)
C.write_fragment(SLUG, 'example', C.example_md(norm, f"Chosen: `{md['task_id']}` (en edition, {ex['sub']}, {ex['dom']} domain, model {ex['model']}), {ex['n_msg']} messages, {ex['chars']} characters; the shortest τ²-Bench trajectory. Step index = unified `step` (0-based message index; step 0 is the system policy prompt)."))
