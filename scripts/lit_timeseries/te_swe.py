import json, sys, glob, os, collections
import numpy as np
root=sys.argv[1]; R=[]
for d in sorted(glob.glob(os.path.join(root,'swe-agent-runs-swe-bench','*'))):
    try:
        st=json.load(open(os.path.join(d,'step_records.json'))); md=json.load(open(os.path.join(d,'trace_metadata.json')))
        k=int(str(md['mistake_step']).strip('"'))
    except Exception: continue
    marks=[]
    for s in st:
        tl=s.get('tool_logs') or []
        if tl:
            f=tl[0]['function']; 
            try: a=json.loads(f['arguments'])
            except Exception: a={}
            cmd=a.get('command','')
            if f['name']=='str_replace_editor':
                path=a.get('path','')
                kind='edit-src' if cmd in ('str_replace','insert') and 'reproduce' not in path and '/tests/' not in path else ('create' if cmd=='create' else cmd)
                marks.append('editor:'+kind)
            else: marks.append(f['name'])
        else: marks.append(s.get('agent_name'))
    ids=[s['step_id'] for s in st]
    if k in ids: R.append((marks, ids.index(k)))
base=collections.Counter(m for r in R for m in r[0]); bt=sum(base.values())
at=collections.Counter(r[0][r[1]] for r in R); n=len(R)
print('n',n,'marks at k*:',[(m,round(c/n,2),round((c/n)/(base[m]/bt),2)) for m,c in at.most_common(6)])
def ev(f):
    e=np.array([abs(f(r[0])-r[1]) for r in R]); return 'exact %.3f +-1 %.3f +-3 %.3f'%(np.mean(e==0),np.mean(e<=1),np.mean(e<=3))
fo=lambda ms,p,dflt: next((i for i,m in enumerate(ms) if p(m)), dflt)
print('first editor:edit-src step:', ev(lambda ms: fo(ms, lambda m: m=='editor:edit-src', int(.41*len(ms)))))
print('first editor:create step:', ev(lambda ms: fo(ms, lambda m: m=='editor:create', int(.41*len(ms)))))
print('position prior 0.41:', ev(lambda ms: int(round(.41*(len(ms)-1)))))
