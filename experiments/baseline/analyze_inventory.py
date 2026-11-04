"""Join std and inventory baseline outputs with gold to test H1 (recovered early errors attract the attributor).
Usage: python3 -I baseline/analyze_inventory.py <slug> [<slug> ...]
For each trajectory with both outputs:
  - std_pred, gold, inventory.decisive, inventory mistakes with fate
  - was the std prediction (when earlier than gold) a step that the inventory tags as 'recovered'?
  - does the inventory list a recovered mistake before gold?  how many mistakes before gold total?
  - exact/±3 accuracy of std vs inventory-decisive
"""
import json, os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))


def load(path):
    out = {}
    if os.path.exists(path):
        for l in open(path):
            r = json.loads(l); out[r['id']] = r
    return out


def toint(x):
    try: return int(x)
    except Exception: return None


def run(slug):
    S = load(os.path.join(HERE, 'out', f'{slug}__std.jsonl')); I = load(os.path.join(HERE, 'out', f'{slug}__inventory.jsonl'))
    ids = [i for i in S if i in I and S[i]['pred'] and I[i]['pred']]
    C = collections.Counter(); C['n'] = len(ids)
    for i in ids:
        g = S[i]['gold']['faulty_step']; gset = set(S[i]['gold']['faulty_steps'] or [])
        sp = toint(S[i]['pred'].get('faulty_step')); inv = I[i]['pred']; dp = toint(inv.get('decisive_step'))
        ms = [(toint(m.get('step')), (m.get('fate') or '').lower()) for m in (inv.get('mistakes') or []) if isinstance(m, dict)]
        ms = [(s, f) for s, f in ms if s is not None]
        if g is None: continue
        C['n_gold'] += 1
        C['std_exact'] += sp == g; C['std_pm3'] += sp is not None and abs(sp - g) <= 3
        C['inv_exact'] += dp == g; C['inv_pm3'] += dp is not None and abs(dp - g) <= 3
        C['n_mistakes_total'] += len(ms)
        before = [(s, f) for s, f in ms if s < g]; C['mistakes_before_gold'] += len(before)
        C['traj_with_recovered_before_gold'] += any(f == 'recovered' for s, f in before)
        C['traj_with_fatal_before_gold'] += any(f == 'fatal' for s, f in before)
        C['gold_in_inventory'] += any(s == g for s, f in ms); C['gold_tagged_fatal'] += any(s == g and f == 'fatal' for s, f in ms)
        C['gold_tagged_recovered'] += any(s == g and f == 'recovered' for s, f in ms)
        if sp is not None and sp < g:
            C['std_earlier'] += 1
            fates = {f for s, f in ms if s == sp}
            if 'recovered' in fates: C['std_earlier_and_inv_says_recovered'] += 1
            elif 'fatal' in fates: C['std_earlier_and_inv_says_fatal'] += 1
            elif fates: C['std_earlier_and_inv_unclear'] += 1
            else: C['std_earlier_not_in_inventory'] += 1
        if sp is not None and sp > g: C['std_later'] += 1
    n = max(C['n_gold'], 1)
    print(f"\n{slug}: {C['n_gold']} trajectories with std + inventory + gold")
    print(f"  std   exact {100*C['std_exact']/n:5.1f}%  ±3 {100*C['std_pm3']/n:5.1f}%   | inventory-decisive exact {100*C['inv_exact']/n:5.1f}%  ±3 {100*C['inv_pm3']/n:5.1f}%")
    print(f"  inventory: {C['n_mistakes_total']/n:.1f} mistakes/traj, {C['mistakes_before_gold']/n:.1f} before gold; traj with a RECOVERED mistake before gold {100*C['traj_with_recovered_before_gold']/n:4.1f}%, with a FATAL one before gold {100*C['traj_with_fatal_before_gold']/n:4.1f}%")
    print(f"  gold step listed in inventory {100*C['gold_in_inventory']/n:4.1f}% (tagged fatal {100*C['gold_tagged_fatal']/n:4.1f}%, recovered {100*C['gold_tagged_recovered']/n:4.1f}%)")
    print(f"  std earlier than gold {100*C['std_earlier']/n:4.1f}% -> inventory tags that step recovered {C['std_earlier_and_inv_says_recovered']}, fatal {C['std_earlier_and_inv_says_fatal']}, unclear {C['std_earlier_and_inv_unclear']}, not listed {C['std_earlier_not_in_inventory']};  std later {100*C['std_later']/n:4.1f}%")


if __name__ == '__main__':
    for s in sys.argv[1:]: run(s)
