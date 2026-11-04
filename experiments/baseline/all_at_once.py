"""All-at-once failure attribution baseline over the unified loaders.

python3 -I baseline/all_at_once.py <slug> [--limit N] [--sample N --seed S] [--budget CHARS] [--thinking] [--workers W] [--variant std|inventory]

variant std       : Who&When-style prompt -> {"faulty_agent","faulty_step","reason"}  (ground truth NOT given)
variant inventory : list every step that contains a mistake, each tagged recovered|fatal|unclear, plus the decisive step.
Outputs one JSONL line per trajectory in experiments/baseline/out/<slug>__<variant>[__think].jsonl (cached LLM calls).
"""
import argparse, json, os, random, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "loaders"))
from common.llm import LLM
from common.render import render
import importlib

SYS = "You are an expert at debugging LLM agent systems. You will be shown the complete log of a run of an agent system that FAILED its task. Answer strictly in the requested JSON."

STD = """The run below failed. Identify the agent responsible for the failure and the decisive error step: the EARLIEST step such that, had that step been done correctly, the run would most likely have succeeded. Steps that went wrong but were later corrected by the system are NOT the decisive error.

{body}

Answer with a single JSON object and nothing else:
{{"faulty_agent": "<agent name exactly as it appears in the step headers>", "faulty_step": <integer step number>, "reason": "<one or two sentences>"}}"""

INV = """The run below failed. Go through the whole run and list EVERY step at which a mistake was made (a wrong decision, wrong claim, wrong tool use, misread observation, bad plan, missed verification), including mistakes that the system later noticed or corrected. For each one say whether the system later RECOVERED from it (a later step corrected it or made it irrelevant), whether it was FATAL (it was never corrected and contributed to the final failure), or UNCLEAR. Then name the single decisive step: the earliest mistake that was never recovered from and without which the run would most likely have succeeded.

{body}

Answer with a single JSON object and nothing else:
{{"mistakes": [{{"step": <int>, "agent": "<name>", "what": "<short description>", "fate": "recovered|fatal|unclear", "recovered_at": <int or null>}}, ...],
 "decisive_step": <int>, "decisive_agent": "<name>", "reason": "<one or two sentences>"}}"""


INV_BLIND = """Below is the complete log of a run of an agent system. You are NOT told whether the run succeeded or failed. Go through the whole run and list EVERY step at which a mistake was made (a wrong decision, wrong claim, wrong tool use, misread observation, bad plan, missed verification), including mistakes that the system later noticed or corrected. For each one say whether the system later RECOVERED from it (a later step corrected it or made it irrelevant), whether it was FATAL (never corrected and would make the final result wrong), or UNCLEAR. Then say whether you believe the run ultimately SUCCEEDED (final result correct) or FAILED, with a probability.

{body}

Answer with a single JSON object and nothing else:
{{"mistakes": [{{"step": <int>, "agent": "<name>", "what": "<short description>", "fate": "recovered|fatal|unclear", "recovered_at": <int or null>}}, ...],
 "verdict": "succeeded|failed", "p_success": <float between 0 and 1>, "decisive_step": <int or null>, "reason": "<one or two sentences>"}}"""

SYS_BLIND = "You are an expert at debugging LLM agent systems. You will be shown the complete log of a run of an agent system. Answer strictly in the requested JSON."


TWOSTAGE = """The run below failed. A first pass already listed candidate mistakes with a guess of their fate:
{inventory}

Now do the consequence check. For EACH candidate in that list, look at the steps AFTER it and decide: was it undone, corrected, or made irrelevant by a later step (give that step number), or did its effect persist to the end? Discard every candidate that was undone. Among the remaining ones, the decisive error is the EARLIEST whose effect persisted and without which the run would most likely have succeeded. If none of the candidates survives, pick the step you now believe is decisive.

{body}

Answer with a single JSON object and nothing else:
{{"checks": [{{"step": <int>, "undone_by": <int or null>, "persisted": true|false}}, ...], "faulty_step": <int>, "faulty_agent": "<name>", "reason": "<one or two sentences>"}}"""


