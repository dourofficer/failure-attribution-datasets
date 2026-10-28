"""Replace @@EXAMPLE@@ in notes/<slug>.md with the rendered example markdown. Usage: python3 -I assemble_notes.py <notes_dir> <rendered_dir> slug..."""
import sys, os
notes, rdir = sys.argv[1], sys.argv[2]
for slug in sys.argv[3:]:
    p = os.path.join(notes, f"{slug}.md")
    with open(p, encoding="utf-8") as fh: md = fh.read()
    with open(os.path.join(rdir, f"{slug}_example.md"), encoding="utf-8") as fh: ex = fh.read()
    assert "@@EXAMPLE@@" in md, slug
    md = md.replace("@@EXAMPLE@@", ex.strip())
    with open(p, "w", encoding="utf-8") as fh: fh.write(md)
    print(slug, len(md), "chars")
