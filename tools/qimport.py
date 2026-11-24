"""qimport.py <flat bin name in ghidra/bin, e.g. q.bin>: import flattened Watcom LE into project Q, find functions, repair, export funcinfo."""
import os, subprocess, sys
BAT = os.path.join(os.path.expanduser("~"), "Documents", "Tools", "ghidra-headless.bat")
G = r"C:\Games\Quarantine\ghidra"; S = os.path.join(G, "scripts")
NW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
def run(args, log):
    p = subprocess.run([BAT, G, "Q", *args], capture_output=True, text=True, errors="replace", creationflags=NW)
    open(os.path.join(G, "logs", log), "w", encoding="utf-8").write(p.stdout + p.stderr); return p.returncode
f = sys.argv[1]; n = os.path.splitext(f)[0]; m = os.path.join(G, "bin", n + ".map")
print("import", run(["-import", os.path.join(G, "bin", f), "-overwrite", "-processor", "x86:LE:32:default", "-cspec", "watcom",
    "-loader", "BinaryLoader", "-loader-baseAddr", "0x10000", "-scriptPath", S, "-preScript", "ScordosSetup.java", m], "import_%s.log" % n), flush=True)
for sc in (["FindWatcomFunctions.java"], ["FixSplitEntries.java"], ["RepairBodies.java"], ["RepairBodies.java"], ["FindWatcomFunctions.java"], ["RepairBodies.java"]):
    print(sc[0], run(["-process", f, "-noanalysis", "-scriptPath", S, "-postScript", *sc], "s_%s_%s.log" % (n, sc[0])), flush=True)
print("export", run(["-process", f, "-noanalysis", "-readOnly", "-scriptPath", S, "-postScript", "ExportFuncInfo.java", os.path.join(G, "funcinfo_%s.tsv" % n)], "export_%s.log" % n))
tsv = os.path.join(G, "funcinfo_%s.tsv" % n)
print("F=", sum(1 for l in open(tsv, encoding="utf-8", errors="replace") if l.startswith("F ")))
