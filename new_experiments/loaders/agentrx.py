"""AgentRx public subset (GitHub microsoft/AgentRx data/): 29 tau-bench retail + 44 Magentic-One trajectories.
tau: OpenAI chat messages (system, user, assistant w/ tool_calls, tool); step_number is 1-based counting the system
message -> idx = step_number - 1. Magentic-One: list of {content, role} (Who&When-style names); step_number 1-based
over the list -> idx = step_number - 1.
labels.error_steps = [root-cause step] first, then the other annotated failure events (sorted by make_record);
labels.extra['root_cause_idx'] keeps the root explicitly; categories = [root failure_category]."""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # for python3 -I
from common.schema import make_record, make_step
from common.util import DATA, read_json

GB = os.path.join(DATA, 'agentrx', 'github', 'data')


def base_agent(a):
    return re.sub(r'\s*\(.*\)$', '', str(a)).strip()


def _tau_steps(traj):
    steps = []
    for i, m in enumerate(traj):
        role = m.get('role')
        c = m.get('content') or ''
        if role == 'assistant':
            agent, r = 'Assistant', 'agent'
            if m.get('tool_calls'):
                calls = '; '.join(f"{tc['function']['name']}({tc['function']['arguments']})" for tc in m['tool_calls'])
                c = (c + '\n' if c else '') + 'Action: ' + calls
        elif role == 'tool':
            agent, r = f"Tool:{m.get('name')}", 'tool'
            c = 'Observation: ' + c
        elif role == 'user':
            agent, r = 'User', 'user'
        elif role == 'system':
            agent, r = 'System', 'system'
        else:
            agent, r = str(role), 'agent'
        steps.append(make_step(i, agent, r, c, native_step=i + 1, meta={'native_role': role, 'tool_call_id': m.get('tool_call_id')}))
    return steps


def _labels(g, n):
    fails = sorted(g['failures'], key=lambda f: int(f['failure_id']))
    rc_id = g['root_cause']['failure_id']
    rc = next((f for f in fails if str(f['failure_id']) == str(rc_id)), None)
    idxs = []
    for f in fails:
        k = int(f['step_number']) - 1
        if 0 <= k < n:
            idxs.append(k)
    rc_idx = int(rc['step_number']) - 1 if rc else None
    if rc_idx is not None and 0 <= rc_idx < n:
        idxs = [rc_idx] + [k for k in idxs if k != rc_idx]
    return rc, rc_idx, idxs, fails


def load(limit=None, domains=('tau_retail', 'magentic_one')):
    recs = []
    if 'tau_retail' in domains:
        traj = {t['task_id']: t for t in read_json(os.path.join(GB, 'tau_retail', 'tau_dataset_failed.json'))}
        for g in read_json(os.path.join(GB, 'ground_truth', 'tau_ground_truth.json')):
            t = traj[g['trajectory_id']]
            steps = _tau_steps(t['traj'])
            rc, rc_idx, idxs, fails = _labels(g, len(steps))
            task = t['info']['task'].get('instruction') or next((s['content'] for s in steps if s['role'] == 'user'), '')
            final = next((s['content'] for s in reversed(steps) if s['role'] == 'agent'), None)
            recs.append(make_record('agentrx', f"tau_retail/{g['trajectory_id']}", task, steps, subset='tau_retail',
                                    ground_truth=json.dumps(t['info']['task'].get('outputs'), ensure_ascii=False) if t['info']['task'].get('outputs') else None,
                                    final_output=final, outcome='fail', error_steps=idxs,
                                    error_agent=rc['failed_agent'] if rc else None,
                                    categories=[rc['failure_category']] if rc else [],
                                    reason=(rc['step_reason'] + ' | ' + g['root_cause'].get('reason_for_root_cause', '')) if rc else g.get('failure_summary'),
                                    extra={'failures': fails, 'root_cause': g['root_cause'], 'root_cause_idx': rc_idx,
                                           'failure_summary': g.get('failure_summary'), 'reward': t.get('reward'),
                                           'all_categories': [f['failure_category'] for f in fails],
                                           'expected_actions': t['info']['task'].get('actions')},
                                    meta={'file': os.path.join(GB, 'tau_retail', 'tau_dataset_failed.json'), 'framework': 'tau-bench',
                                          'benchmark': 'tau-bench retail', 'trial': t.get('trial'), 'user_id': t['info']['task'].get('user_id')}))
            if limit and len(recs) >= limit:
                return recs
    if 'magentic_one' in domains:
        files = {os.path.basename(f)[:-5]: f for f in glob.glob(os.path.join(GB, 'magentic_dataset', '*.json')) if 'steps_by_id' not in f}
        for g in read_json(os.path.join(GB, 'ground_truth', 'magentic_one_ground_truth.json')):
            f = files[g['trajectory_id']]
            d = read_json(f)
            steps = []
            for i, m in enumerate(d):
                a = m.get('role') or 'unknown'
                role = 'user' if a in ('human', 'user') else 'agent'
                steps.append(make_step(i, a, role, m.get('content') or '', native_step=i + 1, meta={'base_agent': base_agent(a)}))
            rc, rc_idx, idxs, fails = _labels(g, len(steps))
            final = next((s['content'] for s in reversed(steps) if 'FINAL ANSWER' in s['content']), None)
            recs.append(make_record('agentrx', f"magentic_one/{g['trajectory_id']}", d[0].get('content') if d else '', steps,
                                    subset='magentic_one', ground_truth=None, final_output=final, outcome='fail',
                                    error_steps=idxs, error_agent=rc['failed_agent'] if rc else None,
                                    categories=[rc['failure_category']] if rc else [],
                                    reason=(rc['step_reason'] + ' | ' + g['root_cause'].get('reason_for_root_cause', '')) if rc else g.get('failure_summary'),
                                    extra={'failures': fails, 'root_cause': g['root_cause'], 'root_cause_idx': rc_idx,
                                           'failure_summary': g.get('failure_summary'),
                                           'all_categories': [f['failure_category'] for f in fails]},
                                    meta={'file': f, 'framework': 'magentic-one', 'benchmark': 'GAIA (Who&When logs)'}))
            if limit and len(recs) >= limit:
                return recs
    return recs


if __name__ == '__main__':
    rs = load()
    from collections import Counter
    print(len(rs), 'records;', sum(len(r['steps']) for r in rs), 'steps;', sum(1 for r in rs if r['labels']['error_steps']), 'with error_steps')
    print(Counter(r['subset'] for r in rs))
    m = Counter()
    for r in rs:
        k = r['labels']['extra']['root_cause_idx']
        a = r['steps'][k]['meta'].get('base_agent', r['steps'][k]['agent'])
        m[(r['subset'], a.lower() == (r['labels']['error_agent'] or '').lower())] += 1
    print(sorted(m.items()))
    print(sum(1 for r in rs if r['labels']['error_steps'] and r['labels']['error_steps'][0] != r['labels']['extra']['root_cause_idx']), 'records where root cause is not the earliest failure')
    r = rs[0]
    print(r['id'], r['labels']['error_steps'], r['labels']['error_agent'], r['labels']['categories'])
