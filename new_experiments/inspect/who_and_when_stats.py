#!/usr/bin/env python3
"""Who&When targeted statistics (beyond length/position):
 1. final answer presence and agreement with ground truth (runs labelled failure that end with the right answer)
 2. label relative to the blamed agent's first/last step; AG step-0 labels content
 3. HC orchestrator ledger flags (is_in_loop, no progress, Stalled/Replanning) before vs after the label
 4. missing specialist turns ("-> X" not followed by X) around the label
 5. repeated WebSurfer actions (stagnation loops) and where the first repeat falls vs the label
 6. visible error strings (timeout / error / traceback / unable) before vs after the label
Writes results/who_and_when/stats.json and prints tables."""
import json, os, re, sys, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, md_table, write_json
from common.schema import error_step
from loaders import load

ERR = re.compile(r'(timeout|timed out|error|traceback|exception|unable to|could not|cannot|failed to|not found|no results)', re.I)

def norm(s):
    s = str(s or '').lower().strip()
    s = re.sub(r'[^a-z0-9. ]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def final_answer(r):
    for s in reversed(r['steps']):
        m = re.search(r'FINAL ANSWER\s*[:\-]?\s*(.*)', s['content'], re.I | re.S)
        if m:
            return s['idx'], m.group(1).strip()[:300]
    return None, None

def answer_match(fa, gt):
    if fa is None or gt is None: return None
    a, g = norm(fa), norm(gt)
    if not g: return None
    if a == g: return 'exact'
    if g in a: return 'contains'
    # numeric
    na = re.findall(r'\d+(?:\.\d+)?', a); ng = re.findall(r'\d+(?:\.\d+)?', g)
    if ng and na and ng[0] in na: return 'number'
    return 'no'

def ledger(c):
    if not c.startswith('Updated Ledger'): return None
    try:
        j = json.loads(c[len('Updated Ledger:'):].strip())
        return {'sat': j['is_request_satisfied']['answer'], 'loop': j['is_in_loop']['answer'], 'prog': j['is_progress_being_made']['answer'], 'next': j['next_speaker']['answer']}
    except Exception:
        return 'unparsed'

def main():
    recs = load('who_and_when')
    out = {}
    rows = []
    for r in recs:
        g = error_step(r); n = len(r['steps']); ga = r['labels']['error_agent']
        fidx, fa = final_answer(r)
        base = [s['meta'].get('base_agent', s['agent']) for s in r['steps']]
        blamed_steps = [i for i, b in enumerate(base) if b.lower() == (ga or '').lower()]
        ws = [i for i, b in enumerate(base) if b == 'WebSurfer']
        d = {'id': r['id'], 'subset': r['subset'], 'n': n, 'gold': g, 'agent': ga, 'has_final': fidx is not None,
             'final_idx': fidx, 'final_match': answer_match(fa, r['ground_truth']), 'final': fa,
             'label_is_first_of_agent': bool(blamed_steps) and blamed_steps[0] == g,
             'label_is_last_of_agent': bool(blamed_steps) and blamed_steps[-1] == g,
             'label_rank_in_agent': blamed_steps.index(g) if g in blamed_steps else None, 'n_agent_steps': len(blamed_steps),
             'label_is_first_websurfer': bool(ws) and ws[0] == g, 'label_is_last': g == n - 1}
        if r['subset'] == 'Hand-Crafted':
            flags = []
            for s in r['steps']:
                L = ledger(s['content'])
                if isinstance(L, dict):
                    if L['loop'] is True: flags.append((s['idx'], 'loop'))
                    if L['prog'] is False: flags.append((s['idx'], 'noprog'))
                if s['content'].startswith('Stalled'): flags.append((s['idx'], 'stalled'))
            d['flags'] = flags
            d['first_flag'] = flags[0][0] if flags else None
            d['n_flags_before'] = sum(1 for i, _ in flags if i < g); d['n_flags_after'] = sum(1 for i, _ in flags if i > g)
            d['first_stall'] = next((i for i, k in flags if k == 'stalled'), None)
            # missing turns
            miss = []
            for s in r['steps']:
                m = re.match(r'Orchestrator \(-> (\w+)\)', s['agent'])
                if m:
                    tgt = m.group(1); j = s['idx'] + 1
                    while j < n and r['steps'][j]['content'].startswith('Next speaker'): j += 1
                    if j < n and base[j] != tgt: miss.append((s['idx'], tgt, base[j]))
                    if j >= n: miss.append((s['idx'], tgt, 'END'))
            d['missing_turns'] = miss
            # repeated websurfer actions
            seen = {}; reps = []
            for i in ws:
                key = r['steps'][i]['content'].split('\n')[0][:120]
                if key in seen: reps.append((i, seen[key]))
                else: seen[key] = i
            d['n_ws'] = len(ws); d['n_ws_repeats'] = len(reps); d['first_repeat'] = reps[0][0] if reps else None
            scroll = [i for i in ws if r['steps'][i]['content'].startswith('I scrolled')]
            d['n_scroll'] = len(scroll)
        # error strings
        eb = sum(1 for s in r['steps'][:g] if ERR.search(s['content'][:4000])); ea = sum(1 for s in r['steps'][g + 1:] if ERR.search(s['content'][:4000]))
        d['err_before'] = eb; d['err_after'] = ea; d['err_at'] = bool(ERR.search(r['steps'][g]['content'][:4000]))
        d['steps_before'] = g; d['steps_after'] = n - g - 1
        rows.append(d)
    # ---- report
    for sub in ('Hand-Crafted', 'Algorithm-Generated'):
        rs = [d for d in rows if d['subset'] == sub]
        print(f'\n## {sub} (n={len(rs)})')
        hf = [d for d in rs if d['has_final']]
        print(f"has FINAL ANSWER: {len(hf)}; final matches GT exact/contains/number/no: {collections.Counter(d['final_match'] for d in hf)}")
        print('label is first step of blamed agent:', sum(d['label_is_first_of_agent'] for d in rs), '; last step of blamed agent:', sum(d['label_is_last_of_agent'] for d in rs), '; label is last step:', sum(d['label_is_last'] for d in rs))
        print('label is first WebSurfer step:', sum(d['label_is_first_websurfer'] for d in rs), 'of', sum(1 for d in rs if d['agent']=='WebSurfer'), 'WebSurfer-blamed')
        print('error-string density before label: %.3f/step, after: %.3f/step, at label: %d' % (sum(d['err_before'] for d in rs)/max(1,sum(d['steps_before'] for d in rs)), sum(d['err_after'] for d in rs)/max(1,sum(d['steps_after'] for d in rs)), sum(d['err_at'] for d in rs)))
        if sub == 'Hand-Crafted':
            print('ledger flags: logs with any flag', sum(1 for d in rs if d['flags']), '; first flag before label', sum(1 for d in rs if d['first_flag'] is not None and d['first_flag'] < d['gold']), '; after', sum(1 for d in rs if d['first_flag'] is not None and d['first_flag'] > d['gold']))
            print('Stalled/Replanning present', sum(1 for d in rs if d['first_stall'] is not None), '; first stall before label', sum(1 for d in rs if d['first_stall'] is not None and d['first_stall'] < d['gold']))
            print('missing specialist turns: logs', sum(1 for d in rs if d['missing_turns']), 'events', sum(len(d['missing_turns']) for d in rs))
            print('WebSurfer repeats: logs with repeats', sum(1 for d in rs if d['n_ws_repeats']), '; first repeat before label', sum(1 for d in rs if d['first_repeat'] is not None and d['first_repeat'] < d['gold']), 'after', sum(1 for d in rs if d['first_repeat'] is not None and d['first_repeat'] > d['gold']))
            nofinal = [d for d in rs if not d['has_final']]
            print('no FINAL ANSWER (timeout/exhaustion):', len(nofinal), 'of which label is first WebSurfer step:', sum(d['label_is_first_websurfer'] for d in nofinal), '; label rank in agent steps (median):', sorted(d['label_rank_in_agent'] for d in nofinal if d['label_rank_in_agent'] is not None))
            wf = [d for d in rs if d['has_final']]
            print('with FINAL ANSWER:', len(wf), 'label is first WebSurfer step:', sum(d['label_is_first_websurfer'] for d in wf), '; label rank in agent steps:', sorted(d['label_rank_in_agent'] for d in wf if d['label_rank_in_agent'] is not None))
    write_json(os.path.join(RESULTS, 'who_and_when', 'stats.json'), rows)
    print('\nright-answer-but-failed:', [(d['id'], d['final'][:60], d['final_match']) for d in rows if d['final_match'] in ('exact', 'contains')])
    print('\nstep-0 labels:', [(d['id'], d['agent']) for d in rows if d['gold'] == 0])

if __name__ == '__main__':
    main()
