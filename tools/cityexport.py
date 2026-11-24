"""Quarantine DOS city -> port/data/<CITY>.json + <CITY>_walls.png (atlas 16 cols x 16 rows of 64x64; rows 0-14 = WALLn.SPR tiles, row 15 = 15 floor tiles cut from <pre>FLOOR.IMG like Q.EXE 0x3aaa0). Quad tile = tex[i][1] & 15 (0x46ec4 -> 0x47d10).."""
import sys, json, os, struct
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blkdec import rd_map, rd_blk, rd_spr
PRE = {'CITY': '', 'JCITY': 'J', 'KCITY': 'K', 'PCITY': 'P', 'SCITY': 'S', 'WCITY': 'W'}
DEC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'decoded', 'dos')
def s8(b): return b - 256 if b > 127 else b
SHMAP = [0] * 16 + [1] * 12 + [2] * 6 + [3] * 4 + [4] * 3 + [5] * 3 + [6, 6, 7, 7, 7, 7, 8, 8, 9, 9, 10, 11, 12, 13, 13, 14, 14, 15, 15, 15]  # Q.EXE 0x7943a
def shade_luts(d6, live):
    """64 rows x 256: distance shade LUTs (Q.EXE 0x3a3c4, fog black). Live dump <CITY>_shade.bin (16x256) wins when present; else rebuilt (equal-distance ties may differ: k-d order 0x3c12c not ported)."""
    if os.path.exists(live): l = open(live, 'rb').read(); luts = [l[i * 256:i * 256 + 256] for i in range(16)]
    else:
        c = [tuple(d6[i * 3:i * 3 + 3]) for i in range(256)]; order = sorted(range(1, 256), key=lambda i: c[i][1]); luts = []
        for L in range(16):
            row = bytearray()
            for r, gg, b in c:
                t = (r + ((-r * L) >> 4), gg + ((-gg * L) >> 4), b + ((-b * L) >> 4))
                row.append(min(order, key=lambda i: (c[i][0] - t[0]) ** 2 + (c[i][1] - t[1]) ** 2 + (c[i][2] - t[2]) ** 2))
            luts.append(bytes(row))
    return b''.join(luts[m] for m in SHMAP)
