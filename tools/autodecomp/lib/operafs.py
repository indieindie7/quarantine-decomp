"""operafs.py <img MODE1/2352> <outdir>: extract 3DO Opera filesystem (data at +16 of each 2352 sector)."""
import sys, os, struct
img, out = sys.argv[1:3]
f = open(img, 'rb'); n = os.path.getsize(img) // 2352
def sec(i): f.seek(i * 2352 + 16); return f.read(2048)
v = sec(0); assert v[1:6] == b'ZZZZZ'
bs, cnt = struct.unpack('>II', v[0x4c:0x54]); root = struct.unpack('>I', v[0x64:0x68])[0]; rootblks = struct.unpack('>I', v[0x58:0x5c])[0]
print('label', v[0x28:0x48].rstrip(b'\0'), 'bs', bs, 'blocks', cnt, 'root', root, 'blks', rootblks, 'secs', n)
assert bs == 2048
def readdir(start, nblk, out_dir):
    os.makedirs(out_dir, exist_ok=True); cnt = 0
    for k in range(nblk):
        b = sec(start + k)
        if len(b) < 20: break
        nxt, prv, fl, free, first = struct.unpack('>iiiii', b[:20]); off = first
        while off + 0x48 <= min(free, 2048):
            flags, ident, typ, ebs, blen, ebc, burst, gap = struct.unpack('>8I', b[off:off + 32])
            name = b[off + 32:off + 64].split(bytes([0]))[0].decode('latin1'); last = struct.unpack('>I', b[off + 64:off + 68])[0]
            st = struct.unpack('>I', b[off + 68:off + 72])[0]
            t = flags & 0xff
            if t == 7: cnt += readdir(st, ebc, os.path.join(out_dir, name))
            elif t in (2, 0x40, 0):
                with open(os.path.join(out_dir, name), 'wb') as o:
                    left = blen; s2 = st
                    while left > 0: o.write(sec(s2)[:min(left, 2048)]); left -= 2048; s2 += 1
                cnt += 1
            if flags & 0x80000000: break
            off += 0x48 + 4 * last
    return cnt
print('files', readdir(root, rootblks, out))
