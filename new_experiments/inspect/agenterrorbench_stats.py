#!/usr/bin/env python3
"""Targeted statistics for AgentErrorBench (beyond length/position).
Uses results/agenterrorbench/compact_turns.json (from agenterrorbench_compact.py) plus the raw records for the
admissible-action lists. Writes results/agenterrorbench/stats.md and stats_per_run.jsonl.
Measures: (1) malformed-action / 'Nothing happens' signature in ALFWorld and WebShop, where it starts vs the label;
(2) loop / repetition before vs after the label (identical actions, bigram repeats, novel observations);
(3) label category vs trajectory signature; (4) WebShop / GAIA termination and tool-error signatures; (5) label-text consistency."""
import json, os, re, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, read_json, append_jsonl, md_table, summarize  # noqa
from common.schema import error_step  # noqa
from loaders import load  # noqa

R = os.path.join(RESULTS, 'agenterrorbench')
turns_all = read_json(os.path.join(R, 'compact_turns.json'))


def admissible(content):
    m = re.search(r'admissible actions of the current situation are:\s*(.*?)(?:\.\s*\n\s*\n|\n\nNow it|\n\nPlease begin|$)', content, re.S)
    if not m:
        return None
    return set(x.strip().lower() for x in re.findall(r"'([^']*)'", m.group(1)))


def norm(a):
    a = a.strip().strip("'\"").strip()
    q = re.findall(r"'([^']{3,60})'", a)
    if q and not a.startswith('search[') and not a.startswith('click['):
        a = q[0]
    a = re.sub(r'^(?:I choose the action:|Choose the action:|Based on the plan, the chosen action is:|the chosen action for the current step is:|Given the admissible actions, the chosen action for the current step is:)\s*', '', a, flags=re.I)
    a = a.strip().strip("'\"").strip().rstrip('.').strip().strip("'\"")
    return a.lower()


def pct(a, b):
    return f'{100 * a / b:.1f}%' if b else 'n/a'


rows = []
recs = {r['id']: r for r in load('agenterrorbench')}
for rid, d in turns_all.items():
    rec = recs[rid]
    env = rec['subset']
    g = d['gold']
    turns = d['turns']
    steps = rec['steps']
    acts_raw = [t['action'] for t in turns]
    acts = [norm(a) for a in acts_raw]
    obs_after = [(t['obs_after'] or '') for t in turns]
    obs_before = [(t['obs_before'] or '') for t in turns]
    gold_pos = next((i for i, t in enumerate(turns) if t['idx'] == g), None)
    # validity vs admissible list (ALFWorld / WebShop)
    valid, malformed, inadmissible, nothing = [], [], [], []
    for i, t in enumerate(turns):
        adm = admissible(steps[t['idx'] - 1]['content']) if t['idx'] >= 1 else None
        raw = acts_raw[i].strip().lower()
        n = acts[i]
        nh = obs_after[i].strip().lower().startswith('nothing happens') or 'invalid action' in obs_after[i].lower()[:200]
        nothing.append(nh)
        if adm is None:
            valid.append(None); malformed.append(False); inadmissible.append(False); continue
        if env == 'webshop':
            # webshop admissible list is given as 'click[x]' ... ; search[...] is always allowed
            ok = raw in adm or n in adm or n.startswith('search[')
            valid.append(ok); malformed.append((not ok) and (nh)); inadmissible.append(False)
        else:
            ok = raw in adm
            valid.append(ok)
            malformed.append((not ok) and n in adm)       # right action, wrong surface form (quotes / prose)
            inadmissible.append((not ok) and n not in adm)  # not available here (wrong place / object)
    # loop metrics before / after gold
    def seg(xs, lo, hi):
        return xs[lo:hi]
    def rep_frac(a):
        seen, rep = set(), 0
        for x in a:
            if x in seen: rep += 1
            seen.add(x)
        return rep / len(a) if a else None
    def bigram_rep(a):
        bg = [tuple(a[i:i + 2]) for i in range(len(a) - 1)]
        return (len(bg) - len(set(bg))) / len(bg) if bg else None
    def novel_obs_frac(o):
        seen, nov = set(), 0
        for x in o:
            k = x.strip()[:200]
            if k not in seen: nov += 1
            seen.add(k)
        return nov / len(o) if o else None
    def max_consec_same(a):
        best = cur = 1
        for i in range(1, len(a)):
            cur = cur + 1 if a[i] == a[i - 1] else 1
            best = max(best, cur)
        return best if a else 0
    gp = gold_pos if gold_pos is not None else len(turns)
    before_a, after_a = acts[:gp], acts[gp + 1:]
    before_o, after_o = obs_after[:gp], obs_after[gp + 1:]
    first_nothing = next((i for i, x in enumerate(nothing) if x), None)
    first_bad = next((i for i, x in enumerate(malformed) if x), None)
    first_inadm = next((i for i, x in enumerate(inadmissible) if x), None)
    last_act = acts[-1] if acts else ''
    ended = 'answer' if last_act.startswith('answer:') else ('buy' if 'buy now' in last_act else ('cap' if len(turns) >= 30 else 'other'))
    tool_err = sum(1 for o in obs_after if re.search(r'\b(error|exception|traceback|failed|not found|invalid)\b', o[:400], re.I))
    row = {'id': rid, 'env': env, 'backbone': rec['meta']['backbone'], 'n_turns': len(turns), 'gold_turn': gold_pos + 1 if gold_pos is not None else None,
           'cats': d['cats'], 'module': d['cats'][0] if d['cats'] else None, 'ftype': (d['cats'][1].split('.', 1)[1] if len(d['cats']) > 1 and '.' in d['cats'][1] else ''),
           'n_nothing': sum(nothing), 'n_malformed': sum(malformed), 'n_inadmissible': sum(inadmissible), 'n_valid': sum(1 for v in valid if v),
           'first_nothing_turn': first_nothing + 1 if first_nothing is not None else None, 'first_malformed_turn': first_bad + 1 if first_bad is not None else None,
           'first_inadmissible_turn': first_inadm + 1 if first_inadm is not None else None,
           'gold_is_nothing': nothing[gold_pos] if gold_pos is not None else None, 'gold_is_malformed': malformed[gold_pos] if gold_pos is not None else None,
           'gold_is_inadmissible': inadmissible[gold_pos] if gold_pos is not None else None,
           'gold_obs_before_nothing': (obs_before[gold_pos].strip().lower().startswith('nothing happens')) if gold_pos is not None else None,
           'nothing_before': sum(nothing[:gp]), 'nothing_after': sum(nothing[gp + 1:]),
           'rep_before': rep_frac(before_a), 'rep_after': rep_frac(after_a), 'bigram_before': bigram_rep(before_a), 'bigram_after': bigram_rep(after_a),
           'novel_before': novel_obs_frac(before_o), 'novel_after': novel_obs_frac(after_o), 'max_consec_same': max_consec_same(acts),
           'distinct_frac': len(set(acts)) / len(acts) if acts else None, 'ended': ended, 'tool_err_obs': tool_err,
           'gold_action': acts_raw[gold_pos][:120] if gold_pos is not None else None, 'reason': d['reason']}
    rows.append(row)

