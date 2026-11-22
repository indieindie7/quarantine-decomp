"""xname.py <ghidra dir> <prog base name> : rule-based provisional names for FUN_ functions from funcinfo_<prog>.tsv
-> work/names_<prog>.txt in ApplyNames hand format ("0x<addr> func <name> hand <comment>").
Priority: referenced string (s_<text>) > named callees (api_/lib name of first non-FUN callee) > size/callee-count role. All provisional."""
import sys, os, re, collections
g, prog = sys.argv[1:3]
funcs, cur = collections.OrderedDict(), None
for ln in open(os.path.join(g, 'funcinfo_%s.tsv' % prog), encoding='utf-8', errors='replace'):
    t = ln.rstrip('\n').split(' ', 4) if ln[:2] in ('F ', 'C ', 'S ') else None
    if not t: continue
    if t[0] == 'F':
        cur = t[1]; funcs[cur] = {'name': t[2], 'size': int(t[4]) if len(t) > 4 else 0, 'C': [], 'S': []}
        # t = [F, addr, name, source, size]
    elif cur and t[0] == 'C': funcs[cur]['C'].append(t[1])
    elif cur and t[0] == 'S': funcs[cur]['S'].append(ln[2:].rstrip('\n'))
names = {a: f['name'] for a, f in funcs.items()}
def clean(s):
    s = re.sub(r'[^A-Za-z0-9]+', '_', s).strip('_')
    return s[:28]
out, stats = [], collections.Counter()
for a, f in funcs.items():
    n = f['name']
    if not (n.startswith('FUN_') or n.startswith('thunk_FUN_')): continue
    th = n.startswith('thunk_')
    strs = [clean(s) for s in f['S'] if re.search(r'[A-Za-z]{3}', s)]
    api = [names[c] for c in f['C'] if c in names and not names[c].startswith(('FUN_', 'thunk_FUN_'))]
    nc, size = len(f['C']), f['size']
    if strs: nm, why = 's_%s_%s' % (strs[0], a), 'string'
    elif api: nm, why = 'api_%s_%s' % (clean(api[0]).lstrip('_'), a), 'callee'
    elif th or (size <= 12 and nc <= 1): nm, why = 'thunk_%s' % a, 'size'
    elif nc == 0 and size <= 40: nm, why = 'leaf_small_%s' % a, 'size'
    elif nc == 0: nm, why = 'leaf_%s' % a, 'size'
    elif nc >= 10: nm, why = 'proc_big_%s' % a, 'size'
    elif size >= 400: nm, why = 'proc_long_%s' % a, 'size'
    else: nm, why = 'proc_%s' % a, 'size'
    stats[why] += 1
    out.append('0x%s func %s hand provisional %s name: %d bytes, %d callees' % (a, nm, why, size, nc))
open(os.path.join(g, 'work', 'names_%s.txt' % prog), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print(prog, len(out), dict(stats))
