import json, sys, glob, os, collections
import numpy as np
root=sys.argv[1]; rows=[]
for d in sorted(glob.glob(os.path.join(root,'*','*'))):
    try:
        st=json.load(open(os.path.join(d,'step_records.json'))); md=json.load(open(os.path.join(d,'trace_metadata.json')))
        k=int(str(md['mistake_step']).strip('"').replace('Step ',''))
    except Exception as e: continue
    marks=[s.get('agent_name') for s in st]; ids=[s['step_id'] for s in st]
    toks=[((s.get('output') or {}).get('usage') or {}).get('total_tokens',0) or 0 for s in st]
    rows.append((md.get('system_name'),marks,ids.index(k) if k in ids else None,toks))
rows=[r for r in rows if r[2] is not None]
print('n',len(rows),collections.Counter(r[0] for r in rows))
for sysn in sorted({r[0] for r in rows}):
    R=[r for r in rows if r[0]==sysn]
    base=collections.Counter(m for r in R for m in r[1]); bt=sum(base.values())
    at=collections.Counter(r[1][r[2]] for r in R); n=sum(at.values())
    print(sysn,'marks at k* (share, lift):',[(m,round(c/n,2),round((c/n)/(base[m]/bt),2)) for m,c in at.most_common(5)])
    def ev(f):
        e=np.array([abs(f(r)-r[2]) for r in R]); return 'exact %.3f +-1 %.3f +-3 %.3f'%(np.mean(e==0),np.mean(e<=1),np.mean(e<=3))
    relmed=np.median([r[2]/len(r[1]) for r in R])
    print('  position prior (rel %.2f):'%relmed, ev(lambda r:int(round(relmed*(len(r[1])-1)))))
    top=at.most_common(1)[0][0]
    print('  first step of most-blamed mark %r:'%top, ev(lambda r: next((i for i,m in enumerate(r[1]) if m==top), 0)))
    # token clock: relative position in cumulative tokens
    tk=[r for r in R if sum(r[3])>0]
    if tk:
        relt=np.median([np.cumsum(r[3])[r[2]]/sum(r[3]) for r in tk])
        def tokpos(r):
            c=np.cumsum(r[3])/sum(r[3]); return int(np.argmin(abs(c-relt)))
        e=np.array([abs(tokpos(r)-r[2]) for r in tk])
        print('  token-clock prior (median cum-token frac %.2f, n=%d): exact %.3f +-1 %.3f +-3 %.3f'%(relt,len(tk),np.mean(e==0),np.mean(e<=1),np.mean(e<=3)))
