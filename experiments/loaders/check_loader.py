"""Smoke test: python3 -I check_loader.py <slug> [limit]. Loads, validates, prints counts and one rendered example."""
import importlib, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schema import validate

slug = sys.argv[1]
limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
mod = importlib.import_module(slug)
n = 0; bad = 0; nsteps = []; roles = collections.Counter(); subsets = collections.Counter(); outcomes = collections.Counter()
labelled = 0; first = None
for t in mod.load(limit=limit):
    n += 1
    e = validate(t)
    if e:
        bad += 1
        if bad <= 5:
            print("INVALID", t.get("id"), e)
        continue
    nsteps.append(len(t["steps"]))
    roles.update(s["role"] for s in t["steps"])
    subsets[t["subset"]] += 1
    outcomes[t["outcome"]] += 1
    if t["annotation"]["faulty_step"] is not None or t["annotation"]["faulty_steps"]:
        labelled += 1
    if first is None:
        first = t
print(f"{slug}: {n} trajectories, {bad} invalid, labelled {labelled}, outcomes {dict(outcomes)}")
print("subsets", dict(subsets))
print("roles", dict(roles))
if nsteps:
    s = sorted(nsteps); print("steps median", s[len(s)//2], "min", s[0], "max", s[-1])
if first:
    t = first
    print("--- example", t["id"], "subset", t["subset"], "system", t["system"])
    print("task:", t["task"][:300].replace("\n", " "))
    print("label:", {k: v for k, v in t["annotation"].items() if k != "extra"})
    print("extra keys:", list(t["annotation"]["extra"].keys()))
    for s in t["steps"][:6]:
        print(f"  [{s['idx']}|{s['native_idx']}] {s['role']}/{s['agent']}: {s['content'][:160]!r}")
