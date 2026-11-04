"""AEGIS: do injected turns announce themselves? Self-announcing cue regex on turns of faulty vs clean agents, and a
no-LLM agent attributor (agent with the most cue hits per turn) vs the constant-agent prior. Appends to results/aegis/stats.md"""
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, md_table  # noqa: E402
from loaders import load  # noqa: E402

ANN = re.compile(r"\b(incorrect(ly)?|miscalculat\w*|wrong(ly)?|erroneous(ly)?|deliberately|intentionally|for emphasis|once again|again for|repeat(ing|ed)? (this|the|these)|unnecessar\w*|disregard\w*|ignor(e|ing) (the|this|all|previous)|irrelevant|prematurely|without verif\w*|will not verify|skip\w* (the )?verif\w*|I refuse|terminate (now|here|immediately)|Incorrect Answer)\b", re.I)


def main():
    recs = load('aegis')
    out = ['\n## (e) Self-announcing cues in turns of faulty vs clean agents (regex: incorrectly / miscalculate / again for emphasis / disregard / prematurely / Incorrect Answer ...)\n']
    rows = []
    tot = Counter()
    for fw in sorted({r['meta']['framework'] for r in recs}):
        rs = [r for r in recs if r['meta']['framework'] == fw]
        f_hit = f_n = c_hit = c_n = 0
        attr_hit = attr_n = prior_hit = 0
        top = Counter(f['agent_name'] for r in rs for f in r['labels']['extra']['faulty_agents']).most_common(1)[0][0]
        for r in rs:
            fa = {f['agent_name'] for f in r['labels']['extra']['faulty_agents']}
            per = defaultdict(lambda: [0, 0])
            for s in r['steps']:
                if s['role'] != 'agent' or s['agent'].lower() in ('user', 'system'):
                    continue
                h = len(ANN.findall(s['content']))
                per[s['agent']][0] += h; per[s['agent']][1] += 1
                if s['agent'] in fa:
                    f_hit += bool(h); f_n += 1
                else:
                    c_hit += bool(h); c_n += 1
            if per:
                best = max(per, key=lambda a: per[a][0] / per[a][1])
                if per[best][0] > 0:
                    attr_n += 1; attr_hit += best in fa
            prior_hit += top in fa
        n = len(rs)
        rows.append([fw, n, f'{100 * f_hit / max(1, f_n):.1f}', f'{100 * c_hit / max(1, c_n):.1f}', f'{attr_n} ({100 * attr_n / n:.0f}%)', f'{100 * attr_hit / max(1, attr_n):.1f}', f'{100 * prior_hit / n:.1f}'])
        tot.update({'f_hit': f_hit, 'f_n': f_n, 'c_hit': c_hit, 'c_n': c_n, 'attr_n': attr_n, 'attr_hit': attr_hit, 'prior_hit': prior_hit, 'n': n})
    rows.append(['ALL', tot['n'], f"{100 * tot['f_hit'] / tot['f_n']:.1f}", f"{100 * tot['c_hit'] / tot['c_n']:.1f}", f"{tot['attr_n']} ({100 * tot['attr_n'] / tot['n']:.0f}%)", f"{100 * tot['attr_hit'] / max(1, tot['attr_n']):.1f}", f"{100 * tot['prior_hit'] / tot['n']:.1f}"])
    out.append(md_table(['framework', 'n', '% faulty-agent turns with cue', '% clean-agent turns with cue', 'records where some agent has a cue', 'cue-argmax agent is faulty %', 'constant-agent prior %'], rows))
    # per-mode: cue rate of the faulty agent's turns by its mode
    out.append('\nper mode (faulty agent turns with a cue):')
    bym = defaultdict(lambda: [0, 0])
    for r in recs:
        fa = {f['agent_name']: f['error_type'] for f in r['labels']['extra']['faulty_agents']}
        for s in r['steps']:
            if s['agent'] in fa:
                bym[fa[s['agent']]][0] += bool(ANN.search(s['content'])); bym[fa[s['agent']]][1] += 1
    out.append(', '.join(f'{m} {100 * h / n:.0f}%' for m, (h, n) in sorted(bym.items())))
    print('\n'.join(out))
    with open(os.path.join(RESULTS, 'aegis', 'stats.md'), 'a') as fh:
        fh.write('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
