import json, sys, math, random, collections
import numpy as np
d = json.load(open(sys.argv[1]))
CODES = list("EPWXVCRO")
def expand(x):
    m = x['m']; seq = [None]*m
    for s,e,c in x['action_segments']:
        for t in range(s, e+1):
            if 1 <= t <= m: seq[t-1] = c
    return seq
fail = [x for x in d if 't_err' in x]; pas = [x for x in d if 't_err' not in x]
print('FAIL', len(fail), 'PASS', len(pas))
cov = [sum(c is None for c in expand(x)) for x in d]
print('records with uncovered steps', sum(c>0 for c in cov))
# mark freq
for name, grp in [('PASS', pas), ('FAIL', fail)]:
    cnt = collections.Counter(c for x in grp for c in expand(x) if c)
    tot = sum(cnt.values()); print(name, 'steps', tot, {k: round(cnt[k]/tot,3) for k in CODES})
# mark at labelled times
base = collections.Counter(c for x in fail for c in expand(x) if c); bt = sum(base.values())
for key in ['t_err','t_commit','t_surface']:
    cnt = collections.Counter(); n=0
    for x in fail:
        t = x.get(key); seq = expand(x)
        if isinstance(t,int) and 1 <= t <= len(seq) and seq[t-1]:
            cnt[seq[t-1]] += 1; n += 1
    print(key, n, {k: (round(cnt[k]/n,3), round((cnt[k]/n)/(base[k]/bt),2)) for k in CODES})
# segment-boundary leakage: is t_err at a segment start more than chance?
hit=0; chance=0; n=0
for x in fail:
    t = x.get('t_err'); 
    if not isinstance(t,int): continue
    starts = {s for s,e,c in x['action_segments']}
    hit += t in starts; chance += len(starts)/x['m']; n+=1
print('t_err at segment start: %.3f vs chance %.3f (n=%d)'%(hit/n, chance/n, n))
# first-order Markov chain on PASS, surprisal on FAIL
idx = {c:i for i,c in enumerate(['BOS']+CODES+['EOS'])}
def chain(grp, alpha=1.0):
    M = np.full((len(idx), len(idx)), alpha)
    for x in grp:
        seq = ['BOS']+expand(x)+['EOS']
        for a,b in zip(seq, seq[1:]): M[idx[a], idx[b]] += 1
    return M/M.sum(1, keepdims=True)
P = chain(pas)
def surpr(seq, P):
    s = ['BOS']+seq
    return [-math.log(P[idx[a], idx[b]]) for a,b in zip(s, s[1:])]
def acc(preds, golds, k):
    return np.mean([abs(p-g) <= k for p,g in zip(preds, golds)])
golds=[]; pm=[]; pos=[]; first3=[]; firstR=[]; rnd=[]
random.seed(0)
for x in fail:
    t = x.get('t_err'); seq = expand(x)
    if not isinstance(t,int) or None in seq: continue
    s = surpr(seq, P); m = len(seq)
    golds.append(t); pm.append(int(np.argmax(s))+1)
    pos.append(max(1, round(0.31*m))); first3.append(min(2,m))
    r = [i+1 for i,c in enumerate(seq) if c in 'R']; firstR.append(r[0]-1 if r else pos[-1])
    rnd.append(random.randint(1,m))
golds=np.array(golds)
for name, p in [('PASS-chain max surprisal', pm), ('position 0.31m', pos), ('step 2', first3), ('step before first R (else 0.31m)', firstR), ('random', rnd)]:
    print('%-35s exact %.3f  +-1 %.3f  +-3 %.3f'%(name, acc(p,golds,0), acc(p,golds,1), acc(p,golds,3)))
print('median m FAIL', np.median([x['m'] for x in fail]), 'PASS', np.median([x['m'] for x in pas]))
# trajectory-level: LLR mean surprisal under PASS vs FAIL chains, leave-task-out by task prefix
def task(x): return x['case_id'].split('__')[0]
tasks = sorted({task(x) for x in d}); random.shuffle(tasks)
folds = [set(tasks[i::5]) for i in range(5)]
scores=[]; labels=[]
for f in folds:
    tr = [x for x in d if task(x) not in f]; te = [x for x in d if task(x) in f]
    Pp = chain([x for x in tr if 't_err' not in x]); Pf = chain([x for x in tr if 't_err' in x])
    for x in te:
        seq = expand(x)
        if None in seq: continue
        sp = surpr(seq, Pp); sf = surpr(seq, Pf)
        scores.append(np.mean(sp)-np.mean(sf)); labels.append(int('t_err' in x))
from itertools import product
s=np.array(scores); l=np.array(labels)
pos_s=s[l==1]; neg_s=s[l==0]
auc = np.mean([(a>b)+0.5*(a==b) for a in pos_s for b in neg_s])
print('trajectory AUROC (fail vs pass) of mark-chain LLR, 5-fold by task: %.3f'%auc)
# m alone
mm=np.array([x['m'] for x in d if None not in expand(x)]); 
auc_m = np.mean([(a>b)+0.5*(a==b) for a in mm[l==1] for b in mm[l==0]])
print('trajectory AUROC of length m alone: %.3f'%auc_m)
# C without preceding V within the last 3 steps before the first C
def cnov(seq):
    if 'C' not in seq: return None
    i = seq.index('C'); return 'V' not in seq[max(0,i-3):i]
for name, grp in [('PASS',pas),('FAIL',fail)]:
    v=[cnov(expand(x)) for x in grp]; v=[a for a in v if a is not None]
    print(name, 'first C without V in prior 3 steps: %.3f (n=%d)'%(np.mean(v), len(v)))
# max run of R or X repeated
def maxrun(seq, codes):
    best=cur=0
    for c in seq:
        cur = cur+1 if c in codes else 0; best=max(best,cur)
    return best
for name, grp in [('PASS',pas),('FAIL',fail)]:
    print(name, 'mean #R steps %.2f, frac with any R %.3f, mean #C %.2f'%(np.mean([expand(x).count('R') for x in grp]), np.mean([('R' in expand(x)) for x in grp]), np.mean([expand(x).count('C') for x in grp])))
