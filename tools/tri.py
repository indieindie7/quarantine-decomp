"""tri.py <out.png> <case> [case ...]: per case one row = port | DOS | diff (white) of the 3D view rows 30-152, 2x. From port/shots/reg_<case>.png (regress.py)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paritylib as L
from PIL import Image, ImageChops
N = sys.argv[2:]; B = (0, 60, 640, 304); out = Image.new('RGB', (1920, 244 * len(N)))
for i, n in enumerate(N):
    p, d = L.load_pair(os.path.join(L.PORT, 'shots', 'reg_%s.png' % n), os.path.join(L.CASES, n, 'dos.png'))
    df = ImageChops.difference(p, d).convert('L').point(lambda v: 255 if v else 0).convert('RGB')
    for k, im in enumerate((p, d, df)): out.paste(im.crop(B), (640 * k, 244 * i))
out.save(sys.argv[1]); print(sys.argv[1], out.size)
