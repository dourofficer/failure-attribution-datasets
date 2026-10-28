#!/usr/bin/env python3
"""Analyse AgentErrorBench (AgentDebug). Usage: python3 -I analyze_agenterrorbench.py"""
import collections
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

C.enable_user_site()
import pandas as pd  # noqa: E402

SLUG = 'agenterrorbench'
D = os.path.join(C.DATA, SLUG)
GD = os.path.join(D, 'gdrive')
ENVDIR = {'alfworld': 'ALFWorld', 'gaia': 'GAIA', 'webshop': 'WebShop'}

# ---------- labels ----------
labels = []
for env in ENVDIR:
    for r in json.load(open(os.path.join(GD, 'Label', f'{env}_labels.json'))):
        r['_env'] = env
        labels.append(r)
print('labels', len(labels), collections.Counter(r['_env'] for r in labels))

# ---------- trajectories (gdrive primary, HF mirror fallback) ----------
hf = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(os.path.join(D, 'hf_davide221/data/*.parquet')))])
hf_map = {r.trajectory_id: r for r in hf.itertuples()}
print('hf mirror rows', len(hf_map))
hf_split = {}
for split in ['train', 'validation', 'test']:
    for tid in pd.read_parquet(os.path.join(D, f'hf_davide221/data/{split}-00000-of-00001.parquet')).trajectory_id:
        hf_split[tid] = split

trajs, missing_gd = {}, []
for r in labels:
    tid = r['trajectory_id']
    p = os.path.join(GD, 'Original_Failure_Trajectory', ENVDIR[r['_env']], tid + '.json')
    if os.path.exists(p):
        trajs[tid] = (json.load(open(p)), 'gdrive')
    elif tid in hf_map:
        trajs[tid] = (json.loads(hf_map[tid].full_trajectory), 'hf_mirror')
        missing_gd.append(tid)
    else:
        print('MISSING', tid)
print('trajectories loaded', len(trajs), 'from hf mirror fallback:', missing_gd)

# ---------- per-trajectory stats ----------
steps, relpos, chars, modules, ftypes, all_ftypes, models, won = [], [], [], collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
per_env_steps = collections.defaultdict(list)
n_annot_steps = []
records = []
msg_counts = []
for r in labels:
    tid = r['trajectory_id']
    tj, src = trajs[tid]
    msgs = tj['messages']
    n_assist = sum(1 for m in msgs if m['role'] == 'assistant')
    meta = tj.get('metadata', {})
    n_steps = meta.get('steps', n_assist)
    if n_steps != n_assist:
        print('step mismatch', tid, n_steps, n_assist)
    k = r['critical_failure_step']
    steps.append(n_assist)
    msg_counts.append(len(msgs))
    per_env_steps[r['_env']].append(n_assist)
    relpos.append(k / n_assist if n_assist else None)
    chars.append(sum(len(m.get('content') or '') for m in msgs))
    modules[r['critical_failure_module']] += 1
    sa = r['step_annotations']
    n_annot_steps.append(len(sa))
    # critical-step failure type(s)
    crit_types = []
    for a in sa:
        if a.get('step') == k:
            for mod, v in a.items():
                if mod != 'step' and isinstance(v, dict):
                    crit_types.append(f"{mod}.{v.get('failure_type')}")
    for t in crit_types:
        ftypes[t] += 1
    for a in sa:
        for mod, v in a.items():
            if mod != 'step' and isinstance(v, dict):
                all_ftypes[f"{mod}.{v.get('failure_type')}"] += 1
    models[r['LLM']] += 1
    won[str(meta.get('won'))] += 1
    records.append(dict(tid=tid, env=r['_env'], model=r['LLM'], n_steps=n_assist, n_msgs=len(msgs), k=k,
                        module=r['critical_failure_module'], types=crit_types, chars=chars[-1], src=src,
                        split=hf_split.get(tid)))

# module name normalisation ('plan' vs 'planning')
MODMAP = {'plan': 'planning', 'reflect': 'reflection', 'act': 'action'}
mod_norm = collections.Counter()
for m, v in modules.items():
    mod_norm[MODMAP.get(m, m)] += v


