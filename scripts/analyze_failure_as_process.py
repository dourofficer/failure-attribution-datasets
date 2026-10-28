#!/usr/bin/env python3
"""Analyse the 'Failure as a Process' annotation release. Usage: python3 -I analyze_failure_as_process.py"""
import collections
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

SLUG = 'failure_as_process'
R = os.path.join(C.DATA, SLUG, 'repo_cli_trajectory_analysis')
recs = json.load(open(os.path.join(R, 'data/traj_data_v2_all89tasks.json')))
tasks = {t['task_id']: t for t in json.load(open(os.path.join(R, 'data/merged_tasks.json')))}
print('records', len(recs), 'tasks', len(tasks))
n_files = len(os.listdir(os.path.join(R, 'data/v2_annotations')))

fails = [r for r in recs if 't_commit' in r]
passes = [r for r in recs if 't_commit' not in r]
for r in recs:
    task, scaffold, model = r['case_id'].split('__')
    r['_task'], r['_scaffold'], r['_model'] = task, scaffold, model
    r['_difficulty'] = tasks.get(task, {}).get('difficulty')
    r['_category'] = tasks.get(task, {}).get('category')
print('fail/pass', len(fails), len(passes))

m_all = [r['m'] for r in recs]
m_fail = [r['m'] for r in fails]
m_pass = [r['m'] for r in passes]
t_err = [r['t_err'] for r in fails]
t_commit = [r['t_commit'] for r in fails]
t_surface = [r['t_surface'] for r in fails if r.get('t_surface') is not None]
rel_err = [r['t_err'] / r['m'] for r in fails]
rel_commit = [r['t_commit'] / r['m'] for r in fails]
rel_surf = [r['t_surface'] / r['m'] for r in fails if r.get('t_surface') is not None]
fixwin = [r['t_commit'] - r['t_err'] for r in fails]
obslag = [r['t_surface'] - r['t_commit'] for r in fails if r.get('t_surface') is not None]
cnt = lambda key, rs: collections.Counter(str(r.get(key)) for r in rs)

kappa = list(csv.DictReader(open(os.path.join(R, 'docs/kappa_agreement/kappa_results.csv'))))

