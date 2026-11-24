"""entexport.py: entity sprite banks (dos/Quarantine/*.SPR: u8 n, n x (w,h), row-major 8bpp) -> port/data/ents_idx.png (L, 1024 wide shelf atlas) + ents_atlas.json {FILE: [[x,y,w,h],..]}."""
import os, json
from PIL import Image
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); G = os.path.join(D, 'dos', 'Quarantine'); O = os.path.join(D, 'port', 'data')
F = ['EXPLO', 'SHAD8DK', 'FIRE', 'ETRACERS', 'PUMTFR1', 'CYCTSPR', 'CYCTWIN', 'CAB1SPR', 'COMPSPR', 'PEDH1', 'PEDH2', 'PEDH3', 'PEDH4', 'CITYOBJ', 'CITYGUN', 'FALCSPR', 'BLAMMOG', 'EMINES', '4X4SPR1', 'BTANKER1', 'BTANKER2', 'CUBVSPR1', 'CUBVSPR2', 'JITNSPR', 'MONSTSPR', 'NOMTSPR', 'RMBKSPR', 'YZBKSPR', 'EMISSILE', 'EPLASMA', 'MFLASH', 'EFFECTS']  # new names: entdump.py finds them by header match
at = Image.new('L', (1024, 4096)); x = y = rowh = 0; J = {}
for f in F:
    p = os.path.join(G, f + '.SPR')
    if not os.path.exists(p): print('missing', f); continue
    b = open(p, 'rb').read(); n = b[0]; o = 1 + n * 2; J[f] = []
    for i in range(n):
        w, h = b[1 + i * 2], b[2 + i * 2]
        if x + w > 1024: x = 0; y += rowh; rowh = 0
        if w and h: at.paste(Image.frombytes('L', (w, h), b[o:o + w * h]), (x, y))
        J[f].append([x, y, w, h]); o += w * h; x += w; rowh = max(rowh, h)
    assert o == len(b), (f, o, len(b))
H = y + rowh; at.crop((0, 0, 1024, 1024 if H <= 1024 else (2048 if H <= 2048 else 4096))).save(os.path.join(O, 'ents_idx.png')); json.dump(J, open(os.path.join(O, 'ents_atlas.json'), 'w')); print('ok height', H, {k: len(v) for k, v in J.items()})
