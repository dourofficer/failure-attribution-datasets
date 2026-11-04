import os; CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','cache')
import pickle, re, collections
recs=pickle.load(open(CACHE+'/sab_recs.pkl','rb')); C=collections.Counter
def rep_score(t):
    toks=re.findall(r'\w+|[^\w\s]', t)[-400:]
    if len(toks)<80: return None
    # fraction of 4-grams that are repeats
    g=[tuple(toks[i:i+4]) for i in range(len(toks)-3)]
    return 1-len(set(g))/len(g)
out=[]
for r in recs:
    A=[m for m in r['trajectory'] if m['role']=='assistant']
    last=A[-1]
    s1=rep_score(last.get('reasoning_content') or ''); s2=rep_score(r['predicted_answer'] or '')
    s=max(x for x in (s1,s2,0) if x is not None)
    out.append((s, r['index'], r['model'], r['root_cause_primary'], r['critical_step']['message_index']==last['message_index']))
out.sort(reverse=True)
for th in (0.3,0.5):
    hi=[o for o in out if o[0]>=th]
    print(f'last step 4-gram repeat >= {th}: {len(hi)}', C(o[2] for o in hi), 'k=last:', sum(o[4] for o in hi), C(o[3] for o in hi))
print(out[:12])
