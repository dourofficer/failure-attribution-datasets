import sys, json, collections
d = json.load(open(sys.argv[1]))
print(type(d), len(d))
r = d[0] if isinstance(d, list) else d
if isinstance(d, dict): print(list(d.keys())[:10]); r = d[list(d.keys())[0]]
print(json.dumps(r, default=str)[:3000])
if isinstance(d, list):
    print(collections.Counter(x['mas_name'] for x in d)); print(collections.Counter(x['llm_name'] for x in d)); print(collections.Counter(x['benchmark_name'] for x in d))
    print(collections.Counter(type(x['trace']).__name__ for x in d))
    print(collections.Counter(type(x['trace'].get('trajectory')).__name__ for x in d if isinstance(x['trace'],dict)))
    print(collections.Counter(tuple(sorted(x['trace'].keys())) for x in d if isinstance(x['trace'],dict)))
