import os; CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','cache')
import pickle, re, collections, unicodedata
recs=pickle.load(open(CACHE+'/sab_recs.pkl','rb'))
C=collections.Counter; c=C()
def norm(s): 
    s=unicodedata.normalize('NFKC', str(s)).lower()
    return re.sub(r'[\s\*\.,;:!?\'"“”‘’()\[\]（）《》<>/\\-]','',s)
mism=[]; leak_rub=[]; leak_dir=[]; leak_rat=[]; fn=[]
for r in recs:
    k=r['critical_step']['message_index']; rat=r['rationale']['failure_rationale']
    nums=[int(x) for x in re.findall(r'[Mm]essage\s*#?\s*(\d+)', rat)]
    first=nums[0] if nums else None
    if first is None: c['rat_no_msgnum']+=1
    elif first!=k: c['rat_first_num_ne_k']+=1; mism.append((r['index'],k,nums[:6]))
    else: c['rat_first_num_eq_k']+=1
    g=norm(r['gold_answer']); 
    if len(g)>=2:
        rub=' '.join(x['requirement'] for x in r['repair_rubrics'])
        if g in norm(rub): leak_rub.append(r['index'])
        if g in norm(r['repair_directive']): leak_dir.append(r['index'])
        if g in norm(rat): leak_rat.append(r['index'])
        p=norm(re.sub(r'</?answer>','',r['predicted_answer'] or ''))
        if g in p: fn.append(r['index'])
    else: c['short_gold']+=1
print(dict(c))
print('rationale first msg num != label:', len(mism)); print(mism[:25])
print('gold in rubrics', len(leak_rub), 'gold in directive', len(leak_dir), 'gold in rationale', len(leak_rat))
print('gold substring of predicted answer', len(fn), fn[:40])
pickle.dump(dict(mism=mism,leak_rub=leak_rub,leak_dir=leak_dir,leak_rat=leak_rat,fn=fn),open(CACHE+'/sab_c2.pkl','wb'))
