"""G4 helpers: who_and_when_pro records re-joined with the raw injection / replay flags that the shared loader strips.
Importable from other inspect/ scripts (sys.path must contain new_experiments/)."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from loaders import who_and_when_pro as wwp  # noqa: E402


def flags_of(fw, traj):
    """Per-step flag dicts in the SAME order as loaders.who_and_when_pro.steps_of()."""
    out = []
    if fw == 'smolagents':
        for e in traj:
            if e.get('kind') in ('user', 'final_answer'):
                continue
            out.append({'injected': None})  # no flags in the raw rows
    elif fw == 'alfagent':
        for e in traj:
            if e.get('kind') == 'action':
                out.append({'injected': None})
    elif fw == 'mathchat':
        for e in traj:
            if e.get('round') is None:
                continue
            out.append({'injected': e.get('is_injected'), 'replayed': e.get('is_replayed')})
    elif fw == 'metagpt':
        for e in traj:
            if e.get('kind') == 'final_answer':
                continue
            if 'stage' in e:
                out.append({'injected': e.get('is_injected'), 'replayed': e.get('is_replayed')})
    elif fw == 'macnet':
        for e in traj:
            if e.get('kind') == 'final_answer':
                continue
            if e.get('role') in ('author', 'critic', 'rewriter', 'sink'):
                out.append({'injected': e.get('is_injected'), 'replayed': e.get('is_replayed')})
    elif fw == 'magentic-one':
        for e in traj:
            if e.get('kind') != 'agent':
                continue
            ph = e.get('phase') or []
            out.append({'injected': 'injected' in ph, 'replayed': 'replayed' in ph, 'live': 'live' in ph,
                        'final_answer': 'final_answer' in ph, 'injection_via': e.get('injection_via'), 'ledger': e.get('ledger')})
    elif fw in ('debate', 'dylan'):
        for e in traj:
            if e.get('kind') == 'round':
                for t in e.get('turns') or []:
                    out.append({'injected': t.get('is_injected'), 'replayed': t.get('is_replayed'), 'live': t.get('is_live')})
    return out


def load_flagged(limit=None, frameworks=None):
    """Records from the shared loader with step['meta']['injected'/'replayed'/...] filled from the raw rows."""
    recs = wwp.load(limit=limit, frameworks=frameworks)
    by_id = {r['id']: r for r in recs}
    with open(wwp.FILE, encoding='utf-8') as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            rec = by_id.get(r['id'])
            if rec is None:
                continue
            fl = flags_of(r['framework'], wwp.J(r['trajectory']))
            assert len(fl) == len(rec['steps']), (r['id'], len(fl), len(rec['steps']))
            for s, f in zip(rec['steps'], fl):
                s['meta'].update(f)
            # single-agent frameworks: the labelled step is the injected step by construction
            if r['framework'] in ('smolagents', 'alfagent'):
                for s in rec['steps']:
                    s['meta']['injected'] = s['idx'] in rec['labels']['error_steps']
    return recs


HEDGE = re.compile(r"\b(i think|i believe|perhaps|maybe|might|probably|likely|assume|assuming|seems|appears|"
                   r"it is possible|not sure|unclear|approximately|roughly|should be|let's assume|suppose)\b", re.I)
CERT = re.compile(r"\b(clearly|obviously|definitely|certainly|must be|exactly|confirmed|verified|final answer)\b", re.I)
SELF = re.compile(r"\b(error|mistake|wrong|incorrect|inject|erroneous|deliberately|intentionally|misread|hallucinat)\w*", re.I)


def style_feats(text):
    t = text or ''
    words = re.findall(r"\w+", t)
    nw = max(1, len(words))
    return {'chars': len(t), 'words': len(words), 'hedge': len(HEDGE.findall(t)) / nw * 1000, 'cert': len(CERT.findall(t)) / nw * 1000,
            'selfref': len(SELF.findall(t)) / nw * 1000, 'digits': sum(ch.isdigit() for ch in t) / max(1, len(t)),
            'newlines': t.count('\n') / max(1, len(t)) * 100, 'code': ('```' in t) or ('Code:' in t)}
