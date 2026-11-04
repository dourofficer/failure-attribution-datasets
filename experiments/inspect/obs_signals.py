"""Observation-side signals around the labelled step.
For each labelled failed trajectory: is the observation immediately BEFORE the labelled agent step an error/empty
observation (tool error, 404, timeout, empty result, 'no results')?  Is the observation right AFTER it?  Compare with the
same rate at random agent steps of the same trajectory (position-matched control).  Also: is the labelled step a retry
(near-duplicate of the previous same-agent step)?   Usage: python3 -I inspect/obs_signals.py <slug> [limit]"""
import importlib, os, re, sys, random, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'loaders'))
sys.path.insert(0, HERE)
from repeat_blocks import sig, similar, bookkeeping

ERR = re.compile(r"(error|exception|traceback|404|403|timeout|timed out|not found|no results|nothing to summarize|failed to|denied|forbidden|unavailable|could not|cannot|unable to|invalid|empty|blocked|captcha|rate limit)", re.I)


def is_err_obs(c):
    c = c.strip()
    if len(c) < 20:
        return True  # empty / trivially short observation
    head = c[:1500]
    return bool(ERR.search(head))


def prev_obs(steps, i):
    for j in range(i - 1, -1, -1):
        if steps[j]['role'] in ('tool', 'env'):
            return steps[j]
        if steps[j]['role'] == 'agent' and not bookkeeping(steps[j]['content']):
            return None  # another decision intervened; no fresh observation
    return None


def next_obs(steps, i):
    for j in range(i + 1, min(len(steps), i + 4)):
        if steps[j]['role'] in ('tool', 'env'):
            return steps[j]
    return None


def prev_same_agent(steps, i):
    for j in range(i - 1, -1, -1):
        if steps[j]['role'] == 'agent' and steps[j]['agent'] == steps[i]['agent'] and not bookkeeping(steps[j]['content']):
            return steps[j]
    return None


def analyse(slug, limit=None):
    mod = importlib.import_module(slug)
    C = collections.Counter(); rng = random.Random(0)
    for t in mod.load(limit=limit):
        fs = t['annotation']['faulty_step']
        if fs is None or t.get('outcome') == 1: continue
        steps = t['steps']
        if steps[fs]['role'] != 'agent': C['label_not_agent'] += 1; continue
        cands = [s['idx'] for s in steps if s['role'] == 'agent' and not bookkeeping(s['content'])]
        if not cands: continue
        ctrl = rng.choice(cands)
        for name, i in (('label', fs), ('control', ctrl)):
            C[name + '_n'] += 1
            po = prev_obs(steps, i); no = next_obs(steps, i); ps = prev_same_agent(steps, i)
            C[name + '_prev_obs_exists'] += po is not None
            C[name + '_prev_obs_err'] += bool(po and is_err_obs(po['content']))
            C[name + '_next_obs_exists'] += no is not None
            C[name + '_next_obs_err'] += bool(no and is_err_obs(no['content']))
            C[name + '_is_retry'] += bool(ps and similar(sig(ps['content']), sig(steps[i]['content'])))
            C[name + '_is_last_agent_step'] += i == cands[-1]
    n = max(C['label_n'], 1); m = max(C['control_n'], 1)
    print(f"{slug}: {C['label_n']} labelled agent steps ({C['label_not_agent']} labels on non-agent steps skipped)")
    for k in ['prev_obs_exists', 'prev_obs_err', 'next_obs_exists', 'next_obs_err', 'is_retry', 'is_last_agent_step']:
        print(f"  {k:<20} label {100*C['label_'+k]/n:5.1f}%   random-step control {100*C['control_'+k]/m:5.1f}%")


if __name__ == '__main__':
    analyse(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
