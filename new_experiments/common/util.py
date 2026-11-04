"""Shared helpers. Import this first in every script: it fixes sys.path for -I runs."""
import json
import os
import statistics
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA = os.path.join(ROOT, 'data')
NEW = os.path.join(ROOT, 'new_experiments')
RESULTS = os.path.join(NEW, 'results')
CACHE = os.path.join(NEW, 'cache')
USER_SITE = '/dataDisk/home/thanhdo/.local/lib/python3.10/site-packages'
for p in (NEW, USER_SITE):
    if p not in sys.path:
        sys.path.append(p)
os.makedirs(RESULTS, exist_ok=True)
os.makedirs(CACHE, exist_ok=True)


def read_json(path):
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


def read_jsonl(path):
    out = []
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)


def append_jsonl(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(obj, ensure_ascii=False) + '\n')


def summarize(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return {'n': 0}
    s = sorted(xs)
    q = lambda p: s[min(len(s) - 1, int(round(p * (len(s) - 1))))]
    return {'n': len(s), 'mean': round(statistics.mean(s), 3), 'median': statistics.median(s),
            'min': s[0], 'max': s[-1], 'p10': q(0.1), 'p90': q(0.9)}


def md_table(headers, rows):
    out = ['| ' + ' | '.join(str(h) for h in headers) + ' |', '|' + '|'.join(['---'] * len(headers)) + '|']
    for r in rows:
        out.append('| ' + ' | '.join(str(c) for c in r) + ' |')
    return '\n'.join(out)
