import os; CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','cache')
# reasoning language by model and query language
import pickle, re, collections
recs=pickle.load(open(CACHE+'/sab_recs.pkl','rb'))
zh=lambda s: len(re.findall(r'[一-鿿]',s))/max(1,len(s))
rows=collections.defaultdict(lambda:[0,0])
for r in recs:
    q='zh' if zh(r['query'])>0.2 else 'en'
    for m in r['trajectory']:
        if m['role']=='assistant' and m.get('reasoning_content'):
            rows[(r['model'],q)][0]+=1; rows[(r['model'],q)][1]+=zh(m['reasoning_content'])>0.2
for k,v in sorted(rows.items()): print(k, v[0], f'{v[1]/v[0]:.1%}')
