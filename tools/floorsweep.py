"""Sweep floor UV debug flags of the port against one saved DOS shot. Usage: floorsweep.py <dos.png> x y z deg -> scores on ground rows (lower = closer)."""
import sys, os, subprocess, itertools
from PIL import Image, ImageChops, ImageStat
T = os.path.dirname(os.path.abspath(__file__)); PORT = os.path.join(T, '..', 'port')
GODOT = r'C:\Games\Tools\godot\Godot_v4.7.2-stable_win64_console.exe'
dos, x, y, z, deg = sys.argv[1], *map(float, sys.argv[2:6])
D = Image.open(dos).convert('RGB').resize((640, 400)); BOX = (0, 205, 640, 288); res = []
for rot, sh, sw, mi in itertools.product(range(4), (-1, 0, 1), (0, 1), (0, 1)):
    a = ['--path', '.', '--', '--city=KCITY', '--bg', '--res=640x400', '--fov=64', '--nofps', f'--pos={x/16},{-z/16},{y/16}', f'--yaw={deg+180}', '--shot=shots/sweep.png', '--frames=6', f'--frot={rot}', f'--fshift={sh}'] + (['--fswap'] if sw else []) + (['--fmir'] if mi else [])
    si = subprocess.STARTUPINFO(); si.dwFlags = 1; si.wShowWindow = 7
    subprocess.run([GODOT, *a], cwd=PORT, startupinfo=si, capture_output=True)
    P = Image.open(os.path.join(PORT, 'shots/sweep.png')).convert('RGB').resize((640, 400))
    res.append((round(sum(ImageStat.Stat(ImageChops.difference(P, D).crop(BOX)).mean) / 3, 2), rot, sh, sw, mi))
for r in sorted(res)[:12]: print(r)
print('worst', sorted(res)[-1])
