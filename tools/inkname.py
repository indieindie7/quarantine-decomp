"""inkname.py <decomp.c> <funcinfo.tsv> <hand.txt> <out.tsv> [lib-hint] : asks Inkling (localread, port 18000) for a name for every
hand line marked 'region name only'; keeps the region prefix (rt_/sos_/fp_/frag_), writes addr<TAB>old<TAB>new<TAB>why to out.tsv
(resumable: skips addrs already in out.tsv). Apply with: inkname.py ... --apply (rewrites hand.txt lines, unique names, comment
'inkling guess: <why>'). 11-25, Quarantine II RWCD."""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.environ.get("LOCALREAD_DIR", r"C:\Users\USER\Documents\Tools\llm"))
from fdigest import blocks, info, squeeze, callee_names
ID = re.compile(r'^[A-Za-z][A-Za-z0-9_]{2,40}$')
SYS = ("You name functions in a decompiled 1994 DOS game (Watcom C 32-bit, DOS4GW, HMI SOS sound library, x87 maths). "
       "Reply on ONE line: <name> | <reason in under 12 words>. name = 2-4 English words joined by underscores describing what it does (e.g. copy_pairs, int21_wrapper, nullsub); NEVER a hex number or address, even if unsure.")
def region(hand):
    return [(int(t[0], 16), t[2]) for t in (l.split() for l in open(hand, encoding='utf-8')) if len(t) > 4 and 'region name only' in ' '.join(t)]
REG = {'rt': 'Watcom C runtime', 'sos': 'HMI SOS sound/timer library', 'fp': 'x87 float runtime',
       'frag': 'x87 maths fragment split off a game function'}
BAD = re.compile(r'[0-9a-fA-F]+|(sub|func|fn|unk)_?[0-9a-fA-F]*')
def prompt(x, pre, B, names, callees, strs, callers):
    return ('Region: %s (%s). Callers: %d. Callees: %s. Strings: %s.\nCode:\n%s\nName this function.' %
            (pre, REG.get(pre, 'runtime'), callers[x], ' '.join(callee_names(x, names, callees)) or '-',
             '; '.join(strs[x][:4]) or '-', squeeze(B[x][2], 2500))) + os.environ.get('INK_EXTRA', '')
def parse(r, pre):
    r = r[0] if r else ''
    nm, _, why = r.partition('|'); nm = re.sub(r'\W', '', nm.strip().strip('`'))
    if nm.lower().startswith(pre + '_'): nm = nm[len(pre) + 1:]
    return nm, re.sub(r'\s+', ' ', why.strip())[:80]
class Server:
    def __init__(self, lr): self.lr = lr; self.own, self.port = lr.open_server('inkling')
    def ask(self, u):
        for _ in range(3):
            try: return self.lr.ask(self.port, SYS, u, 120).strip().splitlines()
            except Exception as e:
                print('server lost, reopening:', e, flush=True); self.close(); self.own, self.port = self.lr.open_server('inkling')
        return None
    def close(self):
        if self.own: self.own.kill()
def run(a):
    dc, fi, hand, out = a[:4]
    import localread; localread.THINK = 'low'
    B = blocks(dc); names, callees, strs, callers = info(fi)
    done = {int(l.split('\t')[0], 16) for l in open(out, encoding='utf-8')} if os.path.exists(out) else set()
    srv = Server(localread)
    try:
        f = open(out, 'a', encoding='utf-8')
        for x, old in region(hand):
            if x in done or x not in B: continue
            pre = old.split('_')[0]; r = srv.ask(prompt(x, pre, B, names, callees, strs, callers))
            if r is None: continue
            nm, why = parse(r, pre)
            f.write('0x%x\t%s\t%s\t%s\n' % (x, old, nm, why)); f.flush()
            names[x] = '%s_%s' % (pre, nm) if nm else old
    finally:
        srv.close()
def proposals(out, used):
    new = {}
    for l in open(out, encoding='utf-8'):
        x, old, nm, why = (l.rstrip('\n').split('\t') + [''] * 4)[:4]
        if not ID.match(nm or '') or BAD.fullmatch(nm): continue
        n = '%s_%s' % (old.split('_')[0], nm)
        if n in used: n = '%s_%s' % (n, x[2:])
        if n in used: continue
        used.add(n); new[x] = (n, why)
    return new
def apply(a):
    hand, out = a[2], a[3]
    lines = open(hand, encoding='utf-8').read().splitlines()
    new = proposals(out, {l.split()[2] for l in lines if l.startswith('0x')}); k = 0
    for i, l in enumerate(lines):
        t = l.split()
        if t and t[0] in new and 'region name only' in l:
            n, why = new[t[0]]; lines[i] = '%s func %s hand inkling guess: %s' % (t[0], n, why or '-'); k += 1
    open(hand, 'w', encoding='utf-8').write('\n'.join(lines) + '\n'); print('applied', k, 'of', len(new))
if __name__ == '__main__': (apply if '--apply' in sys.argv else run)([x for x in sys.argv[1:] if x != '--apply'])
