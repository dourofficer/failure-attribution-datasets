"""Cross-dataset summary table of the std baseline (+ rule baselines where available).  python3 -I baseline/summary.py"""
import os, sys, glob, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from score import score
PUB = {'who_and_when': 'GPT-4o AAO w/ gold 12.5 AG / 5.3 HC; AgenTracer-8B 42.9 / 20.7', 'traceelephant': 'GPT-4o AAO w/o gold 22.7; dynamic 27.6; w/ gold 33.3',
       'mp_bench': 'nDCG task (no exact-step number)', 'longrca': 'V4-Flash AAO 7.6; RCTA 24.1', 'agentrx': 'W&W-style 18.8-22.7; AgentRx 36.4-42.7',
       'who_and_when_pro': 'GPT-5.4 72.3 (text)', 'trajerrbench': 'direct 41.5-52.5 τ² / 10.5-17.4 SWE; TrajDebug 52.8 / 24.4',
       'agenterrorbench': 'direct 28.0; AgentDebug 45.0', 'searchauditbench': 'AAO 32.1; SearchAuditor 39.9 (CS-strict)', 'agenthallu': 'GPT-5 32.7; Gemini 41.1',
       'symtrace': 'n/a (repair benchmark)', 'tracertraj': 'AgenTracer-8B 36.2 agentic / 18.9 code / 57.6 math (w/ gold)', 'correct_error': 'Qwen-7B judge 6-63; CORRECT 17-80 (Acc@1)',
       'trail': 'Gemini-2.5-Pro Loc 0.55 (set metric)', 'horizon': 'judge labels, no leaderboard'}
rows = []
for p in sorted(glob.glob(os.path.join(HERE, 'out', '*__std.jsonl'))):
    s = score(p); slug = os.path.basename(p).split('__')[0]
    rows.append((slug, s['n'], s['parsed'], s['agent_acc'], s['step_exact'], s['step@3'], s['in_label_set'], s['pred_earlier'], s['pred_later'], PUB.get(slug, '')))
print('| dataset | n | parsed | agent | exact | ±3 | in label set | earlier | later | published (exact step, %) |')
print('|---|---|---|---|---|---|---|---|---|---|')
for r in rows: print('| ' + ' | '.join(str(x) for x in r) + ' |')
