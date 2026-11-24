"""Parity check DOS Quarantine vs the Godot port, driven by inputs.
parity.py start                      start DOSBox, skip intro, new game (KCITY)
parity.py snap <name> [key ...]      send keys (dbox.py key syntax: up hold=1.5 wait=2 ...), then DOS shot + cam pose -> port shot at the same pose
                                     -> port/shots/par_<name>.png (port | DOS | abs diff) + score line (mean abs diff 0-255 in the 3D window)
parity.py stop
Pose maths: NOTES.md '11-22 VIEW MATHS' (port yaw = heading/16 + 180, pos = (x/16, -z/16, y/16), hFOV 64, 320x200)."""
import sys, os, subprocess, time, json
from PIL import Image, ImageChops, ImageStat
T = os.path.dirname(os.path.abspath(__file__)); PORT = os.path.join(T, '..', 'port'); PY = [sys.executable, '-I']
GODOT = r'C:\Games\Tools\godot\Godot_v4.7.2-stable_win64_console.exe'
WIN = (0, 110, 640, 288)  # live clip 0x7947e: top 37, bottom 149, x 0..320 (x2 on 640x400); rows 74-110 hidden by cockpit top, dash starts ~290
def dbox(*a): return subprocess.run(PY + [os.path.join(T, 'dbox.py'), *a], capture_output=True, text=True).stdout.strip()
def cam(): return json.loads(subprocess.run(PY + [os.path.join(T, 'dosmem.py'), 'cam'], capture_output=True, text=True).stdout)
def rd16(addr): return int.from_bytes(bytes.fromhex(subprocess.run(PY + [os.path.join(T, 'dosmem.py'), 'rd', '%x' % addr, '2'], capture_output=True, text=True).stdout.strip()), 'little')
sys.path.insert(0, T); import shutil, paritylib as L
def state(c, city='KCITY'): return {'city': city, 'cam': c, 'dmg': rd16(0x836d0), 'odo': rd16(0x81394), 'g2': rd16(0x82344), 'icon': rd16(0x82348), 'anim': list(rdb(0x893b2, 30)), 'radar': radar()}  # anim states 0x893b2 (frame per animated texture, 255 = unused)
def rdb(addr, n): return bytes.fromhex(subprocess.run(PY + [os.path.join(T, 'dosmem.py'), 'rd', '%x' % addr, str(n)], capture_output=True, text=True).stdout.strip())
def radar():
    """Raw radar blip sources (draw 0x35150): list 0x82ea8 (20 shorts) -> recs 0x7c B at 0x7f9d8: x, y (+0, +4), type (+0x1c), sub (+0x20), state (+0x40)."""
    import struct; out = []
    for i in struct.unpack('<20h', rdb(0x82ea8, 40)):
        if not 0 <= i < 400: continue
        r = rdb(0x7f9d8 + i * 0x7c, 0x44); x, y = struct.unpack_from('<ii', r, 0); ty, = struct.unpack_from('<h', r, 0x1c); sub, = struct.unpack_from('<h', r, 0x20); st, = struct.unpack_from('<h', r, 0x40)
        out.append([x, y, ty, sub, st])
    return out
a = sys.argv[1:]
if a[0] == 'start':
    print(dbox('start')); time.sleep(20); dbox('key', 'esc', 'wait=3', 'esc', 'wait=3'); dbox('key', 'enter', 'wait=6'); print(cam())
