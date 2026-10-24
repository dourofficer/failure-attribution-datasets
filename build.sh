#!/bin/bash
# Build the report: merge bib fixes, render trajectories, compile 3x with bibtex.
set -e
export PATH=$HOME/.TinyTeX/bin/x86_64-linux:$PATH
cd "$(dirname "$0")"
python3 ../scripts/merge_bib.py refs.bib bibfix refs_merged.bib
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null || { grep -A3 "^!" main.log | head -30; exit 1; }
bibtex main >/dev/null || true
pdflatex -interaction=nonstopmode main.tex >/dev/null
pdflatex -interaction=nonstopmode main.tex >/dev/null
grep -E "^!" main.log | head; grep -c "Overfull" main.log || true
grep -E "Output written" main.log