BACKWARD = """The run below failed. A first reading named step {k} (agent {kagent}) as the decisive error, with this reason: "{kreason}".

Now check whether that step is a CAUSE or a SYMPTOM. Look at the steps BEFORE step {k}: is there an earlier step whose error made step {k} go wrong or inevitable (for example an instruction that already contained the mistake, a wrong fact that was first introduced earlier, a plan that made step {k} the only option)? If such a step exists AND it was never corrected before step {k}, the decisive error is that earlier step. If the earlier candidate was corrected or worked around before step {k}, it is not the decisive error. If step {k} is the first point where the run went wrong, keep it.

{body}

Answer with a single JSON object and nothing else:
{{"earlier_candidates": [{{"step": <int>, "why": "<short>", "corrected_before_k": true|false}}, ...], "faulty_step": <int>, "faulty_agent": "<name>", "reason": "<one or two sentences>"}}"""


def build_fewshot(trajs, k, seed):
    """Sketch up to 3k labelled trajectories (so that each target can exclude itself): task, steps near the gold step, the label and the rationale."""
    import random
    pool = [t for t in trajs if t["annotation"]["faulty_step"] is not None]
    random.Random(seed + 1).shuffle(pool)
    out = []
    for t in pool[:3 * k]:
        g = t["annotation"]["faulty_step"]; steps = t["steps"]
        lo, hi = max(0, g - 6), min(len(steps), g + 5)
        lines = [f"TASK: {str(t['task'])[:400]}", f"(run of {len(steps)} steps; steps {lo}-{hi - 1} shown)"]
        for s in steps[lo:hi]:
            c = re.sub(r"\s+", " ", s["content"]).strip()[:260]
            mark = "  <== LABELLED DECISIVE ERROR" if s["idx"] == g else ""
            lines.append(f"[step {s['idx']}] {s['agent']}: {c}{mark}")
        lines.append(f"LABEL: step {g}, agent {t['annotation']['faulty_agent']}. RATIONALE: {(t['annotation']['reason'] or 'not given')[:400]}")
        out.append((t["id"], "\n".join(lines)))
    return out


def vote(outs):
    """Majority vote over sampled answers on the step; agent from the winning sample; keep all samples."""
    preds = [parse_json(o.get("text")) for o in outs]
    steps = []
    for p in preds:
        try: steps.append(int(p.get("faulty_step", p.get("decisive_step"))))
        except Exception: steps.append(None)
    valid = [x for x in steps if x is not None]
    if not valid:
        return {"text": outs[0].get("text"), "pred": None, "usage": outs[0].get("usage"), "error": outs[0].get("error"), "cached": outs[0].get("cached"), "samples": steps}
    import collections
    best = collections.Counter(valid).most_common(1)[0][0]
    win = next(p for p, s in zip(preds, steps) if s == best)
    win = dict(win); win["faulty_step"] = best; win["vote_share"] = valid.count(best) / len(steps)
    return {"text": outs[0].get("text"), "pred": win, "usage": outs[0].get("usage"), "error": None, "cached": outs[0].get("cached"), "samples": steps}


def anonymise(t):
    """Rename agents to Agent_k in order of first appearance; replace the names (and common casing/underscore variants)
    inside step contents and the final output; keep the gold under the same mapping so scoring is unchanged."""
    import copy
    t = copy.deepcopy(t)
    names = []
    for s in t["steps"]:
        base = re.sub(r"\s*\(.*\)$", "", s["agent"]).strip()
        if base and base.lower() not in ("user", "human", "system", "tool") and base not in names:
            names.append(base)
    mapping = {n: f"Agent_{i + 1}" for i, n in enumerate(sorted(names, key=len, reverse=True))}
    # ordinal by first appearance, but substitution longest-first to avoid partial overlaps
    order = {n: i for i, n in enumerate(names)}
    mapping = {n: f"Agent_{order[n] + 1}" for n in names}
    pats = [(re.compile(r"(?<![A-Za-z0-9_])" + re.escape(n) + r"(?![A-Za-z0-9_])", re.I), mapping[n]) for n in sorted(names, key=len, reverse=True)]

    def sub(txt):
        if not isinstance(txt, str):
            return txt
        for p, r in pats:
            txt = p.sub(r, txt)
        return txt
    for s in t["steps"]:
        base = re.sub(r"\s*\(.*\)$", "", s["agent"]).strip()
        suffix = s["agent"][len(base):]
        s["agent"] = (mapping.get(base, base) + sub(suffix)) if base in mapping else sub(s["agent"])
        s["content"] = sub(s["content"])
    t["final_output"] = sub(t.get("final_output")); t["task"] = sub(t.get("task"))
    ga = t["annotation"].get("faulty_agent")
    if ga:
        gb = re.sub(r"\s*\(.*\)$", "", ga).strip()
        t["annotation"]["faulty_agent"] = mapping.get(gb, sub(ga))
    t["meta"]["agent_mapping"] = mapping
    return t


