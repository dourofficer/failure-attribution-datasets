import json, sys, glob, os, collections
import numpy as np
root=sys.argv[1]
rows=[]
for sub in ['Hand-Crafted','Algorithm-Generated']:
    for f in sorted(glob.glob(os.path.join(root,sub,'*.json'))):
        x=json.load(open(f)); h=x['history']
        marks=[(m.get('name') or m.get('role')) for m in h]
        try: k=int(str(x['mistake_step']).strip('"'))
        except: continue
        rows.append((sub,marks,k,str(x['mistake_agent']).strip('"')))
print('n',len(rows), collections.Counter(r[0] for r in rows))
for sub in ['Hand-Crafted','Algorithm-Generated']:
    R=[r for r in rows if r[0]==sub]
    # mark lift at k*
    base=collections.Counter(m for r in R for m in r[1]); bt=sum(base.values())
    at=collections.Counter(r[1][r[2]] for r in R if r[2]<len(r[1])); n=sum(at.values())
    print(sub,'top marks at k* (share, lift):',[(m,round(c/n,2),round((c/n)/(base[m]/bt),2)) for m,c in at.most_common(6)])
    # heuristics
    def ev(f):
        e=np.array([abs(f(r[1])-r[2]) for r in R]); return 'exact %.3f +-1 %.3f +-3 %.3f'%(np.mean(e==0),np.mean(e<=1),np.mean(e<=3))
    def first_of(marks, pred, default):
        for i,m in enumerate(marks):
            if pred(m): return i
        return default
    relmed=np.median([r[2]/len(r[1]) for r in R])
    print('  position prior (median rel %.2f):'%relmed, ev(lambda ms: int(round(relmed*(len(ms)-1)))))
    print('  step 1:', ev(lambda ms: 1))
    if sub=='Hand-Crafted':
        print('  first WebSurfer step:', ev(lambda ms: first_of(ms, lambda m: m=='WebSurfer', 1)))
        print('  first non-Orchestrator, non-human step:', ev(lambda ms: first_of(ms, lambda m: not m.startswith('Orchestrator') and m!='human', 1)))
    else:
        print('  first non-terminal agent step after step 0:', ev(lambda ms: first_of(ms[1:], lambda m: m!='Computer_terminal', 0)+1))
        print('  first Computer_terminal step - 1:', ev(lambda ms: max(0, first_of(ms, lambda m: m=='Computer_terminal', 1)-1)))
    # who: is mistake_agent the sender of the first mark that differs? role prior
    agents=collections.Counter(r[3] for r in R); print('  role prior acc (most common agent): %.3f'%(agents.most_common(1)[0][1]/len(R)))
