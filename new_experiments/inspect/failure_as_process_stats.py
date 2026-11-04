#!/usr/bin/env python3
"""Failure-as-a-Process annotation analysis (no step text): fix windows, silent failures, awareness, tail behaviour,
PASS error events, dual-annotator disagreement, matched design (89 tasks x 21 systems)."""
import os, sys, csv, json, ast
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, md_table, summarize
from loaders import load
from collections import Counter, defaultdict
import statistics as st

OUT = os.path.join(RESULTS, 'failure_as_process'); os.makedirs(OUT, exist_ok=True)
recs = load('failure_as_process')
fails = [r for r in recs if r['outcome'] == 'fail']; passes = [r for r in recs if r['outcome'] == 'success']
E = lambda r: r['labels']['extra']
lines = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); lines.append(s)

# ---- 1. fix window / observability
fw = [E(r)['t_lock'] - E(r)['t_err'] for r in fails]
lag = [E(r)['t_obs'] - E(r)['t_lock'] for r in fails if E(r)['t_obs'] is not None]
obs_err = [E(r)['t_obs'] - E(r)['t_err'] for r in fails if E(r)['t_obs'] is not None]
P('## fix window t_lock - t_err', summarize(fw)); P('zero window', sum(1 for x in fw if x == 0), '/', len(fw), f'({100*sum(1 for x in fw if x==0)/len(fw):.1f}%)', ' >=3', sum(1 for x in fw if x >= 3), ' >10', sum(1 for x in fw if x > 10))
P('## t_obs - t_lock (n with t_obs)', summarize(lag)); P('negative (symptom before lock-in)', sum(1 for x in lag if x < 0), ' zero', sum(1 for x in lag if x == 0), ' >=5', sum(1 for x in lag if x >= 5))
P('## t_obs - t_err', summarize(obs_err))
P('silent (no t_obs)', sum(1 for r in fails if E(r)['t_obs'] is None), '/', len(fails))
# relative positions
P('## t_err rel position', summarize([E(r)['t_err'] / max(1, E(r)['m']) for r in fails]))
P('## t_lock rel position', summarize([E(r)['t_lock'] / max(1, E(r)['m']) for r in fails]))
P('## steps after lock-in (m - t_lock)', summarize([E(r)['m'] - E(r)['t_lock'] for r in fails]), 'share of run after lock-in', round(st.mean([(E(r)['m'] - E(r)['t_lock']) / max(1, E(r)['m']) for r in fails]), 3))
# ---- 2. by trigger mechanism
P('\n## by trigger mechanism: n, median fix window, % zero window, % silent, median t_err rel, % forewarning')
tbl = []
for trig, rs in sorted(defaultdict(list, {t: [r for r in fails if E(r)['trigger_mechanism'] == t] for t in set(E(r)['trigger_mechanism'] for r in fails)}).items(), key=lambda kv: -len(kv[1])):
    fwt = [E(r)['t_lock'] - E(r)['t_err'] for r in rs]
    tbl.append([trig, len(rs), st.median(fwt), f'{100*sum(1 for x in fwt if x==0)/len(rs):.0f}', f'{100*sum(1 for r in rs if E(r)["t_obs"] is None)/len(rs):.0f}',
                round(st.median([E(r)['t_err'] / max(1, E(r)['m']) for r in rs]), 2), f'{100*sum(1 for r in rs if E(r)["forewarning_present"])/len(rs):.0f}',
                f'{100*sum(1 for r in rs if E(r)["awareness"]=="never_aware")/len(rs):.0f}', f'{100*sum(1 for r in rs if E(r)["fabrication_present"])/len(rs):.0f}'])
