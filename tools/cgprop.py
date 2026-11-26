"""cgprop.py <funcinfoA.tsv> <funcinfoB.tsv> <handB.txt> [rounds=6] : call-graph name propagation (11-25, Q1 -> Q2).
For every B function whose hand line says 'from Q1 <name>', compare the ordered callee lists with the A function of that
name. Same length -> pair callees by position; a pair counts when the A callee has a real name, the B callee is still
provisional and the sizes are within 35 %. A pair needs 2 votes (a parent with >= 2 callees gives 2, else 1) and no tie.
New lines go to handB as 'hand from Q1 <name> (callgraph rN)'. Repeats until no new pair."""
import sys, re, collections
PROV = re.compile(r'^(proc|leaf|thunk|s|caseD|FUN)_')
def load(p):
    names, size, callees, cur = {}, {}, collections.defaultdict(list), None
    for ln in open(p, encoding='utf-8', errors='replace'):
        t = ln.rstrip('\n').split(' ')
        if t[0] == 'F' and len(t) > 4: cur = int(t[1], 16); names[cur] = t[2]; size[cur] = int(t[4])
        elif t[0] == 'C' and cur is not None: callees[cur].append(int(t[1], 16))
    return names, size, callees
def base(n): return re.sub(r'_[0-9a-f]{5,8}$', '', n)
def seed(hand, byname):
    pair, used = {}, set()
    for ln in open(hand, encoding='utf-8'):
        t = ln.split()
        if not ln.startswith('0x') or len(t) < 3: continue
        used.add(t[2])
        if len(t) > 6 and t[4:6] == ['from', 'Q1'] and t[6] in byname: pair[int(t[0], 16)] = byname[t[6]]
    return pair, used
def close(sa, sb): return sa and abs(sa - sb) <= 0.35 * max(sa, sb)
def vote(A, B, pair, takenA):
    (nA, sA, cA), (nB, sB, cB) = A, B; votes = collections.defaultdict(collections.Counter)
    for b, x in pair.items():
        la, lb = cA[x], cB[b]
        if len(la) != len(lb): continue
        w = 2 if len(la) >= 2 else 1
        for ca, cb in zip(la, lb):
            ok = cb not in pair and ca not in takenA and not PROV.match(nA.get(ca, 'FUN_')) and PROV.match(nB.get(cb, 'x'))
            if ok and close(sA.get(ca), sB.get(cb, 0)): votes[cb][ca] += w
    return votes
def pick(cnt):
    top = cnt.most_common(2)
    return None if top[0][1] < 2 or len(top) > 1 and top[1][1] == top[0][1] else top[0][0]
def one_round(A, B, pair, takenA, used, out, r):
    new = 0
    for cb, cnt in vote(A, B, pair, takenA).items():
        ca = pick(cnt)
        if ca is None or ca in takenA: continue
        nm = base(A[0][ca]); nm = nm if '_' in nm and nm not in used else '%s_%x' % (nm, cb)
        pair[cb] = ca; takenA.add(ca); used.add(nm); new += 1
        out.append('0x%x func %s hand from Q1 %s (callgraph r%d)' % (cb, nm, A[0][ca], r))
    return new
def main(a):
    A, B, hand = load(a[0]), load(a[1]), a[2]; rounds = int(a[3]) if len(a) > 3 else 6
    byname = {n: x for x, n in A[0].items() if not PROV.match(n)}
    pair, used = seed(hand, byname); takenA = set(pair.values()); out = []
    for r in range(rounds):
        new = one_round(A, B, pair, takenA, used, out, r); print('round', r, 'new', new)
        if not new: break
    open(hand, 'a', encoding='utf-8').write(''.join(l + '\n' for l in out)); print('added', len(out))
if __name__ == '__main__': main(sys.argv[1:])