stats = {
    'n_trajectories': len(recs), 'n_failed': len(fails), 'n_success': len(passes),
    'n_annotation_files': n_files,
    'raw_trajectories_included': False,
    'steps_per_traj': m_all, 'steps_per_traj_failed': m_fail, 'steps_per_traj_success': m_pass,
    'total_steps': sum(m_all),
    'error_step_rel_pos': [round(x, 4) for x in rel_err],
    'lock_step_rel_pos': [round(x, 4) for x in rel_commit],
    'surface_step_rel_pos': [round(x, 4) for x in rel_surf],
    't_err': t_err, 't_commit': t_commit, 't_surface': t_surface,
    'fix_window': fixwin, 'observability_lag': obslag,
    'silent_failures_no_t_surface': sum(1 for r in fails if r.get('t_surface') is None),
    'agents_per_traj': [1] * len(recs),
    'faulty_agent_counts': {'single CLI coding agent': len(fails)},
    'category_counts': dict(cnt('trigger_mechanism', fails)),
    'trigger_group_counts': {'epistemic': sum(1 for r in fails if r['trigger_mechanism'] in ('false_premise', 'misread_output', 'ignored_signal', 'spec_neglect', 'premature_action')),
                             'competence': sum(1 for r in fails if r['trigger_mechanism'] in ('knowledge_gap', 'capability_limit')),
                             'environment_other': sum(1 for r in fails if r['trigger_mechanism'] in ('environment_obstacle_mishandled', 'other'))},
    'primary_failure_layer_counts': dict(cnt('primary_failure_layer', fails)),
    'primary_failure_category_counts': dict(cnt('primary_failure_category', fails)),
    'awareness_counts': dict(cnt('awareness', fails)),
    'tail_dominant_behavior_counts': dict(cnt('tail_dominant_behavior', fails)),
    'fabrication_present_counts': dict(cnt('fabrication_present', fails)),
    'fabrication_type_counts': dict(cnt('fabrication_type', [r for r in fails if r.get('fabrication_present')])),
    'forewarning_present_counts': dict(cnt('forewarning_present', fails)),
    'timepoint_confidence_counts': dict(cnt('timepoint_confidence', fails)),
    'solution_directness_counts_pass': dict(cnt('solution_directness', passes)),
    'suspicious_pass_counts': dict(cnt('suspicious_pass', passes)),
    'source_benchmark_counts': {'Terminal-Bench (89 tasks)': len(recs)},
    'scaffold_counts': dict(collections.Counter(r['_scaffold'] for r in recs)),
    'scaffold_counts_failed': dict(collections.Counter(r['_scaffold'] for r in fails)),
    'model_counts': dict(collections.Counter(r['_model'] for r in recs)),
    'model_counts_failed': dict(collections.Counter(r['_model'] for r in fails)),
    'difficulty_counts': dict(collections.Counter(str(r['_difficulty']) for r in recs)),
    'task_category_counts': dict(collections.Counter(str(r['_category']) for r in recs)),
    'pass_rate_by_system': {f'{s}/{m}': round(sum(1 for r in recs if r['_scaffold'] == s and r['_model'] == m and 't_commit' not in r) / max(1, sum(1 for r in recs if r['_scaffold'] == s and r['_model'] == m)), 3) for s in sorted(set(r['_scaffold'] for r in recs)) for m in sorted(set(r['_model'] for r in recs))},
    'inter_annotator_kappa': kappa,
    'splits': {'all (single file traj_data_v2_all89tasks.json)': len(recs), 'FAIL': len(fails), 'PASS': len(passes)},
    'chars_per_traj': [],
    'chars_note': 'raw trajectory text is not part of the release, so character counts cannot be computed',
}
C.write_json(os.path.join(C.NOTES, f'{SLUG}_stats.json'), stats)

L = []
L.append(C.md_table(C.SUMM_HEADERS, [
    C.summ_row('steps per trajectory (all 1,794)', m_all),
    C.summ_row('steps per trajectory (FAIL, 1,184)', m_fail),
    C.summ_row('steps per trajectory (PASS, 610)', m_pass),
    C.summ_row('t_err (decisive error step, 1-based)', t_err),
    C.summ_row('t_commit = t_lock (lock-in step)', t_commit),
    C.summ_row('t_surface = t_obs (first observable signal; non-silent only)', t_surface),
    C.summ_row('t_err / m (relative position)', rel_err),
    C.summ_row('t_lock / m', rel_commit),
    C.summ_row('t_obs / m (non-silent only)', rel_surf),
    C.summ_row('fix window t_lock − t_err', fixwin),
    C.summ_row('observability lag t_obs − t_lock (non-silent)', obslag),
    C.summ_row('num_recovery_attempts (FAIL)', [r.get('num_recovery_attempts') for r in fails]),
    C.summ_row('num_error_events (PASS)', [r.get('num_error_events') for r in passes]),
]))
L.append(f"\nTotal annotated steps: {sum(m_all):,} (FAIL {sum(m_fail):,}, PASS {sum(m_pass):,}). Silent failures (no t_obs): {stats['silent_failures_no_t_surface']} / {len(fails)} ({100 * stats['silent_failures_no_t_surface'] / len(fails):.1f}%).\n")
L.append('Histogram of steps per trajectory (all):\n')
L.append(C.hist_md(m_all, [0, 10, 20, 30, 40, 60, 80, 120, 200]))
L.append('\nHistogram of t_err relative position (FAIL):\n')
L.append(C.md_table(['rel. position', 'n', '%'], [[f'{a:.1f}-{a + 0.2:.1f}', c, f'{100 * c / len(rel_err):.1f}'] for a in [0.0, 0.2, 0.4, 0.6, 0.8] for c in [sum(1 for x in rel_err if a <= x < a + 0.2 or (a == 0.8 and x >= 1.0))]]))
L.append('\nTrigger mechanism (root cause at t_err; FAIL only):\n')
L.append(C.counts_md(collections.Counter(r['trigger_mechanism'] for r in fails), 'trigger_mechanism'))
L.append('\nTrigger groups: ' + json.dumps(stats['trigger_group_counts']) + '\n')
L.append('Primary failure layer / category (free-text-ish taxonomy fields, FAIL):\n')
L.append(C.counts_md(collections.Counter(str(r.get('primary_failure_layer')) for r in fails), 'primary_failure_layer'))
L.append('')
L.append(C.counts_md(collections.Counter(str(r.get('primary_failure_category')) for r in fails), 'primary_failure_category', top=15))
L.append('\nAwareness after lock-in / dominant tail behaviour / fabrication:\n')
L.append(C.counts_md(collections.Counter(r['awareness'] for r in fails), 'awareness'))
L.append('')
L.append(C.counts_md(collections.Counter(r['tail_dominant_behavior'] for r in fails), 'tail_dominant_behavior'))
L.append('')
L.append(C.counts_md(collections.Counter(str(r.get('fabrication_type')) for r in fails if r.get('fabrication_present')), 'fabrication_type (of %d fabrication-present)' % sum(1 for r in fails if r.get('fabrication_present'))))
L.append('\nScaffold × model: trajectories (failed) and pass rate:\n')
scs = sorted(set(r['_scaffold'] for r in recs))
mds = sorted(set(r['_model'] for r in recs))
rows = []
for s in scs:
    row = [s]
    for m in mds:
        tot = sum(1 for r in recs if r['_scaffold'] == s and r['_model'] == m)
        f = sum(1 for r in fails if r['_scaffold'] == s and r['_model'] == m)
        row.append(f'{tot} ({f} fail, {100 * (tot - f) / max(1, tot):.0f}% pass)')
    rows.append(row)
