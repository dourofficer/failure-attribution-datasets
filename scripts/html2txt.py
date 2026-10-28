#!/usr/bin/env python3
"""Convert an arXiv HTML page to plain text (stdlib only; table cells separated by ' | ')."""
import sys
from html.parser import HTMLParser

BLOCK = {'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'figcaption', 'section', 'br', 'tr', 'table', 'ul', 'ol'}
SKIP = {'script', 'style', 'nav', 'header', 'footer', 'annotation', 'annotation-xml'}


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip = 0
        self.in_math = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in SKIP:
            self.skip += 1
        if tag == 'math':
            self.in_math += 1
            alt = a.get('alttext')
            if alt:
                self.out.append(' ' + alt + ' ')
        if tag in BLOCK:
            self.out.append('\n')
        if tag in ('td', 'th'):
            self.out.append(' | ')

    def handle_endtag(self, tag):
        if tag in SKIP and self.skip:
            self.skip -= 1
        if tag == 'math' and self.in_math:
            self.in_math -= 1
        if tag in BLOCK:
            self.out.append('\n')

    def handle_data(self, data):
        if self.skip or self.in_math:
            return
        self.out.append(data)


def main(src, dst):
    p = P()
    p.feed(open(src, encoding='utf-8', errors='replace').read())
    txt = ''.join(p.out)
    lines = [' '.join(l.split()) for l in txt.splitlines()]
    out, blank = [], 0
    for l in lines:
        if not l:
            blank += 1
            if blank > 1:
                continue
        else:
            blank = 0
        out.append(l)
    open(dst, 'w').write('\n'.join(out))
    print(dst, len(out), 'lines')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
