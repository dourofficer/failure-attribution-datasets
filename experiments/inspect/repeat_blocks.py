"""Repetition structure of trajectories under the unified schema.
For each trajectory: group consecutive agent steps into blocks of near-duplicate actions (same agent and either the same
tool call / same first 80 normalised characters or Jaccard >= 0.8 on word shingles); report where the labelled step sits
relative to blocks (inside a block of size>=3? first/last of its block? right before a block boundary?) and how much of
the trajectory after the label is repetition.  Usage: python3 -I inspect/repeat_blocks.py <slug> [limit]"""
import importlib, os, re, sys, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'loaders'))


def sig(content):
    c = re.sub(r'\s+', ' ', content.lower()).strip()
    c = re.sub(r'\d+', '0', c)  # numbers vary across repeats (viewport %, timestamps)
    return c[:80], set(re.findall(r'\w+', c)[:400])


def similar(a, b):
    if a[0] == b[0]:
        return True
    if not a[1] or not b[1]:
        return False
    return len(a[1] & b[1]) / len(a[1] | b[1]) >= 0.8


def blocks(steps):
    """return list of (start_idx, end_idx, size) over AGENT steps that are consecutive near-duplicates (ignoring interleaved
    tool/user/system steps and ignoring orchestrator-style steps of OTHER agents between them)."""
    agent_steps = [s for s in steps if s['role'] == 'agent']
    out = []; i = 0
    while i < len(agent_steps):
        j = i; sg = sig(agent_steps[i]['content'])
        while j + 1 < len(agent_steps) and agent_steps[j + 1]['agent'] == agent_steps[i]['agent'] and similar(sg, sig(agent_steps[j + 1]['content'])):
            j += 1
        out.append((agent_steps[i]['idx'], agent_steps[j]['idx'], j - i + 1)); i = j + 1
    return out


BOOK = re.compile(r'^\s*(updated ledger|next speaker|stalled\.*\s*replanning|initial plan)', re.I)


def bookkeeping(c):
    return len(c.strip()) < 60 or bool(BOOK.match(c))


GAP = 5  # max agent-steps between two repeats (Magentic-One relay: A, Orch thought, Orch instruction, Orch next-speaker, A)


def blocks_loose(steps):
    """same but allowing one other-agent step in between (orchestrator relay pattern: A, Orch, A, Orch, ...)."""
    agent_steps = [s for s in steps if s['role'] == 'agent' and not bookkeeping(s['content'])]
    out = []; i = 0
    while i < len(agent_steps):
        j = i; sg = sig(agent_steps[i]['content']); ag = agent_steps[i]['agent']
        while True:
            nxt = None
            for k in range(j + 1, min(len(agent_steps), j + 1 + GAP)):
                if k < len(agent_steps) and agent_steps[k]['agent'] == ag and similar(sg, sig(agent_steps[k]['content'])):
                    nxt = k; break
            if nxt is None: break
            j = nxt
        out.append((agent_steps[i]['idx'], agent_steps[j]['idx'], j - i + 1)); i = j + 1
    return out


def analyse(slug, limit=None):
    mod = importlib.import_module(slug)
    C = collections.Counter(); rows = []
    for t in mod.load(limit=limit):
        fs = t['annotation']['faulty_step']
        if fs is None or t.get('outcome') == 1: continue
        bl = blocks_loose(t['steps'])
        n_agent = sum(1 for s in t['steps'] if s['role'] == 'agent')
        rep_steps = sum(b[2] - 1 for b in bl)  # steps that repeat a previous one in their block
        C['n'] += 1; C['agent_steps'] += n_agent; C['repeat_steps'] += rep_steps
        big = [b for b in bl if b[2] >= 3]
        C['traj_with_block>=3'] += bool(big)
        # where is the label
        inb = [b for b in bl if b[0] <= fs <= b[1]]
        if inb:
            b = inb[0]
            if b[2] >= 3:
                C['label_inside_block>=3'] += 1
                C['label_first_of_block'] += fs == b[0]; C['label_last_of_block'] += fs == b[1]
        # label immediately before a big block starts (within 2 steps)
        if any(0 < b[0] - fs <= 2 and b[2] >= 3 for b in bl): C['label_just_before_block>=3'] += 1
        # repetition after the label
        after = [s for s in t['steps'] if s['idx'] > fs and s['role'] == 'agent']
        rep_after = sum(min(b[2] - 1, max(0, b[1] - max(fs, b[0] - 1))) for b in bl if b[1] > fs)
        C['agent_steps_after_label'] += len(after); C['repeat_steps_after_label'] += rep_after
        rows.append(dict(id=t['id'], n=len(t['steps']), label=fs, blocks=[b for b in bl if b[2] >= 3][:10]))
    n = max(C['n'], 1)
    print(f"{slug}: {C['n']} labelled failed trajectories")
    print(f"  repeat steps / agent steps overall: {C['repeat_steps']}/{C['agent_steps']} = {100*C['repeat_steps']/max(1,C['agent_steps']):.1f}%")
    print(f"  after the label: {C['repeat_steps_after_label']}/{C['agent_steps_after_label']} = {100*C['repeat_steps_after_label']/max(1,C['agent_steps_after_label']):.1f}%")
    print(f"  trajectories with a repeated block of size>=3: {C['traj_with_block>=3']} ({100*C['traj_with_block>=3']/n:.0f}%)")
    print(f"  label inside such a block: {C['label_inside_block>=3']} (first of block {C['label_first_of_block']}, last {C['label_last_of_block']}); label within 2 steps before a block: {C['label_just_before_block>=3']}")
    return rows


if __name__ == '__main__':
    rows = analyse(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    json.dump(rows, open(os.path.join(HERE, 'out', f'repeat_blocks_{sys.argv[1]}.json'), 'w'))
