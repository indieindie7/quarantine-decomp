"""misdec.py [dir=dos/Quarantine] [out=decoded/missions.json] : Quarantine MISSIL<city>.IMG are TEXT, not images (11-23).
Reader = Q.EXE 0x4bd08 ("missil%d.img", city = 0x836c8 >> 16): skips to the n-th line starting with ':', then reads numbers
separated by ',' up to the next ':'. First number -> 0x8368c; the rest -> u16 array at 0x82ef0 (first four copied to
0x836b2, 0x836ac, 0x836b0, 0x836a6).
Fields from the engine code (11-23, decomp_q.c 42601-43260): first = 0x8368c mission timer (reset 0x3c elsewhere, warnings below
0x14); box = zone in map cells x0, x1, y0, y1 (player cell 0x83616 tested inside it, 43038); rest_head[0] = 0x82ef8 -> 0x83698
(500/1000, reward: provisional); rest_head[1] = 0x82efa count (spawn loop 42980 / 43172; with no rows = a plain count);
rows9 = x cell, y cell (pos = cell * 0x200 + 0x100), type (0x835dc, spawner 0x16adc), byte -> ent +0x7fa36, heading degrees
-> 0x7fa1a, two words -> 0x7fa2c / 0x7fa2e, word -> 0x7fa16 (100: provisional health), word -> 0x7fa1e (20/24: unknown)."""
import sys, os, json, re, glob
src = sys.argv[1] if len(sys.argv) > 1 else 'dos/Quarantine'; out = sys.argv[2] if len(sys.argv) > 2 else 'decoded/missions.json'
res = {}
for f in sorted(glob.glob(os.path.join(src, 'MISSIL[0-9].IMG'))):
    recs = []
    for r in open(f, 'rb').read().decode('latin1').split(':')[1:]:
        v = [int(x) for x in re.findall(r'-?\d+', r)]
        if not v: continue
        m = {'first': v[0], 'box': v[1:5], 'rest_head': [], 'rows9': []}
        t = v[5:]
        # trailing groups of 9 = spawn rows (x, y, a, b, heading, c, d, e, f); the count before them says how many
        for i in range(len(t)):
            if (len(t) - i - 1) % 9 == 0 and t[i] == (len(t) - i - 1) // 9 and t[i] > 0:
                m['rest_head'] = t[:i + 1]; m['rows9'] = [t[i + 1 + 9 * k:i + 10 + 9 * k] for k in range(t[i])]; break
        else: m['rest_head'] = t
        recs.append(m)
    res[os.path.basename(f)] = recs
os.makedirs(os.path.dirname(out) or '.', exist_ok=True); json.dump(res, open(out, 'w'), indent=1)
for k, v in res.items(): print(k, len(v), 'records,', sum(len(m['rows9']) for m in v), 'spawn rows,', sum(1 for m in v if m['rows9']), 'with rows')
