"""maskdec.py <MASKS dir|file> <outdir> : Quarantine II DOS MASKS files (11-25). Loader cfg_Read 0x33f80 (VGA, no extension) /
hiscore_Load 0x34dc0 (SVGA, name + .400 or .480 by screen height); both misnamed, both read the same layout:
4 x u16 header (a, b, c, width: 320 VGA / 640 SVGA), then 4 span lists of u16 ended by 0xFFFF. A list = (skip, len) pairs; the
blitter scr_CopyC 0x34152 walks a pointer: pos += prev_len + skip, copies len pixels at pos (row-major, header width wide).
VGA (width 320) = Mode X: list k = plane k, pos in an 80-byte plane row (x = 4*col + k). SVGA (640) = list k = 64 KiB
bank k (offset = k*65536 + pos). Writes one <name>.png (white = copied pixels); prints header and the covered row range."""
import sys, os, glob, struct, zlib
def parse(d):
    hdr = struct.unpack_from('<4H', d, 0); o = 8; lists = []
    for _ in range(4):
        v = []
        while True:
            x = struct.unpack_from('<H', d, o)[0]; o += 2
            if x == 0xFFFF: break
            v.append(x)
        lists.append(v)
    return hdr, lists, o
def spans(v, svga=False):
    pos, prev, out, i0 = 0, 0, [], 0
    if svga and v:  # scr_Present 0x33xxx SVGA path: v[0]==0 -> copy v[1]+1 at 0; else start at pixel 1, pairs from v[1]
        if v[0] == 0 and len(v) > 1: out.append((0, v[1] + 1)); prev = v[1] + 1; i0 = 2
        else: pos = 1; i0 = 1
    for i in range(i0, len(v) - 1, 2):
        pos += prev + v[i]; out.append((pos, v[i + 1])); prev = v[i + 1]
    return out
def png(path, w, h, px):
    def chunk(t, b): return struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t + b) & 0xffffffff)
    raw = b''.join(b'\0' + bytes(px[y * w:(y + 1) * w]) for y in range(h))
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>2I5B', w, h, 8, 0, 0, 0, 0)) +
                           chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))
def one(p, out):
    d = open(p, 'rb').read(); hdr, lists, end = parse(d); w = hdr[3] or 320
    h = 200 if w == 320 else 480; px = bytearray(w * h); ys = []
    for k, v in enumerate(lists):
        for a, n in spans(v, w != 320):
            for i in range(a, a + n):
                g = (i // 80) * 320 + 4 * (i % 80) + k if w == 320 else k * 65536 + i
                if g < len(px): px[g] = 255; ys.append(g // w)
    png(os.path.join(out, os.path.basename(p).replace('.', '_') + '.png'), w, h, px)
    return hdr, (min(ys), max(ys)) if ys else None, end == len(d)
def main(a):
    src, out = a; os.makedirs(out, exist_ok=True)
    fs = sorted(f for f in glob.glob(os.path.join(src, '*')) if os.path.isfile(f)) if os.path.isdir(src) else [src]
    ok = 0
    for f in fs:
        hdr, res, fit = one(f, out); ok += fit
        if len(fs) < 8 or not fit: print(os.path.basename(f), hdr, res, 'fit' if fit else 'TRAILING')
    print('files', len(fs), 'exact fit', ok)
if __name__ == '__main__': main(sys.argv[1:])
