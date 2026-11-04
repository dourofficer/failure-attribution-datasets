import os; CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','cache')
import pickle, re
multi=pickle.load(open(CACHE+'/sab_multi.pkl','rb'))
def short(p):
    p=re.sub(r'</?answer>','',p or ''); p=re.sub(r'### Related URLs.*','',p,flags=re.S)
    m=re.findall(r'\*\*([^*]{1,80})\*\*', p)
    ex=re.findall(r'(?:Exact Answer|Final Answer|Answer)\s*[:：]\s*(.{1,80})', p)
    return (ex[-1] if ex else (m[-1] if m else p.strip()[-80:])).replace('\n',' ')
for q,v in sorted(multi.items(), key=lambda kv:-len(kv[1])):
    if len(v)<3: continue
    print(f"=== [{v[0]['dataset']}] GOLD={v[0]['gold_answer'][:80]!r}\n Q: {q[:230]}")
    for x in v: print(f"   {x['index']:>5} {x['model'][:14]:14} {x['root_cause_primary'][:22]:22} k={x['critical_step']['message_index']:>3}/{len(x['trajectory'])}  ANS: {short(x['predicted_answer'])[:90]}")
