"""bspdec.py <file.BSP|dir> : Quarantine II DOS maps\\<area>.BSP check (11-25). Written by bsp_Make 0x492f0 (maps_Load 0x4d2d0,
one tree per map block that has items, empty sets write nothing). Per set of n items: u8 splitter index (< n; == n means no item splits cleanly: leaf, nothing follows), node values as
big-endian i32 (wall item kind 0: px, py, nx, ny; floor kind 2: z; other kinds: none), then one side byte per other item
(01 = front, FF = back), then the back set, then the front set. The file has no counts, so this parser searches: root n is
taken from the run of side bytes (longest first, backtracking), node kind by trial (positions |v| < 2^16, normals 2.30 fixed). Prints trees, sets,
node kinds and whether the whole file is consumed."""
import sys, os, glob, struct
sys.setrecursionlimit(100000)
def node(d, p, size, n):
    """values + side bytes for one node kind, or None if they do not fit"""
    if p + size + n - 1 > len(d): return None
    vals = struct.unpack_from('>%di' % (size // 4), d, p)
    if any(abs(v) >= 1 << 26 for v in vals[:2]): return None  # positions / z (wall values fixed point); normals unchecked
    sides = d[p + size:p + size + n - 1]
    if any(c not in (1, 255) for c in sides): return None
    return sides.count(255)
def ends(d, o, n, memo):
    """all offsets where a set of n items starting at o can end (memoized; a floor and a wall reading can both fit)"""
    if n == 0: return (o,)
    if (o, n) in memo: return memo[o, n]
    out = {o + 1} if o < len(d) and d[o] == n else set()  # no splitter found (every item cuts another): count byte = n, leaf
    if o < len(d) and d[o] < n:
        for size in (4, 16, 0):
            back = node(d, o + 1, size, n)
            if back is None: continue
            for q in ends(d, o + size + n, back, memo):
                out.update(ends(d, q, n - 1 - back, memo))
    memo[o, n] = tuple(sorted(out)); return memo[o, n]
def kinds(d, o, n, end, memo, st):
    """walk one valid reading that ends at end and count node kinds"""
    if n == 0: return True
    if d[o] == n and end == o + 1: st['leafn'] = st.get('leafn', 0) + 1; return True
    for size, kind in ((4, 'f'), (16, 'w'), (0, 'x')):
        back = node(d, o + 1, size, n)
        if back is None: continue
        for q in ends(d, o + size + n, back, memo):
            if end in ends(d, q, n - 1 - back, memo):
                st[kind] = st.get(kind, 0) + 1
                return kinds(d, o + size + n, back, q, memo, st) and kinds(d, q, n - 1 - back, end, memo, st)
    return False
def parse(d, o, n, st, memo=None):
    memo = {} if memo is None else memo; e = ends(d, o, n, memo)
    if not e: return None
    kinds(d, o, n, e[-1], memo, st); st['sets'] = sum(v for k, v in st.items() if k != 'sets'); return e[-1]
def roots(d, o, memo):
    """(n, end) for every tree that can start at o; n is bounded by the side-byte run after a 4- or 16-byte node"""
    out = []
    for size in (4, 16, 0):
        p, run = o + 1 + size, 0
        while p + run < len(d) and d[p + run] in (1, 255): run += 1
        for n in range(1, run + 2):
            if d[o] == n: out.append((n, o + 1))
            out += [(n, e) for e in ends(d, o, n, memo)]
    return set(out)
def trees(d):
    """search the tree sequence that reaches the file end; returns ([(n, kinds)], last offset reached)"""
    memo, prev, todo = {}, {0: None}, [0]
    while todo:
        o = min(todo); todo.remove(o)
        if o == len(d): break
        for n, e in roots(d, o, memo):
            if e not in prev: prev[e] = (o, n); todo.append(e)
    if len(d) not in prev: return [], max(prev)
    out, e = [], len(d)
    while prev[e]:
        o, n = prev[e]; st = {}; kinds(d, o, n, e, memo, st); out.append((n, st)); e = o
    return out[::-1], len(d)
def main(a):
    fs = sorted(glob.glob(os.path.join(a[0], '*.BS?'))) if os.path.isdir(a[0]) else [a[0]]
    for f in fs:
        d = open(f, 'rb').read(); t, end = trees(d)
        k = {}
        for _, st in t:
            for x, v in st.items(): k[x] = k.get(x, 0) + v
        print(os.path.basename(f), len(d), 'trees', len(t), 'items', sum(n for n, _ in t), k, 'consumed' if end == len(d) else 'STOP at %d' % end)
if __name__ == '__main__': main(sys.argv[1:])
