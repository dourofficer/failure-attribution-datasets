"""MAST-Data spot check (G4): for sampled traces ask the model which MAST modes are present and the step where each
first appears; compare to the o1 trace-level labels; measure which modes get a step and whether modes are localisable.
Usage: python3 -I inspect/mast_data_probe.py [--ids-file results/mast_data/picks.txt] [--workers 4]
Writes results/mast_data/mode_probe.jsonl and prints a summary."""
import argparse
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, append_jsonl, md_table  # noqa: E402
from common.llm import chat_json_many  # noqa: E402
from common.render import render_steps  # noqa: E402
from loaders import load  # noqa: E402
from loaders.mast_data import MODES  # noqa: E402

SYSTEM = 'You are an expert in multi-agent LLM system failures and the MAST taxonomy.'
PROMPT = ('MAST failure modes:\n{modes}\n\nTASK (first step):\n{task}\n\nTRAJECTORY:\n\n{traj}\n\n'
          'List every MAST mode that occurs in this trajectory. For each, give the step index where it FIRST becomes visible, '
          'the agent, a one-line evidence quote, and whether the mode is a property of a single step ("step") or only visible as a '
          'pattern over several steps ("pattern"), e.g. repetition or missing verification. Also say whether the task appears to '
          'have been completed successfully. Answer with one JSON object only: {{"modes": [{{"mode": "1.3", "first_step": int, '
          '"agent": str, "evidence": str, "kind": "step|pattern"}}], "success": true|false|"unknown", "note": str}}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ids-file', default=os.path.join(RESULTS, 'mast_data', 'picks.txt'))
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    ids = [l.strip() for l in open(a.ids_file) if l.strip()]
    by = {r['id']: r for r in load('mast_data')}
    recs = [by[i] for i in ids if i in by]
    modes_txt = '\n'.join(f'{k}: {v}' for k, v in MODES.items())
    msgs = []
    for r in recs:
        traj, _ = render_steps(r, per_step_cap=4000, total_cap_tokens=90000)
        msgs.append([{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': PROMPT.format(modes=modes_txt, task=r['task'][:2000], traj=traj)}])
    outs = chat_json_many(msgs, workers=a.workers, max_tokens=12000, think=True, tag='mast_probe')
    path = os.path.join(RESULTS, 'mast_data', 'mode_probe.jsonl')
    if os.path.exists(path):
        os.remove(path)
    rows = []
    for r, (p, o) in zip(recs, outs):
        p = p or {}
        row = {'id': r['id'], 'framework': r['meta'].get('framework'), 'n_steps': len(r['steps']), 'gold_modes': r['labels']['categories'],
               'pred': p.get('modes') or [], 'success': p.get('success'), 'note': p.get('note'), 'parsed': bool(p), 'finish': o.get('finish_reason')}
        rows.append(row)
        append_jsonl(path, row)
    ok = [x for x in rows if x['parsed']]
    tp = fp = fn = 0
    kind = defaultdict(Counter)
    pos = defaultdict(list)
    for x in ok:
        pm = {m['mode']: m for m in x['pred'] if isinstance(m, dict) and m.get('mode')}
        g = set(x['gold_modes'])
        tp += len(g & set(pm)); fp += len(set(pm) - g); fn += len(g - set(pm))
        for m, d in pm.items():
            kind[m][d.get('kind')] += 1
            if isinstance(d.get('first_step'), int) and x['n_steps'] > 1:
                pos[m].append(d['first_step'] / (x['n_steps'] - 1))
    print(f'records {len(rows)} parsed {len(ok)}; mode-level vs o1 labels: precision {tp / max(1, tp + fp):.2f} recall {tp / max(1, tp + fn):.2f} (tp {tp} fp {fp} fn {fn})')
    print(md_table(['mode', 'name', 'predicted n', 'step-localisable', 'pattern', 'mean rel. first step'],
                   [[m, MODES.get(m, '?'), sum(kind[m].values()), kind[m]['step'], kind[m]['pattern'], f'{sum(pos[m]) / len(pos[m]):.2f}' if pos[m] else ''] for m in sorted(kind)]))
    print('success judgements:', Counter(str(x['success']) for x in ok))
    print('wrote', path)


if __name__ == '__main__':
    main()
