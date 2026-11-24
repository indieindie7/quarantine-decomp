"""pp.py: token-cheap parity pipeline. One call per step, short stdout, full detail in port/tests/triage.md.
  pp.py triage [N=6] [case ...]   gate (regress.py) -> worst N cases -> fresh port frame -> px grouped by owning item (idp.py)
                                  -> auto verdict per top group: sprite = best (dx, dy) shift; wall = wallref.py model lines of that cell.
                                  Prints 1 line per case. Read triage.md only for the case being fixed.
  pp.py gate                      gate only: total, worse list (1-3 lines). Accepts the baseline when nothing is worse.
  pp.py resnap [case ...]         DOSBox start -> re-snap the cases (default: all s*) at their stored pose -> stop. Prints totals only.
  pp.py fn <addr> [out]           cut one function out of ghidra/decomp_q.c -> file (default %TEMP%/fn_<addr>.c), prints path + line count.
  pp.py ask <addr> "<question>"   local model (Sage, localread.py) answers ONE single-step question about that function; Claude then reads
                                  only the cited lines. Set LOCALREAD_GPU=<idx> first (hoggate.py status --gpu auto --gb N).
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
    else: print(__doc__)
