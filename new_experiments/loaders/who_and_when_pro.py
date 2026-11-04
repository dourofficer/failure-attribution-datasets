"""Who&When Pro (HF Leoxx/whowhen_pro), text split only (data/who_and_when_pro/data/text.jsonl, 6,257 rows).
The trajectory field is a JSON string with a framework-specific shape; steps are flattened following the official
whowhen_eval renderers (as re-implemented in scripts/analyze_who_and_when_pro.py) and ground_truth is mapped to the
flat idx through the framework's step coordinate (native_step):
  smolagents   : planning + action entries; cursor starts at 0 if the first entry is a planning step, else 1; gt.step
  alfagent     : action entries; gt.step == step_number (1-based)
  mathchat     : (round,position) turns; coord = 2*round+position; the bootstrap user_proxy turn is kept as a
                 non-scorable 'input' step (role user)
  metagpt      : architect/engineer/reviewer stages; gt.stage
  macnet       : author/critic/rewriter/sink -> 0.0,1.0,1.1,2.0; gt.(round,position)
  magentic-one : kind=='agent' entries, coord 'round.position'; gt.step is that string
  debate/dylan : turns inside kind=='round' entries, coord 'round.position'; gt gives round + agents list ->
                 error_steps = turns of that round by the listed agents (all turns of the round if none match)
Injection / replay flags (is_injected, injected, is_replayed, phase, is_live, injection_via) are NOT rendered."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # for python3 -I
from common.schema import make_record, make_step
from common.util import DATA

FILE = os.path.join(DATA, 'who_and_when_pro', 'data', 'text.jsonl')
SINGLE_AGENT = {'smolagents', 'alfagent', 'eva', 'openai_cua', 'agentoccam', 'gemini'}
SUPPORTED = {'smolagents', 'alfagent', 'mathchat', 'metagpt', 'macnet', 'magentic-one', 'debate', 'dylan'}


def J(x):
    return json.loads(x) if isinstance(x, str) else x


def steps_of(fw, traj):
    """list of (coord, agent, role, content, meta) + final answer."""
    steps, final = [], None
    if fw == 'smolagents':
        nonframing = [e for e in traj if e.get('kind') not in ('user', 'final_answer')]
        cursor = 0 if nonframing and nonframing[0].get('kind') == 'planning' else 1
        for e in nonframing:
            if e.get('kind') == 'planning':
                steps.append((str(cursor), 'agent', 'agent', 'Plan: ' + (e.get('plan') or ''), {'kind': 'planning'}))
            else:
                c = 'Thought/Code: ' + (e.get('reasoning') or '')
                if e.get('code'):
                    c += '\nCode: ' + str(e.get('code'))
                c += '\nObservation: ' + str(e.get('observation') or '')
                if e.get('error'):
                    c += '\nError: ' + str(e.get('error'))
                steps.append((str(cursor), 'agent', 'agent', c, {'kind': 'action', 'step_number': e.get('step_number')}))
                if e.get('is_final_answer'):
                    final = str(e.get('observation') or '')
            cursor += 1
    elif fw == 'alfagent':
        for e in traj:
            if e.get('kind') == 'action':
                steps.append((str(e['step_number']), 'agent', 'agent',
                              f"Thought: {e.get('reasoning', '')}\nAction: {e.get('action', '')}\nObservation: {e.get('observation', '')}", {}))
                if e.get('is_final_answer'):
                    final = str(e.get('action') or '')
    elif fw == 'mathchat':
        for e in traj:
            if e.get('round') is None:
                if e.get('kind') == 'final_answer':
                    final = e.get('content')
                continue
            if e['round'] == 0 and e['position'] == 0 and e['agent_id'] == 'user_proxy':
                steps.append(('input', 'user_proxy', 'user', e.get('output') or '', {'scorable': False, 'framing_prompt': True}))
                continue
            role = 'tool' if e['agent_id'] == 'user_proxy' else 'agent'
            steps.append((str(2 * e['round'] + e['position']), e['agent_id'], role, e.get('output') or '',
                          {'round': e['round'], 'position': e['position'], 'native_role': e.get('role')}))
    elif fw == 'metagpt':
        for e in traj:
            if e.get('kind') == 'final_answer':
                final = e.get('content')
                continue
            if 'stage' in e:
                steps.append((str(e['stage']), e['agent_id'], 'agent', e.get('output') or '', {'native_role': e.get('role')}))
    elif fw == 'macnet':
        layer = {'author': (0, 0), 'critic': (1, 0), 'rewriter': (1, 1), 'sink': (2, 0)}
        for e in traj:
            if e.get('kind') == 'final_answer':
                final = e.get('content')
                continue
            if e.get('role') in layer:
                r, p = layer[e['role']]
                steps.append((f'{r}.{p}', e['agent_id'], 'agent', e.get('output') or '', {'native_role': e['role'], 'stage': e.get('stage')}))
    elif fw == 'magentic-one':
        for e in traj:
            if e.get('kind') != 'agent':
                continue
            c = e.get('output') or ''
            if e.get('tool_actions'):
                c += '\nAction: ' + json.dumps(e['tool_actions'], ensure_ascii=False)
            steps.append((f"{e['round']}.{e['position']}", e['agent'], 'agent', c,
                          {'native_role': e.get('role'), 'round': e['round'], 'position': e['position']}))
            if isinstance(e.get('phase'), list) and 'final_answer' in e['phase']:
                final = e.get('output')
    elif fw in ('debate', 'dylan'):
        for e in traj:
            if e.get('kind') == 'final_answer':
                final = e.get('content')
                continue
            if e.get('kind') == 'round':
                for pos, t in enumerate(e.get('turns') or []):
                    p = t.get('position', pos)
                    steps.append((f"{e['round']}.{p}", t['agent_id'], 'agent', t.get('output') or '',
                                  {'native_role': t.get('role'), 'round': e['round'], 'position': p}))
    else:
        raise ValueError(fw)
    return steps, final


def gt_coord(fw, gt):
    if fw == 'mathchat':
        return str(2 * gt['round'] + gt['position'])
    if fw == 'metagpt':
        return str(gt['stage'])
    if gt.get('step') is not None:
        return str(gt['step'])
    if gt.get('round') is not None and gt.get('position') is not None:
        return f"{gt['round']}.{gt['position']}"
    return None


def gt_indices(fw, gt, steps):
    coords = [s[0] for s in steps]
    if fw in ('debate', 'dylan'):
        r = str(gt['round'])
        in_round = [i for i, c in enumerate(coords) if c.split('.')[0] == r]
        agents = set(gt.get('agents') or [])
        hit = [i for i in in_round if steps[i][1] in agents]
        return (hit or in_round), in_round
    g = gt_coord(fw, gt)
    if g is None or g not in coords:
        return [], []
    return [coords.index(g)], []


def load(limit=None, frameworks=None):
    recs = []
    skipped = {}
    with open(FILE, encoding='utf-8') as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            fw = r['framework']
            if fw not in SUPPORTED or (frameworks and fw not in frameworks):
                skipped[fw] = skipped.get(fw, 0) + 1
                continue
            gt, traj, ex, task = J(r['ground_truth']), J(r['trajectory']), J(r['extras']), J(r['task'])
            raw_steps, final = steps_of(fw, traj)
            err, round_steps = gt_indices(fw, gt, raw_steps)
            steps = [make_step(i, a, role, c, native_step=coord, meta=dict(m, scorable=m.get('scorable', coord != 'input')))
                     for i, (coord, a, role, c, m) in enumerate(raw_steps)]
            agents = gt.get('agents')
            err_agent = gt.get('agent') or (','.join(agents) if agents else None)
            ex = ex if isinstance(ex, dict) else {}
            recs.append(make_record('who_and_when_pro', r['id'], task.get('query'), steps, subset=fw,
                                    ground_truth=task.get('answer') if not isinstance(task.get('answer'), (dict, list)) else json.dumps(task.get('answer')),
                                    final_output=ex.get('final_answer') or final, outcome='fail',
                                    error_steps=err, error_agent=err_agent, categories=[gt['mode']] if gt.get('mode') else [],
                                    reason=None,
                                    extra={'mode': gt.get('mode'), 'ground_truth_raw': gt, 'agents': agents,
                                           'accepted_predictions': gt.get('accepted_predictions'),
                                           'accepted_predictions_note': gt.get('accepted_predictions_note'),
                                           'round_steps': round_steps, 'gt_coord': gt_coord(fw, gt) if fw not in ('debate', 'dylan') else f"round {gt.get('round')}"},
                                    meta={'file': FILE, 'framework': fw, 'benchmark': r['benchmark'], 'split': 'text',
                                          'single_agent': fw in SINGLE_AGENT, 'roster': ex.get('agents'),
                                          'extras': {k: v for k, v in ex.items() if k not in ('agents', 'final_answer')},
                                          'task_options': task.get('options')}))
            if limit and len(recs) >= limit:
                break
    load.skipped = skipped
    return recs


if __name__ == '__main__':
    rs = load()
    from collections import Counter
    print(len(rs), 'records;', sum(len(r['steps']) for r in rs), 'steps;', sum(1 for r in rs if r['labels']['error_steps']),
          'with error_steps; skipped frameworks', load.skipped)
    print(Counter(r['subset'] for r in rs))
    m = Counter()
    for r in rs:
        if r['labels']['error_steps'] and not r['meta']['single_agent']:
            ea = r['labels']['error_agent']
            a = r['steps'][r['labels']['error_steps'][0]]['agent']
            m[(r['subset'], a == ea or a in (ea or '').split(','))] += 1
    print(sorted(m.items()))
    r = rs[0]
    print(r['id'], r['labels']['error_steps'], r['labels']['error_agent'], [(s['native_step'], s['agent'], len(s['content'])) for s in r['steps']][:6])
