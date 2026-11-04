"""AgentErrorBench (AgentDebug): data/agenterrorbench/gdrive/Label/{alfworld,gaia,webshop}_labels.json +
Original_Failure_Trajectory/<Env>/<trajectory_id>.json ({messages:[{role,content}], metadata}); the 4 trajectories missing
from the Drive folder are filled from the HF mirror parquet (hf_davide221, column full_trajectory).
Steps = messages (user = observation/prompt, assistant = agent turn). Label: critical_failure_step k is a 1-based
agent turn -> message index 2k-1 (verified to be an assistant message; records where it is not are flagged in
labels.extra['index_check']). categories = [module, module.failure_type ...] from step_annotations at step k."""
import ast
import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # for python3 -I
from common.schema import make_record, make_step
from common.util import DATA, read_json

D = os.path.join(DATA, 'agenterrorbench')
GD = os.path.join(D, 'gdrive')
ENVDIR = {'alfworld': 'ALFWorld', 'gaia': 'GAIA', 'webshop': 'WebShop'}
MODMAP = {'plan': 'planning', 'reflect': 'reflection', 'act': 'action'}


def _hf_map():
    import pandas as pd
    out = {}
    for p in sorted(glob.glob(os.path.join(D, 'hf_davide221', 'data', '*.parquet'))):
        split = os.path.basename(p).split('-')[0]
        df = pd.read_parquet(p)
        for r in df.itertuples():
            out[r.trajectory_id] = (r.full_trajectory, split)
    return out


def _parse(v):
    if isinstance(v, str):
        try:
            return ast.literal_eval(v)
        except Exception:  # noqa
            try:
                return json.loads(v)
            except Exception:  # noqa
                return v
    return v


def load(limit=None, envs=('alfworld', 'gaia', 'webshop')):
    hf = None
    recs = []
    for env in envs:
        for r in read_json(os.path.join(GD, 'Label', f'{env}_labels.json')):
            tid = r['trajectory_id']
            p = os.path.join(GD, 'Original_Failure_Trajectory', ENVDIR[env], tid + '.json')
            split = None
            if os.path.exists(p):
                tj, src = read_json(p), 'gdrive'
            else:
                if hf is None:
                    hf = _hf_map()
                if tid not in hf:
                    continue
                tj, src = json.loads(hf[tid][0]), 'hf_mirror'
                p = os.path.join(D, 'hf_davide221', 'data', f'{hf[tid][1]}-00000-of-00001.parquet')
                split = hf[tid][1]
            msgs = tj['messages']
            md = tj.get('metadata') or {}
            steps = []
            for i, m in enumerate(msgs):
                role = 'agent' if m['role'] == 'assistant' else ('user' if m['role'] == 'user' else ('system' if m['role'] == 'system' else 'env'))
                steps.append(make_step(i, 'agent' if m['role'] == 'assistant' else ('env' if m['role'] == 'user' else m['role']), role,
                                       m.get('content') or '', native_step=(i + 1) // 2 if m['role'] == 'assistant' else None,
                                       meta={'native_role': m['role'], 'agent_turn': (i + 1) // 2 if m['role'] == 'assistant' else None}))
            k = int(str(r['critical_failure_step']).strip())
            idx = 2 * k - 1
            ok = 0 <= idx < len(msgs) and msgs[idx]['role'] == 'assistant'
            sa = _parse(r.get('step_annotations')) or []
            cats = [MODMAP.get(r['critical_failure_module'], r['critical_failure_module'])]
            crit = []
            for a in sa if isinstance(sa, list) else []:
                if isinstance(a, dict) and a.get('step') == k:
                    for mod, v in a.items():
                        if mod != 'step' and isinstance(v, dict):
                            crit.append({'module': MODMAP.get(mod, mod), 'failure_type': v.get('failure_type'), 'reasoning': v.get('reasoning')})
            cats += [f"{c['module']}.{c['failure_type']}" for c in crit]
            task = msgs[0]['content'] if msgs else ''
            final = next((s['content'] for s in reversed(steps) if s['role'] == 'agent'), None)
            recs.append(make_record('agenterrorbench', f'{env}/{tid}', task, steps, subset=env, ground_truth=None, final_output=final,
                                    outcome='fail', error_steps=[idx] if 0 <= idx < len(steps) else [], error_agent='agent',
                                    categories=cats, reason='; '.join(c['reasoning'] or '' for c in crit) or None,
                                    extra={'critical_failure_step': k, 'critical_failure_module': r['critical_failure_module'],
                                           'step_annotations': sa, 'critical_annotations': crit, 'index_check': ok,
                                           'n_agent_turns': sum(1 for m in msgs if m['role'] == 'assistant')},
                                    meta={'file': p, 'source': src, 'hf_split': split, 'framework': 'AgentDebug ReAct-style single agent',
                                          'benchmark': ENVDIR[env], 'backbone': r.get('LLM'), 'metadata': md}))
            if limit and len(recs) >= limit:
                return recs
    return recs


if __name__ == '__main__':
    rs = load()
    from collections import Counter
    print(len(rs), 'records;', sum(len(r['steps']) for r in rs), 'steps;', sum(1 for r in rs if r['labels']['error_steps']), 'with error_steps')
    print(Counter(r['subset'] for r in rs), Counter(r['meta']['source'] for r in rs))
    print('index check ok', sum(r['labels']['extra']['index_check'] for r in rs), '/', len(rs),
          [ (r['id'], r['labels']['extra']['critical_failure_step'], len(r['steps'])) for r in rs if not r['labels']['extra']['index_check']])
