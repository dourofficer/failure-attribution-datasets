"""Render a record as a numbered trajectory for prompting, with truncation that respects a token budget."""
from common.llm import approx_tokens


def truncate(text, cap):
    if cap is None or len(text) <= cap:
        return text
    head = int(cap * 0.7)
    tail = cap - head
    return text[:head] + f'\n... [{len(text) - cap} chars truncated] ...\n' + text[-tail:]


def render_steps(rec, per_step_cap=6000, total_cap_tokens=120000, include_roles=True, mask_last=0):
    """Return (text, used_indices). Caps each step to per_step_cap chars, then shrinks caps until the
    whole trajectory fits total_cap_tokens."""
    steps = rec['steps']
    if mask_last:
        steps = steps[:max(0, len(steps) - mask_last)]
    cap = per_step_cap
    while True:
        lines = []
        for s in steps:
            tag = f"[step {s['idx']}] {s['agent']}" + (f" ({s['role']})" if include_roles and s['role'] != 'agent' else '')
            lines.append(tag + ':\n' + truncate(_s(s['content']), cap))
        text = '\n\n'.join(lines)
        if approx_tokens(text) <= total_cap_tokens or cap <= 300:
            return text, [s['idx'] for s in steps]
        cap = int(cap * 0.6)


def _s(v):
    if isinstance(v, (list, dict)):
        import json
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def render_task(rec, with_gt=True):
    out = 'TASK:\n' + _s(rec['task']).strip()
    if with_gt and rec.get('ground_truth'):
        out += '\n\nGROUND-TRUTH ANSWER (for reference):\n' + _s(rec['ground_truth']).strip()
    if rec.get('final_output'):
        out += '\n\nSYSTEM FINAL OUTPUT:\n' + truncate(_s(rec['final_output']).strip(), 2000)
    return out
