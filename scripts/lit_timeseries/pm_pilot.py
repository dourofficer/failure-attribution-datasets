# Pilot: discrete "conformance" baselines on Failure-as-a-Process action_segments (8 step-type codes)
import json, math, random, collections, sys
import numpy as np
random.seed(0); np.random.seed(0)
D=json.load(open(sys.argv[1]))
def seq(r):
    s=[None]*r['m']
    for a,b,c in r['action_segments']:
        for t in range(a,b+1): s[t-1]=c
    assert all(x is not None for x in s)
    return s
P=[seq(r) for r in D if r.get('t_commit') is None]
F=[(seq(r),r) for r in D if r.get('t_commit') is not None]
codes=sorted({c for s in P for c in s}|{c for s,_ in F for c in s}); V=len(codes)+1  # + END
print('PASS',len(P),'FAIL',len(F),'codes',codes)
print('median len PASS',np.median([len(s) for s in P]),'FAIL',np.median([len(s) for s,_ in F]))
def train(seqs,n=3,alpha=0.5):
    cnt=collections.Counter(); ctx=collections.Counter()
    for s in seqs:
        x=['<s>']*(n-1)+s+['</s>']
        for i in range(n-1,len(x)):
            for k in range(1,n+1):  # all orders for backoff
                h=tuple(x[i-k+1:i]); cnt[(h,x[i])]+=1; ctx[h]+=1
    return cnt,ctx,n,alpha
def prob(M,h,c):
    cnt,ctx,n,alpha=M
    # interpolated: simple Jelinek-Mercer with fixed lambdas
    lam=[0.6,0.3,0.1][:n]; p=0
    for j,k in enumerate(range(n,0,-1)):
        hh=tuple(h[len(h)-(k-1):]) if k>1 else tuple()
        p+=lam[j]*(cnt[(hh,c)]+alpha)/(ctx[hh]+alpha*V)
    return p
def surpr(M,s):
    n=M[2]; x=['<s>']*(n-1)+s
    return [-math.log(prob(M,x[i-n+1:i],x[i])) for i in range(n-1,len(x))]
def end_surpr(M,s):
    n=M[2]; x=['<s>']*(n-1)+s; return -math.log(prob(M,x[len(x)-n+1:],'</s>'))
# DFG with frequency threshold from PASS
def dfg(seqs):
    c=collections.Counter()
    for s in seqs:
        x=['<s>']+s+['</s>']
        for a,b in zip(x,x[1:]): c[(a,b)]+=1
    return c
# ---------- trajectory-level AUROC, PASS out-of-fold ----------
from sklearn.metrics import roc_auc_score
K=5; idx=np.random.permutation(len(P)); folds=np.array_split(idx,K)
pass_scores=[None]*len(P); fail_scores=[]
Mall=train(P)
for k in range(K):
    tr=[P[i] for i in idx if i not in set(folds[k])]; M=train(tr)
    for i in folds[k]:
        su=surpr(M,P[i]); pass_scores[i]=(max(su),np.mean(su),np.mean(su+[end_surpr(M,P[i])]),len(P[i]))
for s,r in F:
    su=surpr(Mall,s); fail_scores.append((max(su),np.mean(su),np.mean(su+[end_surpr(Mall,s)]),len(s)))
y=[0]*len(P)+[1]*len(F); S=pass_scores+fail_scores
for j,name in enumerate(['max surprisal','mean surprisal','mean surprisal incl END','length only']):
    print(f'AUROC FAIL-vs-PASS {name}: {roc_auc_score(y,[x[j] for x in S]):.3f}')
# ---------- step-level: per-step decoders vs t_err / t_lock / t_obs ----------
# conformal threshold from out-of-fold PASS step surprisals
oof=[]
for k in range(K):
    tr=[P[i] for i in idx if i not in set(folds[k])]; M=train(tr)
    for i in folds[k]: oof+=surpr(M,P[i])
C=collections.Counter(); 
for s in P: 
    x=['<s>']+s+['</s>']
    for a,b in zip(x,x[1:]): C[(a,b)]+=1
tot=sum(C.values())
rel_err=[ (r['t_err']-1)/max(1,r['m']-1) for s,r in F]
def acc(preds,key,tol):
    ok=[];
    for p,(s,r) in zip(preds,F):
        t=r.get(key)
        if t is None: continue
        ok.append(p is not None and abs(p-t)<=tol)
    return np.mean(ok), len(ok)
