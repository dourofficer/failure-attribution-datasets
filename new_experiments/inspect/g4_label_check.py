"""Label-vs-content LLM check (G4). For each sampled record the model sees the task + full trajectory (no ground truth,
no outcome statement) with the labelled step MARKED, and answers: (1) is the marked step wrong on its own (judged from the
prefix only)? (2) does a later step correct/contradict it? (3) which later steps show visible symptoms? (4) is the final
failure attributable to the marked step, or to a different step? (5) one-line description of what the marked step does
wrong; (6) for datasets with a mode label, which taxonomy mode fits best (free text).
Usage: python3 -I inspect/g4_label_check.py <slug> [--n 60] [--seed 0] [--ids ...] [--per-subset K] [--workers 4] [--tag T]
Writes results/<slug>/label_check[_tag].jsonl"""
import argparse
import json
import os
import random
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common.util import RESULTS, append_jsonl, md_table  # noqa: E402
from common.llm import chat_json_many  # noqa: E402
from common.render import truncate  # noqa: E402
from common.schema import error_step  # noqa: E402

SYSTEM = ('You are an expert auditor of LLM agent trajectories. You will see a task and a trajectory in which ONE step is '
          'marked with <<< MARKED >>>. Answer precisely and only from what is in the text. Do not assume the marked step is wrong.')
PROMPT = ('TASK:\n{task}\n\nTRAJECTORY:\n\n{traj}\n\nQuestions about the MARKED step ([step {k}], by {agent}):\n'
          '1. local_wrong: judging ONLY from the task and the steps BEFORE and INCLUDING the marked step, does the marked step '
          'contain a mistake (wrong fact, wrong computation, contradiction with earlier evidence, wrong tool use, unjustified claim, '
          'deviation from the task)? true/false, and confidence 0-1.\n'
          '2. contradicts_prefix: does the marked step contradict or ignore something established earlier in the trajectory '
          '(an earlier number, a search result, an earlier plan, the task statement)? true/false.\n'
          '3. corrected_later: does any LATER step notice, correct, or override the marked step\'s mistake? true/false, and the step index if so.\n'
          '4. symptoms_later: list the indices of later steps that show visible trouble caused by the marked step (errors, retries, contradictions, loops, "unable to", giving up).\n'
          '5. decisive: given the whole trajectory, is the marked step the step whose correction would most likely have made the run succeed? '
          'Answer "yes", "no_earlier" (an earlier step is the real cause: give index), "no_later" (a later step is the real cause: give index), or "no_other" (e.g. the failure is caused by the environment / the outcome looks actually correct).\n'
          '6. what_wrong: one line describing what the marked step does wrong (or "nothing visible").\n'
          '7. style_odd: does the marked step read differently from the same agent\'s other steps (length, tone, self-description such as '
          '"incorrectly", "again for emphasis", announcing a deviation)? true/false, one phrase why.\n'
          'Answer with one JSON object only: {{"local_wrong": bool, "local_conf": float, "contradicts_prefix": bool, "corrected_later": bool, '
          '"corrected_at": int|null, "symptoms_later": [int], "decisive": "yes|no_earlier|no_later|no_other", "alt_step": int|null, '
          '"what_wrong": str, "style_odd": bool, "style_why": str}}')


