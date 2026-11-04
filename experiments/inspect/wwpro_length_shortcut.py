"""Who&When Pro: can the injected step be found from step LENGTH alone?  Per framework, learn on even-numbered rows
whether the injected step tends to be the shortest or the longest decision step (direction), then on odd rows predict the
argmin/argmax-length decision step and score exact step accuracy vs the official label.  Also: last-decision-step prior."""
import sys, os, collections, statistics
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'loaders'))
import who_and_when_pro
rows = collections.defaultdict(list)
for t in who_and_when_pro.load():
    fs = t['annotation']['faulty_step']
    if fs is None: continue
    dec = [s for s in t['steps'] if s['role'] == 'agent']
    if len(dec) < 2 or fs not in {s['idx'] for s in dec}: continue
    rows[t['subset']].append((fs, [(s['idx'], len(s['content'])) for s in dec]))
print(f"{'framework':<14}{'n':>6} {'dir':>6} {'len-shortcut':>13} {'last-dec':>9} {'random':>8}")
tot = collections.Counter()
for fw, rs in sorted(rows.items(), key=lambda kv: -len(kv[1])):
    train = rs[0::2]; test = rs[1::2]
    # direction: fraction of training rows where label is the shortest vs longest
    sh = sum(1 for fs, d in train if fs == min(d, key=lambda x: x[1])[0]); lo = sum(1 for fs, d in train if fs == max(d, key=lambda x: x[1])[0])
    direction = 'min' if sh >= lo else 'max'
    hit = sum(1 for fs, d in test if fs == (min if direction == 'min' else max)(d, key=lambda x: x[1])[0])
    last = sum(1 for fs, d in test if fs == d[-1][0]); rnd = sum(1 / len(d) for fs, d in test)
    print(f"{fw:<14}{len(test):>6} {direction:>6} {100*hit/len(test):12.1f}% {100*last/len(test):8.1f}% {100*rnd/len(test):7.1f}%")
    tot['n'] += len(test); tot['hit'] += hit; tot['last'] += last; tot['rnd'] += rnd
print(f"{'ALL':<14}{tot['n']:>6} {'':>6} {100*tot['hit']/tot['n']:12.1f}% {100*tot['last']/tot['n']:8.1f}% {100*tot['rnd']/tot['n']:7.1f}%   (paper: GPT-5.4 all-at-once step acc 72.3 text / 60.5 video)")
