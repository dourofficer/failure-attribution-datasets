"""Self-consistency outputs (__std__sc5): accuracy of the vote, and vote share as a confidence signal.
python3 -I baseline/analyze_sc.py"""
import json, os, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__))
print("| dataset | n | greedy exact | vote exact | any-of-5 exact (oracle) | share≥0.8: n, exact | share≤0.4: n, exact |")
print("|---|---|---|---|---|---|---|")
for f in sorted(glob.glob(os.path.join(HERE, "out", "*__std__sc5.jsonl"))):
    slug = os.path.basename(f).split("__")[0]
    std = {}
    for l in open(os.path.join(HERE, "out", f"{slug}__std.jsonl")):
        r = json.loads(l); std[r["id"]] = r
    n = g_ok = v_ok = any_ok = 0; hi = [0, 0]; lo = [0, 0]
    for l in open(f):
        r = json.loads(l)
        if not r["pred"] or r["gold"]["faulty_step"] is None: continue
        g = r["gold"]["faulty_step"]; s = std.get(r["id"])
        try: gp = int(s["pred"]["faulty_step"])
        except Exception: gp = None
        n += 1; g_ok += gp == g; v_ok += r["pred"].get("faulty_step") == g; any_ok += g in (r.get("samples") or [])
        sh = r["pred"].get("vote_share", 0)
        if sh >= 0.8: hi[0] += 1; hi[1] += r["pred"].get("faulty_step") == g
        if sh <= 0.4: lo[0] += 1; lo[1] += r["pred"].get("faulty_step") == g
    if n:
        print(f"| {slug} | {n} | {100*g_ok/n:.1f} | {100*v_ok/n:.1f} | {100*any_ok/n:.1f} | {hi[0]}, {100*hi[1]/max(hi[0],1):.1f} | {lo[0]}, {100*lo[1]/max(lo[0],1):.1f} |")
