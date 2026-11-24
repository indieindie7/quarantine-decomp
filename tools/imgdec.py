"""imgdec.py <in.IMG> <out.png> : Quarantine DOS IMG = 'IMAGEX' + u16 w,h,... + 256x3 palette (13..781; live DAC table 0x82b70[i] = file[13+3i], checked 11-22) + GIF image descriptor (2C x y w h flags) + LZW min code + sub-blocks.
Wrap as GIF87a and let PIL decode."""
import sys, struct, io
from PIL import Image
def load(path):
    d = open(path, 'rb').read()
    assert d[:6] == b'IMAGEX'
    w, h = struct.unpack('<2H', d[6:10])
    pal = d[13:781]
    i = d.index(b'\x2c', 784 - 8) if d[784:785] != b'\x2c' else 784
    body = d[i:]
    gif = b'GIF87a' + struct.pack('<2HBBB', w, h, 0xF7, 0, 0) + pal + body
    if not gif.endswith(b';'): gif += b';'
    im = Image.open(io.BytesIO(gif)); im.load()
    return im
if __name__ == '__main__':
    im = load(sys.argv[1]); im.convert('RGB').save(sys.argv[2]); print(sys.argv[1], im.size)
