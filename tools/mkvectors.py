"""mkvectors.py: build port/tests/vectors/*.json = expected values from the DOS side, checked by the port's own code (`godot --path port -- --test`).
  dsin.json       [[heading, sin*2048], ...] from the DOS quarter table 0x77964 (port/data/sintab.bin), all 4 quadrants + wrap
  draworder.json  per stored case pose: painter order as [cell row (dy + 3) * 7 + dx + 3, item column] from tools/bsporder.py (replica of 0x4736c + 0x4668c + 0x464d0,
                  verified against the live DOS draw list with tools/drawlist.py, NOTES 'ORDER REPLICA VERIFIED'); column = quad idx | nq + wall idx | nq + nw + obj idx
Add a set here whenever a DOS routine gets a Python reference model (RETRO improvement 3)."""
import os, sys, json, struct
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import bsporder
PORT = os.path.normpath(os.path.join(T, '..', 'port')); V = os.path.join(PORT, 'tests', 'vectors'); os.makedirs(V, exist_ok=True)
tab = struct.unpack('<1441h', open(os.path.join(PORT, 'data', 'sintab.bin'), 'rb').read()[:2882])
def dsin(h):
    h %= 5760; q, r = divmod(h, 1440)
    return [tab[r], tab[1440 - r], -tab[r], -tab[1440 - r]][q]
json.dump([[h, dsin(h)] for h in list(range(0, 5760, 7)) + [1440, 2880, 4320, 5759, 5760, -1, -1440, 9000]], open(os.path.join(V, 'dsin.json'), 'w'))
d = json.load(open(os.path.join(PORT, 'data', 'KCITY.json'))); out = []; C = os.path.join(PORT, 'tests', 'cases')
for n in sorted(os.listdir(C)):
    f = os.path.join(C, n, 'case.json')
    if not os.path.exists(f): continue
    c = json.load(open(f))['cam']; seq = []
    for o, dx, dy, cx, cy, bi, kind, idx in bsporder.order(c['x'], c['y'], c['z']):
        b = d['blocks'][bi]; e = (dy + 3) * 7 + dx + 3
        seq.append([e, idx + (0 if kind == 'q' else len(b['q']) + (0 if kind == 'w' else len(b['w'])))])
    out.append({'name': n, 'cam': [c['x'], c['y'], c['z'], c['head']], 'seq': seq})
json.dump(out, open(os.path.join(V, 'draworder.json'), 'w'), separators=(',', ':'))
print('dsin', len(json.load(open(os.path.join(V, 'dsin.json')))), 'draworder poses', len(out), 'items', sum(len(o['seq']) for o in out))
