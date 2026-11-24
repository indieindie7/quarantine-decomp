"""zoomcmp.py <case> x0 y0 x1 y1 [scale 6]: port (left) | DOS (right) crop of a case, nearest-neighbour zoom -> port/shots/zoom.png"""
import sys, os
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import paritylib as L
from PIL import Image
n = sys.argv[1]; box = tuple(int(v) for v in sys.argv[2:6]); s = int(sys.argv[6]) if len(sys.argv) > 6 else 6
p, d = L.load_pair(os.path.join(L.PORT, 'shots', 'par_%s_port.png' % n), os.path.join(L.CASES, n, 'dos.png'))
p = p.resize((320, 200), 0); d = d.resize((320, 200), 0); w = (box[2] - box[0]) * s; h = (box[3] - box[1]) * s
im = Image.new('RGB', (w * 2 + 10, h)); im.paste(p.crop(box).resize((w, h), 0), (0, 0)); im.paste(d.crop(box).resize((w, h), 0), (w + 10, 0)); im.save(os.path.join(L.PORT, 'shots', 'zoom.png'))
