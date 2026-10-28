import json,glob,re,collections,os,sys
root=sys.argv[1]
def load(p):
    d=json.load(open(p,encoding='utf-8'))
    def unq(x):
        if isinstance(x,str) and len(x)>=2 and x[0]==x[-1]=="'": return x[1:-1]
        return x
    return {k:unq(v) for k,v in d.items()}
recs=[]
for sub in ['Hand-Crafted','Algorithm-Generated']:
    for p in sorted(glob.glob(f'{root}/Who&When/{sub}/*.json'),key=lambda x:int(os.path.basename(x)[:-5])):
        d=load(p); d['_sub']=sub; d['_file']=os.path.basename(p); recs.append(d)
print(len(recs))
# 1. paired tasks across subsets
qid=collections.defaultdict(set)
for d in recs: qid[d.get('question_ID')].add(d['_sub'])
both=[q for q,s in qid.items() if len(s)==2]
print('question_IDs in both subsets:',len(both),'of',len(qid))
# duplicates within subset
cnt=collections.Counter((d['_sub'],d.get('question_ID')) for d in recs)
print('dup question within subset:',sum(1 for v in cnt.values() if v>1))
# 2. label position & last step
last=0; first=0; n=0; ws_only=0; reasons=[]
om=0; com=0
kw=collections.Counter()
for d in recs:
    h=d['history']; k=int(d['mistake_step']); n+=1
    if k==len(h)-1: last+=1
    if k==0: first+=1
    r=(d.get('mistake_reason') or '').lower(); reasons.append(r)
    for w in ['did not','didn\'t','fail','without','ignore','incorrect','wrong','hallucinat','assum','verif','not ','premature','format','should have','instead']:
        if w in r: kw[w]+=1
    step=h[k]; c=step.get('content','') if isinstance(step,dict) else str(step)
    if 'screenshot' in c.lower() and ('typed' in c.lower() or 'clicked' in c.lower()): ws_only+=1
print(f'label at last step {last}/{n}, first step {first}; label on a WebSurfer browse action step {ws_only}')
print('reason keywords:',kw.most_common())
# 3. reasons mentioning the final answer / termination
fa=sum(1 for r in reasons if 'final answer' in r or 'answer' in r)
print('reasons mentioning answer:',fa)
# 4. mean reason length
import statistics as st
print('reason chars median',st.median(len(r) for r in reasons))
# 5. does the ground truth string appear anywhere in the log? (info was present)
present=0; present_before=0; present_after=0
for d in recs:
    gt=str(d.get('ground_truth') or d.get('groundtruth') or '').strip().lower()
    if not gt or len(gt)<3: continue
    h=d['history']; k=int(d['mistake_step'])
    idx=[i for i,s in enumerate(h) if gt in (s.get('content','') if isinstance(s,dict) else str(s)).lower()]
    if idx:
        present+=1
        if min(idx)<=k: present_before+=1
        else: present_after+=1
print(f'ground-truth string appears in log: {present}/{n}; first appearance at/before labelled step: {present_before}; only after: {present_after}')
# 6. what does the last step look like: who speaks last, does it contain FINAL ANSWER
lastroles=collections.Counter()
for d in recs:
    s=d['history'][-1]; lastroles[(d['_sub'], s.get('name') or s.get('role'))]+=1
print(lastroles.most_common(8))
# 7. print a few reasons for the paired examples
for q in both[:5]:
    for d in recs:
        if d.get('question_ID')==q: print(d['_sub'],d['_file'],'| agent',d['mistake_agent'],'step',d['mistake_step'],'/',len(d['history']),'|',(d.get('mistake_reason') or '')[:160])
