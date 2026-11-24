"""pp.py: token-cheap parity pipeline. One call per step, short stdout, full detail in port/tests/triage.md.
  pp.py triage [N=6] [case ...]   gate (regress.py) -> worst N cases -> fresh port frame -> px grouped by owning item (idp.py)
                                  -> auto verdict per top group: sprite = best (dx, dy) shift; wall = wallref.py model lines of that cell.
                                  Prints 1 line per case. Read triage.md only for the case being fixed.
  pp.py gate                      gate only: total, worse list (1-3 lines). Accepts the baseline when nothing is worse.
  pp.py resnap [case ...]         DOSBox start -> re-snap the cases (default: all s*) at their stored pose -> stop. Prints totals only.
  pp.py fn <addr> [out]           cut one function out of ghidra/decomp_q.c -> file (default %TEMP%/fn_<addr>.c), prints path + line count.
  pp.py ask <addr> "<question>"   local model (Sage, localread.py) answers ONE single-step question about that function; Claude then reads
                                  only the cited lines. Set LOCALREAD_GPU=<idx> first (hoggate.py status --gpu auto --gb N).
  pp.py try "<what + DOS line>"   ONE call per render edit: gate once; any case worse -> port/shaders + main.gd restored from the last kept
                                  state (port/tests/.keep), prints REVERTED; else keeps the edit (new .keep), accepts regress + chkparity,
                                  logs one line to port/tests/trylog.md. Takes up to 10 min: run it in the background. No hand backups.
  pp.py poke <case> <cx> <cy> <hexword> [cx cy hexword ...] [--at x y ...] [--keep-dos]
                                  DOS side test in one call: DOSBox start if needed -> live map checked against the city json -> cells
                                  written -> snap at the case pose -> diff vs the case's dos.png (count, box, colours at --at px)
                                  -> cells restored, temp case deleted, DOSBox stopped. hexword = cell value, e.g. 9003, 0 = empty.
  pp.py grow [N=8] [prefix=g]     new KCITY cases without asking: N random road cells (>= 3 cells from every stored case), 4 headings
                                  cycled, snap each (invalid / refused poses skipped), then gate. Prints saved cases + their px.
  pp.py keep                      store the current port/shaders + main.gd as the kept state without testing (after a hand revert).
Rule: Claude reads decomp text itself only after `ask` named the lines."""
import sys, os, re, json, subprocess
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
ROOT = os.path.dirname(T); PY = [sys.executable, '-I']; TMP = os.environ.get('TEMP', '.')
REP = os.path.join(ROOT, 'port', 'tests', 'triage.md'); DEC = os.path.join(ROOT, 'ghidra', 'decomp_q.c')
def run(args, **kw): return subprocess.run(PY + args, capture_output=True, text=True, cwd=ROOT, **kw)
def gate(extra=()):
    env = dict(os.environ, JOBS=os.environ.get('JOBS', '6')); r = run([os.path.join(T, 'regress.py'), *extra], env=env); rows = {}
    for l in r.stdout.splitlines():
        m = re.match(r'^(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s*(.*)$', l)
        if m: rows[m.group(1)] = (int(m.group(2)), int(m.group(4)), m.group(5).strip())
    tot = next((l for l in reversed(r.stdout.splitlines()) if l.startswith('total')), 'NO TOTAL ' + r.stderr[-200:])
    return rows, tot
def shift(n, box):
    """Best (dx, dy) of the port frame against DOS inside the group's box -> (px at 0,0, best px, dx, dy)."""
    import paritylib as L
    p, d = L.load_pair(os.path.join(L.PORT, 'shots', 'par_%s_port.png' % n), os.path.join(L.CASES, n, 'dos.png'))
    p = p.convert('RGB').resize((320, 200), 0).load(); d = d.convert('RGB').resize((320, 200), 0).load(); x0, x1, y0, y1 = box; res = []
    for dy in range(-2, 3):
        for dx in range(-3, 4):
            res.append((sum(1 for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if p[min(max(x - dx, 0), 319), min(max(y - dy, 0), 199)] != d[x, y]), abs(dx) + abs(dy), dx, dy))
    z = next(r[0] for r in res if r[2] == 0 and r[3] == 0); b = min(res)
    return z, b[0], b[2], b[3]
