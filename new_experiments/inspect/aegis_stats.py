"""AEGIS targeted statistics (G4): is_injected markers (MacNet), mode vs framework/agent priors, surface cues of injected
turns vs clean turns (same trajectory), strategy split, and picks of injected turns per mode for close reading.
Writes results/aegis/stats.md"""
import os
import random
import re
import sys
from collections import Counter, defaultdict
from statistics import mean, pstdev

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common.util import RESULTS, md_table  # noqa: E402
from g4_common import style_feats  # noqa: E402
from loaders import load  # noqa: E402

OUT = []


def P(*a):
    s = ' '.join(str(x) for x in a); print(s); OUT.append(s)


CUES = {
    'loop_words': re.compile(r"\b(again|repeat|once more|re-?iterate|as (I|we) (said|mentioned) (before|earlier))\b", re.I),
    'terminate': re.compile(r"\b(terminate|TERMINATE|stop here|conclude|final answer|done)\b"),
    'ignore': re.compile(r"\b(ignor|disregard|regardless of|despite)\w*", re.I),
    'hedge_refuse': re.compile(r"\b(cannot|can't|unable|I will not|won't|refuse)\b", re.I),
    'wrong_arith': re.compile(r"\d+\s*[\+\-\*/×]\s*\d+\s*=\s*\d+"),
}


