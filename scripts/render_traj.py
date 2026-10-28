#!/usr/bin/env python3
"""Render notes/<slug>_example_norm.json into report/<group>/<slug>/traj.tex (see report_layout.py).

Usage: python3 -I render_traj.py <norm.json> <out.tex> [--maxchars N]
   e.g. python3 -I render_traj.py ../notes/symtrace_example_norm.json ../report/3_core/symtrace/traj.tex
Every step is emitted (all steps shown); long step bodies are shortened to
--maxchars characters (head + tail) so the report stays compact.
"""
import json, re, sys, argparse

UNI_MAP = {"…": "...", "—": "---", "–": "--", "“": "``", "”": "''", "‘": "`", "’": "'",
    "→": r"$\rightarrow$", "←": r"$\leftarrow$", "•": r"\textbullet{}", "·": r"\textperiodcentered{}",
    "≤": r"$\leq$", "≥": r"$\geq$", "≠": r"$\neq$", "×": r"$\times$", "✓": r"$\checkmark$",
    "✔": r"$\checkmark$", "✗": r"$\times$", "⟵": r"$\longleftarrow$", "°": r"$^\circ$", "★": r"$\star$",
    "☆": r"$\star$", "−": "-", "\u00a0": " ", "\u200b": "", "\ufeff": "", "\u2003": " ", "\u2002": " ",
    "\u2009": " ", "\u202f": " ", "\u2026": "...", "″": "''", "′": "'", "€": r"\euro{}", "£": r"\pounds{}",
    "©": r"\copyright{}", "®": r"\textregistered{}", "™": r"\texttrademark{}", "±": r"$\pm$", "µ": r"$\mu$",
    "α": r"$\alpha$", "β": r"$\beta$", "γ": r"$\gamma$", "δ": r"$\delta$", "π": r"$\pi$", "σ": r"$\sigma$",
    "λ": r"$\lambda$", "θ": r"$\theta$", "∞": r"$\infty$", "√": r"$\surd$", "∑": r"$\sum$", "∈": r"$\in$",
    "≈": r"$\approx$", "⇒": r"$\Rightarrow$", "⇐": r"$\Leftarrow$", "↔": r"$\leftrightarrow$",
    "■": r"$\blacksquare$", "□": r"$\square$", "▪": r"\textbullet{}", "➤": r"$\triangleright$", "►": r"$\triangleright$",
    "⚠": r"\faExclamationTriangle{}", "❌": r"$\times$", "✅": r"$\checkmark$", "🤖": r"\faRobot{}", "👤": r"\faUser{}"}

def is_cjk(ch):
    o = ord(ch)
    return (0x3000 <= o <= 0x30FF) or (0x3400 <= o <= 0x4DBF) or (0x4E00 <= o <= 0x9FFF) or \
           (0xAC00 <= o <= 0xD7AF) or (0xF900 <= o <= 0xFAFF) or (0xFF00 <= o <= 0xFFEF)

CJK_RUN = re.compile("([\u3000-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af\uf900-\ufaff\uff00-\uffef]+)")

AGENT_COLORS = ["agA", "agB", "agC", "agD", "agE", "agF", "agG", "agH"]


def tex_escape(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    # normalise whitespace first
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s).strip("\n")
    repl = {
        "\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "$": r"\$", "&": r"\&",
        "#": r"\#", "_": r"\_", "%": r"\%", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    }
    out = []
    for ch in s:
        if ch in repl:
            out.append(repl[ch])
        elif ord(ch) < 32 and ch != "\n":
            continue
        elif is_cjk(ch):
            out.append(ch)  # wrapped in \cjk{} below
        elif ord(ch) >= 0x2000 and ch not in UNI_MAP:
            out.append("\\ensuremath{\\square}")  # emoji/symbols not in font
        else:
            out.append(ch)
    s = "".join(out)
    # unicode punctuation that the T1/LY1 fonts may lack
    for a, b in UNI_MAP.items():
        s = s.replace(a, b)
    if False:
     for a, b in {"…": "...", "—": "---", "–": "--", "“": "``", "”": "''", "‘": "`", "’": "'",
                 "→": r"$\rightarrow$", "←": r"$\leftarrow$", "•": r"\textbullet{}", "·": r"\textperiodcentered{}",
                 "≤": r"$\leq$", "≥": r"$\geq$", "≠": r"$\neq$", "×": r"$\times$", "✓": r"$\checkmark$",
                 "✔": r"$\checkmark$", "✗": r"$\times$", "⟵": r"$\longleftarrow$", "°": r"$^\circ$",
                 "\u00a0": " ", "\u200b": "", "\u2212": "-", "\ufeff": ""}.items():
        s = s.replace(a, b)
    # paragraph breaks -> small vertical gap; single newlines -> line break
    s = s.replace("\n\n", "\\par ")
    s = s.replace("\n", "\\newline ")
    s = re.sub(r"(\\par )(\\newline )+", r"\1", s)
    s = re.sub(r"^(\\newline )+", "", s)
    s = CJK_RUN.sub(r"\\cjk{\1}", s)
    # allow long tokens (urls, paths) to break
    s = re.sub(r"([/=,;:?])", r"\1\\allowbreak{}", s)
    return s