def export(g, city, out):
    pre = PRE[city]
    pal = open(f'{g}/{pre}FLOOR.IMG', 'rb').read()[13:781]
    atlas = Image.new('P', (1024, 1024)); atlas.putpalette(pal)
    for f in range(15):
        p = f'{g}/{pre}WALL{f + 1}.SPR'
        if not os.path.exists(p): continue
        sp, _ = rd_spr(p)
        for t, (w, h, px) in enumerate(sp[:16]):
            atlas.paste(Image.frombytes('P', (w, h), px), (t * 64, f * 64))
    key = Image.frombytes('L', atlas.size, atlas.tobytes().translate(bytes([0] + [255] * 255)))
    aidx = Image.frombytes('L', atlas.size, atlas.tobytes())  # palette-index atlas for the shade LUT shader
    atlas = atlas.convert('RGBA'); atlas.putalpha(key)
    import imgdec; fl = imgdec.load(f'{g}/{pre}FLOOR.IMG').convert('RGB')  # decode fresh (a stale decoded PNG had the old off-by-one palette)
    for t in range(15): atlas.paste(fl.convert('RGBA').crop((t % 5 * 64, t // 5 * 64, t % 5 * 64 + 64, t // 5 * 64 + 64)), (t * 64, 960))
    atlas.save(f'{out}/{city}_walls.png')
    fl.save(f'{out}/{city}_floor.png')
    flp = imgdec.load(f'{g}/{pre}FLOOR.IMG'); assert flp.mode == 'P', flp.mode
    fli = Image.frombytes('L', flp.size, flp.tobytes())
    for t in range(15): aidx.paste(fli.crop((t % 5 * 64, t // 5 * 64, t % 5 * 64 + 64, t // 5 * 64 + 64)), (t * 64, 960))
    aidx.save(f'{out}/{city}_walls_idx.png')
    d6 = [v >> 2 for v in pal]; Image.frombytes('RGB', (256, 1), bytes((v << 2) | (v >> 4) for v in d6)).save(f'{out}/{city}_pal.png')  # 6-bit DAC as DOSBox shows it
    Image.frombytes('L', (256, 64), shade_luts(d6, f'{out}/{city}_shade.bin')).save(f'{out}/{city}_shade.png')
    if os.path.exists(f'{g}/{pre}SKY.IMG'): imgdec.load(f'{g}/{pre}SKY.IMG').convert('RGB').save(f'{out}/{city}_sky.png')  # 320x200 backdrop, row = screen row
    cab = imgdec.load(f'{g}/CAB.IMG'); cab.putpalette(bytes((v << 2) | (v >> 4) for v in d6)); ck = Image.frombytes('L', cab.size, cab.tobytes().translate(bytes([0] + [255] * 255))); cab = cab.convert('RGBA'); cab.putalpha(ck); cab.save(f'{out}/{city}_cab.png')  # cockpit frame, index 0 = view window (rows 37..149), city palette
    wsp, _ = rd_spr(f'{g}/WHEELSPR.SPR'); wsh = Image.new('P', (140, 47 * len(wsp))); wsh.putpalette(bytes((v << 2) | (v >> 4) for v in d6))  # steering wheel + hands, 7 frames 140x47 stored as 4 mode-X planes (plane p = columns p, p+4, ..); frame 3 = straight, drawn at 89,153 (matched on DOS shot q_044, err 3.9)
    for f, (sw, sh, px) in enumerate(wsp):
        pl = [Image.frombytes('P', (sw // 4, sh), px[k * (sw // 4) * sh:(k + 1) * (sw // 4) * sh]) for k in range(4)]; fr = Image.new('P', (sw, sh))
        for x in range(sw): fr.paste(pl[x & 3].crop((x >> 2, 0, (x >> 2) + 1, sh)), (x, 0))
        wsh.paste(fr, (0, f * 47))
    wk = Image.frombytes('L', wsh.size, wsh.tobytes().translate(bytes([0] + [255] * 255))); wsh = wsh.convert('RGBA'); wsh.putalpha(wk); wsh.save(f'{out}/{city}_wheel.png')
    fsp, _ = rd_spr(f'{g}/CABFONT.SPR'); fsh = Image.new('RGBA', (16 * 24, 11 * 16))  # dash font, 170 glyphs, 4 mode-X planes like the wheel, opaque blocks; glyph n at cell (n % 16, n // 16) of 24x16; 0-9 digits, 10 ':', 11 '$' (matched on DOS shot q_048)
    for n, (sw, sh, px) in enumerate(fsp):
        if sw % 4 or sw > 24 or sh > 16 or len(px) < sw * sh: continue
        fr = Image.new('P', (sw, sh)); fr.putpalette(bytes((v << 2) | (v >> 4) for v in d6))
        for x in range(sw): fr.paste(Image.frombytes('P', (1, sh), bytes(px[(x & 3) * (sw // 4) * sh + yy * (sw // 4) + (x >> 2)] for yy in range(sh))), (x, 0))
        fsh.paste(fr.convert('RGBA'), (n % 16 * 24, n // 16 * 16))
    fsh.save(f'{out}/{city}_font.png'); json.dump([[sw, sh] for sw, sh, _ in fsp], open(f'{out}/cabfont.json', 'w'))
    for sn, on in (('RADAR2', 'radar'), ('WAYP2', 'wayp'), ('FONT2', 'font2')):  # one row atlas <city>_<on>.png + <SN lower>.json [x, w, h], 4 mode-X planes. RADAR2 = set [0x830f8]: 0xb radar frame at 176,3, 0xa centre dot at 197,16, 8/9/10 blips, [0x82348] car icon at 240,5 (decomp 25221-25250, 25736). WAYP2 = set [0x7f388] (load decomp 23342): fare panel arrows 0-7 lit / 8-15 dark, 0x15 '.', 0x16+d digits (0x34a44). FONT2 = fare status text 'FOR HIRE' (set [0x83114], glyph = ASCII - 32, indices 34/36/41 on 0)
        rsp, _ = rd_spr(f'{g}/{sn}.SPR'); rx = 0; rj = []
        rsh = Image.new('RGBA', (sum(max(sw, 1) for sw, sh, _ in rsp), max(sh for sw, sh, _ in rsp)), (0, 0, 0, 0))
        for sw, sh, px in rsp:
            rj.append([rx, sw, sh])
            if sw % 4 == 0 and len(px) >= sw * sh:
                fr = Image.new('P', (sw, sh)); fr.putpalette(bytes((v << 2) | (v >> 4) for v in d6))
                for x in range(sw): fr.paste(Image.frombytes('P', (1, sh), bytes(px[(x & 3) * (sw // 4) * sh + yy * (sw // 4) + (x >> 2)] for yy in range(sh))), (x, 0))
                rsh.paste(fr.convert('RGBA'), (rx, 0))
            rx += max(sw, 1)
        rsh.save(f'{out}/{city}_{on}.png'); json.dump(rj, open(f'{out}/{sn.lower()}.json', 'w'))
    bsp, _ = rd_spr(f'{g}/BFONT1.SPR'); bsh = Image.new('RGBA', (118 * 4, 5))  # 3x5 text font, glyph = ASCII - 32, 4 mode-X planes, background index 62; DOS recolours it at draw time -> white mask sheet, 4 px per glyph
    for n, (sw, sh, px) in enumerate(bsp[:118]):
        for x in range(sw):
            for yy in range(sh):
                if px[(x & 3) * (sw // 4) * sh + yy * (sw // 4) + (x >> 2)] != 62: bsh.putpixel((n * 4 + x, yy), (255, 255, 255, 255))
    bsh.save(f'{out}/bfont.png')
    w, h, cells, _ = rd_map(f'{g}/{city}.MAP')
    _, bl, _ = rd_blk(f'{g}/{city}.BLK')
    blocks = []; bad = [0]
    for b in bl:
        k4 = len(b['tex']) // 4  # tex = 4 texture sets of k4 (file,tile) pairs (stride = short blk+0x20), picked by cell bits 8-9 (0x4699c); ex1-3 unused here
        TX = [b['tex'][v * k4:(v + 1) * k4] for v in range(4)]
        q = [[15, [TX[v][i][1] & 15 for v in range(4)], x[2], 20 + 4 * s8(x[3]), x[0]] + [x[6 + v * 3 + k] * 32 for v in range(4) for k in (0, 1)] for i, x in enumerate(b['quads'])]
        ws = []; cnt = len(b['quads'])  # Q.EXE loader 0x4987c: wall tex index = running count from nquads; ti < 0 -> n textures, else 1
        for x in b['walls']:
            n = x[0]; dx, dy, hh, px, py, z, ti, key = struct.unpack('<8h', x[2:18])
            m = n if ti < 0 else 1
            if cnt + m > k4: bad[0] += 1
            tx = [[list(T[min(cnt + (i if ti < 0 else 0), k4 - 1)]) for i in range(n)] if k4 else [] for T in TX]  # running count == live per-wall table blk+8 (blk 0x5c: 1,2,7,8,9,15,21,24,30,33), NOT abs(ti)
            cnt += m
            ws.append([n, dx, dy, hh, px, py, z, key, tx, ti, x[1]])  # w[9] = raw ti (sign picks the DOS wall routine: < 0 -> 0x487b8, >= 0 -> 0x482fc), w[10] = raw byte 1: no field dropped
        o = [list(struct.unpack('<6h', r)) for r in b['recs']]
        blocks.append({'q': q, 'w': ws, 'o': o})
    # object sprites: Q.EXE 0x48c90 draws bank entry [w,h] of <pre>OBJECTS.SPR, type = byte 8 of the 12-byte record, world size = dim * size / 64, anchor bottom centre
    op = f'{g}/{pre}OBJECTS.SPR'
    if not os.path.exists(op): op = f'{g}/{pre}OBJECT1.SPR'  # PCITY: POBJECT1..9, which one is live = unverified
    osp, _ = rd_spr(op); oat = Image.new('P', (1024, 1024)); oat.putpalette(pal); rects = []; ox = oy = rowh = 0
    for sw, sh, px in osp:
        if sw == 0 or sh == 0: rects.append([0, 0, 0, 0]); continue
        if ox + sw + 1 > 1024: ox = 0; oy += rowh + 1; rowh = 0
        oat.paste(Image.frombytes('P', (sw, sh), px), (ox, oy)); rects.append([ox, oy, sw, sh]); ox += sw + 1; rowh = max(rowh, sh)
    Image.frombytes('L', oat.size, oat.tobytes()).save(f'{out}/{city}_objs_idx.png')
    okey = Image.frombytes('L', oat.size, oat.tobytes().translate(bytes([0] + [255] * 255)))
    oat = oat.convert('RGBA'); oat.putalpha(okey); oat.save(f'{out}/{city}_objs.png')
    # wall flags Q.EXE 0x7f3a8 = first 15 rows of TEXTURE<n>.DAT (12 hex chars + CRLF), n = city order in the exe (city, kcity, pcity, jcity, wcity, scity); bit 2 = two-sided
    td = open(f"{g}/TEXTURE{['CITY', 'KCITY', 'PCITY', 'JCITY', 'WCITY', 'SCITY'].index(city)}.DAT", 'rb').read()
    wf = [[int(chr(c), 36) for c in td[r * 14:r * 14 + 12]] for r in range(15)]
    json.dump({'w': w, 'h': h, 'cells': list(cells), 'blocks': blocks, 'spr': rects, 'wf': wf}, open(f'{out}/{city}.json', 'w'), separators=(',', ':'))
    print(city, w, h, 'tex idx past array0:', bad[0], os.path.getsize(f'{out}/{city}.json'))
if __name__ == '__main__':
    for c in PRE: 
        try: export(sys.argv[1], c, sys.argv[2])
        except Exception as e: print(c, 'FAIL', repr(e))
