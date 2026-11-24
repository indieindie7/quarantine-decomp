"""fdigest.py <decomp.c> <funcinfo.tsv> <hand.txt> [start=0] [n=80] [all] [code=<chars>] : one digest line per function that still has a
provisional name (proc_/leaf_/thunk_/s_/caseD_/FUN_) and is not in <hand.txt> (11-23, for the hand-naming batches).
Line: addr size cr=<callers> sig | c: callees | s: strings | g: globals by use count | k: code hints."""
import sys, re, collections
PROV = re.compile(r'^(proc|leaf|thunk|s|caseD|FUN|fn|unk)_')
def blocks(path):
    out, cur = {}, None
    for ln in open(path, encoding='utf-8', errors='replace'):
        m = re.match(r'// ==== (\S+) @ ([0-9a-f]+) size=(\d+)', ln)
        if m: cur = int(m.group(2), 16); out[cur] = [m.group(1), int(m.group(3)), []]
        elif cur is not None: out[cur][2].append(ln)
    return out
def info(path):
    names, callees, strs, callers, cur = {}, collections.defaultdict(list), collections.defaultdict(list), collections.Counter(), None
    for ln in open(path, encoding='utf-8', errors='replace'):
        t = ln.rstrip('\n').split(' ', 4)
        if t[0] == 'F' and len(t) > 2: cur = int(t[1], 16); names[cur] = t[2]
        elif t[0] == 'C' and cur is not None and len(t) > 1: callees[cur].append(int(t[1], 16)); callers[int(t[1], 16)] += 1
        elif t[0] == 'S' and cur is not None: strs[cur].append(ln[2:].strip()[:40])
    return names, callees, strs, callers
def hints(body):
    s = ''.join(body); k = []
    for word, pat in (('loop', r'\b(while|for|do)\b'), ('port', r'\b(in|out)[bwd]?\(|\bout\('), ('int', r'swi\(|int\('), ('float', r'\bfloat\b|ROUND\('),
                      ('switch', r'\bswitch\b'), ('ptrcall', r'\(\*\*?\(code')):
        n = len(re.findall(pat, s))
        if n: k.append('%s%d' % (word, n))
    g = collections.Counter(re.findall(r'DAT_000([0-9a-f]{5})', s)).most_common(6)
    sig = next((l.strip() for l in body if re.match(r'^\w[\w \*]*\(.*\)\s*$', l)), '')
    sig = re.sub(r'undefined', 'u', re.sub(r'\w+_[0-9a-f]{8}', 'f', sig))[:50]
    cons = collections.Counter(re.findall(r'\b0x[0-9a-f]{2,5}\b', s)).most_common(4)
    return sig, ' '.join('%s*%d' % x for x in g), ' '.join(k) + ' n:' + ','.join(c for c, _ in cons)
def squeeze(body, cap):
    """decompiled body without declarations/comments, whitespace collapsed, globals shortened, cut to cap chars"""
    keep = [l.strip() for l in body if l.strip() and not l.lstrip().startswith(('/*', '//')) and not re.match(r'^\s+[\w \*]+ \**\w+(\s*\[\d+\])*;$', l)]
    t = re.sub(r'DAT_000', 'g', ' '.join(keep)); t = re.sub(r'\(undefined\d? \*\)|\(int\)|\(short\)|\(uint\)|\(ushort\)', '', t)
    return t if len(t) <= cap else t[:cap * 2 // 3] + ' ... ' + t[-cap // 3:]
def callee_names(x, names, callees):
    cs = []
    for c in callees[x]:
        cn = names.get(c, '%x' % c); cn = cn if not PROV.match(cn) else '%x' % c
        if cn not in cs: cs.append(cn)
    return cs[:7]
def main(a):
    bl = blocks(a[0]); names, callees, strs, callers = info(a[1])
    done = {int(l.split()[0], 16) for l in open(a[2], encoding='utf-8') if l.startswith('0x')}
    todo = [x for x in sorted(names) if (PROV.match(names[x]) or 'all' in a) and x not in done]
    st = int(a[3]) if len(a) > 3 else 0; n = int(a[4]) if len(a) > 4 else 80
    cap = next((int(v[5:]) for v in a if v.startswith('code=')), 0)
    print('# todo', len(todo), 'showing', st, st + n)
    for x in todo[st:st + n]:
        nm, size, body = bl.get(x, [names[x], 0, []]); sig, g, k = hints(body)
        head = '%x %d cr%d | c: %s | s: %s' % (x, size, callers[x], ' '.join(callee_names(x, names, callees)), '; '.join(strs[x][:2]))
        print((head + ' || ' + squeeze(body, cap)) if cap else ('%s | %s | g: %s | k: %s' % (head, sig, g, k))[:260])
if __name__ == '__main__': main(sys.argv[1:])
