import os; CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','cache')
import pickle, re, collections
recs=pickle.load(open(CACHE+'/sab_recs.pkl','rb')); C=collections.Counter
R=[r['rationale']['failure_rationale'] for r in recs]
pats={'earliest decisive':r'earliest decisive','"Message N is the ..."':r'^\s*Message \d+ is (the|where)','"remains"/"still the"':r'\b(remains|is still) the (earliest|critical|decisive)','"rather than"':r'rather than','mentions span/adjacent':r'\b(span|adjacent)\b','"because"':r'\bbecause\b'}
for k,p in pats.items(): print(f"{k:28} {sum(1 for x in R if re.search(p,x,re.I|re.M))}")
print('first 4 words:', C(' '.join(re.sub(r'\d+','N',x).split()[:4]) for x in R).most_common(6))
L=[len(x.split()) for x in R]; L.sort(); print('rationale words median', L[len(L)//2], 'p10', L[len(L)//10], 'p90', L[9*len(L)//10])
rem=[ (r['index'],re.search(r'.{0,60}\b(remains|is still) the (earliest|critical|decisive).{0,40}',r['rationale']['failure_rationale']).group(0)) for r in recs if re.search(r'\b(remains|is still) the (earliest|critical|decisive)',r['rationale']['failure_rationale'])]
for x in rem[:8]: print(x)
# repair directives / rubrics templating
D=[r['repair_directive'] for r in recs]
print('directive first 3 words:', C(' '.join(x.split()[:3]) for x in D).most_common(6))
RB=[x['requirement'] for r in recs for x in r['repair_rubrics']]
print('rubric first 2 words:', C(' '.join(x.split()[:2]) for x in RB).most_common(6), 'of', len(RB))