L.append(C.md_table(['scaffold'] + mds, rows))
L.append('\nTask difficulty / category (all trajectories):\n')
L.append(C.counts_md(collections.Counter(str(r['_difficulty']) for r in recs), 'difficulty'))
L.append('')
L.append(C.counts_md(collections.Counter(str(r['_category']) for r in recs), 'task category'))
L.append('\nInter-annotator agreement shipped in `docs/kappa_agreement/kappa_results.csv`:\n')
L.append(C.md_table(['label', 'kappa type', 'n', 'reported', 'recomputed'], [[k['label'], k['kappa_type'], k['n'], k['reported_in_paper'], k['computation_results']] for k in kappa]))
C.write_fragment(SLUG, 'stats', '\n'.join(L))

# ---------- example: the paper's RQ2 case (acl-permissions-inheritance · mini-swe · gemini) ----------
cid = 'acl-permissions-inheritance__miniswe__gemini'
ann = json.load(open(os.path.join(R, 'data/v2_annotations', cid + '.json')))
cs = next((c for c in json.load(open(os.path.join(R, 'data/case_studies_annotations.json'))) if c['case_id'] == cid), None)
task = tasks['acl-permissions-inheritance']
C.write_json(os.path.join(C.NOTES, f'{SLUG}_example.json'), {'annotation_file': f'data/v2_annotations/{cid}.json', 'annotation': ann, 'case_study_record': cs, 'task_metadata': task,
                                                              'note': 'raw trajectory not part of the release; step text reconstructed from the paper (Fig. 6) / replication-package figure source scripts/make_case_cards_v3.py'})
