import os; CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','cache')
import pickle, re, collections
recs=pickle.load(open(CACHE+'/sab_recs.pkl','rb')); C=collections.Counter
tot=C(); hit=C(); ex=[]
for r in recs:
    m=re.search(r'<answer>\s*(.*?)\s*</answer>', r['predicted_answer'] or '', re.S)
    if not m: continue
    a=re.sub(r'[\*\s。.]+$','',re.sub(r'^\*+','',m.group(1).strip()))
    if not (2<=len(a)<=40) or '\n' in a: continue
    rc=r['root_cause_primary']; tot[rc]+=1
    s=r['critical_step']['span_start_message_index']
    first=None
    for msg in r['trajectory'][2:s]:
        if msg['role']!='assistant': continue
        txt=(msg.get('reasoning_content') or '')+(msg.get('content') or '')
        if re.search(r'<answer>\s*\**'+re.escape(a), txt) or re.search(r'(answer|答案)\s*(is|:|：|为|是)\s*\**'+re.escape(a), txt, re.I):
            first=msg['message_index']; break
    if first is not None:
        hit[rc]+=1; ex.append((r['index'], r['model'][:10], rc, first, r['critical_step']['message_index'], len(r['trajectory']), a[:30]))
print('runs with short <answer>:', sum(tot.values()), ' of which final answer already stated as answer BEFORE the labelled span:', sum(hit.values()))
for k in tot: print(f'  {k:28} {hit[k]:3}/{tot[k]:3}')
for e in ex[:15]: print(e)