def parse_json(txt):
    if not txt:
        return None
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        return None
    s = m.group(0)
    for cand in (s, s.replace("\n", " ")):
        try:
            return json.loads(cand)
        except Exception:
            pass
    # tolerate trailing commas
    try:
        return json.loads(re.sub(r",\s*([}\]])", r"\1", s))
    except Exception:
        pass
    return fallback_parse(txt)


def fallback_parse(txt):
    """Prose answers: take an explicit 'faulty_step: N' / 'decisive step ... N' / the last 'step N' mention."""
    if not txt:
        return None
    m = re.search(r"(?:faulty_step|decisive_step)\W{0,5}(\d+)", txt, re.I) or re.search(r"decisive (?:error )?step\D{0,40}?(\d+)", txt, re.I)
    if not m:
        ms = re.findall(r"[Ss]tep\s+(\d+)", txt)
        if not ms:
            return None
        m = None; step = int(ms[-1])
    else:
        step = int(m.group(1))
    ag = re.search(r"(?:faulty_agent|responsible agent|agent)\W{0,5}[\"']?([A-Za-z_][A-Za-z0-9_ ]{1,30})", txt)
    return {"faulty_step": step, "faulty_agent": ag.group(1).strip() if ag else None, "reason": txt[-300:], "parsed_by": "fallback"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug"); ap.add_argument("--limit", type=int); ap.add_argument("--sample", type=int); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--budget", type=int, default=450_000, help="character budget for the rendered trajectory (~130k tokens)")
    ap.add_argument("--thinking", action="store_true"); ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--variant", default="std", choices=["std", "inventory", "inventory_blind", "twostage", "backward"]); ap.add_argument("--subset")
    ap.add_argument("--max-tokens", type=int, default=3000); ap.add_argument("--only-labelled", action="store_true", default=True)
    ap.add_argument("--ids", help="file with one trajectory id per line: run only these (after subset filtering)")
    ap.add_argument("--gold", action="store_true", help="give the model the reference answer (trajectories without one are skipped)")
    ap.add_argument("--fewshot", type=int, default=0, help="K sketched labelled examples from the same dataset (other trajectories) in the prompt")
    ap.add_argument("--samples", type=int, default=1, help="N samples per trajectory (majority vote on the step); use with --temperature")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--anonymise", action="store_true", help="replace agent names by Agent_1.. (order of first appearance) in headers and content")
    a = ap.parse_args()
    mod = importlib.import_module(a.slug)
    if a.variant == "inventory_blind":  # all runs, successful ones included; outcome hidden from the model
        trajs = [t for t in mod.load(limit=a.limit, subset=a.subset) if t["steps"]]
    else:
        trajs = [t for t in mod.load(limit=a.limit, subset=a.subset) if t.get("outcome") != 1 and (t["annotation"]["faulty_step"] is not None or t["annotation"]["faulty_steps"])]
    if a.ids:
        keep = {l.strip() for l in open(a.ids) if l.strip()}
        trajs = [t for t in trajs if t["id"] in keep]
    if a.gold:
        trajs = [t for t in trajs if t.get("ground_truth") not in (None, "", "None")]
    inventory = {}
    if a.variant == "backward":  # second pass over the std prediction
        ip = os.path.join(HERE, "out", f"{a.slug}__std.jsonl")
        for line in open(ip):
            r = json.loads(line)
            if r["pred"] and r["pred"].get("faulty_step") is not None: inventory[r["id"]] = r["pred"]
        trajs = [t for t in trajs if t["id"] in inventory]
    if a.variant == "twostage":
        ip = os.path.join(HERE, "out", f"{a.slug}__inventory.jsonl")
        for line in open(ip):
            r = json.loads(line)
            if r["pred"] and isinstance(r["pred"].get("mistakes"), list): inventory[r["id"]] = r["pred"]
        trajs = [t for t in trajs if t["id"] in inventory]
    examples = build_fewshot(trajs, a.fewshot, a.seed) if a.fewshot else None
    if a.sample and a.sample < len(trajs):
        random.Random(a.seed).shuffle(trajs); trajs = sorted(trajs[:a.sample], key=lambda t: t["id"])
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    suffix = ('__think' if a.thinking else '') + ('__anon' if a.anonymise else '') + ('__gold' if a.gold else '') + (f'__fs{a.fewshot}' if a.fewshot else '') + (f'__sc{a.samples}' if a.samples > 1 else '')
    outp = os.path.join(HERE, "out", f"{a.slug}__{a.variant}{suffix}.jsonl")
    done = set()
    if os.path.exists(outp):
        for line in open(outp):
            try: done.add(json.loads(line)["id"])
            except Exception: pass
    todo = [t for t in trajs if t["id"] not in done]
    print(f"{a.slug}: {len(trajs)} trajectories, {len(done)} done, {len(todo)} to run", flush=True)
    llm = LLM()
    tmpl = {"std": STD, "inventory": INV, "inventory_blind": INV_BLIND, "twostage": TWOSTAGE, "backward": BACKWARD}[a.variant]
    sysmsg = SYS_BLIND if a.variant == "inventory_blind" else SYS
    msgs, infos = [], []
    for t in todo:
        if a.anonymise:
            t = anonymise(t)
        if a.variant == "inventory_blind":
            t = dict(t); t["final_output"] = None  # the final answer is still inside the last step; only the header line is dropped
        body, info = render(t, a.budget)
        if a.gold:
            body = f"REFERENCE (the correct final answer the run should have produced): {str(t['ground_truth'])[:1500]}\n\n" + body
        if examples:
            ex = [e for e in examples if e[0] != t["id"]][:a.fewshot]
            body = "Here are labelled examples from the same benchmark, showing the convention the annotators use for the decisive step:\n\n" + "\n\n".join(e[1] for e in ex) + "\n\n=== NOW THE RUN TO ANALYSE ===\n\n" + body
        if a.variant == "twostage":
            user = tmpl.format(body=body, inventory=json.dumps(inventory[t["id"]].get("mistakes"), ensure_ascii=False)[:6000])
        elif a.variant == "backward":
            pr = inventory[t["id"]]
            user = tmpl.format(body=body, k=pr.get("faulty_step"), kagent=pr.get("faulty_agent"), kreason=str(pr.get("reason") or "")[:800])
        else:
            user = tmpl.format(body=body)
        msgs.append([{"role": "system", "content": sysmsg}, {"role": "user", "content": user}])
        infos.append(info)
    t0 = time.time()
    with open(outp, "a") as f:
        B = 24
        for i in range(0, len(msgs), B):
            if a.samples > 1:
                sample_outs = [llm.chat_many(msgs[i:i + B], workers=a.workers, max_tokens=a.max_tokens, thinking=a.thinking, temperature=a.temperature, tag=f"{a.variant}_sc{k}") for k in range(a.samples)]
                outs = [vote([so[j] for so in sample_outs]) for j in range(len(msgs[i:i + B]))]
            else:
                outs = llm.chat_many(msgs[i:i + B], workers=a.workers, max_tokens=a.max_tokens, thinking=a.thinking, temperature=a.temperature, tag=a.variant)
            for t, info, o in zip(todo[i:i + B], infos[i:i + B], outs):
                pred = o.get("pred") if "pred" in o else parse_json(o.get("text"))
                rec = {"id": t["id"], "subset": t["subset"], "n_steps": len(t["steps"]), "outcome": t.get("outcome"), "render": info,
                       "gold": {k: v for k, v in t["annotation"].items() if k != "extra"},
                       "pred": pred, "raw": (o.get("text") or "")[-1500:], "reasoning": (o.get("reasoning") or "")[:6000],
                       "usage": o.get("usage"), "error": o.get("error"), "cached": o.get("cached"), "samples": o.get("samples")}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            print(f"  {min(i + B, len(msgs))}/{len(msgs)} done, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
