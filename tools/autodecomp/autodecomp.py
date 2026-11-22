"""autodecomp.py <game.zip> [more zips] [--name Name] [--out DIR] : zip in, first-pass decomp out, no questions.
Steps: unzip to a new dir -> detect disc images (Saturn / 3DO Opera / ISO9660) and extract -> find executables
(DOS4GW LE, PE, MZ, Saturn IP + first-read SH-2, 3DO launchme ARM) -> Ghidra import + function finding -> funcinfo ->
provisional names (xname) -> apply -> re-export -> convert known assets (IMAGEX .IMG, Saturn .CMP) -> REPORT.md + NOTES.md.
Everything it cannot do is listed under "Left for a human/Claude" in REPORT.md. Run with py -3.13 -I. One Ghidra job at a time."""
import os, re, struct, subprocess, sys, zipfile, shutil, time
HOME = os.path.expanduser("~"); HERE = os.path.dirname(os.path.abspath(__file__))
LIB, SCR = os.path.join(HERE, "lib"), os.path.join(HERE, "scripts")
BAT = os.path.join(HOME, "Documents", "Tools", "ghidra-headless.bat")
NW = 0x08000000
a = sys.argv[1:]
def opt(k, d=None):
    if k in a:
        i = a.index(k); v = a[i + 1]; del a[i:i + 2]; return v
    return d
name = opt("--name"); out = opt("--out"); zips = a
name = name or re.sub(r"[^A-Za-z0-9]+", "", os.path.splitext(os.path.basename(zips[0]))[0])[:24]
out = out or os.path.join(HOME, "Documents", name + "Auto")
G = os.path.join(out, "ghidra")
for d in ("src", "disc", "decoded", "ghidra/bin", "ghidra/logs", "ghidra/work"): os.makedirs(os.path.join(out, d), exist_ok=True)
log, left, rows = [], [], []
def say(*x):
    s = " ".join(str(i) for i in x); log.append(s); print(s, flush=True)
def py(script, *args): return subprocess.run([sys.executable, "-I", os.path.join(LIB, script), *args], capture_output=True, text=True, errors="replace", creationflags=NW)
def gh(args, lg):
    p = subprocess.run([BAT, G, name, *args], capture_output=True, text=True, errors="replace", creationflags=NW)
    open(os.path.join(G, "logs", lg), "w", encoding="utf-8").write(p.stdout + p.stderr); return p.returncode
safe = lambda s: re.sub(r"[^A-Za-z0-9_.]", "_", s)

# 1 unzip (zip-slip safe)
for z in zips:
    dst = os.path.join(out, "src", safe(os.path.splitext(os.path.basename(z))[0]))
    with zipfile.ZipFile(z) as zf:
        for m in zf.infolist():
            t = os.path.realpath(os.path.join(dst, m.filename))
            if t.startswith(os.path.realpath(dst)): zf.extract(m, dst)
    say("unzipped", os.path.basename(z))
def walk(root): return [os.path.join(r, f) for r, _, fs in os.walk(root) for f in fs]

# 2 disc images
def disc_kind(p):
    if os.path.getsize(p) < 2 * 1024 * 1024: return None
    f = open(p, "rb"); h = f.read(16)
    ss, hd = (2352, 16) if h[:12] == b"\0" + b"\xff" * 10 + b"\0" else (2048, 0)
    def sec(i):
        f.seek(i * ss + hd); return f.read(2048)
    s0, s16 = sec(0), sec(16)
    if s0[:15] == b"SEGA SEGASATURN": return ("saturn", ss, hd)
    if s0[1:6] == b"ZZZZZ": return ("3do", ss, hd)
    if s16[1:6] == b"CD001": return ("iso", ss, hd)
    return None
