"""MP-Bench (adobe-research/multi-agent-eval-bench). One record per execution log (289 = 169 manual + 120 automatic);
three annotators per log. Annotation files MP-Bench/<annotator>/<split>/<n>.json carry a log_source URL; the logs were
fetched to data/mp_bench/sources/<sha1(url)[:16]>/ (index.json maps key -> url/files). The step list is rebuilt exactly
as the official build_annotated_from_log_source.py: Who&When JSON history entries, or MAST console_log.txt turns split
on '---------- <Agent> ----------' delimiters after 'SCENARIO.PY STARTING !#!#'. Annotation `step` is 0-based = idx.
labels.error_steps = union of flagged steps over annotators; votes = {idx: n_annotators};
error_agent = agent of the earliest step flagged by >=2 annotators (else earliest flagged)."""
import glob
import hashlib
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # for python3 -I
from common.schema import make_record, make_step
from common.util import DATA, read_json

RAW = os.path.join(DATA, 'mp_bench', 'adobe_multi-agent-eval-bench', 'MP-Bench')
SRC = os.path.join(DATA, 'mp_bench', 'sources')
_DELIM = re.compile(r'^-{10} (.+?) -{10}$')


def parse_console_log(content):
    marker = 'SCENARIO.PY STARTING !#!#'
    pos = content.find(marker)
    if pos != -1:
        content = content[pos + len(marker):]
    turns, cur, lines = [], None, []
    for line in content.splitlines():
        m = _DELIM.match(line.strip())
        if m:
            if cur is not None:
                turns.append({'role': cur, 'content': '\n'.join(lines).strip()})
            cur, lines = m.group(1).strip(), []
        elif cur is not None:
            lines.append(line)
    if cur is not None:
        turns.append({'role': cur, 'content': '\n'.join(lines).strip()})
    return turns


def base_agent(a):
    return re.sub(r'\s*\(.*\)$', '', a or '').strip()


def load_source(url):
    """Return (question, ground_truth, history[{role,content}], source_kind, is_correct, file) or None if not fetched."""
    key = hashlib.sha1(url.encode()).hexdigest()[:16]
    d = os.path.join(SRC, key)
    if not os.path.isdir(d):
        return None
    if url.endswith('.json'):
        fs = [f for f in os.listdir(d) if f.endswith('.json')]
        if not fs:
            return None
        f = os.path.join(d, fs[0])
        raw = read_json(f)
        hist = [{'role': h.get('name') or h.get('role'), 'content': h.get('content', '')} for h in raw.get('history', [])]
        sub = 'Who&When/Hand-Crafted' if 'Hand-Crafted' in url else 'Who&When/Algorithm-Generated'
        return raw.get('question'), raw.get('ground_truth', raw.get('groundtruth')), hist, sub, raw.get('is_correct', raw.get('is_corrected')), f
    f = os.path.join(d, 'console_log.txt')
    if not os.path.exists(f):
        return None
    with open(f, encoding='utf-8', errors='replace') as fh:
        turns = parse_console_log(fh.read())
    q = gt = ''
    for name in ('prompt.txt', 'expected_answer.txt'):
        p = os.path.join(d, name)
        if os.path.exists(p):
            with open(p, encoding='utf-8', errors='replace') as fh:
                if name == 'prompt.txt':
                    q = fh.read().strip()
                else:
                    gt = fh.read().strip()
    level = 'L3' if 'level_3' in url else ('L2' if 'level_2' in url else 'L?')
    return q, gt, turns, f'MAST/MagenticOne_GAIA {level}', None, f


def load(limit=None, splits=('manual', 'automatic')):
    inst = defaultdict(dict)
    for fpath in sorted(glob.glob(os.path.join(RAW, '*', '*', '*.json'))):
        ann_id, split, fn = fpath.split(os.sep)[-3:]
        if split not in splits:
            continue
        inst[(split, fn)][ann_id] = (fpath, read_json(fpath))
    recs = []
    n_missing = 0
    for (split, fn), anns in sorted(inst.items(), key=lambda kv: (kv[0][0], int(kv[0][1].split('.')[0]))):
        url = next(iter(anns.values()))[1]['log_source']
        src = load_source(url)
        if src is None:
            n_missing += 1
            continue
        q, gt, hist, src_kind, is_corr, f = src
        n = len(hist)
        steps = []
        for i, h in enumerate(hist):
            a = h['role'] or 'unknown'
            role = 'user' if a in ('human', 'user') else 'agent'
            steps.append(make_step(i, a, role, h['content'] or '', native_step=i, meta={'base_agent': base_agent(a)}))
        votes = defaultdict(set)
        per_ann = {}
        cats = set()
        oor = []
        for aid, (fpath, d) in sorted(anns.items()):
            lst = []
            for a in d.get('annotation', []):
                try:
                    s = int(a['step'])
                except (ValueError, TypeError, KeyError):
                    continue
                if str(a.get('fail_annotation', '1')) != '1':
                    continue
                lst.append({'step': s, 'category': a.get('fail_category'), 'reason': a.get('fail_reason'),
                            'ideal_action': a.get('ideal_action')})
                if 0 <= s < n:
                    votes[s].add(aid)
                    if a.get('fail_category'):
                        cats.add(a['fail_category'])
                else:
                    oor.append((aid, s))
            per_ann[aid] = lst
        flagged = sorted(votes)
        maj = [s for s in flagged if len(votes[s]) >= 2]
        primary = (maj or flagged or [None])[0]
        err_agent = base_agent(hist[primary]['role']) if primary is not None else None
        reasons = '; '.join(f"[step {s}, annotator {aid}, {x['category']}] {x['reason']}"
                            for s in flagged for aid in sorted(per_ann) for x in per_ann[aid] if x['step'] == s)
        final = None
        for h in reversed(hist):
            if 'FINAL ANSWER' in (h['content'] or ''):
                final = h['content']
                break
        recs.append(make_record('mp_bench', f'{split}/{fn}', q, steps, subset=split, ground_truth=gt, final_output=final,
                                outcome='fail', error_steps=flagged, error_agent=err_agent, categories=sorted(cats),
                                reason=reasons or None, votes={s: len(v) for s, v in votes.items()},
                                extra={'per_annotator': per_ann, 'votes_annotators': {s: sorted(v) for s, v in votes.items()},
                                       'earliest_majority_step': primary, 'majority_steps': maj,
                                       'out_of_range_flags': oor, 'n_annotators': len(anns), 'is_correct': is_corr},
                                meta={'file': f, 'annotation_files': [p for p, _ in anns.values()], 'log_source': url,
                                      'source_kind': src_kind, 'framework': 'magentic-one' if 'MAST' in src_kind or 'Hand-Crafted' in src_kind else 'captain-agent'}))
        if limit and len(recs) >= limit:
            break
    load.n_missing = n_missing
    return recs


if __name__ == '__main__':
    rs = load()
    print(len(rs), 'records;', sum(len(r['steps']) for r in rs), 'steps;', load.n_missing, 'logs not fetched;',
          sum(1 for r in rs if r['labels']['error_steps']), 'with error_steps')
    from collections import Counter
    print(Counter(r['subset'] for r in rs), Counter(r['meta']['source_kind'] for r in rs))
    print(sum(len(r['labels']['extra']['out_of_range_flags']) for r in rs), 'out-of-range flags')
    r = rs[0]
    print(r['id'], r['labels']['error_steps'], r['labels']['votes'], r['labels']['error_agent'])
