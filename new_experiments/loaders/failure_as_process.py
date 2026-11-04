"""'Failure as a Process' (Terminal-Bench CLI-agent annotation release):
data/failure_as_process/repo_cli_trajectory_analysis/data/traj_data_v2_all89tasks.json (1,794 runs = 1,184 FAIL + 610 PASS).
The release has NO step text: records have steps = [] except PASS runs that appear in pass_obs_input.json, whose
'context' excerpt (the steps around the first error event) is kept as a single 'env' step. outcome fail/pass;
labels.error_steps = [] (t_err, t_commit (= t_lock), t_surface (= t_obs) are 1-based step numbers kept in labels.extra;
all numeric fields in the release are strings and are converted); categories = [trigger_mechanism] for FAIL runs."""
import ast
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # for python3 -I
from common.schema import make_record, make_step
from common.util import DATA, read_json

R = os.path.join(DATA, 'failure_as_process', 'repo_cli_trajectory_analysis', 'data')
FILE = os.path.join(R, 'traj_data_v2_all89tasks.json')


def conv(v):
    if isinstance(v, str):
        s = v.strip()
        if s in ('None', ''):
            return None
        if s == 'True':
            return True
        if s == 'False':
            return False
        try:
            return int(s)
        except ValueError:
            pass
        if s[:1] in '[{':
            try:
                return ast.literal_eval(s)
            except Exception:  # noqa
                return v
    return v


def load(limit=None, outcomes=('fail', 'success')):
    recs = []
    tasks = {t['task_id']: t for t in read_json(os.path.join(R, 'merged_tasks.json'))}
    pass_obs = {p['case_id']: p for p in read_json(os.path.join(R, 'pass_obs_input.json'))}
    pass_err_obs = read_json(os.path.join(R, 'pass_error_observability.json'))
    for r in read_json(FILE):
        r = {k: conv(v) for k, v in r.items()}
        cid = r['case_id']
        task, scaffold, model = cid.split('__')
        failed = r.get('t_commit') is not None
        outcome = 'fail' if failed else 'success'
        if outcome not in outcomes:
            continue
        steps = []
        po = pass_obs.get(cid)
        if po and po.get('context'):
            steps.append(make_step(0, 'cli-agent', 'env', po['context'], native_step='pass_obs_input excerpt',
                                   meta={'first_error_step': po.get('first_error_step'), 'excerpt': True}))
        t = tasks.get(task, {})
        extra = dict(r)
        extra.pop('case_id', None)
        extra['t_lock'] = r.get('t_commit')
        extra['t_obs'] = r.get('t_surface')
        extra['pass_error_observability'] = pass_err_obs.get(cid)
        extra['step_numbering'] = '1-based step numbers of the (unreleased) trajectory; m = number of steps'
        recs.append(make_record('failure_as_process', cid, t.get('core_requirements_summary') and '; '.join(t['core_requirements_summary']) or task, steps,
                                subset=scaffold, ground_truth=None, final_output=None, outcome=outcome, error_steps=[], error_agent=None,
                                categories=[r['trigger_mechanism']] if failed and r.get('trigger_mechanism') else [],
                                reason=r.get('one_sentence_failure_summary') or r.get('one_sentence_strategy_summary'),
                                extra=extra,
                                meta={'file': FILE, 'framework': scaffold, 'backbone': model, 'benchmark': 'Terminal-Bench', 'task_id': task,
                                      'task_meta': t, 'n_steps_m': r.get('m'), 'has_step_text': bool(steps)}))
        if limit and len(recs) >= limit:
            break
    return recs


if __name__ == '__main__':
    rs = load()
    from collections import Counter
    print(len(rs), 'records;', sum(len(r['steps']) for r in rs), 'steps (excerpts);', Counter(r['outcome'] for r in rs))
    print(Counter(r['subset'] for r in rs), sum(r['labels']['extra']['m'] for r in rs), 'annotated steps (sum of m)')
    f = next(r for r in rs if r['outcome'] == 'fail')
    print(f['id'], f['labels']['categories'], {k: f['labels']['extra'][k] for k in ('t_err', 't_commit', 't_surface', 'm', 'awareness', 'tail_dominant_behavior')})
