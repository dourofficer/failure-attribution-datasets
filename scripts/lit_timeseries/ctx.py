import sys,re
t=open(sys.argv[1]).read()
for pat in sys.argv[2:]:
    for m in list(re.finditer(pat,t,flags=re.I))[:6]:
        s=max(0,m.start()-250); print('==',pat,'==', t[s:m.end()+350].replace('\n',' ')); print()