def norm_type(t):
    mod, _, ft = t.partition('.')
    mod = MODMAP.get(mod.strip(), mod.strip())
    ft = ft.strip().lower().replace('plan_inefficient', 'inefficient_plan')
    return f"{mod}.{ft or 'unspecified'}"


ftypes_norm = collections.Counter()
for t, v in ftypes.items():
    ftypes_norm[norm_type(t)] += v
relpos_valid = [r['k'] / r['n_steps'] for r in records if 1 <= r['k'] <= r['n_steps']]

stats = {
    'n_trajectories': len(labels),
    'n_failed': len(labels),
    'n_success': 0,
    'steps_per_traj': steps,
    'messages_per_traj': msg_counts,
    'error_step_rel_pos': [round(x, 4) for x in relpos_valid],
    'error_step_rel_pos_note': 'excludes 1 trajectory whose labelled step exceeds the stored trajectory length',
    'error_step_abs': [r['k'] for r in records],
    'agents_per_traj': [1] * len(labels),
    'faulty_agent_counts': {'assistant (single agent)': len(labels)},
    'category_counts': dict(ftypes_norm),
    'category_counts_raw_labels': dict(ftypes),
    'category_counts_raw_module': dict(modules),
    'module_counts': dict(mod_norm),
    'all_step_annotation_type_counts': dict(all_ftypes),
    'n_annotated_steps_per_traj': n_annot_steps,
    'source_benchmark_counts': dict(collections.Counter(r['env'] for r in records)),
    'model_counts': dict(models),
    'chars_per_traj': chars,
    'splits': {'official': {'alfworld': 100, 'gaia': 50, 'webshop': 50},
               'hf_mirror_davide221': dict(collections.Counter(hf_split.values()))},
    'won_flag_counts': dict(won),
    'trajectory_source': dict(collections.Counter(r['src'] for r in records)),
    'missing_from_gdrive_filled_from_hf_mirror': missing_gd,
    'traj2k': 'not released (no public artefact found as of 2026-10-16)',
}
C.write_json(os.path.join(C.NOTES, f'{SLUG}_stats.json'), stats)

# ---------- stats markdown fragment ----------
L = []
L.append(C.md_table(C.SUMM_HEADERS, [
    C.summ_row('agent steps per trajectory (all)', steps),
    C.summ_row('agent steps (ALFWorld)', per_env_steps['alfworld']),
    C.summ_row('agent steps (GAIA)', per_env_steps['gaia']),
    C.summ_row('agent steps (WebShop)', per_env_steps['webshop']),
    C.summ_row('messages per trajectory (user+assistant)', msg_counts),
    C.summ_row('critical step index (1-based)', [r['k'] for r in records]),
    C.summ_row('critical step relative position (step/len)', stats['error_step_rel_pos']),
    C.summ_row('annotated steps per trajectory', n_annot_steps),
    C.summ_row('characters per trajectory', chars),
]))
L.append('\nHistogram of agent steps per trajectory:\n')
L.append(C.hist_md(steps, [0, 10, 20, 30, 40, 50, 60]))
L.append('\nHistogram of critical-step relative position:\n')
rp = stats['error_step_rel_pos']
L.append(C.md_table(['rel. position', 'n'], [[f'{a:.1f}-{a + 0.2:.1f}', sum(1 for x in rp if a <= x < a + 0.2 or (a == 0.8 and x >= 1.0))] for a in [0.0, 0.2, 0.4, 0.6, 0.8]]))
L.append('\nSource benchmark × model:\n')
cross = collections.Counter((r['env'], r['model']) for r in records)
envs, mods = sorted(ENVDIR), sorted(models)
L.append(C.md_table(['env'] + mods + ['total'], [[e] + [cross[(e, m)] for m in mods] + [sum(cross[(e, m)] for m in mods)] for e in envs]))
L.append('\nCritical-error module (normalised; raw labels use both `plan`/`planning`, `reflect`/`reflection`):\n')
L.append(C.counts_md(mod_norm, 'module'))
L.append('\nCritical-error type (module.failure_type at the critical step; labels normalised — raw labels mix `plan`/`planning`, `plan_inefficient`/`inefficient_plan`, and 27 labels have an empty failure_type):\n')
L.append(C.counts_md(ftypes_norm, 'error type'))
L.append('\nSplits in the third-party HF mirror `davide221/agenterrorbench`: ' + json.dumps(stats['splits']['hf_mirror_davide221']))
C.write_fragment(SLUG, 'stats', '\n'.join(L))

