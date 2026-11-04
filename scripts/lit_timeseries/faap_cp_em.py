import json, sys, math, random
import numpy as np
d = json.load(open(sys.argv[1]))
CODES=list("EPWXVCRO"); S=['BOS']+CODES; idx={c:i for i,c in enumerate(S)}
def expand(x):
    seq=[None]*x['m']
    for s,e,c in x['action_segments']:
        for t in range(s,e+1): seq[t-1]=c
    return seq
seqs=[expand(x) for x in d]; lab=np.array([int('t_err' in x) for x in d])
pairs=[np.array([[idx[a],idx[b]] for a,b in zip(['BOS']+s, s)]) for s in seqs]
auc=lambda s,l: np.mean([(a>b)+0.5*(a==b) for a in s[l==1] for b in s[l==0]])
def run(seed, iters=60, alpha=0.5, geo=None):
    rng=np.random.default_rng(seed)
    q0=rng.dirichlet(np.ones(8)*5, size=9); q1=rng.dirichlet(np.ones(8)*5, size=9); pinf=0.5
    for it in range(iters):
        C0=np.full((9,8),alpha); C1=np.full((9,8),alpha); ll=0; Pinf=0; posts=[]
        for p in pairs:
            m=len(p); l0=np.log(q0[p[:,0],p[:,1]-1]); l1=np.log(q1[p[:,0],p[:,1]-1])
            c0=np.concatenate([[0],np.cumsum(l0)])            # sum_{t<c} l0, c=1..m+1
            c1=np.concatenate([np.cumsum(l1[::-1])[::-1],[0]]) # sum_{t>=c} l1
            lp=c0+c1                                           # index c-1 for c=1..m, last = no change
            prior=np.concatenate([np.full(m,(1-pinf)/m),[pinf]])
            a=lp+np.log(prior); mx=a.max(); w=np.exp(a-mx); Z=w.sum(); w/=Z; ll+=mx+math.log(Z)
            posts.append(w); Pinf+=w[-1]
            # expected counts: step t (0-based) is pre-change with prob P(c>t+1) = sum_{c-1 > t} w
            pre=np.cumsum(w[::-1])[::-1][1:]   # P(c-1 >= t+1) for t=0..m-1
            np.add.at(C0,(p[:,0],p[:,1]-1),pre); np.add.at(C1,(p[:,0],p[:,1]-1),1-pre)
        q0=C0/C0.sum(1,keepdims=True); q1=C1/C1.sum(1,keepdims=True); pinf=Pinf/len(pairs)
    return ll,q0,q1,pinf,posts
best=None
for seed in range(6):
    r=run(seed)
    print('seed',seed,'loglik %.1f pinf %.3f'%(r[0],r[3]))
    if best is None or r[0]>best[0]: best=r
ll,q0,q1,pinf,posts=best
# which regime is "post-change"? report stationary-ish mark usage of q0 vs q1 rows (from BOS-agnostic average)
print('q0 avg next-mark', dict(zip(CODES,np.round(q0.mean(0),3)))); print('q1 avg next-mark', dict(zip(CODES,np.round(q1.mean(0),3))))
fail_score=np.array([1-w[-1] for w in posts])
print('L0 trajectory AUROC P(change) fail vs pass: %.3f'%auc(fail_score,lab))
for key in ['t_err','t_commit','t_surface']:
    ex=[];
    for x,w in zip(d,posts):
        t=x.get(key)
        if 't_err' in x and isinstance(t,int):
            c=int(np.argmax(w[:-1]))+1; ex.append(abs(c-t))
    ex=np.array(ex); print('%-9s n=%d posterior-mode change point exact %.3f +-1 %.3f +-3 %.3f'%(key,len(ex),np.mean(ex==0),np.mean(ex<=1),np.mean(ex<=3)))
rel=[ (int(np.argmax(w[:-1]))+1)/x['m'] for x,w in zip(d,posts) if 't_err' in x]
print('median relative position of inferred change (FAIL): %.2f'%np.median(rel))
