#!/usr/bin/env python3
"""Summarise results/omission_commission/llm_<slug>.jsonl: shape distribution per dataset/subset, and which member of
the omission->acceptance->commission chain the dataset's label sits on (exact, +-1)."""
import collections, glob, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, read_jsonl, md_table
OUT = os.path.join(RESULTS, 'omission_commission')
SHAPES = ['pair', 'commission_only', 'omission_only', 'other']


def pct(a, b):
    return f'{100 * a / b:.0f}%' if b else '-'


def near(label, step, tol):
    return step is not None and label is not None and abs(int(step) - int(label)) <= tol


def member(row, tol):
    """Which chain member the label coincides with (first match in order omission, acceptance, commission)."""
    p = row['parsed']; L = row['label']
    es = set(row.get('error_steps') or [])
    hit = []
    for k in ('omission_step', 'acceptance_step', 'commission_step'):
        v = p.get(k)
        if v is None:
            continue
        try:
            v = int(v)
        except Exception:
            continue
        if near(L, v, tol) or (tol == 0 and v in es):
            hit.append(k.replace('_step', ''))
    return hit


def summarise(rows, group):
    rows = [r for r in rows if r.get('parsed') and r['parsed'].get('shape') in SHAPES]
    n = len(rows)
    sh = collections.Counter(r['parsed']['shape'] for r in rows)
    ok = collections.Counter(r['parsed'].get('omission_kind') for r in rows if r['parsed']['shape'] in ('pair', 'omission_only'))
    ck = collections.Counter(r['parsed'].get('commission_kind') for r in rows if r['parsed']['shape'] in ('pair', 'commission_only'))
    oth = collections.Counter(r['parsed'].get('other_kind') for r in rows if r['parsed']['shape'] == 'other')
    pairs = [r for r in rows if r['parsed']['shape'] == 'pair']
    gap = [int(r['parsed']['commission_step']) - int(r['parsed']['omission_step']) for r in pairs
           if isinstance(r['parsed'].get('commission_step'), int) and isinstance(r['parsed'].get('omission_step'), int)]
    acc = sum(1 for r in pairs if r['parsed'].get('acceptance_step') is not None)
    # strict pair: the commission is a substantive unsupported claim, not just a forced final answer at the very end
    strict = [r for r in pairs if not (r['parsed'].get('commission_kind') == 'action_without_basis'
                                       and isinstance(r['parsed'].get('commission_step'), int) and r['parsed']['commission_step'] >= r['n_steps'] - 2)]
    # label membership on pairs
    mem0 = collections.Counter(); mem1 = collections.Counter()
    for r in pairs:
        h0 = member(r, 0); h1 = member(r, 1)
        mem0[h0[0] if h0 else 'none'] += 1
        mem1[h1[0] if h1 else 'none'] += 1
    dec = sum(1 for r in rows if near(r['label'], r['parsed'].get('decisive_step'), 0))
    dec1 = sum(1 for r in rows if near(r['label'], r['parsed'].get('decisive_step'), 1))
    import statistics as st
    return {'group': group, 'n': n, 'pair': pct(sh['pair'], n), 'pair_strict': pct(len(strict), n), 'comm_only': pct(sh['commission_only'], n), 'omis_only': pct(sh['omission_only'], n),
            'other': pct(sh['other'], n), 'other_kinds': dict(oth.most_common(3)), 'omission_kinds': dict(ok.most_common(4)), 'commission_kinds': dict(ck.most_common(4)),
            'pair_gap_med': st.median(gap) if gap else None, 'pair_with_acceptance': pct(acc, len(pairs)),
            'label_on(pairs,exact)': dict(mem0), 'label_on(pairs,+-1)': dict(mem1), 'decisive=label': f"{pct(dec, n)} / {pct(dec1, n)}"}


if __name__ == '__main__':
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(OUT, 'llm_*.jsonl')))
    allrows = []
    for f in files:
        rows = read_jsonl(f)
        slug = os.path.basename(f)[4:-6]
        bad = sum(1 for r in rows if not r.get('parsed') or r['parsed'].get('shape') not in SHAPES)
        print(f'\n== {slug}: {len(rows)} rows, {bad} unparsed/invalid')
        groups = collections.defaultdict(list)
        for r in rows:
            groups[r['subset']].append(r)
        for g, rs in [('ALL', rows)] + sorted(groups.items(), key=lambda x: str(x[0])):
            if g != 'ALL' and len(groups) == 1:
                continue
            s = summarise(rs, g)
            print('  ' + json.dumps(s, ensure_ascii=False))
        allrows.extend(rows)
    # compact table
    print('\n' + md_table(['dataset', 'n', 'pair', 'pair w/ substantive fabrication', 'commission only', 'omission only', 'other', 'label on omission / acceptance / commission (pairs, +-1)', 'decisive=label (exact/+-1)'],
          [[os.path.basename(f)[4:-6], s['n'], s['pair'], s['pair_strict'], s['comm_only'], s['omis_only'], s['other'],
            ' / '.join(pct(s['label_on(pairs,+-1)'].get(k, 0), sum(s['label_on(pairs,+-1)'].values())) for k in ('omission', 'acceptance', 'commission')) + ' (none ' + pct(s['label_on(pairs,+-1)'].get('none', 0), sum(s['label_on(pairs,+-1)'].values())) + ')',
            s['decisive=label']] for f in files for s in [summarise(read_jsonl(f), 'ALL')]]))
