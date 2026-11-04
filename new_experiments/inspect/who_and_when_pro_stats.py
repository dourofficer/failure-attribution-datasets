"""Who&When Pro targeted statistics (G4): last-step prior, lenient final-answer correctness (construction check),
style of the injected turn vs the same agent's other turns, and continuation symptoms after the injected step vs
after natural labels in Who&When. Writes results/who_and_when_pro/stats.md"""
import os
import re
import sys
from collections import Counter, defaultdict
from statistics import mean, median, pstdev

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common.util import RESULTS, md_table  # noqa: E402
from common.schema import error_step  # noqa: E402
from g4_common import load_flagged, style_feats  # noqa: E402
from loaders import load  # noqa: E402

OUT = []


def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    OUT.append(s)


def norm_ans(x):
    if x is None:
        return ''
    s = str(x).strip()
    m = re.findall(r'\\boxed\{([^{}]*)\}', s)
    if m:
        s = m[-1]
    m = re.findall(r'FINAL ANSWER:\s*(.*)', s)
    if m:
        s = m[-1]
    s = s.strip().strip('.').lower()
    s = re.sub(r'\\(d?frac)\{([^{}]*)\}\{([^{}]*)\}', r'\2/\3', s)
    s = s.replace('$', '').replace('\\', '').replace(',', '').strip()
    return s


def to_num(s):
    try:
        if '/' in s and s.count('/') == 1:
            a, b = s.split('/')
            return float(a) / float(b)
        return float(re.sub(r'[^0-9.eE+-]', '', s)) if re.fullmatch(r'[-+]?[0-9.,]+(e[-+]?\d+)?\s*%?', s.strip()) else None
    except Exception:  # noqa: BLE001
        return None


def lenient_match(pred, gold):
    p, g = norm_ans(pred), norm_ans(gold)
    if not p or not g:
        return None
    if p == g:
        return True
    pn, gn = to_num(p), to_num(g)
    if pn is not None and gn is not None:
        return abs(pn - gn) <= 1e-3 * max(1e-9, abs(gn)) + 1e-9
    if len(g) >= 4 and not to_num(g) and (p.endswith(g) or p.startswith(g) or g == p.strip('"\'')):
        return True
    return False


SYMPTOM = {
    'tool_error': re.compile(r'(Traceback|Error:|error:|Exception|AgentParsingError|ImportError|NameError|SyntaxError|failed to)', re.I),
    'self_correct': re.compile(r"\b(wait|actually|however, (I|the previous)|I apologize|my mistake|mistake|incorrect|let me (re|correct)|re-?try|retry|re-?examine|re-?check|on second thought|correction)\b", re.I),
    'uncertainty': re.compile(r"\b(unable to|cannot find|could not|couldn't|not found|no (clear )?(result|information|data)|unclear|not sure|unfortunately)\b", re.I),
    'loop_marker': re.compile(r"\b(again|repeat|same as before|already tried|stuck|loop)\b", re.I),
}


def symptom_counts(steps):
    c = Counter()
    for s in steps:
        t = s['content']
        for k, rx in SYMPTOM.items():
            if rx.search(t):
                c[k] += 1
    # exact repeats of an action/code block
    sigs = [re.sub(r'\s+', ' ', s['content'][:400]) for s in steps]
    c['repeat'] = sum(1 for i in range(1, len(sigs)) if sigs[i] in sigs[:i])
    c['n'] = len(steps)
    return c


