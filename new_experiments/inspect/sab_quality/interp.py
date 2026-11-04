import os; CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','cache')
# rationales whose argument hinges on how the question is read (upper bound on gold-ambiguity items)
import pickle, re, collections
recs=pickle.load(open(CACHE+'/sab_recs.pkl','rb')); C=collections.Counter
pat=re.compile(r'(interpretation|could instead|did not explicitly|does not explicitly|narrower (reading|interpretation|meaning|counting)|counting (rule|frame|convention)|reading of the (query|prompt|question)|ambiguous|ambiguity|alternative reading|competing (reading|interpretation|meaning)s?)', re.I)
H=[r for r in recs if pat.search(r['rationale']['failure_rationale'])]
print(len(H), C(r['dataset'] for r in H), C(r['root_cause_primary'] for r in H))
