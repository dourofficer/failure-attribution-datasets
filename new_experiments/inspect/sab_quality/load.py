import os; CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','cache')
# Run load.py first: it caches the 1,243 records to cache/sab_recs.pkl. checks2.py -> fn.py, drift.py -> cons.py use intermediate pickles.
import json, sys, pickle
P='/dataDisk/home/thanhdo/failure-attribution-datasets/data/searchauditbench/extracted/benchmark_data_1243.jsonl'
recs=[json.loads(l) for l in open(P)]
pickle.dump(recs, open(CACHE+'/sab_recs.pkl','wb'))
r=recs[0]
print(len(recs)); print(sorted(r.keys()))
for k in r:
    if k!='trajectory': print(k, '=>', json.dumps(r[k], ensure_ascii=False)[:400])
