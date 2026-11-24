"""Regression gate: every stored DOS case vs the port as it is now. No DOSBox needed.
regress.py [name ...]           render + compare; table px differ (of 64000) all / 3D view rows 37-148 vs best so far; exit 1 when any case got worse
regress.py --accept [name ...]  same, then store the new numbers as best (only where lower, or all with --force)
Env PORT_ARGS = extra port flags (experiments; never accepted), JOBS = parallel renders (4). Cases come from `parity.py snap` (port/tests/cases)."""
import sys, os, json, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paritylib as L
a = sys.argv[1:]; acc = '--accept' in a; force = '--force' in a; names = [x for x in a if not x.startswith('--')]
BF = os.path.join(L.PORT, 'tests', 'baseline.json'); base = json.load(open(BF)) if os.path.exists(BF) else {}
key = lambda n: (''.join(c for c in n if not c.isdigit()), int(''.join(c for c in n if c.isdigit()) or 0))
cases = sorted([n for n in os.listdir(L.CASES) if os.path.exists(os.path.join(L.CASES, n, 'case.json')) and (not names or n in names)], key=key)
extra = os.environ.get('PORT_ARGS', '')
def run(n):
    c = json.load(open(os.path.join(L.CASES, n, 'case.json'))); out = f'shots/reg_{n}.png'; f = os.path.join(L.PORT, out)
    if os.path.exists(f): os.remove(f)
    err = L.port_shot(c, out, f'res://tests/cases/{n}/ents.json', extra)
    if not os.path.exists(f): return n, None, None, err or ['no shot']
    p, d = L.load_pair(f, os.path.join(L.CASES, n, 'dos.png'))
    return n, L.px_differ(p, d), L.px_differ(p, d, (0, 37, 320, 149)), err
t0 = time.time(); bad = 0; tot = 0
with ThreadPoolExecutor(int(os.environ.get('JOBS', '4'))) as ex: res = list(ex.map(run, cases))
print('%-8s %6s %6s %6s  %s' % ('case', 'px', 'view', 'best', ''))
for n, px, vw, err in res:
    b = base.get(n)
    if px is None: print('%-8s FAILED %s' % (n, err[:2])); bad += 1; continue
    tot += px; st = 'NEW' if b is None else ('WORSE +%d' % (px - b) if px > b else ('better %d' % (px - b) if px < b else ''))
    if err: st += ' SHADER/ERR: ' + err[0][:80]
    if err or (b is not None and px > b): bad += 1
    print('%-8s %6d %6d %6s  %s' % (n, px, vw, '-' if b is None else b, st))
    if acc and not extra and (force or b is None or px < b): base[n] = px
print('total', tot, 'cases', len(res), 'worse/failed', bad, 'sec', round(time.time() - t0))
if acc and not extra: json.dump(base, open(BF, 'w'), indent=0, sort_keys=True)
sys.exit(1 if bad else 0)
