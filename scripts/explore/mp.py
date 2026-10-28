import json,glob,os,re,collections,sys,urllib.parse
R=sys.argv[1]
base=R+'/data/mp_bench/adobe_multi-agent-eval-bench/MP-Bench'
ann=collections.defaultdict(dict)   # (split,n) -> annotator -> record
for a in ['1','2','3']:
    for split in ['manual','automatic']:
        for f in glob.glob(f'{base}/{a}/{split}/*.json'):
            n=int(os.path.basename(f)[:-5]); ann[(split,n)][a]=json.load(open(f))
print('logs',len(ann))
# W&W labels
ww={}
def unq(x):
    if isinstance(x,str) and len(x)>=2 and x[0]==x[-1]=="'": return x[1:-1]
    return x
for sub in ['Hand-Crafted','Algorithm-Generated']:
    for p in glob.glob(f'{R}/data/who_and_when/Who&When/{sub}/*.json'):
        d=json.load(open(p)); ww[(sub,os.path.basename(p))]={k:unq(v) for k,v in d.items()}
def ww_key(src):
    m=re.search(r'Who%26When/(Hand-Crafted|Algorithm-Generated)/(\d+\.json)',src)
    return (m.group(1),m.group(2)) if m else None
stats=collections.Counter(); sizes=[]; union_sizes=[]; inter_sizes=[]
pos=collections.Counter(); catagree=collections.Counter(); chain=collections.Counter()
earliest_vs_ww=[]
cat_by_ann=collections.defaultdict(collections.Counter)
per_log_cats=[]
for key,recs in ann.items():
    if len(recs)<3: continue
    sets={a:{int(x['step']) for x in r['annotation']} for a,r in recs.items()}
    for a,s in sets.items(): sizes.append(len(s))
    U=set.union(*sets.values()); I=set.intersection(*sets.values())
    union_sizes.append(len(U)); inter_sizes.append(len(I))
    if not U: stats['no_flag_any']+=1
    # earliest flagged step per annotator: agree?
    firsts=[min(s) for s in sets.values() if s]
    if len(firsts)==3:
        stats['earliest_all_same']+= (len(set(firsts))==1)
        stats['earliest_within1']+= (max(firsts)-min(firsts)<=1)
        stats['have3first']+=1
    # categories at the same step: agreement
    bystep=collections.defaultdict(list)
    for a,r in recs.items():
        for x in r['annotation']:
            bystep[int(x['step'])].append(x['fail_category']); cat_by_ann[a][x['fail_category']]+=1
    for s,cats in bystep.items():
        if len(cats)>=2:
            catagree['pairs']+=1; catagree['same']+= (len(set(cats))==1)
    # chain structure: are an annotator's flagged steps contiguous-ish?
    for a,s in sets.items():
        if len(s)>=2:
            ss=sorted(s); chain['multi']+=1; chain['contiguous']+= all(b-a_==1 for a_,b in zip(ss,ss[1:]))
    # compare with W&W
    k=ww_key(recs['1']['log_source'])
    if k and k in ww:
        w=int(ww[k]['mistake_step']); n=len(ww[k]['history'])
        stats['ww_matched']+=1
        votes=sum(1 for s in sets.values() if w in s)
        pos[votes]+=1
        if firsts:
            e=min(firsts); earliest_vs_ww.append((w-e, w, e, n))
print('flags per annotator-log: mean %.2f'%(sum(sizes)/len(sizes)), 'zero-flag annotator-logs', sum(1 for s in sizes if s==0))
print('union mean %.2f, intersection mean %.2f, logs with empty intersection %d/%d'%(sum(union_sizes)/len(union_sizes), sum(inter_sizes)/len(inter_sizes), sum(1 for x in inter_sizes if x==0), len(inter_sizes)))
print('earliest flagged step: all three identical %d, within 1 step %d, of %d'%(stats['earliest_all_same'],stats['earliest_within1'],stats['have3first']))
print('category agreement when two+ annotators flag the same step: same %d / %d pairs'%(catagree['same'],catagree['pairs']))
print('multi-flag annotator-logs %d, contiguous chains %d'%(chain['multi'],chain['contiguous']))
print('W&W logs matched',stats['ww_matched'],'; number of MP annotators whose set contains the W&W step:',sorted(pos.items()))
import statistics as st
d=[x[0] for x in earliest_vs_ww]
print('W&W step minus earliest MP-flagged step: median %.1f, mean %.1f; W&W earlier %d, same %d, later %d'%(st.median(d),st.mean(d),sum(1 for x in d if x<0),sum(1 for x in d if x==0),sum(1 for x in d if x>0)))
for a,c in cat_by_ann.items(): print('annotator',a,c.most_common(6), 'total',sum(c.values()))
