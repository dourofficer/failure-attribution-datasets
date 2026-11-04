import os; CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','cache')
import pickle, sys, textwrap
recs={r['index']:r for r in pickle.load(open(CACHE+'/sab_recs.pkl','rb'))}
for i in map(int, sys.argv[1:]):
    r=recs[i]; cs=r['critical_step']
    print(f"### {i} {r['model']} | RC={r['root_cause_primary']} | k={cs['message_index']} span=({cs['span_start_message_index']},{cs['span_end_message_index']}) n={len(r['trajectory'])}")
    print(textwrap.fill('RATIONALE: '+r['rationale']['failure_rationale'], 180)); print()
