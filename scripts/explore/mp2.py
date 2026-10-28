import json,glob,os,re,collections,sys,statistics as st
R=sys.argv[1]; base=R+'/data/mp_bench/adobe_multi-agent-eval-bench/MP-Bench'
ann=collections.defaultdict(dict)
for a in ['1','2','3']:
    for split in ['manual','automatic']:
        for f in glob.glob(f'{base}/{a}/{split}/*.json'):
            ann[(split,int(os.path.basename(f)[:-5]))][a]=json.load(open(f))
def unq(x):
    if isinstance(x,str) and len(x)>=2 and x[0]==x[-1]=="'": return x[1:-1]
    return x
ww={}
for sub in ['Hand-Crafted','Algorithm-Generated']:
    for p in glob.glob(f'{R}/data/who_and_when/Who&When/{sub}/*.json'):
        ww[(sub,os.path.basename(p))]={k:unq(v) for k,v in json.load(open(p)).items()}
def ww_key(src):
    m=re.search(r'Who%26When/(Hand-Crafted|Algorithm-Generated)/(\d+\.json)',src); return (m.group(1),m.group(2)) if m else None
cats={a:set() for a in '123'}; maj_vs=collections.Counter(); lastq=collections.Counter(); tot=collections.Counter()
reason_len={a:[] for a in '123'}; pairwise=collections.Counter()
for key,recs in ann.items():
    sets={a:{int(x['step']) for x in r['annotation']} for a,r in recs.items()}
    for a,r in recs.items():
        for x in r['annotation']: cats[a].add(x['fail_category']); reason_len[a].append(len(x['fail_reason']))
    for a,b in [('1','2'),('1','3'),('2','3')]:
        u=sets[a]|sets[b]; i=sets[a]&sets[b]
        if u: pairwise[(a,b)]+=len(i)/len(u); pairwise[(a,b,'n')]+=1
    votes=collections.Counter(s for S in sets.values() for s in S)
    maj=[s for s,v in votes.items() if v>=2]
    k=ww_key(recs['1']['log_source'])
    if k and k in ww and maj:
        w=int(ww[k]['mistake_step']); e=min(maj); maj_vs['n']+=1
        maj_vs['ww==earliest_majority']+=(w==e); maj_vs['ww>earliest_majority']+=(w>e); maj_vs['ww<earliest_majority']+=(w<e)
        maj_vs['ww in majority set']+=(w in maj)
print('category vocab sizes:',{a:len(c) for a,c in cats.items()},'| shared by all:',len(cats['1']&cats['2']&cats['3']),'| union:',len(cats['1']|cats['2']|cats['3']))
print('all categories:',sorted(cats['1']|cats['2']|cats['3']))
print('median reason length per annotator:',{a:st.median(v) for a,v in reason_len.items()})
print('pairwise Jaccard of flagged-step sets (mean):',{f'{a}-{b}':round(pairwise[(a,b)]/pairwise[(a,b,'n')],2) for a,b in [('1','2'),('1','3'),('2','3')]})
print('W&W label vs earliest MAJORITY-flagged step:',dict(maj_vs))
