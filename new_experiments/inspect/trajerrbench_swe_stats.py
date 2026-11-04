#!/usr/bin/env python3
"""SWE-Pro subset of TrajErrBench: what kind of step is the gold step, how many edit steps compete with it,
do tests run after the gold step pass (verification theatre), does the final message claim success."""
import os, re, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, md_table
from common.schema import error_step
from loaders import load
from collections import Counter
import statistics as st

def kind(c):
    if 'str_replace_editor' in c and ('"command": "str_replace"' in c or '"command": "create"' in c or '"command": "insert"' in c): return 'edit'
    if 'str_replace_editor' in c: return 'view'
    if 'execute_bash' in c:
        m = re.search(r'"command":\s*"(.*?)"\s*\}', c, re.S)
        cmd = (m.group(1) if m else '')
        if re.search(r'pytest|yarn test|npm test|go test|cargo test|jest|phpunit|mvn test|make test|python -m unittest|\btox\b', cmd): return 'bash_test'
        if re.search(r'sed -i|cat >|tee |echo .*>|git apply|patch ', cmd): return 'bash_edit'
        return 'bash_other'
    if 'Tool calls:' not in c: return 'think/message'
    return 'other_tool'

rows = []
for r in [x for x in load('trajerrbench') if x['subset'] == 'swebenchpro']:
    g = error_step(r); s = r['steps']
    kinds = [(x['idx'], kind(x['content'])) for x in s if x['role'] == 'agent']
    edits = [i for i, k in kinds if k in ('edit', 'bash_edit')]
    tests = [i for i, k in kinds if k == 'bash_test']
    gk = kind(s[g]['content'])
    # test outcomes after gold: look at tool output after a test step
    def test_result(i):
        if i + 1 < len(s):
            o = s[i + 1]['content']
            if re.search(r'(\d+ failed|FAILED|FAIL\b|Error|error)', o) and not re.search(r'(\d+ passed.*0 failed|all tests passed)', o, re.I):
                return 'fail'
            if re.search(r'passed|PASS|ok\b', o): return 'pass'
        return 'unk'
    tests_after = [(i, test_result(i)) for i in tests if i > g]
    tests_before = [(i, test_result(i)) for i in tests if i < g]
    last_agent = [x for x in s if x['role'] == 'agent'][-1]['content']
    claims = bool(re.search(r'(all tests pass|tests pass|successfully|complete|implemented|fixed|resolved)', last_agent, re.I)) and 'Tool calls:' not in last_agent
    edit_rank = (edits.index(g) + 1) if g in edits else None
    rows.append(dict(id=r['id'], n=len(s), gold=g, gold_kind=gk, n_edits=len(edits), edit_rank=edit_rank, first_edit=edits[0] if edits else None,
                     n_tests_after=len(tests_after), tests_after_fail=sum(1 for _, t in tests_after if t == 'fail'), tests_after_pass=sum(1 for _, t in tests_after if t == 'pass'),
                     n_tests_before=len(tests_before), final_claims=claims, cat=r['labels']['categories'][0] if r['labels']['categories'] else None,
                     backbone=r['meta']['backbone'], agent_after=sum(1 for x in s[g + 1:] if x['role'] == 'agent')))
os.makedirs(os.path.join(RESULTS, 'trajerrbench'), exist_ok=True)
json.dump(rows, open(os.path.join(RESULTS, 'trajerrbench', 'g3_swe_struct.json'), 'w'), indent=0)
n = len(rows)
print('n', n)
print('gold kind', Counter(x['gold_kind'] for x in rows))
print('gold kind by category', Counter((x['cat'], x['gold_kind']) for x in rows).most_common(20))
print('n edit steps per run: median', st.median([x['n_edits'] for x in rows]), 'mean', round(st.mean([x['n_edits'] for x in rows]), 1))
er = [x['edit_rank'] for x in rows if x['edit_rank']]
print('gold is an edit:', len(er), '; rank among edits: first', sum(1 for e in er if e == 1), 'median rank', st.median(er) if er else None)
print('gold before first edit:', sum(1 for x in rows if x['first_edit'] is not None and x['gold'] < x['first_edit']), '; gold == first edit', sum(1 for x in rows if x['first_edit'] == x['gold']))
print('runs with >=1 test run after gold:', sum(1 for x in rows if x['n_tests_after'] > 0), '; of which last/any test after gold passes:', sum(1 for x in rows if x['tests_after_pass'] > 0), '; any fails:', sum(1 for x in rows if x['tests_after_fail'] > 0))
print('runs with 0 test runs at all:', sum(1 for x in rows if x['n_tests_after'] + x['n_tests_before'] == 0))
print('final message claims success/completion:', sum(1 for x in rows if x['final_claims']))
print('agent steps after gold: median', st.median([x['agent_after'] for x in rows]))
print('by backbone gold kind', Counter((x['backbone'][:12], x['gold_kind']) for x in rows))
