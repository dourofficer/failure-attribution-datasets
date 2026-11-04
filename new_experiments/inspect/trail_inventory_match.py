#!/usr/bin/env python3
"""Match the inventory-variant predictions (every step the model thinks is a mistake) to TRAIL's gold error spans.
Per gold error: recalled if a predicted mistake step equals its span idx or is within +-1 (the LLM span and its CHAIN /
TOOL neighbours). Reports recall by category and impact, precision of predicted mistakes, and where unmatched
predictions fall relative to the primary. Usage: python3 -I inspect/trail_inventory_match.py [name=all_at_once_inventory]"""
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, md_table, read_jsonl  # noqa: E402
from loaders import load  # noqa: E402


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else 'all_at_once_inventory'
    rows = read_jsonl(os.path.join(RESULTS, 'trail', name + '.jsonl'))
    by = {r['id']: r for r in load('trail')}
    rec_cat = defaultdict(lambda: [0, 0]); rec_imp = defaultdict(lambda: [0, 0]); rec_kind = defaultdict(lambda: [0, 0])
    prec = Counter(); n_pred = 0; unmatched_pos = Counter(); per_rec = []
    for row in rows:
        r = by[row['id']]
        preds = []
        for m in (row.get('pred') or {}).get('mistakes') or []:
            try:
                preds.append(int(m.get('step')))
            except Exception:  # noqa
                pass
        preds = sorted(set(preds))
        n_pred += len(preds)
        errs = [e for e in r['labels']['extra']['errors'] if e['idx'] is not None]
        gold = {e['idx'] for e in errs}
        gold_near = gold | {g + 1 for g in gold} | {g - 1 for g in gold}
        for e in errs:
            hit = any(abs(p - e['idx']) <= 1 for p in preds)
            rec_cat[e['category']][0] += hit; rec_cat[e['category']][1] += 1
            rec_imp[e['impact']][0] += hit; rec_imp[e['impact']][1] += 1
            rec_kind[e['kind']][0] += hit; rec_kind[e['kind']][1] += 1
        p0 = r['labels']['extra']['primary_idx']
        for p in preds:
            if p in gold_near:
                prec['hit gold (+-1)'] += 1
            else:
                prec['no gold'] += 1
                if p0 is not None:
                    unmatched_pos['after primary' if p > p0 else 'before primary'] += 1
        per_rec.append({'id': row['id'], 'n_pred': len(preds), 'n_gold_spans': len(gold), 'recall_spans': sum(1 for g in gold if any(abs(p - g) <= 1 for p in preds)) / max(1, len(gold)),
                        'primary_in_preds': p0 in preds, 'decisive_exact': row['step_exact'], 'decisive_dist': row['step_dist']})
    print(f'{len(rows)} records; predicted mistake steps total {n_pred} (mean {n_pred / max(1, len(rows)):.1f}/trace); gold spans mean {sum(x["n_gold_spans"] for x in per_rec) / len(per_rec):.1f}')
    print('precision of predicted mistakes:', dict(prec), ' unmatched relative to primary:', dict(unmatched_pos))
    print('primary in predicted set:', sum(x['primary_in_preds'] for x in per_rec), '/', len(per_rec), '; decisive exact:', sum(1 for x in per_rec if x['decisive_exact']))
    print(md_table(['impact', 'recalled', 'total', 'recall%'], [[k, v[0], v[1], f'{100 * v[0] / v[1]:.0f}'] for k, v in sorted(rec_imp.items())]))
    print(md_table(['span kind', 'recalled', 'total', 'recall%'], [[k, v[0], v[1], f'{100 * v[0] / v[1]:.0f}'] for k, v in sorted(rec_kind.items(), key=str)]))
    print(md_table(['category', 'recalled', 'total', 'recall%'], [[k, v[0], v[1], f'{100 * v[0] / v[1]:.0f}'] for k, v in sorted(rec_cat.items(), key=lambda x: -x[1][1]) if v[1] >= 3]))
    # decisive-step offsets
    d = [x['decisive_dist'] for x in per_rec if x['decisive_dist'] is not None]
    print('decisive offset (pred - primary): later', sum(1 for x in d if x > 0), 'earlier', sum(1 for x in d if x < 0), 'exact', sum(1 for x in d if x == 0))


if __name__ == '__main__':
    main()
