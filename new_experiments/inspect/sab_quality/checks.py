import os; CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','cache')
import pickle, re, collections, json
recs=pickle.load(open(CACHE+'/sab_recs.pkl','rb'))
C=collections.Counter
c=C()
ds=C((r['model'],r['dataset']) for r in recs)
print('tags', C(r['dataset'] for r in recs))
print('models', C(r['model'] for r in recs))
print('root', C(r['root_cause_primary'] for r in recs))
bad=[]
for r in recs:
    T=r['trajectory']; cs=r['critical_step']; k=cs['message_index']; s=cs['span_start_message_index']; e=cs['span_end_message_index']
    if any(m.get('message_index')!=i for i,m in enumerate(T)): c['msgidx_mismatch']+=1
    if not (0<=k<len(T)): c['k_oob']+=1; continue
    if T[k]['role']!='assistant': c['k_not_asst']+=1
    if not (s<=k<=e): c['k_outside_span']+=1; bad.append((r['index'],s,k,e))
    if e>=len(T): c['span_oob']+=1
    if k==s: c['k_eq_start']+=1
    if T[s]['role']!='assistant': c['span_start_not_asst']+=1
    last=T[-1]
    c['last_role_'+last['role']]+=1
    la=[m for m in T if m['role']=='assistant']
    lastA=la[-1]
    if k==lastA['message_index']: c['k_is_last_asst']+=1
    if e>=lastA['message_index']: c['span_covers_last_asst']+=1
    txt=(lastA.get('content') or '')
    if '<answer>' not in txt: c['last_asst_no_answer_tag']+=1
    if lastA.get('tool_calls'): c['last_asst_has_toolcall']+=1
    fr=lastA.get('finish_reason'); c['finish_'+str(fr)]+=1
    if (r['predicted_answer'] or '').strip()!=txt.strip(): c['pred_ne_lastasst']+=1
print(dict(c)); print('k outside span', bad[:10])