def main():
    recs = load_flagged()
    P('# Who&When Pro targeted statistics (G4)\n')
    # ---------- (a) last-step prior ----------
    P('## (a) Position priors: where is the injected step?\n')
    rows = []
    agg = Counter()
    for fw in sorted({r['subset'] for r in recs}):
        rs = [r for r in recs if r['subset'] == fw]
        n = len(rs)
        last_ag = sum(1 for r in rs if max(r['labels']['error_steps']) == [s for s in r['steps'] if s['role'] == 'agent'][-1]['idx'])
        last_of_agent = 0
        for r in rs:
            a = r['steps'][error_step(r)]['agent']
            la = [s for s in r['steps'] if s['agent'] == a][-1]['idx']
            last_of_agent += (la in r['labels']['error_steps'])
        post = [len([s for s in r['steps'] if s['role'] == 'agent' and s['idx'] > max(r['labels']['error_steps'])]) for r in rs]
        rows.append([fw, n, f'{100 * last_ag / n:.1f}', f'{100 * last_of_agent / n:.1f}', f'{mean(post):.2f}', f'{100 * sum(1 for p in post if p == 0) / n:.1f}', f'{100 * sum(1 for p in post if p >= 3) / n:.1f}'])
        agg['n'] += n; agg['last'] += last_ag; agg['last_of_agent'] += last_of_agent; agg['post0'] += sum(1 for p in post if p == 0); agg['post3'] += sum(1 for p in post if p >= 3); agg['post_sum'] += sum(post)
    rows.append(['ALL', agg['n'], f"{100 * agg['last'] / agg['n']:.1f}", f"{100 * agg['last_of_agent'] / agg['n']:.1f}", f"{agg['post_sum'] / agg['n']:.2f}", f"{100 * agg['post0'] / agg['n']:.1f}", f"{100 * agg['post3'] / agg['n']:.1f}"])
    P(md_table(['framework', 'n', 'label = last agent step %', 'label = last step of its agent %', 'agent steps after label (mean)', 'no continuation %', '>=3 continuation steps %'], rows))

    # ---------- (b) lenient final-answer correctness ----------
    P('\n## (b) Construction check: does the final output actually disagree with the ground truth?\n')
    rows = []
    agg = Counter()
    examples = defaultdict(list)
    for fw in sorted({r['subset'] for r in recs}):
        rs = [r for r in recs if r['subset'] == fw]
        res = Counter()
        for r in rs:
            fo = r['final_output']
            if fw == 'magentic-one':  # the harness's extracted final answer is often a stray number; prefer the FINAL ANSWER line of the last step
                last = r['steps'][-1]['content']
                m = re.findall(r'FINAL ANSWER:\s*(.*)', last)
                if m:
                    fo = m[-1]
            m = lenient_match(fo, r['ground_truth'])
            res['match' if m else ('nogt' if m is None else 'mismatch')] += 1
            if m and len(examples[fw]) < 4:
                examples[fw].append((r['id'], norm_ans(fo)[:60], norm_ans(r['ground_truth'])[:60]))
        n = len(rs)
        rows.append([fw, n, res['match'], res['mismatch'], res['nogt'], f"{100 * res['match'] / max(1, res['match'] + res['mismatch']):.1f}"])
        agg.update(res)
    rows.append(['ALL', len(recs), agg['match'], agg['mismatch'], agg['nogt'], f"{100 * agg['match'] / max(1, agg['match'] + agg['mismatch']):.1f}"])
    P(md_table(['framework', 'n', 'final == GT (lenient)', 'mismatch', 'no GT / no output', '% match among comparable'], rows))
    P('\nexamples of lenient matches (id, final, gt):')
    for fw, ex in examples.items():
        for e in ex:
            P(f'- {fw}: {e}')

    # ---------- (c) style of the injected turn vs the same agent's other turns ----------
    P('\n## (c) Style: injected turn vs the same agent\'s other turns in the same trajectory\n')
    feats = ['chars', 'words', 'hedge', 'cert', 'selfref', 'digits', 'newlines']
    rows = []
    zs_all = defaultdict(list)
    for fw in sorted({r['subset'] for r in recs}):
        rs = [r for r in recs if r['subset'] == fw]
        zs = defaultdict(list)
        n_used = 0
        argmax_len = argmin_len = argmax_abs = 0
        for r in rs:
            inj = [s for s in r['steps'] if s['meta'].get('injected')]
            if not inj:
                continue
            s0 = inj[0]
            others = [s for s in r['steps'] if s['agent'] == s0['agent'] and s['role'] == 'agent' and not s['meta'].get('injected')]
            if len(others) < 2:
                continue
            n_used += 1
            fi = style_feats(s0['content'])
            fo = [style_feats(s['content']) for s in others]
            cand = [fi] + fo
            lens = [c['chars'] for c in cand]
            argmax_len += lens.index(max(lens)) == 0
            argmin_len += lens.index(min(lens)) == 0
            for f in feats:
                vals = [c[f] for c in fo]
                sd = pstdev(vals) or 1e-9
                z = (fi[f] - mean(vals)) / sd
                zs[f].append(max(-5, min(5, z)))
                zs_all[f].append(max(-5, min(5, z)))
            absz = [sum(abs((c[f] - mean([o[f] for o in fo])) / (pstdev([o[f] for o in fo]) or 1e-9)) for f in ('chars', 'hedge', 'digits')) for c in cand]
            argmax_abs += absz.index(max(absz)) == 0
        if n_used:
            chance = mean([1 / (1 + len([s for s in r['steps'] if s['agent'] == [x for x in r['steps'] if x['meta'].get('injected')][0]['agent'] and s['role'] == 'agent' and not s['meta'].get('injected')])) for r in rs if [x for x in r['steps'] if x['meta'].get('injected')] and len([s for s in r['steps'] if s['agent'] == [x for x in r['steps'] if x['meta'].get('injected')][0]['agent'] and s['role'] == 'agent' and not s['meta'].get('injected')]) >= 2])
            rows.append([fw, n_used] + [f'{mean(zs[f]):+.2f}' for f in feats] + [f'{100 * argmax_len / n_used:.0f}', f'{100 * argmin_len / n_used:.0f}', f'{100 * argmax_abs / n_used:.0f}', f'{100 * chance:.0f}'])
    if zs_all['chars']:
        rows.append(['ALL', len(zs_all['chars'])] + [f'{mean(zs_all[f]):+.2f}' for f in feats] + ['', '', '', ''])
    P(md_table(['framework', 'n (agent has >=2 other turns)'] + [f'z {f}' for f in feats] + ['injected is longest %', 'shortest %', 'argmax |z| (len,hedge,digits) %', 'chance %'], rows))

    # ---------- (d) continuation symptoms: after injected step (WWP) vs after natural label (WW) ----------
    P('\n## (d) Continuation symptoms per agent step: after the labelled step, WWP (injected) vs Who&When (natural)\n')
    ww = load('who_and_when')
    rows = []
    for name, rs in (('WWP smolagents', [r for r in recs if r['subset'] == 'smolagents']), ('WWP magentic-one', [r for r in recs if r['subset'] == 'magentic-one']),
                     ('WWP mathchat', [r for r in recs if r['subset'] == 'mathchat']), ('WWP alfagent', [r for r in recs if r['subset'] == 'alfagent']),
                     ('WWP all', recs), ('WW hand-crafted', [r for r in ww if 'and' in str(r['subset']).lower()]), ('WW alg-generated', [r for r in ww if 'alg' in str(r['subset']).lower()]), ('WW all', ww)):
        before = Counter(); after = Counter(); at = Counter()
        n_with_after = 0
        for r in rs:
            g = error_step(r)
            if g is None:
                continue
            ag = [s for s in r['steps'] if s['role'] in ('agent', 'tool')]
            b = [s for s in ag if s['idx'] < g]; a = [s for s in ag if s['idx'] > g]
            before.update(symptom_counts(b)); after.update(symptom_counts(a)); at.update(symptom_counts([r['steps'][g]]))
            n_with_after += bool(a)
        def rate(c, k):
            return f"{100 * c[k] / max(1, c['n']):.1f}"
        for k in ('tool_error', 'self_correct', 'uncertainty', 'loop_marker', 'repeat'):
            rows.append([name, k, len(rs), before['n'], rate(before, k), at['n'], rate(at, k), after['n'], rate(after, k)])
    P(md_table(['set', 'marker', 'records', 'steps before', '% before', 'labelled steps', '% at label', 'steps after', '% after'], rows))

    # ---------- (e) mode vs framework / agent ----------
    P('\n## (e) Mode distribution per framework and the constant-agent prior\n')
    rows = []
    for fw in sorted({r['subset'] for r in recs}):
        rs = [r for r in recs if r['subset'] == fw]
        modes = Counter(r['labels']['extra']['mode'] for r in rs)
        agents = Counter(r['labels']['error_agent'] for r in rs)
        rows.append([fw, len(rs), ', '.join(f'{m} {100 * c / len(rs):.0f}%' for m, c in modes.most_common(4)), ', '.join(f'{a} {100 * c / len(rs):.0f}%' for a, c in agents.most_common(3))])
    P(md_table(['framework', 'n', 'top modes', 'top labelled agents'], rows))
    with open(os.path.join(RESULTS, 'who_and_when_pro', 'stats.md'), 'w') as fh:
        fh.write('\n'.join(OUT) + '\n')


if __name__ == '__main__':
    main()
