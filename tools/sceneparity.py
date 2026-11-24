"""sceneparity.py: parity test for the SCENE route of the port (port/areas/<CITY>.tscn + one scene per area), per editable area.
  sceneparity.py status [CITY]        per area: stored DOS cases, best px sum (tests/baseline.json), bake fresh/STALE (txt newer than _walls.res)
  sceneparity.py check [case ...]     each stored case rendered 3 ways: map scene | --noarea (JSON cells) | --area=<its area> alone.
                                      RULES: scene == noarea (0 px); area alone == scene when the camera is >= 4 cells inside the area
                                      (DOS draws 7x7 cells); px vs DOS not above baseline. exit 1 on a broken rule.
  sceneparity.py poses [CITY] [n]     snap commands for areas with fewer than n (1) cases: empty cell with most blocks around, 4 headings
  sceneparity.py snap [CITY] [n]      run those snaps (DOSBox must be in game: parity.py start); names s<AREA><k>
Areas come from port/areas/<CITY>/areas.json (tools/areas.py split). Cases from port/tests/cases (parity.py snap)."""
import sys, os, json, subprocess
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageChops
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import paritylib as L
MARGIN = 4
def areas(city):
    f = os.path.join(L.PORT, 'areas', city, 'areas.json')
    return json.load(open(f)) if os.path.exists(f) else {}
def area_of(A, cx, cy):
    """-> (name, cells to the nearest border) of the area holding cell (cx, cy)."""
    for k, (ox, oy, w, h) in A.items():
        if ox <= cx < ox + w and oy <= cy < oy + h: return k, min(cx - ox, ox + w - 1 - cx, cy - oy, oy + h - 1 - cy)
    return None, 0
def cases(names=()):
    out = {}
    for n in sorted(os.listdir(L.CASES)):
        f = os.path.join(L.CASES, n, 'case.json')
        if os.path.exists(f) and (not names or n in names): out[n] = json.load(open(f))
    return out
def by_area(city):
    A = areas(city); R = {k: [] for k in A}
    for n, c in cases().items():
        if c.get('city', 'KCITY') != city: continue
        k = area_of(A, c['cam']['x'] >> 9, c['cam']['y'] >> 9)[0]
        if k: R[k].append(n)
    return A, R
def stale(city, k):
    d = os.path.join(L.PORT, 'areas', city); t = os.path.join(d, k + '.txt'); r = os.path.join(d, k + '_walls.res')
    if not os.path.exists(r): return 'NO BAKE'
    return 'STALE' if os.path.getmtime(t) > os.path.getmtime(r) + 2 else 'fresh'
def status(city):
    A, R = by_area(city); base = json.load(open(os.path.join(L.PORT, 'tests', 'baseline.json'))); cov = 0
    print('%-5s %5s %7s  %-8s %s' % ('area', 'cases', 'best px', 'bake', 'names'))
    for k in A:
        cov += bool(R[k]); print('%-5s %5d %7s  %-8s %s' % (k, len(R[k]), sum(base.get(n, 0) for n in R[k]) if R[k] else '-', stale(city, k), ' '.join(R[k])))
    print(city, 'areas with cases', cov, 'of', len(A))
    return cov
def diff_px(a, b):
    """320x200 pixels that differ between two port frames."""
    x = Image.open(a).convert('RGB').resize((320, 200), 0); y = Image.open(b).convert('RGB').resize((320, 200), 0)
    return sum(1 for v in ImageChops.difference(x, y).convert('L').tobytes() if v)
def shot(n, c, tag, extra):
    out = 'shots/sp_%s_%s.png' % (n, tag); f = os.path.join(L.PORT, out)
    if os.path.exists(f): os.remove(f)
    err = L.port_shot(c, out, 'res://tests/cases/%s/ents.json' % n, extra)
    return f if os.path.exists(f) else None, err
def check_one(item):
    """-> dict name, area, edge, px (scene vs DOS), na (scene vs noarea), solo (scene vs area alone), err"""
    n, c = item; k, edge = area_of(areas(c.get('city', 'KCITY')), c['cam']['x'] >> 9, c['cam']['y'] >> 9)
    fs, e1 = shot(n, c, 'scene', ''); fn, e2 = shot(n, c, 'noarea', '--noarea'); fo, e3 = shot(n, c, 'solo', '--area=%s' % k)
    R = dict(name=n, area=k, edge=edge, err=(e1 + e2 + e3)[:1], px=None, na=None, solo=None)
    if not (fs and fn and fo): R['err'] = R['err'] or ['no shot']; return R
    p, d = L.load_pair(fs, os.path.join(L.CASES, n, 'dos.png'))
    R.update(px=L.px_differ(p, d), na=diff_px(fs, fn), solo=diff_px(fs, fo))
    return R
