import json, sys
import numpy as np
d=json.load(open(sys.argv[1]))
def expand(x):
    seq=[None]*x['m']
    for s,e,c in x['action_segments']:
        for t in range(s,e+1): seq[t-1]=c
    return seq
fail=[(expand(x),x) for x in d if 't_err' in x]
def first(seq,codes,default):
    for i,c in enumerate(seq):
        if c in codes: return i+1
    return default
H={'first W':lambda s:first(s,'W',max(1,round(.31*len(s)))),
   'first W or X':lambda s:first(s,'WX',1),
   'first non-E':lambda s:first(s,'PWXVCRO',1),
   'first P or W':lambda s:first(s,'PW',max(1,round(.31*len(s)))),
   'first V':lambda s:first(s,'V',len(s)),
   'first C':lambda s:first(s,'C',len(s))}
for key in ['t_err','t_commit','t_surface']:
    print(key)
    for name,f in H.items():
        e=np.array([abs(f(s)-x[key]) for s,x in fail if isinstance(x.get(key),int)])
        print('   %-14s exact %.3f +-1 %.3f +-3 %.3f'%(name,np.mean(e==0),np.mean(e<=1),np.mean(e<=3)))
# how often is t_err the first W step / in first W segment
fw=[first(s,'W',None) for s,x in fail]; 
print('t_err == first W step: %.3f; FAIL runs with any W: %.3f'%(np.mean([a==x['t_err'] for a,(s,x) in zip(fw,fail)]), np.mean([a is not None for a in fw])))
