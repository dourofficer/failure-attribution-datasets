"""Slice baseline accuracy by gold category, subset, label position, trajectory length, repeat-block membership (H3),
rationale tags (H4), MP-Bench vote count (H11) and AgentRx root-is-first (H1).  Usage: python3 -I baseline/slice.py <slug> [variant]"""
import json, os, sys, collections, importlib
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'loaders')); sys.path.insert(0, os.path.join(ROOT, 'inspect')); sys.path.insert(0, HERE)
from repeat_blocks import blocks_loose
from score import norm_agent


def toint(x):
    try: return int(x)
    except Exception: return None


def table(name, groups):
    rows = [(k, v) for k, v in groups.items() if v['n'] >= 5]
    if not rows: return
    print(f"\n  by {name}: {'group':<36}{'n':>5}{'exact':>8}{'±3':>7}{'agent':>8}{'earlier':>9}{'later':>7}")
    for k, v in sorted(rows, key=lambda kv: -kv[1]['n']):
        n = v['n']; print(f"  {'':<6}{str(k)[:36]:<36}{n:>5}{100*v['exact']/n:7.1f}%{100*v['pm3']/n:6.1f}%{100*v['agent']/n:7.1f}%{100*v['earlier']/n:8.1f}%{100*v['later']/n:6.1f}%")


def run(slug, variant='std'):
    path = os.path.join(HERE, 'out', f'{slug}__{variant}.jsonl')
    preds = {}
    for l in open(path):
        r = json.loads(l)
        if r['pred']: preds[r['id']] = r
    mod = importlib.import_module(slug)
    tags = {}
    tp = os.path.join(ROOT, 'inspect', 'out', 'reason_tags.jsonl')
    if os.path.exists(tp):
        for l in open(tp):
            r = json.loads(l)
            if r['dataset'] == slug and r['tags']: tags[r['id']] = r['tags']
    G = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.Counter()))
    n = 0; same_block = 0; in_block = 0
    for t in mod.load():
        r = preds.get(t['id'])
        if not r or t['annotation']['faulty_step'] is None: continue
        n += 1
        g = t['annotation']['faulty_step']; p = toint(r['pred'].get('faulty_step', r['pred'].get('decisive_step')))
        pa = r['pred'].get('faulty_agent', r['pred'].get('decisive_agent')); ga = t['annotation']['faulty_agent']
        m = {'n': 1, 'exact': int(p == g), 'pm3': int(p is not None and abs(p - g) <= 3), 'agent': int(bool(ga) and norm_agent(pa) == norm_agent(ga)),
             'earlier': int(p is not None and p < g), 'later': int(p is not None and p > g)}
        T = len(t['steps'])
        keys = {'subset': t['subset'], 'category': (t['annotation']['category'] or 'none')[:36], 'rel_pos': f"{int(10 * g / max(T - 1, 1)) / 10:.1f}",
                'n_steps': '<=10' if T <= 10 else '<=30' if T <= 30 else '<=100' if T <= 100 else '>100',
                'gold_agent': (ga or 'none').lower()[:20], 'label_role': t['steps'][g]['role']}
        # repeat blocks
        bl = blocks_loose(t['steps']); gb = [b for b in bl if b[0] <= g <= b[1] and b[2] >= 3]
        if gb:
            in_block += 1; keys['gold_in_block>=3'] = 'yes'
            if p is not None and gb[0][0] <= p <= gb[0][1]: same_block += 1; keys['pred_in_same_block'] = 'yes'
            else: keys['pred_in_same_block'] = 'no'
        else: keys['gold_in_block>=3'] = 'no'
        tg = tags.get(t['id']) or tags.get(t['id'].split('/')[-1]) or tags.get(os.path.basename(t['meta'].get('file', '')))
        if tg:
            for k in ('A', 'B', 'D', 'E', 'F', 'G', 'I'): keys['tag_' + k] = str(bool(tg.get(k)))
        ex = t['annotation']['extra']
        if 'votes' in ex: keys['votes_at_gold'] = str(ex['votes'].get(str(g), ex['votes'].get(g, 0)))
        if 'root_cause_is_first_failure' in ex: keys['root_is_first_event'] = str(ex['root_cause_is_first_failure'])
        for k, v in keys.items():
            for mk, mv in m.items(): G[k][v][mk] += mv
    print(f"{slug} [{variant}]: {n} scored; gold inside a repeat block (>=3) in {in_block}, prediction in the SAME block in {same_block}")
    for k in G: table(k, G[k])


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'std')
