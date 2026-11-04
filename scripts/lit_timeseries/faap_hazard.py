import json, sys, math, random, collections
import numpy as np
from scipy.optimize import minimize
d = json.load(open(sys.argv[1]))
CODES = list("EPWXVCRO"); ci = {c:i for i,c in enumerate(CODES)}
def expand(x):
    seq=[None]*x['m']
    for s,e,c in x['action_segments']:
        for t in range(s,e+1): seq[t-1]=c
    return seq
def task(x): return x['case_id'].split('__')[0]
data = [(expand(x), x) for x in d]
lab = np.array([int('t_err' in x) for _,x in data]); mm = np.array([x['m'] for _,x in data])
auc = lambda s,l: np.mean([(a>b)+0.5*(a==b) for a in s[l==1] for b in s[l==0]])
print('traj AUROC length m alone: %.3f'%auc(mm.astype(float), lab))
NB=5
def feats(seq, use_pos):
    F=[]; prev='BOS'
    for t,c in enumerate(seq):
        f=np.zeros(1+9*8+ (NB if use_pos else 0))
        f[0]=1; f[1+ (8 if prev=='BOS' else ci[prev])*8 + ci[c]]=1
        if use_pos: f[1+72+min(NB-1,int(NB*t/len(seq)))]=1
        F.append(f); prev=c
    return np.array(F)
def nll(w, items, lam=1e-2):
    tot=0; g=np.zeros_like(w)
    for F,y in items:
        z=F@w; h=1/(1+np.exp(-z)); h=np.clip(h,1e-9,1-1e-9)
        L=np.sum(np.log1p(-h))
        if y==0: tot-=L; g+= (h[:,None]*F).sum(0)
        else:
            S=math.exp(L); tot-=math.log(max(1e-12,1-S)); g-= S/max(1e-12,1-S)*(h[:,None]*F).sum(0)
    return tot+lam*w@w, g+2*lam*w
def posterior(F,w):
    h=1/(1+np.exp(-(F@w))); surv=np.concatenate([[1],np.cumprod(1-h)[:-1]]); p=h*surv; return p/p.sum()
random.seed(1); tasks=sorted({task(x) for _,x in data}); random.shuffle(tasks); folds=[set(tasks[i::5]) for i in range(5)]
for use_pos in [False, True]:
    res=collections.defaultdict(list); trajs=[]; trajl=[]
    for f in folds:
        tr=[(feats(s,use_pos), int('t_err' in x)) for s,x in data if task(x) not in f]
        w0=np.zeros(tr[0][0].shape[1]); w0[0]=-3
        w=minimize(nll, w0, args=(tr,), jac=True, method='L-BFGS-B').x
        for s,x in data:
            if task(x) not in f: continue
            F=feats(s,use_pos); h=1/(1+np.exp(-(F@w)))
            trajs.append(1-np.prod(1-h)); trajl.append(int('t_err' in x))
            if 't_err' not in x: continue
            p=posterior(F,w); pred=int(np.argmax(p))+1
            for key in ['t_err','t_commit','t_surface']:
                t=x.get(key)
                if isinstance(t,int): res[key].append(abs(pred-t))
    print('hazard (prev,cur mark)%s: traj AUROC %.3f'%(' + 5 position bins' if use_pos else '', auc(np.array(trajs),np.array(trajl))))
    for key,v in res.items():
        v=np.array(v); print('   %-9s n=%d exact %.3f +-1 %.3f +-3 %.3f'%(key,len(v),np.mean(v==0),np.mean(v<=1),np.mean(v<=3)))
# reference: position baselines for t_commit, t_surface and surprisal for t_surface
fail=[(s,x) for s,x in data if 't_err' in x]
pas=[s for s,x in data if 't_err' not in x]
idx={c:i for i,c in enumerate(['BOS']+CODES+['EOS'])}
M=np.ones((10,10))
for s in pas:
    q=['BOS']+s+['EOS']
    for a,b in zip(q,q[1:]): M[idx[a],idx[b]]+=1
P=M/M.sum(1,keepdims=True)
for key,rel in [('t_err',0.31),('t_commit',None),('t_surface',None)]:
    ts=[(s,x[key]) for s,x in fail if isinstance(x.get(key),int)]
    relmed=np.median([t/len(s) for s,t in ts])
    pos=np.array([abs(max(1,round(relmed*len(s)))-t) for s,t in ts])
    sur=[]
    for s,t in ts:
        q=['BOS']+s; v=[-math.log(P[idx[a],idx[b]]) for a,b in zip(q,q[1:])]; sur.append(abs(int(np.argmax(v))+1-t))
    sur=np.array(sur)
    print('%-9s median rel pos %.2f | position prior exact %.3f +-1 %.3f +-3 %.3f | PASS-chain max-surprisal exact %.3f +-1 %.3f +-3 %.3f'%(key,relmed,np.mean(pos==0),np.mean(pos<=1),np.mean(pos<=3),np.mean(sur==0),np.mean(sur<=1),np.mean(sur<=3)))
