#!/usr/bin/env python3
"""Fill <<STATS>> and <<EXAMPLE>> placeholders in notes/<slug>.md from scratchpad/<slug>_summary.md.
Run: python3 -I splice_notes.py <scratch_dir> slug [slug ...]"""
import sys, re
NOTES = '/dataDisk/home/thanhdo/failure-attribution-datasets/notes'
SCR = sys.argv[1]
START = {'longrca': '### Stats table', 'tracertraj': '### Split table', 'aegis': '### Overall table', 'agentrx': '### Stats table'}
for slug in sys.argv[2:]:
    summ = open(f'{SCR}/{slug}_summary.md', encoding='utf-8').read()
    i = summ.index(START[slug]); j = summ.index('### Example', i)
    stats = summ[i:j].strip(); example = summ[j:].strip()
    # demote headings so they nest under the note's "## " sections
    stats = stats.replace('\n### ', '\n#### ').replace('### ', '#### ', 1)
    example = re.sub(r'^### Example[^\n]*\n', '', example)
    note = open(f'{NOTES}/{slug}.md', encoding='utf-8').read()
    assert '<<STATS>>' in note and '<<EXAMPLE>>' in note, slug
    note = note.replace('<<STATS>>', stats).replace('<<EXAMPLE>>', example)
    open(f'{NOTES}/{slug}.md', 'w', encoding='utf-8').write(note)
    print(slug, 'ok', len(note), 'chars')
