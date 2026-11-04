"""Reading-free rule baselines in the same metrics as the LLM baseline (exact, ±3) for every step-labelled dataset.
Rules: first decision, last decision, longest decision step, shortest decision step, random decision (expected), and
'first decision after the longest repeat block' (the pivot rule).  Usage: python3 -I inspect/rule_baselines.py slug..."""
import importlib, os, sys, collections, random
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'loaders')); sys.path.insert(0, HERE)
from repeat_blocks import bookkeeping, blocks_loose


def run(slug, subset=None):
    mod = importlib.import_module(slug); rng = random.Random(0)
    R = collections.defaultdict(lambda: [0, 0]); n = 0
    for t in mod.load(subset=subset):
        g = t['annotation']['faulty_step']
        if g is None or t.get('outcome') == 1: continue
        dec = [s for s in t['steps'] if s['role'] == 'agent' and not bookkeeping(s['content'])]
        if not dec: continue
        n += 1
        bl = [b for b in blocks_loose(t['steps']) if b[2] >= 3]
        after_block = None
        if bl:
            big = max(bl, key=lambda b: b[2]); nxt = [s['idx'] for s in dec if s['idx'] > big[1]]
            after_block = nxt[0] if nxt else big[1]
        preds = {'first': dec[0]['idx'], 'last': dec[-1]['idx'], 'longest': max(dec, key=lambda s: len(s['content']))['idx'],
                 'shortest': min(dec, key=lambda s: len(s['content']))['idx'], 'random': rng.choice(dec)['idx'],
                 'after_biggest_block': after_block if after_block is not None else dec[-1]['idx'],
                 'first_of_biggest_block': (max(bl, key=lambda b: b[2])[0] if bl else dec[0]['idx'])}
        for k, p in preds.items():
            R[k][0] += p == g; R[k][1] += abs(p - g) <= 3
    tag = slug + (f"/{subset}" if subset else '')
    print(f"{tag:<28} n={n:<5} " + "  ".join(f"{k} {100*v[0]/n:4.1f}/{100*v[1]/n:4.1f}" for k, v in R.items()))


if __name__ == '__main__':
    print("rule baselines: exact/±3 (%)")
    for a in sys.argv[1:]:
        s, _, sub = a.partition(':'); run(s, sub or None)
