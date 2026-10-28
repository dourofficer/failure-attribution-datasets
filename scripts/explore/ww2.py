import json,glob,os,re,collections,sys
R=sys.argv[1]
def unq(x):
    if isinstance(x,str) and len(x)>=2 and x[0]==x[-1]=="'": return x[1:-1]
    return x
recs=[]
for sub in ['Hand-Crafted','Algorithm-Generated']:
    for p in glob.glob(f'{R}/data/who_and_when/Who&When/{sub}/*.json'):
        d={k:unq(v) for k,v in json.load(open(p)).items()}; d['_sub']=sub; d['_f']=os.path.basename(p); recs.append(d)
# paired tasks
byq=collections.defaultdict(list)
for d in recs: byq[d['question_ID']].append(d)
pairs=[v for v in byq.values() if len(v)==2]
print('pairs',len(pairs))
same_phase=0
for v in pairs:
    hc=[d for d in v if d['_sub']=='Hand-Crafted'][0]; ag=[d for d in v if d['_sub']=='Algorithm-Generated'][0]
    rh=hc['mistake_reason'].lower(); ra=ag['mistake_reason'].lower()
    print(f"HC step {hc['mistake_step']:>3}/{len(hc['history']):<3} {hc['mistake_agent']:<22} | AG step {ag['mistake_step']:>2}/{len(ag['history']):<3} {ag['mistake_agent']:<28} | HC: {rh[:70]} | AG: {ra[:70]}")