def shorten(s: str, maxchars: int) -> str:
    if len(s) <= maxchars:
        return s
    head = int(maxchars * 0.72)
    tail = maxchars - head
    return s[:head].rstrip() + "\n[…] (" + f"{len(s)-maxchars:,}" + " chars omitted) […]\n" + s[-tail:].lstrip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--maxchars", type=int, default=900)
    ap.add_argument("--maxtask", type=int, default=700)
    a = ap.parse_args()
    d = json.load(open(a.src, encoding="utf-8"))
    ann = d.get("annotation") or {}
    fs = ann.get("faulty_step")
    faulty = set()
    if isinstance(fs, list):
        faulty = {str(x) for x in fs}
    elif fs is not None:
        faulty = {str(fs)}
    agents = []
    for st in d.get("steps", []):
        ag = str(st.get("agent") or "?")
        if ag not in agents:
            agents.append(ag)
    color_of = {ag: AGENT_COLORS[i % len(AGENT_COLORS)] for i, ag in enumerate(agents)}

    L = []
    L.append("% auto-generated by scripts/render_traj.py -- do not edit\n")
    task = d.get("task") or ""
    L.append("\\trajtask{%s}{%s}\n" % (tex_escape(d.get("source_id") or ""), tex_escape(shorten(task, a.maxtask))))
    for st in d.get("steps", []):
        idx = st.get("idx"); ag = str(st.get("agent") or "?")
        body = shorten(str(st.get("content") or ""), a.maxchars)
        is_f = str(idx) in faulty
        env = "faultystep" if is_f else "trajstep"
        L.append("\\begin{%s}{%s}{%s}{%s}\n%s\n\\end{%s}\n" % (
            env, tex_escape(idx), tex_escape(ag), color_of[ag], tex_escape(body), env))
    gt = d.get("ground_truth"); fo = d.get("final_output")
    cat = ann.get("category")
    if isinstance(cat, (list, dict)):
        cat = json.dumps(cat, ensure_ascii=False)
    fa = ann.get("faulty_agent")
    fs_txt = ", ".join(sorted(faulty, key=lambda x: (len(x), x))) if faulty else "—"
    extra = ann.get("extra") or {}
    extra_txt = ""
    if extra:
        items = []
        for k, v in extra.items():
            if isinstance(v, (dict, list)):
                v = json.dumps(v, ensure_ascii=False)
            items.append("\\textbf{%s}: %s" % (tex_escape(k), tex_escape(shorten(str(v), 500))))
        extra_txt = "; ".join(items)
    L.append("\\trajannotation{%s}{%s}{%s}{%s}{%s}{%s}{%s}\n" % (
        tex_escape(fa) if fa else "—",
        tex_escape(fs_txt),
        tex_escape(shorten(str(cat), 400)) if cat else "—",
        tex_escape(shorten(str(ann.get("reason") or ""), 1500)),
        tex_escape(shorten(str(gt), 300)) if gt not in (None, "") else "—",
        tex_escape(shorten(str(fo), 260)) if fo not in (None, "") else "—",
        extra_txt))
    open(a.dst, "w", encoding="utf-8").write("".join(L))
    print(f"{a.dst}: {len(d.get('steps', []))} steps, agents={agents}, faulty={sorted(faulty)}")


if __name__ == "__main__":
    main()
