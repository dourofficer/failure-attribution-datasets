# Guide for writing one dataset section (`report/<group>/<slug>/<slug>.tex`)

Layout: `report/<group>/<slug>/` holds everything of one dataset — `<slug>.tex` (the section), `traj.tex` (generated), `figures/{cat,agent,bench,fw}.pdf` (generated), `refs.bib`. Groups: `3_core`, `4_injected`, `5_taxonomy`, `6_related` (the slug→group map is `scripts/report_layout.py`; `report/README.md` shows the tree).

Root: `/dataDisk/home/thanhdo/failure-attribution-datasets`. All paths below are relative to it.
Compile tooling: `export PATH=$HOME/.TinyTeX/bin/x86_64-linux:$PATH` then `pdflatex`.

## Inputs you have
- `notes/<slug>.md` — the analysis notes (identity, description, schema, statistics, example, caveats). This is your primary source. Use the numbers in it; do not invent numbers.
- `notes/<slug>_stats.json` — machine-readable stats (only if you need a number not in the md).
- `report/<group>/<slug>/figures/{cat,agent,bench,fw}.pdf` — small bar charts (category distribution, faulty-agent distribution, source benchmark, framework). Some may not exist — check with `ls report/<group>/<slug>/figures/`. Include the ones that are informative (1–2 per dataset, side-by-side with the stats table). Do NOT include one that duplicates a table you already print; prefer the figure over a long table.
- `report/<group>/<slug>/traj.tex` — the pre-rendered example trajectory (ALL steps + annotation box). Include it with `\input{<group>/<slug>/traj}` (paths are relative to `report/`, where pdflatex runs). Do not rewrite it. If it does not exist, say so in your reply.
- `report/preamble.tex` — macros. `report/3_core/who_and_when/who_and_when.tex` — THE TEMPLATE. Match its structure, tone, density and macro usage exactly.

## Required structure (copy from the template)
```
% ===================== <Name> =====================
\subsection{<Name>}\label{ds:<slug>}
<badges line>          % \naturalbadge or \injected (or \lbl{taxonomy}); \okbadge / \gatedbadge / \nobadge / \partialbadge; then 2–4 \lbl{...} chips: label granularity (agent + step / step only / failure modes / ...), single-/multi-agent, source benchmarks
\begin{identity} Paper & ... \\ Links & ... \\ License & ... \\ Status & ... \\ \end{identity}
\paragraph{Description} ...  (purpose; how built: frameworks, benchmarks, natural vs injected, annotation protocol & agreement; label types; itemize subsets if any)
\paragraph{Metrics and baselines} ... (small booktabs tabular of reported baseline numbers if the notes have them; otherwise 2–3 sentences)
\paragraph{Schema} ... (file layout + key fields with \code{})
\paragraph{Statistics} computed from the downloaded data.\par\nobreak\vspace{1pt}   % or "from the paper" if not downloaded — say which
\noindent\begin{minipage}[t]{0.56\linewidth}\vspace{0pt}\small  <booktabs table of the key stats>  \smallskip <one short paragraph of extra numbers> \end{minipage}\hfill
\begin{minipage}[t]{0.42\linewidth}\vspace{0pt}\includegraphics[width=\linewidth]{<group>/<slug>/figures/<cat|agent|bench|fw>.pdf}\end{minipage}
\paragraph{Example trajectory} <1–2 sentences: which record, how many steps/agents, what goes wrong in plain words>
\input{<group>/<slug>/traj}
\paragraph{Notes} (i) ... (ii) ... (iii) ...   % quirks, caveats, overlaps with other datasets, what is unique
```
Choose the two widths so the row fills the line: the table minipage is the table's natural width plus ~0.015 (never below 0.48), the figure minipage is 0.98 minus that. Figures are generated 3.4in wide (= 0.47\linewidth) so they print close to true size; `\fitbox{...}` around a tabular shrinks it only if it is wider than its minipage. If no figure exists, make the first minipage full width (`\linewidth`) and drop the second one. If the trajectory file has many steps (>30), add a sentence before `\input` warning the reader that the trajectory is long and (optionally) use `\input` anyway — all steps must be shown.

## Style rules
- Compact: aim for ≤ 1.3 pages of prose+tables per dataset (the trajectory adds whatever it needs). Short sentences, numbers inline.
- Use `\code{...}` for field names / repo ids (escape `_` as `\_` inside \code and elsewhere; `&` as `\&`; `%` as `\%`; `#` as `\#`).
- Cite the paper once with `\cite{<bibkey>}` in the identity box (keys below). Also write a corrected BibTeX entry (same key; real authors from the notes, real title, venue, year, arXiv id) to `report/<group>/<slug>/refs.bib` (every `*/refs*.bib` under `report/` is merged over `bib/refs.bib` by key; later paths in sorted order win).
- Links with `\href{url}{text}`. Use `\textperiodcentered` between links.
- No `\section` (only `\subsection`, `\paragraph`). No new packages. No `\newcommand`. One-column layout: no `multicols`.
- Availability badge must reflect reality: `\okbadge` (downloaded, public), `\gatedbadge` (needs approval), `\partialbadge` (only a subset is public / downloaded), `\nobadge` (no public release yet — then statistics come from the paper and the example may be reconstructed from the paper; say so explicitly).
- Be honest about what is paper-reported vs computed; write "(paper)" after paper-only numbers.

## Bib keys
who_and_when→zhang2025who, traceelephant→traceelephant2026, mp_bench→mpbench2026, who_and_when_pro→whowhenpro2026, longrca→longrca2026, agentrx→agentrx2026, tracertraj→agentracer2026, aegis→aegis2026, correct_error→correct2026, agenterrata→agenterrata2026, mast_data→cemri2025mast, trail→trail2025, agenterrorbench→agentdebug2026, searchauditbench→searchauditor2026, failure_as_process→failureprocess2026, trajerrbench→trajdebug2026, agenthallu→agenthallu2026, memtrace→memtrace2026, horizon→horizon2026, megarca_mix→megarca2026, symtrace→luan2026symtrace

## Compile check (mandatory for each section)
Create `report/test_<slug>.tex`:
```
\input{preamble}
\usepackage[numbers,sort&compress]{natbib}
\begin{document}
\section{Test}
\input{<group>/<slug>/<slug>}
\bibliographystyle{plainnat}\bibliography{bib/refs}
\end{document}
```
Run from `report/`: `pdflatex -interaction=nonstopmode test_<slug>.tex` (twice). Requirements: zero lines starting with `!` in the log; no `Overfull \hbox` worse than 15pt in YOUR section (the trajectory file may have a few — ignore those inside `traj/`). Then rasterise page 1–2 with
`python3 -c "import pymupdf; d=pymupdf.open('test_<slug>.pdf'); [d[i].get_pixmap(dpi=80).save(f'test_<slug>_p{i}.png') for i in range(min(2,len(d)))]"`
and LOOK at the PNGs (Read tool) to check that the two minipages sit side by side, nothing overflows the margin, tables fit. Fix and recompile until clean. Delete the test_*.aux/log/bbl/blg/pdf/png files when done (keep the .tex is fine).
