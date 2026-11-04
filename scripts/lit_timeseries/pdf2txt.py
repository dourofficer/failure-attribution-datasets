import sys, fitz
d = fitz.open(sys.argv[1]); t = ''.join(p.get_text() for p in d)
open(sys.argv[2], 'w').write(t); print(len(t))