out = []
def tbl(title, headers, data):
    out.append(f'\n### {title}\n'); out.append(md_table(headers, data))

# --- 1. malformed action signature
tbl('1. Action-validity signature per env x backbone (turn counts summed over runs)', ['env', 'backbone', 'runs', 'turns', 'valid', 'malformed (right action, wrong surface form)', 'inadmissible', "obs 'Nothing happens'", 'runs with >=1 malformed', 'runs with >=50% Nothing'],
    [[e, b, len(rs), sum(r['n_turns'] for r in rs), sum(r['n_valid'] for r in rs), sum(r['n_malformed'] for r in rs), sum(r['n_inadmissible'] for r in rs), sum(r['n_nothing'] for r in rs),
      sum(1 for r in rs if r['n_malformed']), sum(1 for r in rs if r['n_nothing'] >= 0.5 * r['n_turns'])]
     for (e, b), rs in sorted(defaultdict(list, {k: [r for r in rows if (r['env'], r['backbone']) == k] for k in {(r['env'], r['backbone']) for r in rows}}).items())])

# --- 2. where is the label relative to the first malformed / first Nothing
alf = [r for r in rows if r['env'] == 'alfworld' and r['gold_turn']]
def rel(r, key):
    if r[key] is None: return 'none'
    return 'label<first' if r['gold_turn'] < r[key] else ('label==first' if r['gold_turn'] == r[key] else 'label>first')
tbl('2. ALFWorld: label turn vs first malformed action / first inadmissible action / first "Nothing happens"', ['relation', 'vs first malformed', 'vs first inadmissible', 'vs first Nothing'],
    [[k, sum(1 for r in alf if rel(r, 'first_malformed_turn') == k), sum(1 for r in alf if rel(r, 'first_inadmissible_turn') == k), sum(1 for r in alf if rel(r, 'first_nothing_turn') == k)] for k in ('none', 'label<first', 'label==first', 'label>first')])
tbl('2b. ALFWorld: is the labelled turn itself a malformed / inadmissible / Nothing-happens turn, by module', ['module', 'n', 'gold malformed', 'gold inadmissible', "gold -> 'Nothing happens'", "obs before gold = 'Nothing happens'", 'median Nothing count in run'],
    [[m, len(rs), sum(1 for r in rs if r['gold_is_malformed']), sum(1 for r in rs if r['gold_is_inadmissible']), sum(1 for r in rs if r['gold_is_nothing']), sum(1 for r in rs if r['gold_obs_before_nothing']), summarize([r['n_nothing'] for r in rs])['median']]
     for m, rs in sorted(defaultdict(list, {k: [r for r in alf if r['module'] == k] for k in {r['module'] for r in alf}}).items())])

# --- 3. loops before vs after label
def mean(xs):
    xs = [x for x in xs if x is not None]; return f'{sum(xs) / len(xs):.2f}' if xs else 'n/a'