# Step text transcribed from the replication package figure source (scripts/make_case_cards_v3.py, CASES['sudo']),
# which renders Fig. 6 of the paper. Steps 5-10 are only summarised there.
turns = {
    1: ("I'll create the directory /srv/shared as requested. I'll use sudo because creating directories in /srv requires root privileges.",
        'sudo mkdir -p /srv/shared', '/bin/sh: 1: sudo: not found'),
    2: ("It seems I don't have sudo privileges. I'll try creating /srv/shared without it, and also create the research group since it probably doesn't exist.",
        'mkdir -p /srv/shared && sudo groupadd research', '/bin/sh: 1: sudo: not found'),
    3: ("I lack permissions to create /srv/shared. I'll use /tmp/srv/shared instead, and create the group and users alice and bob to test the ACL requirements.",
        'mkdir -p /tmp/srv/shared && sudo groupadd research && sudo useradd alice && sudo useradd bob', '/bin/sh: 1: sudo: not found'),
    4: ("I'm blocked — I can't create directories in /srv or /tmp and sudo is off-limits. I'll pivot and try to create the research group and the users without sudo.",
        'groupadd research && useradd alice && useradd bob', "groupadd: group 'research' already exists"),
    11: ("I've set up the shared directory with permissions and ACLs. Now I'll verify the configuration by checking the ACLs with getfacl.",
         'getfacl ~/srv/shared', '# file: root/srv/shared\n# owner: root\n...  (ACLs all set, but dir is under /root)'),
}
steps_norm = []
for i in range(1, ann['m'] + 1):
    if i in turns:
        th, cmd, out = turns[i]
        content = f'Thought: {th}\nAction: $ {cmd}\nObservation: {out}'
        src = 'paper_figure'
    else:
        code = next((c for a, b, c in ann['action_segments'] if a <= i <= b), '?')
        codes = {'E': 'explore/read', 'P': 'planning', 'W': 'write/edit', 'X': 'execute/run', 'V': 'verify/test', 'C': 'completion claim', 'R': 'recover/retry', 'O': 'other'}
        if 5 <= i <= 10:
            content = f'[step not reproduced in the paper figure; summarised there as "steps 5–10: builds ~/srv/shared, sets its group and owner, applies the setfacl ACL rules"; annotated action code {code} = {codes.get(code)}]'
        else:
            content = f'[step not reproduced in the paper figure; annotated action code {code} = {codes.get(code)}]'
        src = 'summary_only'
    steps_norm.append({'idx': i, 'agent': 'coding agent (mini-swe-agent scaffold, Gemini 2.5 Pro)', 'content': content, 'source': src})
norm = {'dataset': SLUG, 'source_id': cid, 'from_paper': True,
        'task': 'Terminal-Bench task `acl-permissions-inheritance` (' + task['category'] + ', ' + task['difficulty'] + '): ' + '; '.join(task['core_requirements_summary']),
        'ground_truth': 'hidden test suite: ' + task.get('solution_ref', ''), 'final_output': None, 'steps': steps_norm,
        'annotation': {'faulty_agent': 'coding agent (single agent)', 'faulty_step': ann['t_err'], 'category': ann['trigger_mechanism'],
                       'reason': ann['trigger_explanation'],
                       'extra': {k: ann[k] for k in ['t_err_evidence', 't_commit', 't_commit_evidence', 't_surface', 't_surface_evidence', 'primary_failure_layer', 'primary_failure_category', 'primary_failure_subtype', 'root_cause_label', 'one_sentence_failure_summary', 'forewarning_present', 'forewarning_types', 'awareness', 'first_awareness_step', 'num_recovery_attempts', 'tail_dominant_behavior', 'fabrication_present', 'fabrication_type', 'verification_ever', 'action_segments', 'timepoint_confidence'] if k in ann}}}
C.write_json(os.path.join(C.NOTES, f'{SLUG}_example_norm.json'), norm)
C.write_fragment(SLUG, 'example', C.example_md(norm, f"Chosen: `{cid}` (m = {ann['m']} steps; t_err = {ann['t_err']}, t_lock = {ann['t_commit']}, t_obs = {ann['t_surface']}). The release ships annotations only; the step text below is transcribed from the paper's Fig. 6 source in the replication package (`scripts/make_case_cards_v3.py`), which shows steps 1–4 and 11 and summarises steps 5–10. Steps are 1-based agent turns (thought + command + output)."))
print('example annotation', json.dumps(ann)[:1500])