def render_marked(rec, k, cap=3500, total_chars=240000):
    lines = []
    for s in rec['steps']:
        tag = f"[step {s['idx']}] {s['agent']}" + (f" ({s['role']})" if s['role'] != 'agent' else '')
        if s['idx'] == k:
            tag = '<<< MARKED >>> ' + tag
        lines.append(tag + ':\n' + truncate(s['content'], cap))
    text = '\n\n'.join(lines)
    while len(text) > total_chars and cap > 400:
        cap = int(cap * 0.6)
        text = '\n\n'.join((('<<< MARKED >>> ' if s['idx'] == k else '') + f"[step {s['idx']}] {s['agent']}" + (f" ({s['role']})" if s['role'] != 'agent' else '') + ':\n' + truncate(s['content'], cap)) for s in rec['steps'])
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('--n', type=int, default=60)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--ids', default=None)
    ap.add_argument('--per-subset', type=int, default=None)
    ap.add_argument('--max-steps', type=int, default=60)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--tag', default='')
    ap.add_argument('--step-override', default=None, help='json {id: step} to mark a different step than the label')
    a = ap.parse_args()
    if a.slug == 'who_and_when_pro':
        from g4_common import load_flagged
        recs = load_flagged()
    else:
        from loaders import load
        recs = load(a.slug)
    recs = [r for r in recs if r['labels']['error_steps'] and len(r['steps']) <= a.max_steps]
    rnd = random.Random(a.seed)
    if a.ids:
        want = set(a.ids.split(','))
        recs = [r for r in recs if r['id'] in want]
    elif a.per_subset:
        by = defaultdict(list)
        for r in recs:
            by[r['subset']].append(r)
        recs = [r for sub in sorted(by) for r in rnd.sample(by[sub], min(a.per_subset, len(by[sub])))]
    else:
        rnd.shuffle(recs)
        recs = recs[:a.n]
    override = json.loads(a.step_override) if a.step_override else {}
    msgs, ks = [], []
    for r in recs:
        k = int(override.get(r['id'], error_step(r)))
        ks.append(k)
        user = PROMPT.format(task=r['task'][:4000], traj=render_marked(r, k), k=k, agent=r['steps'][k]['agent'])
        msgs.append([{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': user}])
    print(f'{len(recs)} records', file=sys.stderr)
    outs = chat_json_many(msgs, workers=a.workers, max_tokens=12000, think=True, tag='g4_label_check')
    name = 'label_check' + (f'_{a.tag}' if a.tag else '')
    path = os.path.join(RESULTS, a.slug, name + '.jsonl')
    if os.path.exists(path):
        os.remove(path)
    rows = []
    for r, k, (p, o) in zip(recs, ks, outs):
        p = p or {}
        row = {'id': r['id'], 'subset': r['subset'], 'n_steps': len(r['steps']), 'marked': k, 'gold': error_step(r), 'agent': r['steps'][k]['agent'],
               'categories': r['labels']['categories'], 'mode': (r['labels']['extra'] or {}).get('mode'), 'error_source': (r['labels']['extra'] or {}).get('error_source'),
               'post_steps': len([s for s in r['steps'] if s['idx'] > k and s['role'] == 'agent']), **{f'q_{kk}': v for kk, v in p.items()},
               'parsed': bool(p), 'finish': o.get('finish_reason'), 'reasoning_tail': (o.get('reasoning') or '')[-1500:]}
        rows.append(row)
        append_jsonl(path, row)
    ok = [x for x in rows if x['parsed']]
    n = len(ok)
    def pct(f):
        return f'{100 * sum(1 for x in ok if f(x)) / max(1, n):.1f}%'
    print(md_table(['metric', 'value'], [
        ['records (parsed)', f'{len(rows)} ({n})'],
        ['local_wrong', pct(lambda x: x.get('q_local_wrong'))],
        ['contradicts_prefix', pct(lambda x: x.get('q_contradicts_prefix'))],
        ['corrected_later', pct(lambda x: x.get('q_corrected_later'))],
        ['has symptoms_later', pct(lambda x: x.get('q_symptoms_later'))],
        ['decisive = yes', pct(lambda x: x.get('q_decisive') == 'yes')],
        ['decisive = no_earlier', pct(lambda x: x.get('q_decisive') == 'no_earlier')],
        ['decisive = no_later', pct(lambda x: x.get('q_decisive') == 'no_later')],
        ['decisive = no_other', pct(lambda x: x.get('q_decisive') == 'no_other')],
        ['style_odd', pct(lambda x: x.get('q_style_odd'))],
    ]))
    by = defaultdict(list)
    for x in ok:
        by[x['subset']].append(x)
    print(md_table(['subset', 'n', 'local_wrong', 'contradicts_prefix', 'corrected_later', 'symptoms', 'decisive yes', 'style_odd'],
                   [[s, len(v)] + [f'{100 * sum(1 for x in v if f(x)) / len(v):.0f}' for f in (lambda x: x.get('q_local_wrong'), lambda x: x.get('q_contradicts_prefix'), lambda x: x.get('q_corrected_later'), lambda x: bool(x.get('q_symptoms_later')), lambda x: x.get('q_decisive') == 'yes', lambda x: x.get('q_style_odd'))] for s, v in sorted(by.items())]))
    print('wrote', path)


if __name__ == '__main__':
    main()
