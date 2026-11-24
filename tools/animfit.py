"""animfit.py: cases snapped before parity.py stored the DOS anim states (0x893b2) get a FITTED state per animated wall texture:
per anim every distinct frame is rendered and the one with the fewest px vs dos.png kept. Writes case['anim'] + case['anim_fit'] = true
(a fit, not a DOS read; a re-snap replaces it). Cases that already hold 'anim' without 'anim_fit' are skipped.
  animfit.py [case ...]    JOBS=n threads"""
import sys, os, json
from concurrent.futures import ThreadPoolExecutor
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import paritylib as L
def px(n, c, st, tag):
    c = dict(c); c['anim'] = st; out = 'shots/af_%s_%s.png' % (n, tag); f = os.path.join(L.PORT, out)
    if os.path.exists(f): os.remove(f)
    L.port_shot(c, out, 'res://tests/cases/%s/ents.json' % n)
    if not os.path.exists(f): return None
    p, d = L.load_pair(f, os.path.join(L.CASES, n, 'dos.png')); return L.px_differ(p, d)
def fit(n):
    f = os.path.join(L.CASES, n, 'case.json'); c = json.load(open(f))
    if 'anim' in c: return n, 'has state' + (' (fit)' if c.get('anim_fit') else ''), None, None
    A = json.load(open(os.path.join(L.PORT, 'data', c.get('city', 'KCITY') + '_anim.json'))); K = len(A['from']); st = [0] * K
    base = best = px(n, c, st, 'b')
    if best is None: return n, 'no shot', None, None
    alt = [next((s for s, fr in enumerate(A['frames'][k]) if fr != A['frames'][k][0]), 0) for k in range(K)]
    if px(n, c, alt, 'a') is not None and open(os.path.join(L.PORT, 'shots/af_%s_a.png' % n), 'rb').read() == open(os.path.join(L.PORT, 'shots/af_%s_b.png' % n), 'rb').read(): K = 0  # no animated tile in view
    for k in range(K):
        seen = {tuple(A['frames'][k][0])}
        for s, fr in enumerate(A['frames'][k]):
            if tuple(fr) in seen: continue
            seen.add(tuple(fr)); t = st[:]; t[k] = s; v = px(n, c, t, 'k%d' % k)
            if v is not None and v < best: best = v; st = t
    c['anim'] = st; c['anim_fit'] = True; json.dump(c, open(f, 'w'))
    return n, st, base, best
if __name__ == '__main__':
    names = sys.argv[1:] or sorted(x for x in os.listdir(L.CASES) if os.path.exists(os.path.join(L.CASES, x, 'case.json')))
    with ThreadPoolExecutor(int(os.environ.get('JOBS', '4'))) as ex:
        tot = 0
        for n, st, b, v in ex.map(fit, names):
            if b is not None and v != b: tot += b - v
            print(n, st, b, v, flush=True)
    print('px gained', tot)
