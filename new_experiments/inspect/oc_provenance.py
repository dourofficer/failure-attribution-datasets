#!/usr/bin/env python3
"""Text-free omission/commission proxies on every loader.

Per record (failed runs with a labelled step where available):
  gt_obs     : first step whose OBSERVATION text (tool/env/user returns, or the Observation:/Tool responses: part of an
               agent step) contains the ground-truth string  -> omission side ("evidence never arrived" if never)
  gt_agent   : first AGENT text containing it
  final_origin: where the final answer string first appears before the final step:
               evidence (an observation), memory (agent text before any observation), none (nowhere before the final step)
  pair proxy : gt never observed AND final_origin in {memory, none}
Strings shorter than 3 normalised chars, purely numeric < 4 digits, or longer than MAXLEN are skipped (coverage reported).
Usage: python3 inspect/oc_provenance.py <slug> [<slug> ...]   -> results/omission_commission/provenance_<slug>.jsonl + summary
"""
import os, re, sys, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, append_jsonl
from common.schema import error_step
from loaders import load

OUT = os.path.join(RESULTS, 'omission_commission')
MAXLEN = 120
OBS_MARK = re.compile(r'(?:^|\n)\s*(?:Observation:|Tool responses?:|Tool logs:|OS response:|Tool result:)', re.I)
# output-only MAS logs (Who&When, MP-Bench, AgentRx Magentic) have no tool role: these agents ARE the observation channel
TOOLISH = re.compile(r'websurfer|filesurfer|computer_terminal|executor|terminal|shell|code_?runner|browser', re.I)
# TRAIL: the framework's answer_single_question span and the agent-run spans carry the GAIA annotator metadata (the gold answer)
LEAK = re.compile(r'annotator metadata|answer_single_question', re.I)


def norm(s):
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]+', ' ', str(s or '').lower())).strip()


def usable(s):
    n = norm(s)
    if len(n) < 3 or len(n) > MAXLEN:
        return None
    if n.replace(' ', '').isdigit() and len(n.replace(' ', '')) < 4:
        return None
    return n


def split_step(step):
    """-> (agent_text, observation_text) normalised."""
    c = step['content'] if isinstance(step['content'], str) else json.dumps(step['content'], ensure_ascii=False)
    if LEAK.search(c[:4000]) and step['role'] in ('env', 'tool', 'system', 'user'):
        return '', ''
    if step['role'] == 'tool' and re.match(r'\s*Tool:\s*final_answer', c):  # TRAIL: the final answer call is the agent's claim, not evidence
        return '', ''
    if step['role'] in ('tool', 'env'):
        return '', norm(c)
    if step['role'] == 'user' and step['idx'] > 0:
        return '', norm(c)
    if step['role'] in ('system',) or (step['role'] == 'user' and step['idx'] == 0):
        return '', ''
    m = OBS_MARK.search(c)
    if m:
        return norm(c[:m.start()]), norm(c[m.start():])
    if TOOLISH.search(step['agent']) and 'orchestrator' not in step['agent'].lower() and '->' not in step['agent']:
        return '', norm(c)
    return norm(c), ''


def final_answer_text(rec):
    f = rec.get('final_output')
    if f:
        return f
    return None


def analyse(rec):
    g = error_step(rec)
    steps = rec['steps']
    parts = [split_step(s) for s in steps]
    agent_idx = [s['idx'] for s in steps if s['role'] == 'agent']
    last_agent = agent_idx[-1] if agent_idx else len(steps) - 1
    gt = usable(rec.get('ground_truth'))
    fin = usable(final_answer_text(rec))
    out = {'dataset': rec['dataset'], 'id': rec['id'], 'subset': rec['subset'], 'label': g, 'n_steps': len(steps),
           'outcome': rec['outcome'], 'gt_usable': gt is not None, 'final_usable': fin is not None,
           'final_eq_gt': bool(gt and fin and (gt == fin or gt in fin or fin in gt))}
    if gt:
        obs = [s['idx'] for s, (a, o) in zip(steps, parts) if gt in o]
        ag = [s['idx'] for s, (a, o) in zip(steps, parts) if gt in a]
        out['gt_obs_first'] = obs[0] if obs else None
        out['gt_agent_first'] = ag[0] if ag else None
        out['gt_obs_rel'] = (None if not obs else 'before' if g is not None and obs[0] < g else 'at' if g is not None and obs[0] == g else 'after' if g is not None else 'nolabel')
    if fin:
        obs = [s['idx'] for s, (a, o) in zip(steps, parts) if fin in o and s['idx'] < last_agent]
        ag = [s['idx'] for s, (a, o) in zip(steps, parts) if fin in a and s['idx'] < last_agent]
        out['fin_obs_first'] = obs[0] if obs else None
        out['fin_agent_first'] = ag[0] if ag else None
        if obs and (not ag or obs[0] <= ag[0]):
            origin = 'evidence'
        elif ag:
            origin = 'memory'
        else:
            origin = 'none'
        out['final_origin'] = origin
        fo = obs[0] if obs else ag[0] if ag else None
        out['fin_first'] = fo
        out['fin_first_rel'] = (None if fo is None or g is None else 'before' if fo < g else 'at' if fo == g else 'after')
    if gt and fin:
        out['pair_proxy'] = (out['gt_obs_first'] is None) and out['final_origin'] in ('memory', 'none')
        out['ignored_proxy'] = (out['gt_obs_first'] is not None) and out['final_origin'] in ('memory', 'none')
    return out


def pct(a, b):
    return f'{100 * a / b:.0f}%' if b else '-'


def summarise(rows, by='subset'):
    groups = collections.defaultdict(list)
    for r in rows:
        groups[r.get(by)].append(r)
    groups['ALL'] = rows
    lines = []
    for k, rs in groups.items():
        rs = [r for r in rs if r['outcome'] != 'success']
        n = len(rs)
        gtu = [r for r in rs if r['gt_usable']]
        fu = [r for r in rs if r['final_usable'] and not r['final_eq_gt']]
        both = [r for r in rs if r['gt_usable'] and r['final_usable'] and not r['final_eq_gt']]
        gnever = sum(1 for r in gtu if r['gt_obs_first'] is None)
        gbefore = sum(1 for r in gtu if r.get('gt_obs_rel') in ('before', 'at'))
        orig = collections.Counter(r['final_origin'] for r in fu)
        pair = sum(1 for r in both if r['pair_proxy'])
        ign = sum(1 for r in both if r['ignored_proxy'])
        lines.append(f"  {str(k):22s} n={n:5d} | GT usable {len(gtu):5d}: never observed {pct(gnever, len(gtu)):>4}, observed at/before label {pct(gbefore, len(gtu)):>4} "
                     f"| final usable {len(fu):5d}: evidence {pct(orig['evidence'], len(fu)):>4} memory {pct(orig['memory'], len(fu)):>4} none {pct(orig['none'], len(fu)):>4} "
                     f"| both {len(both):5d}: pair(GT never obs & final memory/none) {pct(pair, len(both)):>4}, ignored(GT obs & final memory/none) {pct(ign, len(both)):>4}")
    return '\n'.join(lines)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for slug in sys.argv[1:]:
        kw = {}
        rows = []
        for rec in load(slug, **kw):
            if not rec['steps']:
                continue
            rows.append(analyse(rec))
        path = os.path.join(OUT, f'provenance_{slug}.jsonl')
        if os.path.exists(path):
            os.remove(path)
        for r in rows:
            append_jsonl(path, r)
        print(f'== {slug}: {len(rows)} records')
        print(summarise(rows))
        sys.stdout.flush()