elif a[0] == 'stop': dbox('stop')
elif a[0] == 'snap':
    name = a[1]; keys = a[2:]; want = None
    if '--pose' in keys:  # --pose x y head: teleport first, refuse when the car did not land there
        k = keys.index('--pose'); want = [int(v) for v in keys[k + 1:k + 4]]; keys = keys[:k] + keys[k + 4:]
    # PREFLIGHT (RETRO hitch 2: snaps taken at the title screen / wrong pose / with stray flags counted as results)
    try: c0 = cam()
    except Exception as e: sys.exit('PREFLIGHT: DOSBox / game memory not readable (%s). Run: parity.py start' % e)
    if not (0 < c0['x'] < 1 << 20 and 0 < c0['y'] < 1 << 20): sys.exit('PREFLIGHT: camera %s is not in a city (title screen?). Run: parity.py stop; parity.py start' % c0)
    if want:
        for t in range(3):
            subprocess.run(PY + [os.path.join(T, 'dostp.py'), *map(str, want)], capture_output=True); time.sleep(1.5); c0 = cam()
            if [c0['x'], c0['y'], c0['head']] == want: break
            dbox('key', 'enter', 'wait=1.5')  # a waiting screen (after start) holds the camera copy still; enter clears it
        else: sys.exit('PREFLIGHT: teleport to %s landed at %s' % (want, c0))
    if keys: dbox('key', *keys)
    # fires/cars animate: pause the game (key p; any key resumes), dump the entity list while it stands still, grab at once (the grab key resumes the game)
    for t in range(4):  # p toggles pause; a paused grab carries the PAUSED text (masked below)
        dbox('key', 'p', 'wait=0.3')
        if subprocess.run(PY + [os.path.join(T, 'entsync.py'), 'paused'], capture_output=True, text=True).stdout.strip() == '1': break
    r = subprocess.run(PY + [os.path.join(T, 'entsync.py'), os.path.join(PORT, 'data', 'ents_live.json')], capture_output=True, text=True)
    if r.returncode: sys.exit('entsync: ' + r.stdout + r.stderr)
    dos = r.stdout.splitlines()[-1]; c1 = cam(); st = state(c1)  # state read before the game runs on
    dbox('key', 'p', 'wait=0.2')
    if want and [c1['x'], c1['y'], c1['head']] != want: sys.exit('PREFLIGHT: pose moved to %s during the grab (wanted %s)' % (c1, want))
    extra = os.environ.get('PORT_ARGS', '')
    out = f'shots/par_{name}_port.png'; err = L.port_shot(st, out, extra=extra)
    p, d = L.load_pair(os.path.join(PORT, out), dos)
    df = ImageChops.difference(p, d); sc = sum(ImageStat.Stat(df.crop(WIN)).mean) / 3
    eq = lambda box: round(df.crop(box).convert('L').point(lambda v: 255 if v == 0 else 0).histogram()[255] / ((box[2] - box[0]) * (box[3] - box[1])), 3)
    EQ = {'top': eq((0, 0, 640, 74)), 'view': eq((0, 74, 640, 300)), 'dash': eq((0, 300, 640, 400))}
    sh = Image.new('RGB', (1920, 400)); sh.paste(p, (0, 0)); sh.paste(d, (640, 0)); sh.paste(df, (1280, 0)); sh.save(os.path.join(PORT, f'shots/par_{name}.png'))
    valid = EQ['dash'] >= 0.5 and not err  # cockpit dash far off = DOS is not showing the game view (title, menu, map)
    saved = False
    if valid and not extra:  # a clean snap becomes a regression case (tools/regress.py)
        cd = os.path.join(L.CASES, name); os.makedirs(cd, exist_ok=True); shutil.copy(dos, os.path.join(cd, 'dos.png')); shutil.copy(os.path.join(PORT, 'data', 'ents_live.json'), os.path.join(cd, 'ents.json')); json.dump(st, open(os.path.join(cd, 'case.json'), 'w')); saved = True
    print(json.dumps({'name': name, 'cam': c1, 'moved': c0 != c1, 'dos': dos, 'px': L.px_differ(p, d), 'score': round(sc, 2), 'equal': EQ, 'flags': extra, 'valid': valid, 'case_saved': saved, 'err': err[:2]}))
    if not valid: sys.exit('INVALID SNAP: dash equal %s, errors %s' % (EQ['dash'], err[:1]))
