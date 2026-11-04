import os; CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','cache')
import pickle, re, collections
recs={r['index']:r for r in pickle.load(open(CACHE+'/sab_recs.pkl','rb'))}
errpat=re.compile(r'(error|failed to|timed? ?out|exception|429|403 forbidden|rate limit|could not be|unable to (fetch|access|retrieve)|no results found|captcha|access denied)', re.I)
C=collections.Counter()
for r in recs.values():
    for m in r['trajectory']:
        if m['role']=='tool' and errpat.search((m['content'] or '')[:400]):
            C[re.sub(r'\d+','N',(m['content'] or '')[:90]).replace('\n',' ')]+=1
for k,v in C.most_common(15): print(v, '|', k)
for i in (338, 757):
    r=recs[i]; k=r['critical_step']['message_index']
    print(f"\n#### {i} {r['model']} {r['dataset']} RC={r['root_cause_primary']} k={k} span=({r['critical_step']['span_start_message_index']},{r['critical_step']['span_end_message_index']}) n={len(r['trajectory'])}")
    print('Q:', r['query'][:200]); print('GOLD:', r['gold_answer'][:100])
    print('RATIONALE:', r['rationale']['failure_rationale'][:700])
    for m in r['trajectory'][2:]:
        if m['role']=='tool': print(f"  [{m['message_index']}] tool: {(m['content'] or '')[:110]!r}")
        else:
            tc=m.get('tool_calls') or []
            print(f"  [{m['message_index']}] {m['role']}: calls={[ (t['tool_name'], str(t['tool_arguments'])[:90]) for t in tc]} content={(m.get('content') or '')[:80]!r}")
        if m['message_index']>40: print('  ...'); break
