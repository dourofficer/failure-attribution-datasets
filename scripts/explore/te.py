import json,glob,os,re,collections,sys,statistics as st
R=sys.argv[1]; base=R+'/data/traceelephant/extracted/data'
def text_of(msg):
    c=msg.get('content')
    if isinstance(c,str): return c
    if isinstance(c,list): return ' '.join(p.get('text','') for p in c if isinstance(p,dict))
    return ''
gt_in_input=0; gt_any=0; n_gt=0; selfflag=collections.Counter(); mtype=collections.Counter(); tokfrac=[]
ww_ids=set()
def unq(x):
    if isinstance(x,str) and len(x)>=2 and x[0]==x[-1]=="'": return x[1:-1]
    return x
for p in glob.glob(f'{R}/data/who_and_when/Who&When/*/*.json'):
    ww_ids.add(unq(json.load(open(p)).get('question_ID')))
overlap=0; n=0; mistake_is_toolcall=0; mistake_agent_steps=[]
ledger_before=[]; ledger_total=0
for md in glob.glob(base+'/*/*/trace_metadata.json'):
    m=json.load(open(md)); d=os.path.dirname(md); n+=1
    if m.get('task_id') in ww_ids: overlap+=1
    try: k=int(str(m['mistake_step']).replace('Step','').strip())
    except: continue
    steps=json.load(open(d+'/step_records.json'))
    s=steps[k-1]
    out=s.get('output') or {}
    msg=(out.get('choices') or [{}])[0].get('message',{}) if isinstance(out,dict) else {}
    has_tc=bool(msg.get('tool_calls')) or bool(s.get('tool_logs'))
    mtype[(m['system_name'],'tool_call' if has_tc else 'text')]+=1
    # tokens of input at mistake step relative to max in trace
    toks=[((x.get('output') or {}).get('usage') or {}).get('prompt_tokens') for x in steps]
    toks=[t for t in toks if t]
    tk=((out.get('usage') or {}).get('prompt_tokens'))
    if toks and tk: tokfrac.append(tk/max(toks))
    # ground truth presence in the INPUT context of the mistake step or any earlier step
    gt=str(m.get('ground_truth') or '').strip().lower()
    if gt and len(gt)>=3 and m['system_name']!='swe-agent':
        n_gt+=1
        ctx=' '.join(text_of(mm) for mm in s['input']['messages']).lower()
        if gt in ctx: gt_in_input+=1
        allctx=' '.join(text_of(mm) for x in steps for mm in x['input']['messages']).lower()+' '.join(str(x.get('output')) for x in steps).lower()
        if gt in allctx: gt_any+=1
    # Magentic-One self-monitoring: ledger flags before the mistake step
    if m['system_name']=='magentic-one':
        flags=[]
        for x in steps[:k-1]:
            o=str((x.get('output') or {}))
            if re.search(r'"is_in_loop":\s*\{[^}]*"answer":\s*true',o,re.S) or re.search(r'"is_progress_being_made":\s*\{[^}]*"answer":\s*false',o,re.S): flags.append(x['step_id'])
        ledger_total+=1
        if flags: ledger_before.append((len(flags),k))
print('traces',n,'task_id overlap with Who&When',overlap)
print('mistake step type:',sorted(mtype.items()))
print('ground truth string in the mistake step INPUT context: %d/%d; anywhere in trace: %d/%d'%(gt_in_input,n_gt,gt_any,n_gt))
print('prompt tokens at mistake step / max prompt tokens in trace: median %.2f'%st.median(tokfrac))
print('Magentic-One traces where the orchestrator ledger flagged loop/no-progress BEFORE the labelled step: %d/%d'%(len(ledger_before),ledger_total))
