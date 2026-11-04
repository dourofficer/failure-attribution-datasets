import os; CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','cache')
# runs forced to answer by the scaffold budget ("FINAL ANSWER MODE")
import pickle, collections, statistics as st
recs=pickle.load(open(CACHE+'/sab_recs.pkl','rb')); C=collections.Counter
F=[(r,[m['message_index'] for m in r['trajectory'][2:] if m['role']=='user' and (m['content'] or '').startswith('FINAL ANSWER MODE')]) for r in recs]
F=[(r,f[0]) for r,f in F if f]
print('forced-final runs', len(F), C(r['model'] for r,_ in F)); print('root causes', C(r['root_cause_primary'] for r,_ in F))
gap=sorted(f-r['critical_step']['message_index'] for r,f in F); print('messages from critical step to forced cut: median', st.median(gap))
