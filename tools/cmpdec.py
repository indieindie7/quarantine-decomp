"""cmpdec.py <in.CMP> <out.png> [sheet=<cols>] : Quarantine Saturn CMP = a VDP2 tile screen, not compressed (rewritten 11-23; the old fixed-width
reader only worked when blocks were unique and in order).
Layout (BE): u32 pixel_bytes, u32 map_bytes, u32 pal_bytes, then
  pixels  8bpp, 256 bytes per 16x16 block (four 8x8 cells, row-major; each cell 64 bytes row-major)
  map     u16 entries, pages of 32x32 blocks (0x800 bytes per page; 1, 2, 3 or 4 pages). entry & 0x3ff = first cell number
          (block = that / 2), 0x400 = flip horizontal, 0x800 = flip vertical (flip bits: only WHEEL.CMP uses them)
  palette pal_bytes / 4 entries of (00,B,G,R)
Output: each page cropped to its used blocks, pages joined left to right. Entry 0 = empty (block 0)."""
import sys, struct
from PIL import Image, ImageOps
def blocks_of(pix):
    out = []
    for k in range(len(pix) // 256):
        im = Image.new('P', (16, 16))
        for t in range(4):
            o = k * 256 + t * 64; im.paste(Image.frombytes('P', (8, 8), pix[o:o + 64]), ((t % 2) * 8, (t // 2) * 8))
        out.append(im)
    return out
def page(mp, blocks):
    """one 32x32 page -> image cropped to its used blocks (None when empty)"""
    out = Image.new('P', (512, 512)); used = []
    for j, v in enumerate(mp):
        k = (v & 0x3ff) // 2
        if v == 0 or k >= len(blocks): continue
        im = blocks[k]
        if v & 0x400: im = ImageOps.mirror(im)
        if v & 0x800: im = ImageOps.flip(im)
        x, y = (j % 32) * 16, (j // 32) * 16; out.paste(im, (x, y)); used.append((x, y))
    if not used: return None
    return out.crop((min(x for x, _ in used), min(y for _, y in used), max(x for x, _ in used) + 16, max(y for _, y in used) + 16))
def load(path):
    d = open(path, 'rb').read()
    n, a, b = struct.unpack('>3I', d[:12])
    mp = struct.unpack('>%dH' % (a // 2), d[12 + n:12 + n + a]); pal = d[12 + n + a:12 + n + a + b]
    rgb = b''.join(bytes((pal[i*4+3], pal[i*4+2], pal[i*4+1])) for i in range(b // 4))
    blocks = blocks_of(d[12:12 + n])
    pg = [q for q in (page(mp[i:i + 1024], blocks) for i in range(0, len(mp), 1024)) if q]
    out = Image.new('P', (sum(q.width for q in pg), max(q.height for q in pg))); x = 0
    for q in pg:
        out.paste(q, (x, 0)); x += q.width
    out.putpalette(rgb); return out
def sheet(path, cols):
    """blocks in file order, cols per row (WHEEL.CMP: sheet=10 -> wheel frames of 10x4 blocks)"""
    d = open(path, 'rb').read(); n, a, b = struct.unpack('>3I', d[:12]); pal = d[12 + n + a:12 + n + a + b]
    bl = blocks_of(d[12:12 + n]); out = Image.new('P', (cols * 16, -(-len(bl) // cols) * 16))
    for k, im in enumerate(bl): out.paste(im, ((k % cols) * 16, (k // cols) * 16))
    out.putpalette(b''.join(bytes((pal[i*4+3], pal[i*4+2], pal[i*4+1])) for i in range(b // 4))); return out
if __name__ == '__main__':
    im = sheet(sys.argv[1], int(sys.argv[3][6:])) if len(sys.argv) > 3 else load(sys.argv[1]); im.convert('RGB').save(sys.argv[2]); print(sys.argv[1], im.size)
