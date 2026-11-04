"""Score baseline outputs: python3 -I baseline/score.py out/<file>.jsonl [...]  -> per-file metrics table."""
import json, sys, collections


def norm_agent(a):
    return (a or "").strip().strip("'\"").lower().replace(" ", "").split("(")[0]


def score(path):
    rows = [json.loads(l) for l in open(path)]
    import importlib.util, os
    spec = importlib.util.spec_from_file_location("aao", os.path.join(os.path.dirname(os.path.abspath(__file__)), "all_at_once.py")); aao = importlib.util.module_from_spec(spec); spec.loader.exec_module(aao)
    for r in rows:
        if not r["pred"] and r.get("raw"):
            r["pred"] = aao.fallback_parse(r["raw"])
    n = len(rows); parsed = 0; sa = 0; ss = 0; s1 = 0; s3 = 0; s5 = 0; sset = 0; early = 0; late = 0; dist = []
    for r in rows:
        p = r["pred"]; g = r["gold"]
        if not p:
            continue
        parsed += 1
        ps = p.get("faulty_step", p.get("decisive_step")); pa = p.get("faulty_agent", p.get("decisive_agent"))
        try: ps = int(ps)
        except Exception: ps = None
        gs = g.get("faulty_step"); gset = set(g.get("faulty_steps") or [])
        if g.get("faulty_agent") and norm_agent(pa) == norm_agent(g["faulty_agent"]):
            sa += 1
        if ps is not None and gs is not None:
            d = ps - gs; dist.append(d)
            ss += d == 0; s1 += abs(d) <= 1; s3 += abs(d) <= 3; s5 += abs(d) <= 5; early += d < 0; late += d > 0
        if ps is not None and ps in gset:
            sset += 1
    k = max(parsed, 1)
    return {"file": path.split("/")[-1], "n": n, "parsed": parsed, "agent_acc": round(100 * sa / k, 1), "step_exact": round(100 * ss / k, 1),
            "step@1": round(100 * s1 / k, 1), "step@3": round(100 * s3 / k, 1), "step@5": round(100 * s5 / k, 1), "in_label_set": round(100 * sset / k, 1),
            "pred_earlier": round(100 * early / k, 1), "pred_later": round(100 * late / k, 1),
            "median_signed_dist": sorted(dist)[len(dist) // 2] if dist else None}


if __name__ == "__main__":
    res = [score(p) for p in sys.argv[1:]]
    keys = list(res[0].keys())
    print("| " + " | ".join(keys) + " |"); print("|" + "---|" * len(keys))
    for r in res:
        print("| " + " | ".join(str(r[k]) for k in keys) + " |")