def judge(L, n, c, g, out):
    """Auto verdict for the top differing group of one case -> one stdout line."""
    m = re.search(r'(\d+) px\s+cell (\d+),(\d+) \(d (-?\d+),(-?\d+)\) (\w+)\s+item (-?\d+)\s+x (\d+)-(\d+) rows (\d+)-(\d+)', g[1]) if len(g) > 1 else None
    if not m: return 'no group'
    px, cx, cy, dx, dy, kind, item, x0, x1, y0, y1 = m.groups(); v = ''
    if kind == 'spr': v = judge_spr(L, n, (int(x0), int(x1), int(y0), int(y1)), out)
    elif kind == 'wall':
        cam = c['cam']; w = [l for l in run([os.path.join(T, 'wallref.py'), str(cam['x']), str(cam['y']), str(cam['z']), str(cam['head']), cx, cy]).stdout.splitlines() if 'KILL' not in l]
        out += ['wallref drawn walls of cell %s,%s:' % (cx, cy)] + w; v = '%d model walls drawn in cell' % len(w)
    out.append('verdict: ' + v + chr(10))
    return '%s px %s cell %s,%s item %s x %s-%s rows %s-%s | %s' % (px, kind, cx, cy, item, x0, x1, y0, y1, v)
def judge_spr(L, n, box, out):
    z, b, sx, sy = shift(n, box); out.append('ents: ' + json.dumps(json.load(open(os.path.join(L.CASES, n, 'ents.json'))))[:1500])
    return 'shift %+d,%+d gives %d (now %d)' % (sx, sy, b, z) if b < z * 0.6 else 'no shift helps (frame/shade/missing?)'
def triage(a):
    import paritylib as L
    N = next((int(x) for x in a if x.isdigit()), 6); names = [x for x in a if not x.isdigit()]
    rows, tot = gate(); pick = names or [k for k, v in sorted(rows.items(), key=lambda kv: -kv[1][0])[:N]]
    out = ['# triage (pp.py)', tot, '']; print(tot)
    for n in pick:
        c = json.load(open(os.path.join(L.CASES, n, 'case.json')))
        L.port_shot(c, 'shots/par_%s_port.png' % n, 'res://tests/cases/%s/ents.json' % n)  # idp.py compares this frame: keep it fresh
        g = run([os.path.join(T, 'idp.py'), n]).stdout.splitlines(); out += ['## %s px %s' % (n, rows.get(n, ('?',))[0])] + g
        print(n, rows.get(n, ('?',))[0], judge(L, n, c, g, out))
    open(REP, 'w').write('\n'.join(out)); print('detail', REP)
KEEP = os.path.join(ROOT, 'port', 'tests', '.keep')
def tracked():
    import glob
    return sorted(glob.glob(os.path.join(ROOT, 'port', 'shaders', '*.gdshader'))) + [os.path.join(ROOT, 'port', 'main.gd'), os.path.join(ROOT, 'tools', 'paritylib.py')]
def keep():
    import shutil
    os.makedirs(KEEP, exist_ok=True); open(os.path.join(KEEP, '.gdignore'), 'w').close()
    for f in tracked(): shutil.copy2(f, os.path.join(KEEP, os.path.basename(f)))
def tryedit(note):
    import shutil, time, filecmp
    if not os.path.isdir(KEEP): print('no kept state: run `pp.py keep` on a known-good tree first'); return 2
    ch = [os.path.basename(f) for f in tracked() if not filecmp.cmp(f, os.path.join(KEEP, os.path.basename(f)), False)]
    if not ch: print('nothing changed since the kept state'); return 0
    rows, tot = gate(); bad = [k + ' ' + v[2] for k, v in rows.items() if 'WORSE' in v[2] or 'FAIL' in v[2]]
    log = lambda v: open(os.path.join(ROOT, 'port', 'tests', 'trylog.md'), 'a', encoding='utf-8').write('- %s %s | %s | %s | %s' % (time.strftime('%m-%d %H:%M'), v, tot, ','.join(ch), note) + chr(10))
    if bad or not tot.startswith('total'):
        rej = os.path.join(TMP, 'pp_rejected'); os.makedirs(rej, exist_ok=True)
        for f in tracked(): shutil.copy2(f, os.path.join(rej, os.path.basename(f))); shutil.copy2(os.path.join(KEEP, os.path.basename(f)), f)
        log('REVERTED'); print('REVERTED', tot, '| worse:', '; '.join(bad[:8]), '| rejected files in', rej); return 1
    r1 = run([os.path.join(T, 'regress.py'), '--accept', '--force'], env=dict(os.environ, JOBS=os.environ.get('JOBS', '6'))).stdout.strip().splitlines()[-1:]
    r2 = [l for l in run([os.path.join(T, 'chkparity.py'), '--accept']).stdout.splitlines() if l.startswith('ticks')]
    keep(); log('KEPT'); print('KEPT', tot, '|', (r1 or ['regress: no output'])[0][:90], '|', (r2 or ['chkparity: no output'])[0][:170]); return 0
