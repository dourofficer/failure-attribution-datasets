"""Position and role priors per dataset (what a label-free guesser gets). Usage: python3 -I inspect/priors.py slug [slug ...]"""
import importlib, os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'loaders')); sys.path.insert(0, HERE)
from repeat_blocks import bookkeeping


def run(slug):
    mod = importlib.import_module(slug)
    n = 0; first = 0; last_agent = 0; last_any = 0; rel = []; agents = collections.Counter(); gold_agents = collections.Counter(); n_agents = []
    within3_first = 0; within3_last = 0; step_counts = []
    for t in mod.load():
        fs = t['annotation']['faulty_step']
        if fs is None or t.get('outcome') == 1: continue
        n += 1; steps = t['steps']; T = len(steps); step_counts.append(T)
        dec = [s['idx'] for s in steps if s['role'] == 'agent' and not bookkeeping(s['content'])]
        first += fs == (dec[0] if dec else 0); last_agent += bool(dec) and fs == dec[-1]; last_any += fs == T - 1
        within3_first += bool(dec) and fs in dec[:3]; within3_last += bool(dec) and fs in dec[-3:]
        rel.append(fs / max(T - 1, 1))
        ag = t['annotation']['faulty_agent']
        if ag: gold_agents[ag.strip().lower()] += 1
        n_agents.append(len({s['agent'].strip().lower() for s in steps if s['role'] == 'agent'}))
    if not n: print(slug, 'no labelled failures'); return
    rel.sort(); sc = sorted(step_counts)
    top = gold_agents.most_common(1)[0] if gold_agents else ('-', 0)
    print(f"{slug:<18} n={n:<5} steps med {sc[len(sc)//2]:<4} rel.pos med {rel[len(rel)//2]:.2f} | first-decision {100*first/n:4.1f}%  first-3 {100*within3_first/n:4.1f}%  last-decision {100*last_agent/n:4.1f}%  last-3 {100*within3_last/n:4.1f}%  last-step {100*last_any/n:4.1f}% | agents/traj med {sorted(n_agents)[len(n_agents)//2]}  majority-agent prior {top[0][:22]} {100*top[1]/n:4.1f}%")


if __name__ == '__main__':
    for s in sys.argv[1:]: run(s)
