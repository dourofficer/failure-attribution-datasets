import os; CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','cache')
import pickle, sys, textwrap, re
WS=lambda x: re.sub(r'\s+',' ',x or '')
recs={r['index']:r for r in pickle.load(open(CACHE+'/sab_recs.pkl','rb'))}
i=int(sys.argv[1]); W=int(sys.argv[2]) if len(sys.argv)>2 else 300
lo=int(sys.argv[3]) if len(sys.argv)>3 else None; hi=int(sys.argv[4]) if len(sys.argv)>4 else None
r=recs[i]; cs=r['critical_step']; k=cs['message_index']
print(f"### {i} {r['model']} {r['dataset']} RC={r['root_cause_primary']} k={k} span=({cs['span_start_message_index']},{cs['span_end_message_index']}) n={len(r['trajectory'])}")
print('Q:', r['query']); print('GOLD:', r['gold_answer'])
print(textwrap.fill('RATIONALE: '+r['rationale']['failure_rationale'],170))
print(textwrap.fill('DIRECTIVE: '+r['repair_directive'],170))
for x in r['repair_rubrics']: print('  RUBRIC:', x['requirement'][:220])
for m in r['trajectory'][2:]:
    j=m['message_index']
    if lo is not None and not (lo<=j<=hi): continue
    mark='>>' if j==k else ('| ' if cs['span_start_message_index']<=j<=cs['span_end_message_index'] else '  ')
    if m['role']=='tool': print(f"{mark}[{j}] TOOL: {WS(m['content'])[:W]}")
    else:
        rc=WS(m.get('reasoning_content'))
        tc=[(t['tool_name'], str(t['tool_arguments'])[:160]) for t in (m.get('tool_calls') or [])]
        print(f"{mark}[{j}] {m['role'].upper()} think: {rc[-W:]}\n      calls={tc} content={WS(m.get('content'))[:W]}")
