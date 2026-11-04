import os; CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','cache')
import pickle, re, collections
recs=pickle.load(open(CACHE+'/sab_recs.pkl','rb'))
C=collections.Counter
dates=C(re.findall(r'Current date: ([\d-]+)', r['trajectory'][0]['content'] or '')[0] if 'Current date' in (r['trajectory'][0]['content'] or '') else 'none' for r in recs)
print('system dates', dates.most_common(8))
pat=re.compile(r'\b(most recent|latest|currently|current|as of now|to date|so far|last|still|newest|recent|this year|today)\b|最新|目前|至今|现在|当前|截至', re.I)
tr=[r for r in recs if pat.search(r['query'])]
print('time-relative queries', len(tr), C(r['dataset'] for r in tr))
# duplicate queries across models
byq=collections.defaultdict(list)
for r in recs: byq[r['query'].strip()].append(r)
multi={q:v for q,v in byq.items() if len(v)>1}
print('unique queries', len(byq), 'queries failed by >=2 models', len(multi), 'records in them', sum(len(v) for v in multi.values()))
print('dist of #models per query', C(len(v) for v in byq.values()))
# root-cause agreement on same query
agree=C()
for q,v in multi.items():
    rcs=[x['root_cause_primary'] for x in v]
    agree['all_same' if len(set(rcs))==1 else 'differ']+=1
print('root cause on same query across models', agree)
pickle.dump(multi, open(CACHE+'/sab_multi.pkl','wb'))
