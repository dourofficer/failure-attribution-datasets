import os; CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','cache')
import pickle, re, collections
recs=pickle.load(open(CACHE+'/sab_recs.pkl','rb'))
C=collections.Counter
bym=collections.defaultdict(list)
for r in recs: bym[r['model']].append(len(r['trajectory']))
for m,L in bym.items():
    mx=max(L); print(f"{m:28} n={len(L):4} max_len={mx:4} n_at_max={L.count(mx):3} n>=0.95max={sum(l>=0.95*mx for l in L)}")
# user messages beyond the first (forced-answer prompts?)
um=C()
for r in recs:
    for m in r['trajectory'][2:]:
        if m['role']=='user': um[(m['content'] or '')[:120]]+=1
print('later user msgs:', um.most_common(8))
# tool-return error patterns
errpat=re.compile(r'(error|failed to|timed? ?out|exception|429|403 forbidden|rate limit|could not be|unable to (fetch|access|retrieve)|no results found|captcha|access denied|页面无法)', re.I)
tot=errs=0; per=[]
for r in recs:
    tm=[m for m in r['trajectory'] if m['role']=='tool']
    e=sum(1 for m in tm if errpat.search((m['content'] or '')[:400]))
    tot+=len(tm); errs+=e
    if tm: per.append((e/len(tm), r['index'], len(tm), r['model']))
print('tool msgs', tot, 'with error-like prefix', errs, f'{errs/tot:.1%}')
per.sort(reverse=True)
print('runs with >=50% error-like tool returns:', sum(1 for p in per if p[0]>=0.5), C(p[3] for p in per if p[0]>=0.5))
print(per[:8])
# degenerate final answers
deg=[r['index'] for r in recs if re.search(r'(</think>\s*){3,}', r['predicted_answer'] or '') or len(set((r['predicted_answer'] or 'x').split()))<4]
print('degenerate/very short answers', len(deg), deg[:20])
nc=[r['index'] for r in recs if re.search(r'NO_CANDIDATE|无法(给出|确定|找到)|cannot (determine|find|provide)', r['predicted_answer'] or '', re.I)]
print('abstain-like answers', len(nc))
