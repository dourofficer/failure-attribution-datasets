"""Outcome-blind inventory: what does the model find in SUCCESSFUL runs, and can it tell success from failure?
python3 -I baseline/analyze_blind.py <slug> [...]"""
import json, os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))


def toint(x):
    try: return int(x)
    except Exception: return None


def auroc(pos, neg):
    if not pos or not neg: return None
    wins = sum(1 for p in pos for n in neg if p > n) + 0.5 * sum(1 for p in pos for n in neg if p == n)
    return wins / (len(pos) * len(neg))


def run(slug):
    path = os.path.join(HERE, 'out', f'{slug}__inventory_blind.jsonl')
    rows = [json.loads(l) for l in open(path)]
    by = collections.defaultdict(list)
    for r in rows:
        if r['pred'] and r.get('outcome') in (0, 1): by[r['outcome']].append(r)
    print(f"\n{slug}: {len(by[1])} successful, {len(by[0])} failed runs with parsed blind inventories")
    ps = {o: [] for o in by}
    for o in (1, 0):
        rs = by[o]
        if not rs: continue
        nm = []; nf = []; nr = []; verd = 0; dec = 0; gold_hit = 0; gold_n = 0
        for r in rs:
            ms = [m for m in (r['pred'].get('mistakes') or []) if isinstance(m, dict)]
            nm.append(len(ms)); nf.append(sum(1 for m in ms if (m.get('fate') or '').lower() == 'fatal')); nr.append(sum(1 for m in ms if (m.get('fate') or '').lower() == 'recovered'))
            v = (r['pred'].get('verdict') or '').lower(); verd += (v.startswith('succ') and o == 1) or (v.startswith('fail') and o == 0)
            p = r['pred'].get('p_success'); 
            try: ps[o].append(float(p))
            except Exception: pass
            d = toint(r['pred'].get('decisive_step')); dec += d is not None
            g = r['gold'].get('faulty_step')
            if g is not None: gold_n += 1; gold_hit += d == g
        n = len(rs); med = lambda xs: sorted(xs)[len(xs) // 2]
        print(f"  outcome={o}: mistakes/run mean {sum(nm)/n:.1f} med {med(nm)}, FATAL/run mean {sum(nf)/n:.1f} (runs with >=1 fatal {100*sum(1 for x in nf if x)/n:.0f}%), recovered/run mean {sum(nr)/n:.1f}; verdict correct {100*verd/n:.0f}%; names a decisive step {100*dec/n:.0f}%" + (f"; decisive == gold {100*gold_hit/gold_n:.0f}% of {gold_n}" if gold_n else ''))
    a = auroc(ps.get(1, []), ps.get(0, []))
    if a is not None: print(f"  p_success AUROC (success vs failure) = {a:.3f}")


if __name__ == '__main__':
    for s in sys.argv[1:]: run(s)
