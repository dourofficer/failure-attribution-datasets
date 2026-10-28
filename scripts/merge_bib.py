#!/usr/bin/env python3
"""Merge every */refs*.bib found under <fixdir> (recursively; the base and output files and build/ are skipped)
over the base bib by key -> output bib (the file main.tex cites). Later paths in sorted order win."""
import sys, re, glob, os
base, fixdir, out = sys.argv[1:4]
def entries(txt):
    out = {}
    for m in re.finditer(r"@\w+\{([^,]+),", txt):
        start = m.start(); depth = 0; i = m.end() - 1
        # find matching brace from the '{' after @type
        i = txt.index("{", start)
        j = i; depth = 0
        while j < len(txt):
            if txt[j] == "{": depth += 1
            elif txt[j] == "}":
                depth -= 1
                if depth == 0: break
            j += 1
        out[m.group(1).strip()] = txt[start:j+1]
    return out
ents = entries(open(base, encoding="utf-8").read())
skip = {os.path.abspath(base), os.path.abspath(out)}
for f in sorted(glob.glob(os.path.join(fixdir, "**", "*.bib"), recursive=True)):
    if os.path.abspath(f) in skip or os.sep + "build" + os.sep in os.path.abspath(f):
        continue
    for k, v in entries(open(f, encoding="utf-8").read()).items():
        ents[k] = v
open(out, "w", encoding="utf-8").write("\n\n".join(ents.values()) + "\n")
print(f"merged {len(ents)} entries -> {out}")
