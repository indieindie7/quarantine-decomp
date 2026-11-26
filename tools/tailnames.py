"""tailnames.py <hand.txt> <tail_start_hex> [addr=name ...] : reads fdigest light lines on stdin; every listed function at or
above tail_start gets a name: the given addr=name pairs first (read from the digest by hand, comment 'runtime, from
digest strings'), else <prefix>_<addr> where prefix = prefix of the nearest hand-named function below it (rt/sos/fp/...),
comment 'region name only, not studied'. Generic version of rtnames.py (11-25, Quarantine II RWCD runtime tail)."""
import sys, bisect
def named(hand):
    pts = []
    for ln in open(hand, encoding='utf-8'):
        t = ln.split()
        if ln.startswith('0x') and len(t) > 2: pts.append((int(t[0], 16), t[2].split('_')[0] or 'rt'))
    return sorted(pts)
def line(x, known, pts, keys):
    if x in known: return '0x%x func %s hand runtime, from digest strings' % (x, known[x])
    i = bisect.bisect_left(keys, x) - 1; pre = pts[i][1] if i >= 0 else 'rt'
    return '0x%x func %s_%x hand region name only, not studied' % (x, pre, x)
def stdin_addrs(start):
    rows = [ln.split() for ln in sys.stdin]
    return [x for x in (int(t[0], 16) for t in rows if t and t[0] != '#') if x >= start]
def main(a):
    hand, start = a[0], int(a[1], 16); known = dict((int(k, 16), v) for k, v in (x.split('=') for x in a[2:]))
    pts = named(hand); keys = [p[0] for p in pts]
    out = [line(x, known, pts, keys) for x in stdin_addrs(start)]
    open(hand, 'a', encoding='utf-8').write(''.join(l + '\n' for l in out)); print('added', len(out), 'known', len(known))
if __name__ == '__main__': main(sys.argv[1:])
