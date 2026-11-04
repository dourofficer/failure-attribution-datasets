import os; CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','cache')
import pickle, re, collections
recs={r['index']:r for r in pickle.load(open(CACHE+'/sab_recs.pkl','rb'))}
d=pickle.load(open(CACHE+'/sab_c2.pkl','rb'))
print(collections.Counter(recs[i]['dataset'] for i in d['fn']))
for i in d['fn'][:73]:
    r=recs[i]
    pa=re.sub(r'\s+',' ',re.sub(r'</?answer>','',r['predicted_answer']))
    print(f"--- {i} {r['model']} {r['dataset']} RC={r['root_cause_primary']}\n Q: {r['query'][:160]}\n GOLD: {r['gold_answer'][:150]}\n PRED(len {len(pa)}): {pa[-260:]}")
