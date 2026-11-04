#!/usr/bin/env python3
"""Compact per-turn view of AgentErrorBench runs: for each agent turn, the raw <action> text and the environment's
reply (the 'current observation is:' text for ALFWorld/WebShop, the tool result head for GAIA). Writes one file per
record to results/agenterrorbench/compact/<id>.txt and a JSON with the parsed turns for other scripts.
Usage: python3 -I inspect/agenterrorbench_compact.py [--ids a,b] [--print]
"""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, write_json  # noqa
from common.schema import error_step  # noqa
from loaders import load  # noqa

OUT = os.path.join(RESULTS, 'agenterrorbench', 'compact')


def action_of(content):
    m = re.findall(r'<action>(.*?)</action>', content, re.S)
    if m:
        return m[-1].strip()
    m = re.search(r'<answer>(.*?)</answer>', content, re.S)
    if m:
        return 'ANSWER: ' + m.group(1).strip()
    return '(no action tag) ' + content.strip()[-200:]


def obs_of(content, env):
    m = re.search(r'current observation is:\s*(.*?)(?:\nYour admissible actions|\n\nNow it\'s your turn|$)', content, re.S)
    if m:
        return m.group(1).strip()
    # GAIA: the observation is the last 'Observation k:' or 'Current Observation:' block
    m = re.findall(r"\[Observation \d+: '(.*?)', Action \d+:", content, re.S)
    m2 = re.search(r'Current Observation:\s*(.*?)(?:\n\nInstructions:|$)', content, re.S)
    if m2 and 'Start working' not in m2.group(1):
        return m2.group(1).strip()
    if m:
        return m[-1].strip()
    return content.strip()[:300]


def task_of(t):
    m = re.search(r'(?:Your task is(?: to)?:|Task:)\s*(.*)', t)
    return (m.group(1) if m else t)[:400]


def parse(rec):
    env = rec['subset']
    turns = []
    steps = rec['steps']
    for s in steps:
        if s['role'] != 'agent':
            continue
        nxt = steps[s['idx'] + 1]['content'] if s['idx'] + 1 < len(steps) else ''
        prev = steps[s['idx'] - 1]['content'] if s['idx'] >= 1 else ''
        turns.append({'idx': s['idx'], 'turn': s['native_step'], 'action': action_of(s['content']),
                      'obs_before': obs_of(prev, env), 'obs_after': obs_of(nxt, env) if nxt else None,
                      'has_think': '<think>' in s['content'], 'len': len(s['content'])})
    return turns


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--ids'); ap.add_argument('--print', action='store_true'); a = ap.parse_args()
    recs = load('agenterrorbench')
    if a.ids:
        want = set(a.ids.split(',')); recs = [r for r in recs if r['id'] in want]
    os.makedirs(OUT, exist_ok=True)
    allp = {}
    for r in recs:
        g = error_step(r)
        turns = parse(r)
        allp[r['id']] = {'gold': g, 'n_steps': len(r['steps']), 'cats': r['labels']['categories'], 'reason': r['labels']['reason'], 'turns': turns}
        lines = [f"ID {r['id']} backbone={r['meta'].get('backbone')} n_steps={len(r['steps'])} gold_idx={g} cats={r['labels']['categories']}",
                 f"REASON: {r['labels']['reason']}", 'TASK: ' + task_of(r['task']), '']
        for t in turns:
            mark = '  <<<< GOLD' if t['idx'] == g else ''
            lines.append(f"-- turn {t['turn']} (idx {t['idx']}){mark}\n   OBS: {(t['obs_before'] or '')[:400]!s}\n   ACT: {t['action'][:400]}")
        if turns and turns[-1]['obs_after']:
            lines.append(f"-- final OBS: {turns[-1]['obs_after'][:400]}")
        txt = '\n'.join(lines)
        with open(os.path.join(OUT, r['id'].replace('/', '__') + '.txt'), 'w') as fh:
            fh.write(txt)
        if a.print:
            print(txt, '\n')
    if not a.ids:
        write_json(os.path.join(RESULTS, 'agenterrorbench', 'compact_turns.json'), allp)
        print('wrote', len(allp), 'records')


if __name__ == '__main__':
    main()