CASES = os.path.join(ROOT, 'port', 'tests', 'cases')
def dos_up():
    """DOSBox in game with the city of the json loaded -> (Reader, map base, city dict); starts DOSBox when needed."""
    from dosrd import Reader, DELTA
    import struct
    d = json.load(open(os.path.join(ROOT, 'port', 'data', 'KCITY.json')))
    for t in range(2):
        try:
            R = Reader(); base = R.u32(0x830a8) - DELTA; w = R.u32(0x8356a) >> 16; n = d['w'] * 4
            if w == d['w'] and struct.unpack('<%dH' % n, R.rd(base + d['w'] * 40 * 2, n * 2)) == tuple(d['cells'][d['w'] * 40:d['w'] * 40 + n]): return R, base, d
        except Exception: pass
        if t == 0: run([os.path.join(T, 'parity.py'), 'stop']); run([os.path.join(T, 'parity.py'), 'start'])
    sys.exit('DOS: live map does not match KCITY.json (not in game, or another city)')
def snap(name, pose):
    r = run([os.path.join(T, 'parity.py'), 'snap', name, '--pose', *map(str, pose)])
    try: return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: return {'valid': False, 'err': (r.stdout + r.stderr).strip()[-160:]}
def poke(a):
    import shutil, struct, paritylib as L
    stop = '--keep-dos' not in a; a = [v for v in a if v != '--keep-dos']; at = []
    if '--at' in a: k = a.index('--at'); at = [int(v) for v in a[k + 1:]]; a = a[:k]
    n = a[0]; c = json.load(open(os.path.join(CASES, n, 'case.json')))['cam']; R, base, d = dos_up(); old = []
    wr = lambda ad, v: run([os.path.join(T, 'dosmem.py'), 'wr', '%x' % ad, struct.pack('<H', v).hex()])
    try:
        for i in range(1, len(a) - 2, 3):
            ad = base + (int(a[i]) + d['w'] * int(a[i + 1])) * 2; old.append((ad, struct.unpack('<H', R.rd(ad, 2))[0])); wr(ad, int(a[i + 2], 16))
        j = snap('zz_poke', [c['x'], c['y'], c['head']])
    finally:
        for ad, v in old: wr(ad, v)
        bad = [hex(ad) for ad, v in old if struct.unpack('<H', R.rd(ad, 2))[0] != v]
        if stop: run([os.path.join(T, 'parity.py'), 'stop'])
    f = os.path.join(CASES, 'zz_poke', 'dos.png')
    if not j.get('valid') or not os.path.exists(f): print('POKE snap invalid:', str(j)[:200], '| restore failed at' if bad else '', *bad); shutil.rmtree(os.path.join(CASES, 'zz_poke'), True); return 1
    x, y0 = L.load_pair(f, os.path.join(CASES, n, 'dos.png')); x = x.convert('RGB').resize((320, 200), 0).load(); y = y0.convert('RGB').resize((320, 200), 0).load()
    df = [(i, k) for k in range(37, 149) for i in range(320) if x[i, k] != y[i, k]]; shutil.copy(f, os.path.join(TMP, 'pp_poke.png')); shutil.rmtree(os.path.join(CASES, 'zz_poke'), True)
    print('POKE', n, 'cells', [(hex(ad), '%04x' % v) for ad, v in old], '| DOS px changed vs case (rows 37-148):', len(df), ('box x %d-%d rows %d-%d' % (min(i for i, k in df), max(i for i, k in df), min(k for i, k in df), max(k for i, k in df))) if df else '',
          '|', ' '.join('(%d,%d) poked %02x%02x%02x case %02x%02x%02x' % (at[i], at[i + 1], *x[at[i], at[i + 1]], *y[at[i], at[i + 1]]) for i in range(0, len(at) - 1, 2)), '| frame', os.path.join(TMP, 'pp_poke.png'), '| RESTORE FAILED ' + ' '.join(bad) if bad else '| restored')
    return 0
