"""Quarantine port: areas (the 6 city maps) as editable units.
usage: areas.py export [CITY..]   port/data/<CITY>.json -> port/areas/<CITY>.txt (editable cell grid, main.gd loads it over the JSON cells) + <CITY>_overview.png (top-down, 16 px per cell, grid labels every 8 cells)
       areas.py overview [CITY..] redraw the overview from the (edited) .txt
       areas.py set <CITY> <cx> <cy> <hex4>   edit one cell
       areas.py split <CITY> [cols rows]   cut the map into area scenes: port/areas/<CITY>/areas.json (name -> [ox, oy, w, h], edit to move borders, then split again) + <name>.txt + <name>.tscn + port/areas/<CITY>.tscn (map scene instancing every area). main.gd loads the map scene when present (--noarea off, --area=NAME one area only)
Cell = 4 hex digits of the .MAP u16: bits 0-6 = block number (0 = empty, N = BLK file block N-1), bits 8-9 = texture set, other bits = flags (unread). '....' = 0000."""
import sys, os, json
from PIL import Image, ImageDraw
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'port')
ALL = ['CITY', 'JCITY', 'KCITY', 'PCITY', 'SCITY', 'WCITY']
def rd(city):
    w = h = 0; cells = []
    for l in open(f'{R}/areas/{city}.txt'):
        t = l.split()
        if not t or t[0].startswith('#'): continue
        if t[0] == 'area': w, h = int(t[2]), int(t[3]); continue
        cells += [0 if x == '....' else int(x, 16) for x in t]
    assert len(cells) == w * h, (city, len(cells), w, h)
    return w, h, cells
def wr(city, w, h, cells):
    with open(f'{R}/areas/{city}.txt', 'w', newline='\n') as f:
        f.write(f'# Quarantine area {city}: {w} x {h} cells of 512 units, row 0 = y 0. Cell = 4 hex digits: bits 0-6 block (00 = empty, N = block N-1), bits 8-9 texture set, rest flags. .... = empty.\narea {city} {w} {h}\n')
        for y in range(h): f.write(' '.join('....' if c == 0 else '%04x' % c for c in cells[y * w:y * w + w]) + '\n')
