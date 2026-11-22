"""cmpdec.py <in.CMP> <out.png> [width=320] : Quarantine Saturn CMP (not compressed).
Layout (BE): u32 pixel_bytes, u32 0x800, u32 0x400, then pixel_bytes of 8bpp indices stored as 16x16 blocks (row-major blocks,
each block = four 8x8 tiles in row-major order, each tile 64 bytes row-major), then 0x800-byte table (unread), then 0x400 palette
= 256 x (00,B,G,R). Width is not in the header: default 320 (blocks per row = width/16)."""
import sys, struct
from PIL import Image
def load(path, width=320):
    d = open(path, 'rb').read()
    n, a, b = struct.unpack('>3I', d[:12])
    pix = d[12:12 + n]; pal = d[-b:]
    rgb = b''.join(bytes((pal[i*4+3], pal[i*4+2], pal[i*4+1])) for i in range(b // 4))
    bw = width // 16; nb = n // 256; bh = -(-nb // bw)
    im = Image.new('P', (width, bh * 16))
    for k in range(nb):
        bx, by = (k % bw) * 16, (k // bw) * 16
        for t in range(4):
            tx, ty = bx + (t % 2) * 8, by + (t // 2) * 8
            o = k * 256 + t * 64
            im.paste(Image.frombytes('P', (8, 8), pix[o:o + 64]), (tx, ty))
    im.putpalette(rgb); return im
if __name__ == '__main__':
    w = int(sys.argv[3]) if len(sys.argv) > 3 else 320
    im = load(sys.argv[1], w); im.convert('RGB').save(sys.argv[2]); print(sys.argv[1], im.size)
