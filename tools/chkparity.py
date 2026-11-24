"""chkparity.py: checksum parity test (shape of OpenCiv4 docs/PORTING.md 7-9; NOTES "CHECKSUM PARITY"). One tick = one stored DOS pose (port/tests/cases).
Per tick, crc32 of:
  order  the port's painter order (godot --chk) against the DOS order (tests/vectors/draworder.json, from the bsporder.py replica verified on the live
         DOS draw list), limited to items the port draws; 'extra' = items the port draws that DOS does not list
  frame  the port frame, rendered twice (A, B) and against the stored dos.png (same RGB565 quantising as regress.py)
Checks: 1 determinism (run A == run B, order and frame); 2 order port == DOS; 3 frame port == DOS (px count when not); 4 stored checksums
(port/tests/chk.json) so any change of port output shows as CHANGED. Reports the FIRST tick that differs for each check.
  chkparity.py [case ...]    all checks; exit 1 on nondeterminism or an order mismatch
  chkparity.py --noframes    order only (2 s, no renders)
  chkparity.py --accept      store this run's checksums as the reference
Env JOBS = parallel renders (4). Frame equality with DOS is information (the px gate is regress.py), not an exit condition."""
import sys, os, json, zlib, subprocess, tempfile, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paritylib as L
a = sys.argv[1:]; names = [x for x in a if not x.startswith('--')]; acc = '--accept' in a; frames = '--noframes' not in a
crc = lambda b: '%08x' % (zlib.crc32(b) & 0xffffffff)
ckeys = lambda ks: crc(b''.join(int(k).to_bytes(4, 'little') for k in ks))
ORD_W = 128
def chk_run(tag):
    out = os.path.join(tempfile.gettempdir(), f'qchk_{tag}.json')
    if os.path.exists(out): os.remove(out)
    si = subprocess.STARTUPINFO(); si.dwFlags = 1; si.wShowWindow = 7
    r = subprocess.run([L.GODOT, '--headless', '--path', '.', '--', '--city=KCITY', '--chk=' + out.replace('\\', '/')], cwd=L.PORT, startupinfo=si, creationflags=0x08000000, capture_output=True, text=True, errors='replace')
    if not os.path.exists(out): sys.exit('godot --chk wrote nothing: ' + (r.stdout + r.stderr)[-600:])
    return {p['name']: p for p in json.load(open(out))}
def shot(n, tag):
    c = json.load(open(os.path.join(L.CASES, n, 'case.json'))); out = f'shots/chk_{n}_{tag}.png'; f = os.path.join(L.PORT, out)
    if os.path.exists(f): os.remove(f)
    L.port_shot(c, out, f'res://tests/cases/{n}/ents.json')
    return f if os.path.exists(f) else None
def frame(n):
    fa, fb = shot(n, 'a'), shot(n, 'b')
    if not fa or not fb: return n, None
    dp = os.path.join(L.CASES, n, 'dos.png'); pa, d = L.load_pair(fa, dp); pb, _ = L.load_pair(fb, dp)
    r = (crc(pa.tobytes()), crc(pb.tobytes()), crc(d.tobytes()), L.px_differ(pa, d))
    for f in (fa, fb): os.remove(f)
    return n, r
t0 = time.time(); A = chk_run('a'); B = chk_run('b')
dos = {p['name']: p for p in json.load(open(os.path.join(L.PORT, 'tests', 'vectors', 'draworder.json')))}
key = lambda n: (''.join(c for c in n if not c.isdigit()), int(''.join(c for c in n if c.isdigit()) or 0))
ticks = sorted([n for n in A if not names or n in names], key=key)
FR = {}
if frames:
    with ThreadPoolExecutor(int(os.environ.get('JOBS', '4'))) as ex: FR = dict(ex.map(frame, ticks))
SF = os.path.join(L.PORT, 'tests', 'chk.json'); stored = json.load(open(SF)) if os.path.exists(SF) else {}
first = {}; rows = []; new = {}
def mark(k, n):
    first.setdefault(k, n)
print('%-6s %-8s %-8s %5s %4s  %-8s %-8s %6s  %s' % ('tick', 'ord_port', 'ord_dos', 'extra', 'ties', 'frm_port', 'frm_dos', 'px', 'notes'))
for n in ticks:
    po = A[n]['order']; drawn = set(po); seq = [int(e) * ORD_W + int(c) for e, c in dos[n]['seq'] if int(c) < ORD_W]
    listed = set(seq); want = [k for k in seq if k in drawn]; have = [k for k in po if k in listed]; extra = len(drawn - listed)
    cp, cd = ckeys(have), ckeys(want); notes = []
    if A[n]['order'] != B[n]['order'] or A[n]['sin'] != B[n]['sin']: notes.append('ORDER NOT DETERMINISTIC'); mark('nondet', n)
    if cp != cd or extra: notes.append('ORDER != DOS'); mark('order', n)
    if A[n]['ties']: notes.append('ties')
    fr = FR.get(n); fp = fd = '-'; px = -1
    if frames:
        if fr is None: notes.append('NO FRAME'); mark('nondet', n)
        else:
            fp, fb, fd, px = fr
            if fp != fb: notes.append('FRAME NOT DETERMINISTIC'); mark('nondet', n)
            if fp != fd: mark('frame', n)
    new[n] = {'order': cp, 'frame': fp}
    s = stored.get(n)
    if s and (s['order'] != cp or (frames and s.get('frame', '-') not in ('-', fp))): notes.append('CHANGED vs stored'); mark('changed', n)
    print('%-6s %-8s %-8s %5d %4d  %-8s %-8s %6s  %s' % (n, cp, cd, extra, A[n]['ties'], fp, fd, px if px >= 0 else '-', ', '.join(notes)))
eq = sum(1 for n in ticks if FR.get(n) and FR[n][0] == FR[n][2])
print('ticks %d | determinism: %s | order vs DOS: %s | frames equal to DOS: %s | vs stored: %s | sec %d' % (
    len(ticks), 'first bad ' + first['nondet'] if 'nondet' in first else 'ok',
    'first differs ' + first['order'] if 'order' in first else 'ok',
    ('%d of %d, first differs %s' % (eq, len(ticks), first.get('frame', '-'))) if frames else 'skipped',
    'first changed ' + first['changed'] if 'changed' in first else ('ok' if stored else 'no reference'), time.time() - t0))
if acc:
    if not frames:
        for n in new: new[n]['frame'] = stored.get(n, {}).get('frame', '-')
    stored.update(new); json.dump(stored, open(SF, 'w'), indent=0, sort_keys=True); print('stored', SF)
sys.exit(1 if 'nondet' in first or 'order' in first else 0)