P(md_table(['trigger', 'n', 'med fix win', '% win=0', '% silent', 'med t_err rel', '% forewarn', '% never aware', '% fabric'], tbl))
# ---- 3. awareness x tail x fabrication
P('\n## awareness x tail behaviour')
aw = sorted(set(E(r)['awareness'] for r in fails)); tails = sorted(set(E(r)['tail_dominant_behavior'] for r in fails))
P(md_table(['awareness'] + tails + ['n'], [[a] + [sum(1 for r in fails if E(r)['awareness'] == a and E(r)['tail_dominant_behavior'] == t) for t in tails] + [sum(1 for r in fails if E(r)['awareness'] == a)] for a in aw]))
P('recovery attempts per failed run', summarize([E(r)['num_recovery_attempts'] for r in fails]), '; runs with >=1 attempt', sum(1 for r in fails if E(r)['num_recovery_attempts'] >= 1))
P('verification_ever', Counter(E(r)['verification_ever'] for r in fails), '; verification step after lock-in', sum(1 for r in fails if E(r)['verification_ever'] and E(r)['first_relevant_verification_step'] is not None and E(r)['first_relevant_verification_step'] > E(r)['t_lock']))
P('awareness x silent:', {a: (sum(1 for r in fails if E(r)['awareness'] == a and E(r)['t_obs'] is None), sum(1 for r in fails if E(r)['awareness'] == a)) for a in aw})
P('tail x silent:', {t: (sum(1 for r in fails if E(r)['tail_dominant_behavior'] == t and E(r)['t_obs'] is None), sum(1 for r in fails if E(r)['tail_dominant_behavior'] == t)) for t in tails})
# fabrication onset vs lock
fo = [E(r)['fabrication_onset_step'] - E(r)['t_lock'] for r in fails if E(r)['fabrication_present'] and isinstance(E(r)['fabrication_onset_step'], int)]
P('fabrication onset - t_lock', summarize(fo), 'fabrication at last step', sum(1 for r in fails if E(r)['fabrication_present'] and E(r)['fabrication_onset_step'] == E(r)['m']))
# forewarning
fwp = [r for r in fails if E(r)['forewarning_present']]
P('forewarning present', len(fwp), '/', len(fails), '; forewarning_first_step < t_err', sum(1 for r in fwp if E(r)['forewarning_first_step'] < E(r)['t_err']), '== t_err', sum(1 for r in fwp if E(r)['forewarning_first_step'] == E(r)['t_err']), '> t_err', sum(1 for r in fwp if E(r)['forewarning_first_step'] > E(r)['t_err']))
P('forewarning types', Counter(t for r in fwp for t in (E(r)['forewarning_types'] or [])))
# ---- 4. action segments: what code is at t_err / t_lock / t_obs
def code_at(r, t):
    for a, b, c in (E(r)['action_segments'] or []):
        if a <= t <= b: return c
    return None
P('\n## action code at t_err / t_lock / t_obs (E explore P plan W write X execute V verify C claim R repair O other)')
P('t_err', Counter(code_at(r, E(r)['t_err']) for r in fails)); P('t_lock', Counter(code_at(r, E(r)['t_lock']) for r in fails)); P('t_obs', Counter(code_at(r, E(r)['t_obs']) for r in fails if E(r)['t_obs']))
P('last step code FAIL', Counter(code_at(r, E(r)['m']) for r in fails), ' PASS', Counter(code_at(r, E(r)['m']) for r in passes))
# segment at t_err: is it the first W/X segment?
def first_code_step(r, codes):
    for a, b, c in (E(r)['action_segments'] or []):
        if c in codes: return a
    return None
P('t_err == first W step', sum(1 for r in fails if first_code_step(r, 'W') == E(r)['t_err']), '; t_err == first X step', sum(1 for r in fails if first_code_step(r, 'X') == E(r)['t_err']), '; t_err in first segment', sum(1 for r in fails if E(r)['action_segments'] and E(r)['action_segments'][0][0] <= E(r)['t_err'] <= E(r)['action_segments'][0][1]))
# ---- 5. PASS runs
P('\n## PASS runs: error events')
ne = [E(r)['num_error_events'] for r in passes]; P('error events', summarize(ne), 'share >=1', round(sum(1 for x in ne if x >= 1) / len(ne), 3))
P('recoveries', summarize([E(r)['num_recoveries'] for r in passes]), 'max detour', summarize([E(r)['max_detour_length'] for r in passes if E(r)['max_detour_length'] is not None]))
P('first_error_step rel', summarize([E(r)['first_error_step'] / max(1, E(r)['m']) for r in passes if E(r)['first_error_step']]))
P('suspicious pass', sum(1 for r in passes if E(r)['suspicious_pass']), Counter(E(r)['suspicious_pass_type'] for r in passes if E(r)['suspicious_pass']))
P('solution_directness', Counter(E(r)['solution_directness'] for r in passes), ' verification_before_claim', Counter(E(r)['verification_before_claim'] for r in passes))
P('near miss', sum(1 for r in passes if E(r)['near_miss']))
peo = Counter((E(r)['pass_error_observability'] or {}).get('label') for r in passes); P('pass error observability', peo)
# compare: first error event in PASS vs t_err in FAIL for the same task
P('\n## matched design: same task, FAIL t_err vs PASS first_error_step (absolute)')
bytask = defaultdict(lambda: {'fail': [], 'success': []})
for r in recs: bytask[r['meta']['task_id']][r['outcome']].append(r)
pairs = []
for t, d in bytask.items():
    if d['fail'] and d['success']:
        fe = st.median([E(r)['t_err'] for r in d['fail']]); pe = [E(r)['first_error_step'] for r in d['success'] if E(r)['first_error_step']]
        if pe: pairs.append((t, fe, st.median(pe), len(d['fail']), len(d['success'])))
