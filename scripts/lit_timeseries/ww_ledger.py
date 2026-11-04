import json, sys, glob, os, re
import numpy as np
rows=[]
for f in sorted(glob.glob(os.path.join(sys.argv[1],'*.json'))):
    x=json.load(open(f)); k=int(str(x['mistake_step']).strip('"')); H=x['history']
    flags=[]
    for i,m in enumerate(H):
        c=m['content']
        if 'is_in_loop' in c:
            loop=re.search(r'"is_in_loop":\s*\{[^}]*"answer":\s*(true|false)', c)
            prog=re.search(r'"is_progress_being_made":\s*\{[^}]*"answer":\s*(true|false)', c)
            if (loop and loop.group(1)=='true') or (prog and prog.group(1)=='false'): flags.append(i)
    rows.append((k,len(H),flags))
n=len(rows); has=[r for r in rows if r[2]]
print('HC logs',n,'with >=1 stall flag (in_loop true or progress false):',len(has))
first=np.array([r[2][0] for r in has]); ks=np.array([r[0] for r in has])
print('first stall flag after k*: %.3f, at/before k*: %.3f; median gap (flag - k*): %.1f steps'%(np.mean(first>ks),np.mean(first<=ks),np.median(first-ks)))
print('median rel pos first flag %.2f vs k* %.2f'%(np.median([r[2][0]/r[1] for r in has]),np.median([r[0]/r[1] for r in has])))
# step-before-first-flag as predictor of k*? and 'last WebSurfer step before first flag'
def ev(p,g,k): return np.mean(np.abs(np.array(p)-np.array(g))<=k)
print('first flag as k* predictor: exact %.3f +-3 %.3f'%(ev(first,ks,0),ev(first,ks,3)))