dec={}
dec['first step (1)']=[1 for s,r in F]
dec['median-rel-position prior']=[1+round(np.median(rel_err)*(len(s)-1)) for s,r in F]
dec['random step']=[random.randint(1,len(s)) for s,r in F]
dec['argmax surprisal']=[1+int(np.argmax(surpr(Mall,s))) for s,r in F]
for a in [0.2,0.05]:
    th=np.quantile(oof,1-a)
    def first_above(s,th=th):
        su=surpr(Mall,s)
        for t,v in enumerate(su):
            if v>th: return t+1
        return None
    dec[f'first step surprisal>q{1-a:.2f}(PASS)']=[first_above(s) for s,r in F]
for thr in [0.001,0.005]:
    def first_dev(s,thr=thr):
        x=['<s>']+s
        for t in range(1,len(x)):
            if C[(x[t-1],x[t])]/tot<thr: return t
        return None
    dec[f'DFG first rare transition (<{thr})']=[first_dev(s) for s,r in F]
# first 'R' (recover) step = first visible symptom proxy
dec['first R (recover) step']=[ (s.index('R')+1 if 'R' in s else None) for s,r in F]
print()
print(f"{'decoder':45s} | cover | " + ' | '.join(f'{k}@{t}' for k in ['t_err','t_commit','t_surface'] for t in [0,1,3]))
for name,pr in dec.items():
    cov=np.mean([p is not None for p in pr])
    row=[]
    for k in ['t_err','t_commit','t_surface']:
        for t in [0,1,3]:
            row.append(f'{acc(pr,k,t)[0]:.3f}')
    print(f'{name:45s} | {cov:.2f} | '+' | '.join(row))
# where does first deviation fall relative to t_err/t_commit/t_surface?
pr=dec['first step surprisal>q0.80(PASS)']
rel=collections.Counter()
for p,(s,r) in zip(pr,F):
    if p is None: rel['none']+=1; continue
    if p<r['t_err']: rel['before t_err']+=1
    elif p<=r['t_commit']: rel['in [t_err,t_lock]']+=1
    elif r['t_surface'] is None or p<=r['t_surface']: rel['in (t_lock,t_obs] or silent']+=1
    else: rel['after t_obs']+=1
print('\nfirst-deviation (q0.80) location:',dict(rel))
print('N with t_surface',sum(r['t_surface'] is not None for s,r in F))
print('median t_err,t_commit,t_surface',np.median([r['t_err'] for s,r in F]),np.median([r['t_commit'] for s,r in F]),np.median([r['t_surface'] for s,r in F if r['t_surface'] is not None]))
# code at t_err vs PASS code distribution
ce=collections.Counter(s[r['t_err']-1] for s,r in F); cp=collections.Counter(c for s in P for c in s); n=sum(cp.values())
print('\ncode at t_err (share) vs PASS step share:'); 
for c in codes: print(f'  {c}: t_err {ce[c]/len(F):.3f}  PASS {cp[c]/n:.3f}')
print()
def first_of(s,cs):
    for t,c in enumerate(s):
        if c in cs: return t+1
    return None
extra={'first W step':[first_of(s,{'W'}) for s,r in F],
       'first W-or-P step':[first_of(s,{'W','P'}) for s,r in F],
       'first non-E step':[first_of(s,{'W','P','X','V','C','R','O'}) for s,r in F]}
# how often does first-surprisal decoder coincide with first W
pr=dec['first step surprisal>q0.80(PASS)']; fw=extra['first W step']
print('first-surprisal==first W:',np.mean([a==b for a,b in zip(pr,fw)]))
for name,pr in extra.items():
    cov=np.mean([p is not None for p in pr]); row=[]
    for k in ['t_err','t_commit','t_surface']:
        for t in [0,1,3]: row.append(f'{acc(pr,k,t)[0]:.3f}')
    print(f'{name:45s} | {cov:.2f} | '+' | '.join(row))
# surprisal decoder restricted to failures where t_err is NOT the first W step
sub=[i for i,(s,r) in enumerate(F) if fw[i]!=r['t_err']]
p1=dec['first step surprisal>q0.80(PASS)']
print('on',len(sub),'failures where t_err != first W: surprisal-first exact',np.mean([p1[i]==F[i][1]['t_err'] for i in sub]),' first-W exact 0 by construction; median prior exact',np.mean([dec['median-rel-position prior'][i]==F[i][1]['t_err'] for i in sub]))
