"""TracerTraj targeted statistics (G4): injected vs diagnosed (agentic), label position, what the labelled step is,
coding long rows, symptom markers after the label by label source. Writes results/tracertraj/stats.md"""
import os
import random
import re
import sys
from collections import Counter
from statistics import mean, median

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common.util import RESULTS, md_table  # noqa: E402
from common.schema import error_step  # noqa: E402
from loaders import load  # noqa: E402
from who_and_when_pro_stats import symptom_counts  # noqa: E402

OUT = []


def P(*a):
    s = ' '.join(str(x) for x in a); print(s); OUT.append(s)


def main():
    recs = load('tracertraj')
    P('# TracerTraj targeted statistics (G4)\n')
    groups = {}
    for r in recs:
        dom = r['meta']['domain']
        src = r['labels']['extra'].get('error_source') or 'n/a'
        groups.setdefault(f'{dom}/{src}', []).append(r)
    P('## (a) Label position and continuation by domain / label source\n')
    rows = []
    for g, rs in sorted(groups.items()):
        n = len(rs)
        ks = [error_step(r) for r in rs]
        ag = [[s['idx'] for s in r['steps'] if s['role'] == 'agent'] for r in rs]
        last = sum(1 for r, k, a in zip(rs, ks, ag) if a and k == a[-1])
        post = [len([i for i in a if i > k]) for k, a in zip(ks, ag)]
        rel = [k / max(1, len(r['steps']) - 1) for r, k in zip(rs, ks)]
        nsteps = [len(r['steps']) for r in rs]
        rows.append([g, n, f'{mean(nsteps):.1f}/{median(nsteps)}', f'{mean(rel):.2f}', f'{100 * last / n:.1f}', f'{mean(post):.1f}', f'{100 * sum(1 for p in post if p == 0) / n:.1f}', f'{100 * sum(1 for p in post if p >= 3) / n:.1f}', f'{mean(len(r["steps"][k]["content"]) for r, k in zip(rs, ks)):.0f}'])
    P(md_table(['domain/source', 'n', 'steps mean/median', 'rel pos', 'label = last agent step %', 'agent steps after', 'no continuation %', '>=3 after %', 'labelled step chars'], rows))
    # agentic: what does the labelled step contain (tool call? final answer?)
    P('\n## (b) Agentic rows: content type of the labelled step by source\n')
    rows = []
    for g in ('agentic/Injection Error', 'agentic/Diagnosis Error'):
        rs = groups.get(g, [])
        c = Counter()
        for r in rs:
            t = r['steps'][error_step(r)]['content']
            c['has_tool_call'] += bool(re.search(r'(<tool_call>|"name":|function|Action:|```)', t))
            c['has_final'] += bool(re.search(r'(final answer|FINAL ANSWER|<answer>|\\boxed)', t, re.I))
            c['mentions_error'] += bool(re.search(r'\b(error|mistake|wrong|incorrect|fail)', t, re.I))
            c['very_short'] += len(t) < 200
        n = len(rs)
        rows.append([g, n] + [f'{100 * c[k] / n:.1f}' for k in ('has_tool_call', 'has_final', 'mentions_error', 'very_short')])
    P(md_table(['source', 'n', 'tool call %', 'final answer %', 'mentions error/wrong %', '<200 chars %'], rows))
    INJ_STYLE = re.compile(r"\b(by (changing|modifying|altering|replacing|using|sorting|initializ)|instead of|this step is critical because|the (change|modification|perturbation))\b", re.I)
    for d in ('coding', 'math'):
        rs = [r for r in recs if r['meta']['domain'] == d and r['labels']['reason']]
        P(f"{d}: mistake_reason written from an injector's perspective (regex 'by changing/instead of/this step is critical because'): {100 * sum(1 for r in rs if INJ_STYLE.search(r['labels']['reason'])) / max(1, len(rs)):.1f}% of {len(rs)}; starts with 'This step is critical': {100 * sum(1 for r in rs if r['labels']['reason'].lower().startswith('this step is critical')) / max(1, len(rs)):.1f}%")
    P('\nerror_source values: ' + str(Counter(r['labels']['extra'].get('error_source') for r in recs)))
    # mistake_reason presence
    P('mistake_reason non-empty by domain: ' + str(Counter((r['meta']['domain'], bool(r['labels']['reason'])) for r in recs)))
    # (c) symptoms after label by group
    P('\n## (c) Symptom markers per step before / at / after the label by label source\n')
    rows = []
    for g, rs in sorted(groups.items()):
        before = Counter(); after = Counter(); at = Counter()
        for r in rs:
            k = error_step(r)
            st = [s for s in r['steps'] if s['role'] in ('agent', 'tool')]
            before.update(symptom_counts([s for s in st if s['idx'] < k])); after.update(symptom_counts([s for s in st if s['idx'] > k])); at.update(symptom_counts([r['steps'][k]]))
        for m in ('tool_error', 'self_correct', 'uncertainty', 'repeat'):
            rows.append([g, m, before['n'], f"{100 * before[m] / max(1, before['n']):.1f}", f"{100 * at[m] / max(1, at['n']):.1f}", after['n'], f"{100 * after[m] / max(1, after['n']):.1f}"])
    P(md_table(['group', 'marker', 'steps before', '% before', '% at label', 'steps after', '% after'], rows))
    # (d) coding long rows
    P('\n## (d) Coding rows: length and label placement\n')
    cod = [r for r in recs if r['meta']['domain'] == 'coding']
    long = [r for r in cod if len(r['steps']) >= 100]
    P(f'coding rows: {len(cod)}; >=100 steps: {len(long)}; >=200: {sum(1 for r in cod if len(r["steps"]) >= 200)}')
    for r in sorted(long, key=lambda r: -len(r['steps']))[:8]:
        k = error_step(r)
        P(f"- {r['id']}: n={len(r['steps'])}, label idx {k} ({r['labels']['error_agent']}), rel {k / (len(r['steps']) - 1):.2f}; agents {Counter(s['agent'] for s in r['steps']).most_common(4)}; reason: {str(r['labels']['reason'])[:200]}")
    # label agent per domain
    P('\nblamed agent by domain: ' + str({d: Counter(r['labels']['error_agent'] for r in recs if r['meta']['domain'] == d).most_common(5) for d in ('coding', 'math')}))
    # questions repeated with different labels (math injected variants)
    byq = {}
    for r in recs:
        byq.setdefault((r['meta']['domain'], r['meta']['question_ID']), []).append(r)
    multi = [v for v in byq.values() if len(v) > 1]
    P(f'\nquestion_IDs with >1 row: {len(multi)} ({Counter(v[0]["meta"]["domain"] for v in multi)}); labels across variants (first 8): ' + '; '.join(str([error_step(r) for r in v]) for v in multi[:8]))
    with open(os.path.join(RESULTS, 'tracertraj', 'stats.md'), 'w') as fh:
        fh.write('\n'.join(OUT) + '\n')
    random.seed(7)
    pick = []
    diag = [r for r in recs if r['labels']['extra'].get('error_source') and 'diag' in str(r['labels']['extra'].get('error_source')).lower()]
    inj = [r for r in recs if r['labels']['extra'].get('error_source') and 'inj' in str(r['labels']['extra'].get('error_source')).lower()]
    pick += [r['id'] for r in random.sample(diag, 8)] + [r['id'] for r in random.sample(inj, 4)]
    pick += [r['id'] for r in random.sample([r for r in cod if len(r['steps']) <= 40], 2)] + [r['id'] for r in sorted(long, key=lambda r: -len(r['steps']))[:1]]
    pick += [r['id'] for r in random.sample([r for r in recs if r['meta']['domain'] == 'math'], 2)]
    print('PICK', ','.join(pick))


if __name__ == '__main__':
    main()
