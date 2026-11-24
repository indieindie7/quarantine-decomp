"""aimport.py <file in g3do/bin>: import ARM BE raw at 0 into project QA with full auto-analysis, export funcinfo."""
import os, subprocess, sys
BAT = os.path.join(os.path.expanduser("~"), "Documents", "Tools", "ghidra-headless.bat")
G = r"C:\Games\Quarantine\g3do"; S = os.path.join(G, "scripts")
def run(args, log):
    p = subprocess.run([BAT, G, "QA", *args], capture_output=True, text=True, errors="replace", creationflags=0x08000000)
    open(os.path.join(G, "logs", log), "w", encoding="utf-8").write(p.stdout + p.stderr); return p.returncode
f = sys.argv[1]; n = os.path.splitext(f)[0]
print("import", run(["-import", os.path.join(G, "bin", f), "-overwrite", "-processor", "ARM:BE:32:v4", "-loader", "BinaryLoader", "-loader-baseAddr", "0x0"], "import_%s.log" % n), flush=True)
print("export", run(["-process", f, "-noanalysis", "-readOnly", "-scriptPath", S, "-postScript", "ExportFuncInfo.java", os.path.join(G, "funcinfo_%s.tsv" % n)], "export_%s.log" % n))
t = os.path.join(G, "funcinfo_%s.tsv" % n)
print(f, "F=", sum(1 for l in open(t, encoding="utf-8", errors="replace") if l.startswith("F ")))
