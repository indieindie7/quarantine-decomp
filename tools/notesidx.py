"""notesidx.py: (1) move NOTES.md entries tagged '[SUPERSEDED' to NOTES-history.md, (2) rebuild NOTES-index.md = topic -> NOTES.md line numbers + first words.
Read NOTES-index.md first, then only the listed lines (sed -n 'Np' NOTES.md | cut -c1-600)."""
import os, re
Q = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); N = os.path.join(Q, 'NOTES.md')
L = open(N, encoding='utf-8').read().split('\n')
old = [l for l in L if '[SUPERSEDED' in l[:200] and l.startswith('- ')]
if old:
    open(os.path.join(Q, 'NOTES-history.md'), 'a', encoding='utf-8').write('\n'.join(old) + '\n')
    L = [l for l in L if l not in old]; open(N, 'w', encoding='utf-8', newline='\n').write('\n'.join(L))
T = [('rules + tools', r'Working rules|TOOL|tools/\w+\.py|PAUSE|GRAB|TELEPORT|Probe'),
     ('walls', r'WALL|wall range|atan|0x482fc|0x487b8|0x425ec'),
     ('floor', r'FLOOR|0x4a6e4|floorref'),
     ('sky', r'SKY'),
     ('map sprites + objects', r'SPRITE|OBJ|0x48c90'),
     ('draw order + cull', r'BSP|PAINTER|DRAW ORDER|ORDER REPLICA|OCCLUSION|CULL|0x4736c|0x4668c'),
     ('entities', r'ENTIT|ENT |0x33fb8|entdump'),
     ('dash + hud', r'DASH|RADAR|FARE|COMPASS|CABFONT|BFONT'),
     ('camera + view maths', r'VIEW MATHS|VIEW OFFSET|SIN TABLE|WTAB|cam |heading'),
     ('formats + loaders', r'\.MAP|\.BLK|\.SPR|\.IMG|\.CMP|BLOCK|loader|TEXTURE\d'),
     ('sweeps + results', r'SWEEP|VIEW 1 = 100|px differ'),
     ('areas + scenes', r'AREA|SCENES|\.tscn'),
     ('ross + user goals', r'USER|ROSS|VIDEO'),
     ('decomp + publish + other platforms', r'Saturn|3DO|autodecomp|Published|Studio|decomp code')]
out = ['# NOTES.md index (built by tools/notesidx.py; line numbers of NOTES.md, %d lines)' % len(L), '']
for name, pat in T:
    hits = [(i + 1, l) for i, l in enumerate(L) if l.startswith(('- ', '## ')) and re.search(pat, l[:160])]
    out.append('## %s (%d)' % (name, len(hits)))
    out += ['%d: %s' % (i, re.sub(r'\s+', ' ', l[2:90])) for i, l in hits]; out.append('')
open(os.path.join(Q, 'NOTES-index.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(out))
print('moved', len(old), 'index lines', len(out))
