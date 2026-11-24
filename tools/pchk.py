"""pchk.py <ref par png> <x> <y> <head> [old=>new]: port-only render at the pose (optionally with temp text swaps in main.gd / port/shaders/*.gdshader, restored after), compare with the DOS third of ref inside box 163..319 x 40..127; prints mismatch px and per-column bad counts."""
import sys, os, subprocess, shutil
from PIL import Image
Q = r'C:\Games\Quarantine'; PORT = Q + r'\port'; G = r'C:\Games\Tools\godot\Godot_v4.7.2-stable_win64_console.exe'
ref, x, y, h = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]); m = PORT + r'\main.gd'; src = open(m, encoding='utf-8', newline='').read()
box = [int(v) for v in os.environ.get('BOX', '163,40,320,128').split(',')]
import re, glob
FILES = [m] + sorted(glob.glob(PORT + r'\shaders\*.gdshader')); keep = {}
def swap(a, b):
    """Swap text a -> b in main.gd or a shader file; whitespace in a matches any whitespace (shader statements sit on separate lines)."""
    pat = re.compile(r'\s*'.join(re.escape(t) for t in re.split(r'\s+', a.strip()))); n = 0
    for f in FILES:
        t = open(f, encoding='utf-8', newline='').read()
        if pat.search(t): keep.setdefault(f, t); open(f, 'w', encoding='utf-8', newline='').write(pat.sub(lambda _: b, t)); n += 1
    assert n, 'pattern missing ' + a
try:
    for sw in sys.argv[5:]: swap(*sw.split('=>'))
    si = subprocess.STARTUPINFO(); si.dwFlags = 1; si.wShowWindow = 7
    subprocess.run([G, '--path', '.', '--', '--city=KCITY', '--bg', '--res=640x400', '--fov=64', '--nofps', f'--pos={x / 16.0},0,{y / 16.0}', f'--yaw={h / 16.0 + 180.0}', '--shot=shots/pchk.png', '--frames=12'], cwd=PORT, startupinfo=si, capture_output=True)
finally:
    for f, t in keep.items(): open(f, 'w', encoding='utf-8', newline='').write(t)
p = Image.open(PORT + r'\shots\pchk.png').convert('RGB').resize((640, 400), 0); r = Image.open(ref).convert('RGB'); w = r.width // 3; d = r.crop((w, 0, 2 * w, 400))
q5 = lambda v: ((v >> 3) << 3) | (v >> 5); q6 = lambda v: ((v >> 2) << 2) | (v >> 6)
pp = p.load(); dp = d.load(); n = 0; cols = {}
for X in range(box[0], box[2]):
    for Y in range(box[1], box[3]):
        a = pp[X * 2, Y * 2]; a = (q5(a[0]), q6(a[1]), q5(a[2]))
        if a != dp[X * 2, Y * 2]: n += 1; cols[X] = cols.get(X, 0) + 1
print('bad', n, 'cols', len(cols), ' '.join('%d:%d' % (k, v) for k, v in sorted(cols.items()) if v > 0))

if os.environ.get('DBG'):
    lin = lambda v: (v / 255.0) / 12.92 if v / 255.0 <= 0.04045 else ((v / 255.0 + 0.055) / 1.055) ** 2.4
    for Y in (64, 76, 100):
        print(Y, ' '.join('%d:%s' % (X, ','.join(str(round(lin(c) * 80) - 8) for c in pp[X * 2, Y * 2])) for X in range(116, 320, 12)))
if os.environ.get('OUT'):
    import json
    lin = lambda v: (v / 255.0) / 12.92 if v / 255.0 <= 0.04045 else ((v / 255.0 + 0.055) / 1.055) ** 2.4
    D = lambda c: [round(lin(q) * 80) - 8 for q in c]
    json.dump([[(lambda t: t[0] + t[1] * 64 + t[2] * 4096)(D(pp[X * 2, Y * 2])) for X in range(320)] for Y in range(37, 149)], open(os.environ['OUT'], 'w'))
