# Pilot: alignment of agent tool-call sequence vs BFCL gold call sequence (AgentHallu BFCL subset)
import json, glob, sys, re, random, numpy as np
from sklearn.metrics import roc_auc_score
random.seed(0)
R=[json.load(open(f)) for f in sorted(glob.glob(sys.argv[1]+'/*.json'))]
def gold_names(r):
    out=[]
    for turn in r['true_answer']:
        for c in turn: out.append(c.split('(')[0].strip())
    return out
def agent_calls(r):
    ev=[]
    for h in r['history']:
        for t in (h.get('tool_calls') or []): ev.append((int(h['step']),t['name']))
    return ev
def align(A,G):  # A: list of names (log), G: gold names (model); costs: sync 0, log move 1, model move 1
    n,m=len(A),len(G); D=np.zeros((n+1,m+1)); D[:,0]=np.arange(n+1); D[0,:]=np.arange(m+1)
    for i in range(1,n+1):
        for j in range(1,m+1):
            D[i,j]=min(D[i-1,j]+1,D[i,j-1]+1,D[i-1,j-1] if A[i-1]==G[j-1] else 1e9)
    i,j,moves=n,m,[]
    while i>0 or j>0:
        if i>0 and j>0 and A[i-1]==G[j-1] and D[i,j]==D[i-1,j-1]: moves.append(('sync',i-1)); i-=1; j-=1
        elif i>0 and D[i,j]==D[i-1,j]+1: moves.append(('log',i-1)); i-=1
        else: moves.append(('model',i)); j-=1   # skipped gold call; located before agent call index i
    return D[n,m], moves[::-1]
rows=[]
for r in R:
    ev=agent_calls(r); A=[x[1] for x in ev]; G=gold_names(r); T=len(r['history'])
    cost,moves=align(A,G)
    def step_of(k): return ev[k][0] if k<len(ev) else T
    first_any=next((step_of(k) for mv,k in moves if mv!='sync'),None)
    first_model=next((step_of(k) for mv,k in moves if mv=='model'),None)
    gs=set(G); first_unseen=next((s for s,nm in ev if nm not in gs),None)
    rows.append(dict(h=r['is_hallucination']=='true', k=int(r['hallucination_step']) if r['is_hallucination']=='true' else None,
        T=T, cost=cost, ncost=cost/max(1,len(G)), first_any=first_any, first_model=first_model, first_unseen=first_unseen))
H=[x for x in rows if x['h']]; C=[x for x in rows if not x['h']]
print('BFCL runs',len(rows),'hallucinated',len(H),'clean',len(C),'median steps',np.median([x['T'] for x in rows]))
y=[x['h'] for x in rows]
for key in ['cost','ncost','T']:
    print(f'AUROC hallucinated-vs-clean by {key}: {roc_auc_score(y,[x[key] for x in rows]):.3f}')
rel=[(x['k']-1)/max(1,x['T']-1) for x in H]; med=np.median(rel)
dec={'first step':[1 for x in H],'last step':[x['T'] for x in H],'median-rel prior (in-sample)':[1+round(med*(x['T']-1)) for x in H],
     'random':[random.randint(1,x['T']) for x in H],
     'first non-sync move':[x['first_any'] for x in H],'first skipped gold call (model move)':[x['first_model'] for x in H],
     'first call to tool not in gold set':[x['first_unseen'] for x in H]}
print(f"{'decoder':40s} cover exact  +-1  +-2")
for n,p in dec.items():
    ok=lambda tol:np.mean([q is not None and abs(q-x['k'])<=tol for q,x in zip(p,H)])
    print(f"{n:40s} {np.mean([q is not None for q in p]):.2f}  {ok(0):.3f} {ok(1):.3f} {ok(2):.3f}")
print('median rel pos of k*',round(med,3))
