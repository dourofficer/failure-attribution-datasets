import os; CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','cache')
import pickle, re, collections, json
recs=pickle.load(open(CACHE+'/sab_recs.pkl','rb'))
C=collections.Counter
stat=collections.defaultdict(C); runfail=[]
def kind(args):
    if isinstance(args,str):
        try: args=json.loads(args)
        except Exception: return 'unparsable'
    q=args.get('query') if isinstance(args,dict) else None
    if isinstance(q,list): return 'list'
    if isinstance(q,str):
        s=q.strip()
        if s.startswith('['): return 'str_list'
        if q.startswith('\n'): return 'str_leading_nl'
        return 'str'
    return 'other'
for r in recs:
    T=r['trajectory']; tool_out={}
    # map tool_call_id -> content if present, else sequential
    tmsgs=[m for m in T if m['role']=='tool']
    calls=[]
    for m in T:
        if m['role']=='assistant':
            for tc in (m.get('tool_calls') or []): calls.append((m['message_index'],tc))
    nores=n=0
    for (mi,tc) in calls:
        if tc['tool_name']!='search': continue
        k=kind(tc['tool_arguments'])
        # find next tool message after mi
        nxt=next((t for t in tmsgs if t['message_index']>mi),None)
        if nxt is None: continue
        c=(nxt['content'] or '')
        res='nores' if c.lstrip().startswith('No results found') else ('ok' if 'found' in c[:300] else 'other')
        stat[(r['model'],k)][res]+=1
        n+=1; nores+= res=='nores'
    if n>=5: runfail.append((nores/n, r['index'], r['model'], r['root_cause_primary'], n))
print(f"{'model':28} {'format':15} {'calls':>6} {'nores%':>7}")
for (m,k),c in sorted(stat.items()):
    t=sum(c.values()); print(f"{m:28} {k:15} {t:6} {c['nores']/t:7.1%}")
tot=C(); 
for (m,k),c in stat.items(): tot[k+'_n']+=sum(c.values()); tot[k+'_nores']+=c['nores']
print({k:v for k,v in tot.items()})
hi=[x for x in runfail if x[0]>=0.5]
print('runs (>=5 searches) where >=50% of searches return No results:', len(hi), 'of', len(runfail))
print(' by model', C(x[2] for x in hi)); print(' by root cause', C(x[3] for x in hi))
pickle.dump(hi,open(CACHE+'/sab_hi.pkl','wb'))
