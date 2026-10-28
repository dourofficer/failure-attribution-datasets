"""Shared helpers for the failure-attribution dataset analysis scripts.

Run the dataset scripts with `python3 -I <script>` from the scripts directory;
each script inserts this directory on sys.path explicitly.
"""
import json
import os
import statistics
import sys

USER_SITE = '/dataDisk/home/thanhdo/.local/lib/python3.10/site-packages'  # pandas/pyarrow live here
ROOT = '/dataDisk/home/thanhdo/failure-attribution-datasets'
DATA = os.path.join(ROOT, 'data')
NOTES = os.path.join(ROOT, 'notes')
SCRATCH = ('/tmp/claude-1007/-dataDisk-home-thanhdo-failure-attribution-datasets/'
           '49059b6c-011c-4276-b515-12a17c5e0852/scratchpad/fragments')
os.makedirs(SCRATCH, exist_ok=True)


def enable_user_site():
    if USER_SITE not in sys.path:
        sys.path.append(USER_SITE)


def summarize(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return {'n': 0}
    s = sorted(xs)
    q = lambda p: s[min(len(s) - 1, int(round(p * (len(s) - 1))))]
    return {'n': len(s), 'mean': round(statistics.mean(s), 2), 'median': statistics.median(s),
            'min': s[0], 'max': s[-1], 'p10': q(0.1), 'p90': q(0.9)}


def hist(xs, edges):
    """edges: list of ints; bins are [e_i, e_{i+1}) plus a final >= last edge bin."""
    out = []
    for i, e in enumerate(edges):
        if i + 1 < len(edges):
            hi = edges[i + 1]
            n = sum(1 for x in xs if e <= x < hi)
            out.append((f'{e}-{hi - 1}', n))
        else:
            n = sum(1 for x in xs if x >= e)
            out.append((f'>={e}', n))
    return out


def hist_md(xs, edges, label='steps'):
    rows = hist(xs, edges)
    tot = max(1, len(xs))
    return md_table([label, 'n', '%'], [[a, b, f'{100 * b / tot:.1f}'] for a, b in rows])


def md_table(headers, rows):
    out = ['| ' + ' | '.join(str(h) for h in headers) + ' |',
           '|' + '|'.join(['---'] * len(headers)) + '|']
    for r in rows:
        out.append('| ' + ' | '.join(str(c) for c in r) + ' |')
    return '\n'.join(out)


def counts_md(counter, label, total=None, top=None):
    items = sorted(counter.items(), key=lambda kv: -kv[1])
    if top:
        items = items[:top]
    total = total or sum(counter.values()) or 1
    return md_table([label, 'n', '%'], [[k, v, f'{100 * v / total:.1f}'] for k, v in items])


def summ_row(name, xs):
    s = summarize(xs)
    if s['n'] == 0:
        return [name, 0, '-', '-', '-', '-', '-', '-']
    return [name, s['n'], s['mean'], s['median'], s['min'], s['max'], s['p10'], s['p90']]


SUMM_HEADERS = ['quantity', 'n', 'mean', 'median', 'min', 'max', 'p10', 'p90']


def trunc(s, limit=500, head=400, tail=90):
    s = '' if s is None else str(s)
    if len(s) <= limit:
        return s
    return s[:head] + ' […] ' + s[-tail:]


def norm_content(s, limit=4000, head=3000, tail=500):
    """Return (content, trimmed_flag) following the normalised-example rule."""
    s = '' if s is None else str(s)
    if len(s) <= limit:
        return s, False
    return s[:head] + ' […] ' + s[-tail:], True


def write_json(path, obj):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, default=str)
    print('wrote', path, os.path.getsize(path), 'bytes')


def example_md(norm, header_note=''):
    """Render the normalised example as the markdown 'Example trajectory' section."""
    ann = norm['annotation']
    faulty = ann.get('faulty_step')
    faulty_set = set(faulty) if isinstance(faulty, list) else ({faulty} if faulty is not None else set())
    lines = []
    if header_note:
        lines.append(header_note)
        lines.append('')
    lines.append(f"**Source id:** `{norm['source_id']}`  ")
    lines.append(f"**Task:** {trunc(norm['task'], 900, 800, 80)}")
    lines.append('')
    for st in norm['steps']:
        mark = '  ⟵ ANNOTATED ERROR STEP' if st['idx'] in faulty_set else ''
        lines.append(f"**[step {st['idx']}] {st['agent']}{mark}**")
        lines.append('')
        body = trunc(st['content'])
        lines.append('```text')
        lines.append(body.replace('```', "'''"))
        lines.append('```')
        lines.append('')
    lines.append('**Annotation**')
    lines.append('')
    lines.append(f"- Faulty agent: `{ann.get('faulty_agent')}`")
    lines.append(f"- Faulty step: `{ann.get('faulty_step')}`")
    lines.append(f"- Category: `{ann.get('category')}`")
    lines.append(f"- Reason / root cause: {ann.get('reason')}")
    for k, v in (ann.get('extra') or {}).items():
        vs = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
        lines.append(f"- {k}: {trunc(vs, 1200, 1100, 80)}")
    if norm.get('ground_truth') is not None:
        lines.append(f"- Ground truth: {trunc(str(norm['ground_truth']), 600, 500, 80)}")
    if norm.get('final_output') is not None:
        lines.append(f"- Produced answer / final output: {trunc(str(norm['final_output']), 800, 700, 80)}")
    return '\n'.join(lines)


def write_fragment(slug, name, text):
    p = os.path.join(SCRATCH, f'{slug}_{name}.md')
    with open(p, 'w', encoding='utf-8') as f:
        f.write(text)
    print('fragment', p, len(text), 'chars')