def verdict(R, base):
    """-> list of broken rules for one case."""
    if R['px'] is None: return ['FAILED ' + str(R['err'][0])[:60]]
    v = ['SHADER/ERR'] if R['err'] else []
    if R['na']: v.append('scene != noarea')
    if R['solo'] and R['edge'] >= MARGIN: v.append('area alone != scene')
    if R['name'] in base and R['px'] > base[R['name']]: v.append('WORSE +%d' % (R['px'] - base[R['name']]))
    return v
def check(names):
    base = json.load(open(os.path.join(L.PORT, 'tests', 'baseline.json'))); bad = 0; tot = 0; per = {}
    with ThreadPoolExecutor(int(os.environ.get('JOBS', '4'))) as ex: res = list(ex.map(check_one, cases(names).items()))
    print('%-6s %-4s %4s %6s %6s %6s %6s  %s' % ('case', 'area', 'edge', 'px', 'best', 'noarea', 'solo', ''))
    for R in res:
        v = verdict(R, base); bad += bool(v); tot += R['px'] or 0; per[R['area']] = per.get(R['area'], 0) + (R['px'] or 0)
        note = ', '.join(v) or ('border view (solo differs: neighbour area in sight)' if R['solo'] else '')
        print('%-6s %-4s %4d %6s %6s %6s %6s  %s' % (R['name'], R['area'], R['edge'], R['px'], base.get(R['name'], '-'), R['na'], R['solo'], note))
    print('total px', tot, 'per area', per, 'cases', len(res), 'broken', bad, 'PASS' if not bad else 'FAIL')
    return bad
def best_cell(d, ox, oy, w, h):
    """Empty cell (block 0) of the area, >= MARGIN inside, with most built cells in its 7x7; -> (score, cx, cy) or None."""
    W = d['w']; H = d['h']; best = None
    for cy in range(max(oy + MARGIN, 3), min(oy + h - MARGIN, H - 3)):
        for cx in range(max(ox + MARGIN, 3), min(ox + w - MARGIN, W - 3)):
            if d['cells'][cy * W + cx] & 0x7f: continue
            s = sum(1 for y in range(cy - 3, cy + 4) for x in range(cx - 3, cx + 4) if d['cells'][y * W + x] & 0x7f)
            if best is None or s > best[0]: best = (s, cx, cy)
    return best
def poses(city, need=1):
    """-> [(name, x, y, head)] for areas with fewer than `need` cases."""
    A, R = by_area(city); d = json.load(open(os.path.join(L.PORT, 'data', city + '.json'))); out = []
    for k, (ox, oy, w, h) in A.items():
        b = best_cell(d, ox, oy, w, h) if len(R[k]) < need else None
        if not b or not b[0]: continue
        out += [('s%s%d' % (k, i), b[1] * 512 + 256, b[2] * 512 + 256, i * 1440) for i in range(4)]
    return out
def snap(city, need):
    ok = 0; P = poses(city, need)
    for n, x, y, hd in P:
        r = subprocess.run([sys.executable, '-I', os.path.join(T, 'parity.py'), 'snap', n, '--pose', str(x), str(y), str(hd)], capture_output=True, text=True)
        good = r.returncode == 0 and os.path.exists(os.path.join(L.CASES, n, 'case.json')); ok += good
        print(n, x, y, hd, 'OK' if good else 'REFUSED', (r.stdout + r.stderr).strip().split('\n')[-1][:140])
    print('snaps', ok, 'of', len(P))
    return ok
if __name__ == '__main__':
    a = sys.argv[1:]; cmd = a[0] if a else 'status'; city = next((x for x in a[1:] if x.isupper()), 'KCITY'); n = next((int(x) for x in a[1:] if x.isdigit()), 1)
    if cmd == 'status': status(city)
    elif cmd == 'check': sys.exit(1 if check(a[1:]) else 0)
    elif cmd == 'poses':
        for p in poses(city, n): print('py -3.13 -I tools/parity.py snap %s --pose %d %d %d' % p)
    elif cmd == 'snap': snap(city, n)
    else: print(__doc__)
