"""CORRECT-Error targeted statistics (G4): position priors, label/agent consistency, what the labelled step is
(final answer? planner summary?), symptom markers after the label. Writes results/correct_error/stats.md"""
import os
import random
import re
import sys
from collections import Counter, defaultdict
from statistics import mean

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common.util import RESULTS, md_table  # noqa: E402
from common.schema import error_step  # noqa: E402
from loaders import load  # noqa: E402

OUT = []


def P(*a):
    s = ' '.join(str(x) for x in a); print(s); OUT.append(s)


FINAL = re.compile(r'(FINAL ANSWER|final answer|TERMINATE)', re.I)


def main():
    recs = load('correct_error')
    P('# CORRECT-Error targeted statistics (G4)\n')
    rows = []
    for bench in sorted({r['subset'] for r in recs}) + ['ALL']:
        rs = [r for r in recs if bench == 'ALL' or r['subset'] == bench]
        n = len(rs)
        g = [error_step(r) for r in rs]
        last = sum(1 for r, k in zip(rs, g) if k == len(r['steps']) - 1)
        last_ag = sum(1 for r, k in zip(rs, g) if k == [s for s in r['steps'] if s['role'] == 'agent'][-1]['idx'])
        planner_last = sum(1 for r in rs if r['steps'][-1]['meta']['base_agent'] == 'Planner')
        lab_planner = sum(1 for r in rs if r['labels']['error_agent'] == 'Planner')
        lab_is_final = sum(1 for r, k in zip(rs, g) if FINAL.search(r['steps'][k]['content']))
        user0 = sum(1 for k in g if k == 0)
        mism = sum(1 for r, k in zip(rs, g) if r['steps'][k]['meta']['base_agent'] != r['labels']['error_agent'])
        post = [len(r['steps']) - 1 - k for r, k in zip(rs, g)]
        rows.append([bench, n, f'{mean(len(r["steps"]) for r in rs):.1f}', f'{100 * last / n:.1f}', f'{100 * last_ag / n:.1f}', f'{100 * planner_last / n:.1f}', f'{100 * lab_planner / n:.1f}', f'{100 * lab_is_final / n:.1f}', user0, f'{100 * mism / n:.1f}', f'{mean(post):.1f}'])
    P('## (a) Position / agent priors\n')
    P(md_table(['benchmark', 'n', 'steps', 'label = last step %', 'label = last agent step %', 'last step is Planner %', 'label agent Planner %', 'labelled step contains FINAL ANSWER/TERMINATE %', 'label at user msg', 'agent/step mismatch %', 'steps after label (mean)'], rows))
    # the "Planner at last step" prior accuracy
    hit = sum(1 for r in recs if error_step(r) == len(r['steps']) - 1 and r['steps'][-1]['meta']['base_agent'] == r['labels']['error_agent'])
    P(f'\n"last step + its agent" prior: step exact {100 * sum(1 for r in recs if error_step(r) == len(r["steps"]) - 1) / len(recs):.1f}%, step+agent {100 * hit / len(recs):.1f}%')
    # distribution of label-to-end distance
    d = Counter(min(len(r['steps']) - 1 - error_step(r), 6) for r in recs)
    P('steps between label and end (capped 6): ' + ', '.join(f'{k}: {100 * v / len(recs):.1f}%' for k, v in sorted(d.items())))
    # the mismatch rows: what is the labelled step's agent vs the label?
    mm = Counter((r['steps'][error_step(r)]['meta']['base_agent'], r['labels']['error_agent']) for r in recs if r['steps'][error_step(r)]['meta']['base_agent'] != r['labels']['error_agent'])
    P('\nagent/step mismatches (step agent -> label agent): ' + ', '.join(f'{a}->{b}: {c}' for (a, b), c in mm.most_common(12)))
    # does the label agent speak at label+-1?
    adj = Counter()
    for r in recs:
        k = error_step(r); la = r['labels']['error_agent']
        if r['steps'][k]['meta']['base_agent'] == la:
            continue
        for off in (-1, 1, -2, 2):
            j = k + off
            if 0 <= j < len(r['steps']) and r['steps'][j]['meta']['base_agent'] == la:
                adj[off] += 1
                break
        else:
            adj['none'] += 1
    P('for mismatched rows, nearest step by the labelled agent at offset: ' + str(dict(adj)))
    # variants of the same question: do labels differ?
    byq = defaultdict(list)
    for r in recs:
        byq[(r['meta']['backbone'], r['subset'], re.sub(r'_\d+$', '', str(r['meta']['question_id'])))].append(r)
    multi = [v for v in byq.values() if len(v) > 1]
    same_len = sum(1 for v in multi if len({len(r['steps']) for r in v}) == 1)
    same_prefix = 0
    for v in multi:
        ks = [error_step(r) for r in v]
        kmin = min(ks)
        pre = [tuple(s['content'][:200] for s in r['steps'][:kmin]) for r in v]
        same_prefix += len(set(pre)) == 1
    P(f'\nquestions with >1 injected variant: {len(multi)} (rows {sum(len(v) for v in multi)}); variants with identical step count: {same_len}; identical prefix up to min label: {same_prefix}')
    P('label steps across variants (first 10): ' + '; '.join(str([error_step(r) for r in v]) for v in multi[:10]))
    with open(os.path.join(RESULTS, 'correct_error', 'stats.md'), 'w') as fh:
        fh.write('\n'.join(OUT) + '\n')
    # choose records for close reading
    random.seed(3)
    pick = []
    for bench in ('gaia_level1', 'hotpotqa', 'musique', '2wiki', 'arc', 'math500', 'mmlu_pro'):
        rs = [r for r in recs if bench in r['subset'].lower()]
        if rs:
            pick += [r['id'] for r in random.sample(rs, min(2, len(rs)))]
    pick += [r['id'] for r in random.sample([r for r in recs if error_step(r) == 0], 2)]
    pick += [r['id'] for r in random.sample([r for r in recs if r['steps'][error_step(r)]['meta']['base_agent'] != r['labels']['error_agent']], 2)]
    print('PICK', ','.join(pick))


if __name__ == '__main__':
    main()