def main():
    recs = load('aegis')
    P('# AEGIS targeted statistics (G4)\n')
    P(f'records {len(recs)}; with is_injected markers {sum(1 for r in recs if r["labels"]["extra"]["has_step_marker"])}; frameworks {Counter(r["meta"]["framework"] for r in recs).most_common()}')
    P('\n## (a) Mode x framework and the structural-agent prior\n')
    rows = []
    for fw in sorted({r['meta']['framework'] for r in recs}):
        rs = [r for r in recs if r['meta']['framework'] == fw]
        pairs = [(f['agent_name'], f['error_type']) for r in rs for f in r['labels']['extra']['faulty_agents']]
        ag = Counter(a for a, _ in pairs); md = Counter(m for _, m in pairs)
        strat = Counter(f.get('injection_strategy') for r in rs for f in r['labels']['extra']['faulty_agents'])
        rows.append([fw, len(rs), f'{mean(len(r["steps"]) for r in rs):.1f}', f'{mean(len(r["labels"]["extra"]["faulty_agents"]) for r in rs):.2f}', ', '.join(f'{a} {100 * c / len(pairs):.0f}%' for a, c in ag.most_common(3)), ', '.join(f'{m} {100 * c / len(pairs):.0f}%' for m, c in md.most_common(3)), dict(strat)])
    P(md_table(['framework', 'n', 'turns', 'pairs/traj', 'top faulty agents', 'top modes', 'strategies'], rows))
    # agent prior: predict the most frequent faulty agent per framework -> agent-level recall
    hit = tot = 0
    top = {fw: Counter(f['agent_name'] for r in recs if r['meta']['framework'] == fw for f in r['labels']['extra']['faulty_agents']).most_common(1)[0][0] for fw in {r['meta']['framework'] for r in recs}}
    for r in recs:
        tot += 1; hit += top[r['meta']['framework']] in {f['agent_name'] for f in r['labels']['extra']['faulty_agents']}
    P(f'\nconstant-agent prior (most frequent faulty agent of the framework) hits a faulty agent in {100 * hit / tot:.1f}% of records')
    # how many distinct agents speak vs are faulty
    P(f'mean distinct speaking agents {mean(len({s["agent"] for s in r["steps"]}) for r in recs):.2f}; mean faulty agents {mean(len({f["agent_name"] for f in r["labels"]["extra"]["faulty_agents"]}) for r in recs):.2f}; fraction of speaking agents that are faulty {mean(len({f["agent_name"] for f in r["labels"]["extra"]["faulty_agents"]}) / max(1, len({s["agent"] for s in r["steps"]})) for r in recs):.2f}')

    P('\n## (b) MacNet is_injected markers: every turn of an injected agent?\n')
    mac = [r for r in recs if r['labels']['extra']['has_step_marker']]
    c = Counter()
    for r in mac:
        inj_agents = {f['agent_name'] for f in r['labels']['extra']['faulty_agents']}
        turns_by_inj_agents = [s for s in r['steps'] if s['agent'] in inj_agents]
        marked = [s for s in r['steps'] if s['meta'].get('is_injected')]
        c['all_turns_of_faulty_marked'] += len(marked) == len(turns_by_inj_agents) and all(s['meta'].get('is_injected') for s in turns_by_inj_agents)
        c['marked_subset_of_faulty'] += all(s['agent'] in inj_agents for s in marked)
        c['n_marked'] += len(marked); c['n_turns'] += len(r['steps']); c['n_faulty_turns'] += len(turns_by_inj_agents)
        c['first_marked_is_first_turn_of_agent'] += bool(marked) and marked[0]['idx'] == turns_by_inj_agents[0]['idx']
    n = len(mac)
    P(f'MacNet records {n}: every turn of the faulty agents marked in {100 * c["all_turns_of_faulty_marked"] / n:.1f}%; marked turns always by faulty agents {100 * c["marked_subset_of_faulty"] / n:.1f}%; marked turns per record {c["n_marked"] / n:.2f} of {c["n_turns"] / n:.1f} turns; first marked = first turn of the agent {100 * c["first_marked_is_first_turn_of_agent"] / n:.1f}%')
    P('=> the marker is an agent flag, not a step label; the "error_steps" of the loader is simply the first turn of the first injected agent.')

    P('\n## (c) Surface cues: turns of injected agents vs clean agents in the same trajectory (all frameworks, using faulty_agents)\n')
    feats = ['chars', 'hedge', 'cert', 'selfref', 'digits']
    rows = []
    for fw in sorted({r['meta']['framework'] for r in recs}):
        rs = [r for r in recs if r['meta']['framework'] == fw]
        d = defaultdict(list); cue = defaultdict(lambda: [0, 0])
        n_ok = 0
        for r in rs:
            inj = {f['agent_name'] for f in r['labels']['extra']['faulty_agents']}
            a = [s for s in r['steps'] if s['role'] == 'agent' and s['agent'] in inj]
            b = [s for s in r['steps'] if s['role'] == 'agent' and s['agent'] not in inj]
            if not a or not b:
                continue
            n_ok += 1
            fa = [style_feats(s['content']) for s in a]; fb = [style_feats(s['content']) for s in b]
            for f in feats:
                d[f].append(mean(x[f] for x in fa) - mean(x[f] for x in fb))
            for k, rx in CUES.items():
                cue[k][0] += sum(1 for s in a if rx.search(s['content'])) / len(a)
                cue[k][1] += sum(1 for s in b if rx.search(s['content'])) / len(b)
        if n_ok:
            rows.append([fw, n_ok] + [f'{mean(d[f]):+.3g}' for f in feats] + [f'{100 * cue[k][0] / n_ok:.0f}/{100 * cue[k][1] / n_ok:.0f}' for k in CUES])
    P(md_table(['framework', 'n'] + [f'd {f} (inj-clean)' for f in feats] + [f'{k} % inj/clean' for k in CUES], rows))

    P('\n## (d) The same (agent, mode) label: how much does the malicious_action_description vary?\n')
    desc = Counter()
    for r in recs:
        for f in (r['labels']['extra']['injected_agents'] or []):
            desc[(f.get('error_type'), (f.get('malicious_action_description') or '')[:80])] += 1
    by_mode = defaultdict(Counter)
    for (m, dsc), c in desc.items():
        by_mode[m][dsc] += c
    for m in sorted(by_mode):
        tot = sum(by_mode[m].values())
        P(f'- {m}: {tot} pairs, {len(by_mode[m])} distinct descriptions; top: ' + ' | '.join(f'"{d}" ({c})' for d, c in by_mode[m].most_common(2)))
    with open(os.path.join(RESULTS, 'aegis', 'stats.md'), 'w') as fh:
        fh.write('\n'.join(OUT) + '\n')
    # picks: 10 injected turns for each of 4 modes (prefer MacNet with markers, else first turn of the faulty agent)
    random.seed(11)
    picks = []
    for m in ('FM-1.3', 'FM-2.6', 'FM-3.1', 'FM-2.5'):
        cands = [r for r in recs if any(f['error_type'] == m for f in r['labels']['extra']['faulty_agents']) and r['subset'] == 'test']
        picks += [(m, r['id']) for r in random.sample(cands, min(10, len(cands)))]
    with open(os.path.join(RESULTS, 'aegis', 'picks.txt'), 'w') as fh:
        for m, i in picks:
            fh.write(f'{m}\t{i}\n')
    print('picks written', len(picks))


if __name__ == '__main__':
    main()
