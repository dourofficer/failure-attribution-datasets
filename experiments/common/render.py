"""Render a unified trajectory (see loaders/SCHEMA.md) as text for an LLM prompt, with a character budget.

render(traj, budget_chars) keeps every step but trims long step contents (head+tail) until the whole rendering
fits the budget; it returns (text, info) where info records how many steps were trimmed. Step headers carry OUR idx
so that the model's answer maps back to annotation.faulty_step directly.
"""


def _trim(s, limit):
    s = s if isinstance(s, str) else str(s)
    if len(s) <= limit:
        return s, False
    head = int(limit * 0.7)
    tail = limit - head
    return s[:head] + f"\n[... {len(s) - limit} characters omitted ...]\n" + s[-tail:], True


def render(traj, budget_chars=400_000, min_per_step=600):
    steps = traj["steps"]
    n = len(steps)
    header = [f"TASK:\n{traj['task']}"]
    if traj.get("final_output"):
        header.append(f"\nFINAL OUTPUT OF THE SYSTEM:\n{str(traj['final_output'])[:4000]}")
    head_txt = "\n".join(header)
    avail = max(budget_chars - len(head_txt) - 200 * n, n * min_per_step)
    # start with the actual lengths; shrink the per-step cap until it fits
    lens = [len(s["content"]) for s in steps]
    cap = max(lens) if lens else 0
    total = sum(lens)
    if total > avail and n:
        lo, hi = min_per_step, cap
        while lo < hi:  # binary search the largest cap that fits
            mid = (lo + hi + 1) // 2
            if sum(min(l, mid) + (60 if l > mid else 0) for l in lens) <= avail:
                lo = mid
            else:
                hi = mid - 1
        cap = lo
    out = [head_txt, "\nTRAJECTORY (one entry per step; step numbers are what you must refer to):"]
    trimmed = 0
    for s in steps:
        c, t = _trim(s["content"], cap) if cap else (s["content"], False)
        trimmed += t
        role = s["role"]
        tag = f"[step {s['idx']}] {s['agent']}" + (f" ({role})" if role != "agent" else "")
        out.append(f"\n=== {tag} ===\n{c}")
    return "\n".join(out), {"n_steps": n, "cap": cap, "trimmed_steps": trimmed, "chars": sum(len(x) for x in out)}