# ---------- example ----------
bad_k = [r['tid'] for r in records if r['k'] > r['n_steps'] or r['k'] < 1]
print('label step outside trajectory length:', len(bad_k), bad_k[:10])
stats['n_label_step_beyond_traj_length'] = len(bad_k)
stats['label_step_beyond_traj_length_ids'] = bad_k
C.write_json(os.path.join(C.NOTES, f'{SLUG}_stats.json'), stats)
cands = [r for r in records if 3 <= r['n_steps'] <= 15 and 1 <= r['k'] <= r['n_steps'] and r['module'] not in ('system',)]
if not cands:
    cands = [r for r in records if r['n_steps'] <= 15 and r['k'] <= r['n_steps']] or sorted(records, key=lambda r: r['n_steps'])[:5]
cands.sort(key=lambda r: (r['chars'], r['n_steps']))
ex = cands[0]
print('example', ex)
tj, src = trajs[ex['tid']]
lab = next(r for r in labels if r['trajectory_id'] == ex['tid'])
raw = {'trajectory_file': f"gdrive/Original_Failure_Trajectory/{ENVDIR[ex['env']]}/{ex['tid']}.json" if src == 'gdrive' else 'hf_mirror', 'trajectory': tj, 'label': {k: v for k, v in lab.items() if not k.startswith('_')}}
C.write_json(os.path.join(C.NOTES, f'{SLUG}_example.json'), raw)

msgs = tj['messages']
task = msgs[0]['content']
steps_norm = []
k_idx = 0
i = 0
# step k = (user message k-1 as observation, assistant message k); first user message = task prompt (contains initial observation)
assistant_positions = [j for j, m in enumerate(msgs) if m['role'] == 'assistant']
for n, j in enumerate(assistant_positions, start=1):
    obs = msgs[j - 1]['content'] if j - 1 >= 0 and msgs[j - 1]['role'] == 'user' else ''
    if n == 1:
        obs_txt = '(task prompt + initial observation; see `task`)'
    else:
        obs_txt = obs
    content = f"Observation (environment/user message {j - 1}):\n{obs_txt}\n\nAgent output (assistant message {j}):\n{msgs[j]['content']}"
    c, trimmed = C.norm_content(content)
    st = {'idx': n, 'agent': 'assistant (single ReAct-style agent)', 'content': c}
    if trimmed:
        st['trimmed'] = True
    steps_norm.append(st)
k = lab['critical_failure_step']
crit = [a for a in lab['step_annotations'] if a.get('step') == k]
reason, cat = None, None
for a in crit:
    for mod, v in a.items():
        if mod != 'step' and isinstance(v, dict):
            cat = f"{mod}.{v.get('failure_type')}"
            reason = v.get('reasoning')
final_out = msgs[-1]['content'] if msgs[-1]['role'] == 'assistant' else None
norm = {'dataset': SLUG, 'source_id': ex['tid'], 'task': task, 'ground_truth': None, 'final_output': final_out,
        'steps': steps_norm,
        'annotation': {'faulty_agent': 'assistant (single agent)', 'faulty_step': k, 'category': cat, 'reason': reason,
                       'extra': {'critical_failure_module': lab['critical_failure_module'],
                                 'step_annotations': lab['step_annotations'],
                                 'step_numbering': '1-based index of assistant turns (message index 2k-1)',
                                 'llm': lab['LLM'], 'env': ex['env'], 'won': tj.get('metadata', {}).get('won')}}}
C.write_json(os.path.join(C.NOTES, f'{SLUG}_example_norm.json'), norm)
C.write_fragment(SLUG, 'example', C.example_md(norm, f"Chosen: `{ex['tid']}` ({ex['env']}, {ex['model']}), {ex['n_steps']} agent steps, {ex['chars']} characters; shortest-by-characters failed trajectory with ≤15 steps whose critical error is not a system error. Each step below = environment observation + the agent's response (the dataset stores alternating user/assistant messages; step k = assistant message 2k−1)."))
