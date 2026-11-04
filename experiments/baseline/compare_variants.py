"""Panel comparison: for each dataset, score every variant file on exactly the ids it contains, with the std run
restricted to the same ids.  python3 -I baseline/compare_variants.py"""
import json, os, glob, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from score import norm_agent
import importlib.util
spec = importlib.util.spec_from_file_location("aao", os.path.join(HERE, "all_at_once.py")); aao = importlib.util.module_from_spec(spec); spec.loader.exec_module(aao)


def load(path):
    out = {}
    for l in open(path):
        r = json.loads(l)
        if not r["pred"] and r.get("raw"): r["pred"] = aao.fallback_parse(r["raw"])
        out[r["id"]] = r
    return out


def metrics(rows):
    n = len(rows); ex = pm1 = pm3 = ag = early = late = 0
    for r in rows:
        g = r["gold"]["faulty_step"]; p = r["pred"] or {}
        try: ps = int(p.get("faulty_step", p.get("decisive_step")))
        except Exception: ps = None
        if ps is not None and g is not None:
            d = ps - g; ex += d == 0; pm1 += abs(d) <= 1; pm3 += abs(d) <= 3; early += d < 0; late += d > 0
        if r["gold"].get("faulty_agent") and norm_agent(p.get("faulty_agent", p.get("decisive_agent"))) == norm_agent(r["gold"]["faulty_agent"]): ag += 1
    return n, 100 * ex / n, 100 * pm1 / n, 100 * pm3 / n, 100 * ag / n, 100 * early / n, 100 * late / n


files = sorted(glob.glob(os.path.join(HERE, "out", "*.jsonl")))
by = collections.defaultdict(dict)
for f in files:
    b = os.path.basename(f)[:-6]
    if b.startswith("misses__") or b.startswith("predtags__") or "inventory" in b: continue
    slug, _, variant = b.partition("__")
    by[slug][variant or "std"] = f
print("| dataset | variant | n | exact | ±1 | ±3 | agent | earlier | later |")
print("|---|---|---|---|---|---|---|---|---|")
for slug, vs in sorted(by.items()):
    if "std" not in vs or len(vs) < 2: continue
    std = load(vs["std"])
    for v, f in sorted(vs.items()):
        if v == "std": continue
        rows = [r for r in load(f).values() if r["id"] in std and r["gold"]["faulty_step"] is not None]
        ids = {r["id"] for r in rows}
        base = [std[i] for i in ids]
        if not rows: continue
        m0 = metrics(base); m1 = metrics(rows)
        print(f"| {slug} | std (same ids) | {m0[0]} | {m0[1]:.1f} | {m0[2]:.1f} | {m0[3]:.1f} | {m0[4]:.1f} | {m0[5]:.0f} | {m0[6]:.0f} |")
        print(f"| {slug} | **{v}** | {m1[0]} | {m1[1]:.1f} | {m1[2]:.1f} | {m1[3]:.1f} | {m1[4]:.1f} | {m1[5]:.0f} | {m1[6]:.0f} |")
