"""Validator for the unified trajectory schema (see SCHEMA.md)."""
ROLES = {"agent", "tool", "user", "system", "env"}


def validate(t):
    errs = []
    for k in ("dataset", "id", "subset", "system", "task", "steps", "annotation", "meta"):
        if k not in t:
            errs.append(f"missing key {k}")
    if errs:
        return errs
    if t.get("outcome") not in (0, 1, None):
        errs.append("outcome must be 0/1/None")
    steps = t["steps"]
    for i, s in enumerate(steps):
        if s.get("idx") != i:
            errs.append(f"step {i} idx={s.get('idx')} not contiguous")
            break
        if s.get("role") not in ROLES:
            errs.append(f"step {i} bad role {s.get('role')}")
            break
        if not isinstance(s.get("content"), str):
            errs.append(f"step {i} content not str")
            break
        if not isinstance(s.get("agent"), str):
            errs.append(f"step {i} agent not str")
            break
    a = t["annotation"]
    for k in ("faulty_step", "faulty_steps", "faulty_agent", "category", "reason", "extra"):
        if k not in a:
            errs.append(f"annotation missing {k}")
    fs = a.get("faulty_step")
    if fs is not None and not (isinstance(fs, int) and 0 <= fs < len(steps)):
        errs.append(f"faulty_step {fs} out of range (n={len(steps)})")
    for x in a.get("faulty_steps") or []:
        if not (isinstance(x, int) and 0 <= x < len(steps)):
            errs.append(f"faulty_steps entry {x} out of range")
            break
    if fs is not None and fs not in (a.get("faulty_steps") or []):
        errs.append("faulty_step not in faulty_steps")
    return errs