def iso_first_file(p, ss, hd):
    f = open(p, "rb")
    def sec(i):
        f.seek(i * ss + hd); return f.read(2048)
    pvd = sec(16); lba, size = struct.unpack("<I", pvd[158:162])[0], struct.unpack("<I", pvd[166:170])[0]
    skip = {pvd[o2:o2 + 37].decode("latin1").split(";")[0].strip().upper() for o2 in (702, 739, 776)}
    d = b"".join(sec(lba + i) for i in range((size + 2047) // 2048)); o = 0; best = None
    while o < len(d):
        n = d[o]
        if n == 0:
            o = (o // 2048 + 1) * 2048; continue
        fl, nl = d[o + 25], d[o + 32]; nm = d[o + 33:o + 33 + nl].split(b";")[0].decode("latin1")
        l = struct.unpack("<I", d[o + 2:o + 6])[0]
        if not fl & 2 and nl > 1 and nm.upper() not in skip and (best is None or l < best[0]): best = (l, nm)
        o += n
    return best[1] if best else None
targets = []   # (kind, path, base)
for p in walk(os.path.join(out, "src")):
    try: k = disc_kind(p)
    except Exception: k = None
    if not k: continue
    dd = os.path.join(out, "disc", safe(os.path.basename(p))); say("disc", k[0], os.path.basename(p), "sector", k[1])
    if k[0] == "3do":
        if k[1] != 2352:
            left.append("3DO image with 2048 sectors: operafs.py expects 2352 (%s)" % p); continue
        py("operafs.py", p, dd)
    else:
        py("isoextract.py", p, dd, str(k[1]), str(k[2]))
    if k[0] == "saturn":
        f = open(p, "rb"); ip = b""
        for i in range(16):
            f.seek(i * k[1] + k[2]); ip += f.read(2048)
        fr = struct.unpack(">I", ip[0xF0:0xF4])[0] or 0x06004000
        ipp = os.path.join(G, "bin", "IP_src.BIN"); open(ipp, "wb").write(ip[:0x1000]); targets.append(("sh2", ipp, "0x06002000"))
        ff = iso_first_file(p, k[1], k[2]); say("saturn first-read", hex(fr), ff)
        m = [x for x in walk(dd) if os.path.basename(x).upper() == (ff or "").upper()]
        if m: targets.append(("sh2", m[0], hex(fr)))
        else: left.append("Saturn first-read file not found: " + str(ff))

# 3 executables
def exe_kind(p):
    b = os.path.basename(p).lower()
    if b == "launchme": return "arm"
    h = open(p, "rb").read(0x40)
    if h[:2] != b"MZ": return None
    d = open(p, "rb").read(); e = struct.unpack("<I", h[0x3c:0x40])[0]
    if d[e:e + 4] == b"PE\0\0": return "pe"
    if d[e:e + 2] in (b"LE", b"LX") or (re.search(rb"DOS/4G|DOS4GW|PMODE/W|CauseWay", d[:0x8000]) and b"LE\0\0" in d): return "le"
    return "mz"
seen = set()
for p in walk(os.path.join(out, "src")) + walk(os.path.join(out, "disc")):
    try: k = exe_kind(p)
    except Exception: k = None
    if not k: continue
    key = (os.path.basename(p).lower(), os.path.getsize(p))
    if key in seen: continue
    seen.add(key)
    if k == "mz" and os.path.getsize(p) < 40000:
        left.append("small 16-bit MZ skipped: " + os.path.basename(p)); continue
    if k in ("pe", "mz", "le") and os.path.basename(p).lower().startswith(("a32", "dos4g", "unins", "setup", "install")):
        left.append("helper exe skipped: " + os.path.basename(p)); continue
    targets.append((k, p, "0"))

# 4 Ghidra per target
def count(tsv):
    F = U = S = B = 0
    for l in open(tsv, encoding="utf-8", errors="replace"):
        if l.startswith("F "):
            t = l.split(" "); F += 1; U += t[2].startswith(("FUN_", "thunk_FUN_")); S += t[2].startswith("s_")
            try: B += int(t[4])
            except Exception: pass
    return F, U, S, B
used = set()
for kind, p, base in targets:
    n = safe(os.path.splitext(os.path.basename(p))[0]).replace("_src", "") or "prog"
    while n.lower() in used: n += "_"
    used.add(n.lower()); f = n + ".bin"; bp = os.path.join(G, "bin", f); t0 = time.time()
    if kind == "le":
        r = py("leflatten.py", p, os.path.join(G, "bin", n))
        if not os.path.exists(bp):
            left.append("LE flatten failed: %s %s" % (p, r.stderr.strip().splitlines()[-1:])); continue
        mp = os.path.join(G, "bin", n + ".map"); base = re.search(r"imagebase (\S+)", open(mp).read()).group(1)
        gh(["-import", bp, "-overwrite", "-processor", "x86:LE:32:default", "-cspec", "watcom", "-loader", "BinaryLoader", "-loader-baseAddr", base,
            "-scriptPath", SCR, "-preScript", "ScordosSetup.java", mp], "import_%s.log" % n)
        for sc in ("FindWatcomFunctions", "FixSplitEntries", "RepairBodies", "RepairBodies", "FindWatcomFunctions", "RepairBodies"):
            gh(["-process", f, "-noanalysis", "-scriptPath", SCR, "-postScript", sc + ".java"], "s_%s_%s.log" % (n, sc))
    else:
        shutil.copyfile(p, bp)
        if kind == "sh2":
            gh(["-import", bp, "-overwrite", "-processor", "SuperH:BE:32:SH-2", "-loader", "BinaryLoader", "-loader-baseAddr", base,
                "-scriptPath", SCR, "-postScript", "FindSh2FunctionsMem.java", "-postScript", "CreateAt.java", base], "import_%s.log" % n)
        elif kind == "arm":
            gh(["-import", bp, "-overwrite", "-processor", "ARM:BE:32:v4", "-loader", "BinaryLoader", "-loader-baseAddr", "0x0"], "import_%s.log" % n)
        else:
            gh(["-import", bp, "-overwrite"], "import_%s.log" % n)
    tsv = os.path.join(G, "funcinfo_%s.tsv" % n)
    ex = ["-process", f, "-noanalysis", "-readOnly", "-scriptPath", SCR, "-postScript", "ExportFuncInfo.java", tsv]
    gh(ex, "export_%s.log" % n)
    if not os.path.exists(tsv):
        left.append("Ghidra import/export failed: %s (see ghidra/logs/import_%s.log)" % (p, n)); continue
    py("xname.py", G, n)
    nf = os.path.join(G, "work", "names_%s.txt" % n)
    if os.path.exists(nf) and os.path.getsize(nf) > 2:
        gh(["-process", f, "-noanalysis", "-scriptPath", SCR, "-postScript", "ApplyNames.java", nf], "names_%s.log" % n); gh(ex, "export2_%s.log" % n)
    F, U, S, B = count(tsv); rows.append((n, kind, base, os.path.basename(p), F, U, S, B, int(time.time() - t0)))
    say("done", n, kind, "F=%d FUN_=%d s_=%d" % (F, U, S))

# 5 assets
ext = {}
img_ok = cmp_ok = 0
for p in walk(os.path.join(out, "src")) + walk(os.path.join(out, "disc")):
    e = os.path.splitext(p)[1].upper() or "(none)"; ext[e] = ext.get(e, 0) + 1
    try: h = open(p, "rb").read(12)
    except Exception: continue
    o = os.path.join(out, "decoded", safe(os.path.basename(p)) + ".png")
    if h[:6] == b"IMAGEX": img_ok += py("imgdec.py", p, o).returncode == 0
    elif e == ".CMP" and len(h) == 12 and h[4:12] == b"\0\0\x08\0\0\0\x04\0": cmp_ok += py("cmpdec.py", p, o).returncode == 0
known = {".IMG", ".CMP", ".EXE", ".BIN", ".TXT", ".DLL"}
left.append("unread data formats (count): " + ", ".join("%s %d" % kv for kv in sorted(ext.items(), key=lambda kv: -kv[1])[:14] if kv[0] not in known))
left += ["names are provisional (string/size); hand naming not done", "runtime library signatures not matched", "no rebuild, no behaviour tests (games-bench level L1-L2 only)"]

# 6 report
R = ["# %s: automatic first-pass decomp (%s)" % (name, time.strftime("%Y-%m-%d")), "Input: " + ", ".join(os.path.basename(z) for z in zips), "",
     "| program | kind | base | source file | functions | FUN_ left | string-named | bytes | sec |", "|---|---|---|---|---|---|---|---|---|"]
R += ["| %s | %s | %s | %s | %d | %d | %d | %d | %d |" % r for r in rows]
R += ["", "Total functions: %d" % sum(r[4] for r in rows), "Assets converted: IMAGEX %d, CMP %d (decoded/)" % (img_ok, cmp_ok), "", "## Left for a human/Claude"] + ["- " + x for x in left]
R += ["", "## Log"] + ["- " + x for x in log]
open(os.path.join(out, "REPORT.md"), "w", encoding="utf-8").write("\n".join(R) + "\n")
if not os.path.exists(os.path.join(out, "NOTES.md")):
    open(os.path.join(out, "NOTES.md"), "w", encoding="utf-8").write("# %s notes (private)\n- Auto pass: see REPORT.md. Ghidra project ghidra/ (%s).\n## Open\n" % (name, name) + "\n".join("- " + x for x in left) + "\n")
print("REPORT", os.path.join(out, "REPORT.md"))
