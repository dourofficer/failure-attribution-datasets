import json,glob,os,re,collections,sys,statistics as st
R=sys.argv[1]
recs=[]
for f in glob.glob(R+'/data/longrca/data/full/*/*.json'):
    d=json.load(open(f)); d['_src']=f.split('/')[-2]; recs.append(d)
print(len(recs))
kw={'redundant/duplicate/repeat':r'redundan|duplicat|repeat|re-issu|again','loop/stuck':r'loop|stuck|stall','ignore/fail to read/overlook':r'ignor|overlook|fail(ed)? to (read|check|notice|use|consult)|did not (read|check|use|consult)','wrong/incorrect':r'incorrect|wrong|erroneous|mistak','premature/early':r'prematur|too early|before','hallucinat/fabricat':r'hallucinat|fabricat|invent','constraint/budget':r'constraint|budget|requirement','verification':r'verif|validat','approve/accept wrongly':r'approv|accept|confirm|pass(ed)? the'}
by=collections.defaultdict(collections.Counter)
rootrole=collections.Counter(); roottype=collections.Counter()
after_dup=[]; post_frac=[]
for d in recs:
    r=d['mistake_reason'].lower(); src=d['_src']
    for k,p in kw.items():
        if re.search(p,r): by[src][k]+=1
    by[src]['_n']+=1
    k=d['mistake_step']; h=d['history']; s=h[k]
    rootrole[(src,s['role'])]+=1
    c=s['content']
    t='tool_call' if c.startswith('Tool call') or 'Tool call:' in c[:40] else ('handoff' if '(->' in s['name'] or 'Next speaker' in c[:30] else ('observation' if s['role']=='user' else 'message'))
    roottype[t]+=1
    # post-root: repeated identical contents (loops)
    post=[x['content'] for x in h[k+1:]]
    cnt=collections.Counter(post); dup=sum(v-1 for v in cnt.values() if v>1)
    after_dup.append(dup/len(post) if post else 0); post_frac.append(len(post)/len(h))
print('root step role by source:',sorted(rootrole.items()))
print('root step type:',roottype.most_common())
print('fraction of post-root records that are exact duplicates of another post-root record: mean %.2f, median %.2f; >0.3 in %d trajectories'%(st.mean(after_dup),st.median(after_dup),sum(1 for x in after_dup if x>0.3)))
for src,c in by.items():
    n=c['_n']; print(src,n,{k:round(100*v/n) for k,v in c.most_common() if k!='_n'})
# evaluator feedback presence: does the trajectory show the evaluator's verdict / scoring?
ev=collections.Counter()
for d in recs:
    last=d['history'][-1]['content'].lower()
    ev[(d['_src'], 'fail' in last or 'incorrect' in last or 'error' in last)]+=1
print('last record mentions fail/incorrect/error:',sorted(ev.items()))
# sample reasons for travelplanner duplicates
n=0
for d in recs:
    if d['_src']=='travelplanner' and re.search(r'redundan|duplicat|repeat',d['mistake_reason'].lower()):
        print('-',d['question_ID'],d['mistake_step'],'/',len(d['history']),'|',d['mistake_reason'][:260]); n+=1
        if n>=5: break
