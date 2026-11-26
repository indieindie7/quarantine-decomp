"""q2misdec.py <dir> <outdir> : Quarantine II DOS text data. The files the game reads (MISSIONS/MISnnn.DAT/.FRE/.GER,
DATA/LEVEL.*, PHYSICAL.DAT, GAME.DAT, COLLDAT.DAT, TRIGDAT.DAT, CARDATA.ENC, ...) are plain text XOR 0x55; the .BAK/.OLD
copies and most area files are plain text. A file counts as XORed when the XORed bytes hold more CR LF pairs than the raw
bytes. Writes <name>.txt for every text file (raw or decoded), skips binary ones; prints which were XORed (11-25)."""
import sys, os, glob
def text(b): return len(b) > 0 and sum(32 <= c < 127 or c in (9, 10, 13, 26) for c in b) / len(b) > 0.97
def main(a):
    src, out = a; os.makedirs(out, exist_ok=True); n = 0; xs = []
    for p in sorted(f for f in glob.glob(os.path.join(src, '*')) if os.path.isfile(f)):
        d = open(p, 'rb').read(); x = bytes(c ^ 0x55 for c in d)
        if x.count(b'\r\n') > d.count(b'\r\n') and text(x): d = x; xs.append(os.path.basename(p))
        elif not text(d): continue
        open(os.path.join(out, os.path.basename(p) + '.txt'), 'wb').write(d); n += 1
    print('text files', n, 'xored', len(xs)); print(' '.join(xs))
if __name__ == '__main__': main(sys.argv[1:])
