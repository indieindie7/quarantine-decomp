"""Shared by parity.py (live DOS snap) and regress.py (stored cases): port render at a case's pose + pixel compare with a DOS grab.
Case = port/tests/cases/<name>/: dos.png (DOSBox grab), case.json {city, cam{x,y,z,head,deg}, dmg, odo, g2, icon}, ents.json (live entity list of that frame)."""
import os, subprocess, json
from PIL import Image, ImageChops
T = os.path.dirname(os.path.abspath(__file__)); PORT = os.path.normpath(os.path.join(T, '..', 'port')); CASES = os.path.join(PORT, 'tests', 'cases')
GODOT = r'C:\Games\Tools\godot\Godot_v4.7.2-stable_win64_console.exe'
def blips(case):
    """Radar blips as DOS 0x35150 draws them: -> [[glyph, x, y]] (RADAR2 glyph 8/9/10 at dx + 0xc5, dy + 0x10; rel pos in view space / 64, y negated)."""
    import struct
    tab = struct.unpack('<1441h', open(os.path.join(PORT, 'data', 'sintab.bin'), 'rb').read()[:2882])
    def dsin(h):
        h %= 5760; q, r = divmod(h, 1440)
        return [tab[r], tab[1440 - r], -tab[r], -tab[1440 - r]][q]
    t64 = lambda v: int(v / 64)  # C division toward zero
    c = case['cam']; f0, f1 = -dsin(c['head']), dsin(c['head'] + 1440); out = []
    for x, y, ty, sub, st in case.get('radar', []):
        if st in (0, 3) or not (ty == 3 or (ty == 4 and st == 2)): continue
        rx, ry = x - c['x'], y - c['y']; dx = t64(-((f1 * rx + f0 * ry) >> 11)); dy = t64(-((-f0 * rx + f1 * ry) >> 11))  # dx: 0x370f8 (decomp_q.c 26580-26582) negates AFTER the >> 11
        if -12 < dx < 12 and -11 < dy < 11: out.append([10 if ty == 4 else (8 + (sub != 11)), dx + 0xc5, dy + 0x10])
    return out
def port_shot(case, out, ents='res://data/ents_live.json', extra=''):
    c = case['cam']
    args = ['--path', '.', '--', f"--city={case.get('city', 'KCITY')}", '--bg', '--res=640x400', '--fov=64', '--nofps', f"--pos={c['x'] / 16.0},{-c['z'] / 16.0},{c['y'] / 16.0}", f"--yaw={c['deg'] + 180.0}", f'--shot={out}', '--frames=12', f"--dmg={case['dmg']}", f"--odo={case['odo']}", f"--g2={case['g2']}", f"--icon={case['icon']}", f'--ents={ents}'] + (["--anim=" + ','.join(str(v) for v in case['anim'])] if case.get('anim') else []) + (["--blips=" + ','.join('%d:%d:%d' % tuple(b) for b in blips(case))] if blips(case) else []) + extra.split()
    si = subprocess.STARTUPINFO(); si.dwFlags = 1; si.wShowWindow = 7
    r = subprocess.run([GODOT, *args], cwd=PORT, startupinfo=si, creationflags=0x08000000, capture_output=True, text=True, errors='replace')  # CREATE_NO_WINDOW; project.godot starts minimized + no_focus
    return [l for l in (r.stdout + r.stderr).splitlines() if 'ERROR' in l or 'SHADER' in l]
q5 = lambda v: ((v >> 3) << 3) | (v >> 5); q6 = lambda v: ((v >> 2) << 2) | (v >> 6)
def load_pair(port_png, dos_png):
    """Both at 640x400; port quantised to RGB565 like the DOSBox grab; PAUSED text box (320 coords x 96-225, rows 88-103) blacked in both."""
    p = Image.open(port_png).convert('RGB').resize((640, 400), 0); d = Image.open(dos_png).convert('RGB').resize((640, 400), 0)
    r, g, b = p.split(); p = Image.merge('RGB', (r.point(q5), g.point(q6), b.point(q5)))
    for im in (p, d): im.paste((0, 0, 0), (192, 176, 452, 208))
    return p, d
STALE = [(38, 149), (39, 149), (280, 149), (281, 149)]
def px_differ(p, d, box=(0, 0, 320, 200)):
    """Count of 320x200 pixels that differ at all inside box (320 coords)."""
    df = ImageChops.difference(p, d).resize((320, 200), 0).convert('L').point(lambda v: 255 if v else 0); ps = p.resize((320, 200), 0).convert('RGB')
    for xy in STALE:  # DOS leaves these 4 px of row 149 undrawn when the view ends above it (cam z -20): they hold an older frame (NOTES 'ROW 149 STALE PX'); skipped only where the port is black
        if ps.getpixel(xy) == (0, 0, 0): df.putpixel(xy, 0)
    return df.crop(box).histogram()[255]