def overview(city, w, h, cells):
    d = json.load(open(f'{R}/data/{city}.json')); fl = Image.open(f'{R}/data/{city}_floor.png').convert('RGB'); S = 16
    avg = [fl.crop((t % 5 * 64, t // 5 * 64, t % 5 * 64 + 64, t // 5 * 64 + 64)).resize((1, 1), Image.BOX).getpixel((0, 0)) for t in range(15)]
    im = Image.new('RGB', (w * S, h * S), (0, 0, 0)); dr = ImageDraw.Draw(im)
    for cy in range(h):
        for cx in range(w):
            c = cells[cy * w + cx]; bi = (c & 0x7f) - 1
            if bi < 0 or bi >= len(d['blocks']): continue
            b = d['blocks'][bi]; st = (c >> 8) & 3; ox = cx * S; oy = cy * S; k = S / 512.0
            for q in sorted(b['q'], key=lambda q: -q[3]):
                p = [(ox + q[5 + v * 2] * k, oy + q[6 + v * 2] * k) for v in range(4)]; dr.polygon(p, fill=avg[q[1][st] % 15])
            for wl in b['w']:
                n, dx, dy, hh, px, py = wl[:6]; dr.line((ox + px * k, oy + py * k, ox + (px + dx * n) * k, oy + (py + dy * n) * k), fill=(255, 255, 255) if hh > 100 else (150, 150, 150))
    for x in range(0, w, 8): dr.line((x * S, 0, x * S, h * S), fill=(255, 0, 0)); dr.text((x * S + 2, 1), str(x), fill=(255, 255, 0))
    for y in range(0, h, 8): dr.line((0, y * S, w * S, y * S), fill=(255, 0, 0)); dr.text((2, y * S + 1), str(y), fill=(255, 255, 0))
    im.save(f'{R}/areas/{city}_overview.png')
NL = chr(10)
def split(city, cols=8, rows=2):
    w, h, cells = rd(city); D = f'{R}/areas/{city}'; os.makedirs(D, exist_ok=True); J = f'{D}/areas.json'
    if os.path.exists(J): ar = json.load(open(J))
    else:
        ar = {}; xs = [round(i * w / cols) for i in range(cols + 1)]; ys = [round(i * h / rows) for i in range(rows + 1)]
        for j in range(rows):
            for i in range(cols):
                if any(cells[y * w + x] for y in range(ys[j], ys[j + 1]) for x in range(xs[i], xs[i + 1])): ar['%s%d' % (chr(65 + i), j + 1)] = [xs[i], ys[j], xs[i + 1] - xs[i], ys[j + 1] - ys[j]]
        json.dump(ar, open(J, 'w'), indent=1)
    own = [None] * (w * h)
    for n, (ox, oy, aw, ah) in ar.items():
        for y in range(oy, oy + ah):
            for x in range(ox, ox + aw):
                assert own[y * w + x] is None, ('areas overlap', n, own[y * w + x], x, y); own[y * w + x] = n
        with open(f'{D}/{n}.txt', 'w', newline='\n') as f:
            f.write(f'# Quarantine {city} area {n}: {aw} x {ah} cells at map cell ({ox},{oy}). Cell = 4 hex digits: bits 0-6 block (00 = empty), bits 8-9 texture set, rest flags. .... = empty.\narea {n} {aw} {ah} {ox} {oy}\n')
            for y in range(oy, oy + ah): f.write(' '.join('....' if c == 0 else '%04x' % c for c in cells[y * w + ox:y * w + ox + aw]) + '\n')
        ex = [('Script', 'res://areas/area.gd')]; nodes = ''
        for nm in ('walls', 'objs'):
            if os.path.exists(f'{D}/{n}_{nm}.res') and os.path.exists(f'{D}/_{nm}_preview.res'):
                ex += [('ArrayMesh', f'res://areas/{city}/{n}_{nm}.res'), ('ShaderMaterial', f'res://areas/{city}/_{nm}_preview.res')]
                nodes += f'{NL}[node name="{nm}" type="MeshInstance3D" parent="."]{NL}mesh = ExtResource("{len(ex) - 1}"){NL}material_override = ExtResource("{len(ex)}"){NL}extra_cull_margin = 16384.0{NL}'
        open(f'{D}/{n}.tscn', 'w', newline=NL).write(f'[gd_scene load_steps={len(ex) + 1} format=3]{NL}{NL}' + ''.join(f'[ext_resource type="{t}" path="{q}" id="{k + 1}"]{NL}' for k, (t, q) in enumerate(ex)) + f'{NL}[node name="{n}" type="Node3D"]{NL}script = ExtResource("1"){NL}city = "{city}"{NL}cells_file = "res://areas/{city}/{n}.txt"{NL}' + nodes)
    lost = sum(1 for k, c in enumerate(cells) if c and own[k] is None)
    t = f'[gd_scene load_steps={len(ar) + 1} format=3]\n\n' + ''.join(f'[ext_resource type="PackedScene" path="res://areas/{city}/{n}.tscn" id="{k + 1}"]\n' for k, n in enumerate(ar)) + f'\n[node name="{city}" type="Node3D"]\n' + ''.join(f'\n[node name="{n}" parent="." instance=ExtResource("{k + 1}")]\n' for k, n in enumerate(ar))
    open(f'{R}/areas/{city}.tscn', 'w', newline='\n').write(t)
    im = Image.open(f'{R}/areas/{city}_overview.png').convert('RGB'); dr = ImageDraw.Draw(im)
    for n, (ox, oy, aw, ah) in ar.items(): dr.rectangle((ox * 16, oy * 16, (ox + aw) * 16 - 1, (oy + ah) * 16 - 1), outline=(0, 255, 0), width=3); dr.text((ox * 16 + 8, oy * 16 + 14), n, fill=(0, 255, 0))
    im.save(f'{D}/areas_overview.png'); print(city, len(ar), 'areas, used cells outside every area:', lost)
if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'bake':  # split, run the port once with --bake (saves meshes + preview materials), split again so the scenes hold the meshes (visible in the Godot editor)
        import subprocess, re
        G = eval(re.search(r'^GODOT'+chr(92)+'s*='+chr(92)+'s*(.+)$', open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'parity.py'), encoding='utf-8').read(), re.M).group(1))
        for c in sys.argv[2:]:
            split(c); si = subprocess.STARTUPINFO(); si.dwFlags |= subprocess.STARTF_USESHOWWINDOW; si.wShowWindow = 7
            r = subprocess.run([G, '--path', '.', '--', f'--city={c}', '--bg', '--nofps', '--bake', '--frames=6', '--shot=' + os.path.abspath(f'{R}/shots/_bake.png')], cwd=R, startupinfo=si, capture_output=True, text=True)
            print(''.join(l + NL for l in (r.stdout + r.stderr).split(NL) if 'baked' in l or 'ERROR' in l)[:600]); split(c)
        sys.exit()
    if cmd == 'split': split(sys.argv[2], *map(int, sys.argv[3:5])); sys.exit()
    if cmd == 'set':
        w, h, c = rd(sys.argv[2]); c[int(sys.argv[4]) * w + int(sys.argv[3])] = int(sys.argv[5], 16); wr(sys.argv[2], w, h, c); overview(sys.argv[2], w, h, c)
    else:
        for city in sys.argv[2:] or ALL:
            if cmd == 'export': d = json.load(open(f'{R}/data/{city}.json')); wr(city, d['w'], d['h'], [int(x) for x in d['cells']])
            w, h, c = rd(city); overview(city, w, h, c); print(city, w, h, sum(1 for x in c if x), 'cells used')
