import sys, site; sys.path.append(site.getusersitepackages())
import sys, pandas as pd, json, collections
df = pd.read_parquet(sys.argv[1])
print(df.shape); print(df.dtypes)
print(df[['dataset','generator_model']].value_counts())
print('mistake_agent:', collections.Counter(df.mistake_agent).most_common(20))
print('is_corrected', df.is_corrected.value_counts().to_dict(), 'level', df.level.value_counts().to_dict(), 'gaia_level', df.gaia_level.value_counts(dropna=False).to_dict())
lens = df.history.apply(len); print('steps', lens.describe())
print('mistake_step describe', df.mistake_step.describe())
roles = collections.Counter(); 
for h in df.history:
    for m in h: roles[m['role']] += 1
print('roles', roles.most_common(30))
r = df.iloc[0]
print(json.dumps({k:(r[k] if k!='history' else None) for k in df.columns}, default=str)[:1500])
for i,m in enumerate(r.history[:6]): print(i, m['role'], '|', m['content'][:300].replace('\n',' '))
print('reason empty frac', (df.mistake_reason.fillna('')=='').mean())
print(df.mistake_reason.iloc[0][:800])
