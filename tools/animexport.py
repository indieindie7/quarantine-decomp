"""animexport.py: animated wall textures -> port/data/<CITY>_anim.json {"from": [[tile, file]], "frames": [[[tile, file], ...]], "speed": [mask]}.
Source: TEXTURE<n>.DAT flag & 4 in scan order (file 0-14, tile 0-11) = anim id k (Q.EXE 0x89358), ANIM<n>.DAT line k = `sSS:ff,tt` x 10, file 99 = end (loader 0x3c400).
DOS state byte 0x893b2[k] = index into frames (step 0x3c5cc). NOTES '11-23 ANIMATED WALLS'."""
import os, re, json
T = os.path.dirname(os.path.abspath(__file__)); G = os.path.join(T, '..', 'dos', 'Quarantine'); OUT = os.path.join(T, '..', 'port', 'data')
def flagged(n):
    rows = open(os.path.join(G, 'TEXTURE%d.DAT' % n), 'rb').read().replace(b'\r', b'').split(b'\n')[:15]
    return [[t, f] for f, r in enumerate(rows) for t in range(12) if int(chr(r[t]), 16) & 4]
def anims(n):
    out = []
    for line in open(os.path.join(G, 'ANIM%d.DAT' % n), 'r', errors='replace').read().split('s')[1:]:
        fr = [[int(t), int(f)] for f, t in re.findall(r':(\d+),(\d+)', line)]
        out.append((int(line[:2]), fr[:next((i for i, v in enumerate(fr) if v[1] == 99), len(fr))]))
    return out
for n, city in enumerate(['CITY', 'KCITY', 'PCITY', 'JCITY', 'WCITY', 'SCITY']):
    if not os.path.exists(os.path.join(G, 'ANIM%d.DAT' % n)): print(city, 'no ANIM file'); continue
    F = flagged(n); A = anims(n); k = min(len(F), len(A))
    json.dump({'from': F[:k], 'frames': [a[1] for a in A[:k]], 'speed': [a[0] for a in A[:k]]}, open(os.path.join(OUT, city + '_anim.json'), 'w'), separators=(',', ':'))
    print(city, 'flagged', len(F), 'anim lines', len(A), 'first frame == flagged tile:', sum(1 for i in range(k) if A[i][1] and A[i][1][0] == F[i]), 'of', k)
