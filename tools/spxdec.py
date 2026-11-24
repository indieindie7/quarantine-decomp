"""spxdec.py <in.SPX | dir> <out.png | outdir> [pal.IMG] : Hard Rock Cab (PSX Quarantine) sprite bank -> sheet PNG (11-23).
Layout (LE): u16 n, u16 size (= file length - 4), n x (u8 w, u8 h, u16 offset from file start), then per sprite raw 8bpp
w*h bytes row-major, each sprite padded to a multiple of 4 bytes (checked on all 374 files: 292 need no pad, 82 padded).
Palette: not in the file; default = DOS FLOOR.IMG bytes 13..781 (same indices as the DOS .SPR twins)."""
import sys, os, glob, struct
from PIL import Image
def sprites(d):
    n, sz = struct.unpack('<HH', d[:4])
    if sz != len(d) - 4: raise ValueError('size field %d != %d' % (sz, len(d) - 4))
    out = []
    for i in range(n):
        w, h, o = struct.unpack('<BBH', d[4 + 4 * i:8 + 4 * i])
        out.append(Image.frombytes('P', (w, h), d[o:o + w * h]))
    return out
def sheet(ims, pal):
    out = Image.new('P', (sum(i.width + 1 for i in ims), max(i.height for i in ims))); x = 0
    for i in ims:
        out.paste(i, (x, 0)); x += i.width + 1
    out.putpalette(pal); return out
def main(a):
    here = os.path.dirname(os.path.abspath(__file__))
    pal = open(a[2] if len(a) > 2 else os.path.join(here, '..', 'dos', 'Quarantine', 'FLOOR.IMG'), 'rb').read()[13:781]
    if not os.path.isdir(a[0]):
        sheet(sprites(open(a[0], 'rb').read()), pal).convert('RGB').save(a[1]); return
    n = bad = 0
    for f in glob.glob(os.path.join(a[0], '**', '*.SPX'), recursive=True):
        o = os.path.join(a[1], os.path.relpath(f, a[0]) + '.png'); os.makedirs(os.path.dirname(o), exist_ok=True)
        try: sheet(sprites(open(f, 'rb').read()), pal).convert('RGB').save(o); n += 1
        except Exception as e: bad += 1; print('BAD', f, e)
    print('converted', n, 'bad', bad)
if __name__ == '__main__': main(sys.argv[1:])