P('tasks with both', len(pairs), '; median over tasks of (median FAIL t_err)', st.median([p[1] for p in pairs]), 'vs (median PASS first error)', st.median([p[2] for p in pairs]))
P('pass rate per task', summarize([len(d['success']) / (len(d['success']) + len(d['fail'])) for d in bytask.values()]), '; tasks with 0 pass', sum(1 for d in bytask.values() if not d['success']), '; tasks all pass', sum(1 for d in bytask.values() if not d['fail']))
# per-system (scaffold x model) silent share, fabrication share
P('\n## per system: n fail, pass rate, % silent, % fabrication, median fix window, % verification theatre')
tbl = []
sysd = defaultdict(lambda: {'fail': [], 'success': []})
for r in recs: sysd[(r['subset'], r['meta']['backbone'])][r['outcome']].append(r)
for k, d in sorted(sysd.items()):
    f = d['fail']
    tbl.append([f'{k[0]}/{k[1]}', len(f), f'{100*len(d["success"])/(len(f)+len(d["success"])):.0f}', f'{100*sum(1 for r in f if E(r)["t_obs"] is None)/len(f):.0f}', f'{100*sum(1 for r in f if E(r)["fabrication_present"])/len(f):.0f}',
                st.median([E(r)['t_lock'] - E(r)['t_err'] for r in f]), f'{100*sum(1 for r in f if E(r)["tail_dominant_behavior"]=="verification_theater")/len(f):.0f}', f'{100*sum(1 for r in f if E(r)["awareness"]=="never_aware")/len(f):.0f}', st.median([E(r)['m'] for r in f])])
P(md_table(['system', 'n fail', 'pass%', '% silent', '% fabric', 'med fix win', '% verif theatre', '% never aware', 'med m'], tbl))
# ---- 6. dual annotation
P('\n## dual annotation (docs/kappa_agreement/dual_annotations.csv): released == annotator A for t_err in 1184/1184')
rows = list(csv.DictReader(open(os.path.join(os.path.dirname(recs[0]['meta']['file']), '..', 'docs', 'kappa_agreement', 'dual_annotations.csv'))))
by = defaultdict(dict)
for x in rows: by[x['label']][int(x['item'])] = (x['annotator_A'], x['annotator_B'])
for lab in ('t_err', 't_lock', 't_obs'):
    d = by[lab]; diffs = []
    for i, (a, b) in d.items():
        try: diffs.append(int(b) - int(a))
        except ValueError: diffs.append(None)
    dd = [x for x in diffs if x is not None]
    P(lab, 'n', len(d), 'exact agree', sum(1 for x in dd if x == 0), f'({100*sum(1 for x in dd if x==0)/len(dd):.1f}%)', 'B later', sum(1 for x in dd if x > 0), 'B earlier', sum(1 for x in dd if x < 0), '|diff|>=3', sum(1 for x in dd if abs(x) >= 3), '|diff|>=10', sum(1 for x in dd if abs(x) >= 10), 'diff dist', Counter(dd).most_common(8), 'non-int', len(diffs) - len(dd))
# relate t_err disagreement to run properties
d = by['t_err']; big = []; small = []
for i, r in enumerate(fails):
    a, b = d[i]
    try: dif = abs(int(b) - int(a))
    except ValueError: continue
    (big if dif >= 3 else small).append(r)
def prof(rs):
    return dict(n=len(rs), med_m=st.median([E(r)['m'] for r in rs]), med_fix=st.median([E(r)['t_lock'] - E(r)['t_err'] for r in rs]), silent=round(sum(1 for r in rs if E(r)['t_obs'] is None) / len(rs), 2),
                long=round(sum(1 for r in rs if E(r)['long_traj']) / len(rs), 2), trig=Counter(E(r)['trigger_mechanism'] for r in rs).most_common(4), unc_terr=round(sum(1 for r in rs if 't_err' in (E(r)['uncertain_fields'] or [])) / len(rs), 2),
                conf=Counter(E(r)['timepoint_confidence'] for r in rs).most_common(3))
P('t_err |A-B|>=3:', prof(big)); P('t_err |A-B|<3:', prof(small))
for lab in ('root_cause (trigger)', 'awareness', 'tail_behavior', 'fabrication_present'):
    d = by[lab]; dis = Counter((a, b) for a, b in d.values() if a != b)
    P(lab, 'disagree', sum(dis.values()), '/', len(d), 'top confusions', dis.most_common(6))
# uncertain fields / timepoint confidence in release
P('\nuncertain_fields (FAIL)', Counter(f for r in fails for f in (E(r)['uncertain_fields'] or [])), ' timepoint_confidence', Counter(E(r)['timepoint_confidence'] for r in fails))
P('long_traj FAIL', sum(1 for r in fails if E(r)['long_traj']), 'PASS', sum(1 for r in passes if E(r)['long_traj']))
open(os.path.join(OUT, 'g3_stats.md'), 'w').write('\n'.join(lines))