tbl('3. Repetition before vs after the labelled turn (means over runs; cap runs only, n_turns=30)', ['env', 'runs', 'repeat-action frac before', 'after', 'bigram repeat before', 'after', 'novel-obs frac before', 'after', "'Nothing' per turn before", 'after', 'median max consecutive identical action'],
    [[e, len(rs), mean([r['rep_before'] for r in rs]), mean([r['rep_after'] for r in rs]), mean([r['bigram_before'] for r in rs]), mean([r['bigram_after'] for r in rs]), mean([r['novel_before'] for r in rs]), mean([r['novel_after'] for r in rs]),
      mean([r['nothing_before'] / max(1, r['gold_turn'] - 1) for r in rs if r['gold_turn'] and r['gold_turn'] > 1]), mean([r['nothing_after'] / max(1, r['n_turns'] - r['gold_turn']) for r in rs if r['gold_turn'] and r['n_turns'] > r['gold_turn']]), summarize([r['max_consec_same'] for r in rs])['median']]
     for e, rs in [(e, [r for r in rows if r['env'] == e and r['n_turns'] >= 30 and r['gold_turn'] and 1 < r['gold_turn'] < 30]) for e in ('alfworld', 'webshop', 'gaia')]])
# distinct-fraction distribution
tbl('3b. Distinct-action fraction and tail stagnation per env (all runs)', ['env', 'runs', 'median distinct-action frac', 'runs with distinct frac < 0.5', 'runs whose last 10 turns contain <=3 distinct actions', 'runs with >=5 consecutive identical actions'],
    [[e, len(rs), summarize([r['distinct_frac'] for r in rs])['median'], sum(1 for r in rs if r['distinct_frac'] is not None and r['distinct_frac'] < 0.5), sum(1 for r in rs if len(set(norm(t['action']) for t in turns_all[r['id']]['turns'][-10:])) <= 3 and r['n_turns'] >= 10), sum(1 for r in rs if r['max_consec_same'] >= 5)]
     for e, rs in [(e, [r for r in rows if r['env'] == e]) for e in ('alfworld', 'webshop', 'gaia')]])

# --- 4. termination
tbl('4. How runs end, per env (answer / buy / step cap / other) and tool-error observations', ['env', 'runs', 'answer', 'buy now', 'cap (30 turns)', 'other', 'runs with >=1 error-like observation', 'label at last turn'],
    [[e, len(rs)] + [sum(1 for r in rs if r['ended'] == k) for k in ('answer', 'buy', 'cap', 'other')] + [sum(1 for r in rs if r['tool_err_obs']), sum(1 for r in rs if r['gold_turn'] == r['n_turns'])]
     for e, rs in [(e, [r for r in rows if r['env'] == e]) for e in ('alfworld', 'webshop', 'gaia')]])
tbl('4b. Module of the label by how the run ended', ['ended', 'n', 'planning', 'reflection', 'memory', 'action', 'system'],
    [[k, len(rs)] + [sum(1 for r in rs if r['module'] == m) for m in ('planning', 'reflection', 'memory', 'action', 'system')] for k, rs in [(k, [r for r in rows if r['ended'] == k]) for k in ('answer', 'buy', 'cap', 'other')]])

# --- 5. label text consistency: numbers in the reason that differ from the label turn
num_mismatch = []
for r in rows:
    if not r['reason']: continue
    nums = [int(x) for x in re.findall(r'[Ss]tep\s*(\d+)', r['reason'])]
    if nums and r['gold_turn'] not in nums:
        num_mismatch.append((r['id'], r['gold_turn'], nums))
tbl('5. Label-text consistency', ['check', 'count'],
    [['records with empty failure_type', sum(1 for r in rows if r['ftype'] == '')],
     ['records with no reason text', sum(1 for r in rows if not r['reason'])],
     ['reason mentions step numbers, none equal to the label turn', len(num_mismatch)],
     ['label = last turn (30) with category system.step_limit', sum(1 for r in rows if r['gold_turn'] == r['n_turns'] and 'step_limit' in (r['ftype'] or ''))],
     ['label = last turn, other category', sum(1 for r in rows if r['gold_turn'] == r['n_turns'] and 'step_limit' not in (r['ftype'] or ''))],
     ['ALFWorld runs with >=1 malformed action but label module != action', sum(1 for r in alf if r['n_malformed'] and r['module'] != 'action')],
     ['ALFWorld runs with >=10 malformed actions', sum(1 for r in alf if r['n_malformed'] >= 10)],
     ['ALFWorld runs with >=10 malformed actions whose label module != action', sum(1 for r in alf if r['n_malformed'] >= 10 and r['module'] != 'action')]])
out.append('\nreason/label step mismatches: ' + '; '.join(f'{i} label {g} reason {n}' for i, g, n in num_mismatch[:30]))
with open(os.path.join(R, 'stats.md'), 'w') as fh:
    fh.write('# AgentErrorBench targeted statistics\n' + '\n'.join(out))
p = os.path.join(R, 'stats_per_run.jsonl')
if os.path.exists(p): os.remove(p)
for r in rows: append_jsonl(p, r)
print('\n'.join(out))
