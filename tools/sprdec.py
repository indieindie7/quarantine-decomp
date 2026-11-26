"""sprdec.py <in.SPR|dir> <outdir> [palette.VGA|.IMG] : Quarantine II DOS .SPR = u8 n, n x (u8 w, u8 h), then n raw 8bpp frames
(w*h bytes each, row-major, index 0 = transparent). Layout fits all 602 RWCD .SPR files exactly (11-25). Writes one PNG sheet per file
(frames left to right, RGBA). Palette = 256x3 at offset 13 of an IMAGEX file (6-bit DAC values are scaled x4 if all < 64);
default = first .VGA in the same folder, else grey."""
import sys, os, glob, zlib, struct
def frames(d):
    n = d[0]; t = [(d[1 + 2 * i], d[2 + 2 * i]) for i in range(n)]; o = 1 + 2 * n; out = []
    for w, h in t: out.append((w, h, d[o:o + w * h])); o += w * h
    assert o == len(d), 'size mismatch'
    return out
def palette(p):
    if not p: return [(i, i, i) for i in range(256)]
    raw = open(p, 'rb').read()[13:781]; k = 4 if max(raw) < 64 else 1
    return [(raw[3 * i] * k, raw[3 * i + 1] * k, raw[3 * i + 2] * k) for i in range(256)]
def png(path, w, h, rows):
    def chunk(t, b): return struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t + b) & 0xffffffff)
    raw = b''.join(b'\0' + r for r in rows)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>2I5B', w, h, 8, 6, 0, 0, 0)) +
                           chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))
def sheet(fr, pal):
    W = max(1, sum(w for w, h, _ in fr) + len(fr) - 1); H = max([1] + [h for _, h, _ in fr])
    px = [bytearray(4 * W) for _ in range(H)]; x0 = 0
    for w, h, b in fr:
        for y in range(h):
            for x in range(w):
                c = b[y * w + x]
                if c: px[y][4 * (x0 + x):4 * (x0 + x) + 4] = bytes(pal[c]) + b'\xff'
        x0 += w + 1
    return W, H, [bytes(r) for r in px]
def one(src, outdir, pal_path):
    pal_path = pal_path or next(iter(sorted(glob.glob(os.path.join(os.path.dirname(src), '*.VGA')))), None)
    fr = frames(open(src, 'rb').read()); W, H, rows = sheet(fr, palette(pal_path))
    png(os.path.join(outdir, os.path.basename(src) + '.png'), W, H, rows); return len(fr)
def main(a):
    src, outdir = a[0], a[1]; pal = a[2] if len(a) > 2 else None; os.makedirs(outdir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(src, '**', '*.SPR'), recursive=True)) if os.path.isdir(src) else [src]
    n = sum(one(f, outdir, pal) for f in files); print('files', len(files), 'frames', n)
if __name__ == '__main__': main(sys.argv[1:])
