import os; CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','cache')
# trivial positional baselines on CS-Strict / CS-Loose and majority root cause
import pickle, collections
recs=pickle.load(open(CACHE+'/sab_recs.pkl','rb')); C=collections.Counter
def sc(pick):
    s=l=0
    for r in recs:
        A=[m['message_index'] for m in r['trajectory'] if m['role']=='assistant']; k=pick(A); cs=r['critical_step']
        s+=k==cs['message_index']; l+=cs['span_start_message_index']<=k<=cs['span_end_message_index']
    return round(s/len(recs),3), round(l/len(recs),3)
print('last asst', sc(lambda A:A[-1]), 'first asst', sc(lambda A:A[0]))
print('majority RC', C(r['root_cause_primary'] for r in recs).most_common(1)[0][1]/len(recs))