def grow(a):
    import random, glob
    N = int(a[0]) if a else 8; pre = a[1] if len(a) > 1 else 'g'; R, base, d = dos_up(); W = d['w']
    have = [json.load(open(f))['cam'] for f in glob.glob(os.path.join(CASES, '*', 'case.json'))]; have = [(c['x'] >> 9, c['y'] >> 9) for c in have]
    road = [(i % W, i // W) for i, v in enumerate(d['cells']) if v & 0x7f == 0 and 3 <= i % W < W - 3 and 3 <= i // W < d['h'] - 3]
    road = [c for c in road if any(d['cells'][(c[1] + dy) * W + c[0] + dx] & 0x7f for dx in (-1, 0, 1) for dy in (-1, 0, 1))]  # next to a block = street, not open void
    random.seed(len(have)); random.shuffle(road); got = []; tried = 0
    for cx, cy in road:
        if len(got) >= N or tried >= N * 4: break
        if any(abs(cx - hx) < 3 and abs(cy - hy) < 3 for hx, hy in have): continue
        tried += 1; h = (360, 1800, 3240, 4680)[tried % 4]; nm = '%s%d_%d_%d' % (pre, cx, cy, h); j = snap(nm, [cx * 512 + 256, cy * 512 + 256, h])
        if j.get('case_saved'): got.append((nm, j.get('px'))); have.append((cx, cy))
    run([os.path.join(T, 'parity.py'), 'stop']); rows, tot = gate(['--accept', '--force'])
    print('GROW tried', tried, 'saved', len(got), '|', tot); print(' '.join('%s %s' % (n, rows[n][0] if n in rows else px) for n, px in got) or 'no case saved (poses refused: see parity.py snap output by hand)')
    return 0
def fn(addr, out=None):
    addr = '%08x' % int(addr, 16); L = open(DEC, errors='replace').read().split('\n')
    s = next((i for i, l in enumerate(L) if l.startswith('// ====') and '@ ' + addr in l), None)
    if s is None: sys.exit('no function at ' + addr)
    e = next((i for i in range(s + 1, len(L)) if L[i].startswith('// ====')), len(L)); out = out or os.path.join(TMP, 'fn_%s.c' % addr)
    open(out, 'w').write('\n'.join('%d: %s' % (i + 1, L[i]) for i in range(s, e))); return out, s + 1, e
if __name__ == '__main__':
    a = sys.argv[1:]; cmd = a[0] if a else ''
    if cmd == 'triage': triage(a[1:])
    elif cmd == 'gate':
        rows, tot = gate(); bad = [k + ' ' + v[2] for k, v in rows.items() if 'WORSE' in v[2] or 'FAIL' in v[2]]; print(tot); print('worse:', '; '.join(bad[:8]) or 'none')
        if not bad: print(gate(['--accept'])[1], '(accepted)')
    elif cmd == 'resnap':
        import paritylib as L
        N = a[1:] or sorted(n for n in os.listdir(L.CASES) if n.startswith('s')); ok = 0; log = open(os.path.join(TMP, 'pp_resnap.txt'), 'w')
        print('start', (run([os.path.join(T, 'parity.py'), 'start']).stdout.strip().split('\n') or [''])[-1][:80])
        for n in N:
            c = json.load(open(os.path.join(L.CASES, n, 'case.json')))['cam']
            for t in range(2):
                r = run([os.path.join(T, 'parity.py'), 'snap', n, '--pose', str(c['x']), str(c['y']), str(c['head'])]); o = (r.stdout + r.stderr).strip().split('\n')[-1]
                good = '"case_saved": true' in o
                if good: break
            ok += good; log.write('%s %s %s\n' % (n, 'OK' if good else 'REFUSED', o[:200])); log.flush()
        run([os.path.join(T, 'parity.py'), 'stop']); print('snaps', ok, 'of', len(N), 'log', log.name)
    elif cmd == 'fn': o, s, e = fn(a[1], a[2] if len(a) > 2 else None); print(o, 'decomp_q.c lines', s, '-', e)
    elif cmd == 'ask':
        o, s, e = fn(a[1]); r = subprocess.run([sys.executable, r'C:\Games\Tools\llm\localread.py', o, a[2] + ' Cite the line numbers shown at the start of the lines.'], capture_output=True, text=True)
        print('fn lines', s, '-', e); print((r.stdout or r.stderr)[-1500:])
    elif cmd == 'try': sys.exit(tryedit(' '.join(a[1:])))
    elif cmd == 'poke': sys.exit(poke(a[1:]))
    elif cmd == 'grow': sys.exit(grow(a[1:]))
    elif cmd == 'keep': keep(); print('kept', len(tracked()), 'files in', KEEP)
    else: print(__doc__)
