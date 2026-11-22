"""simport.py <file in gsat/bin> <base>: import SH-2 BE raw at base into project QS, find functions, export funcinfo + decomp dump."""
import os, subprocess, sys
BAT = os.path.join(os.path.expanduser("~"), "Documents", "Tools", "ghidra-headless.bat")
G = r"C:\Users\USER\Documents\Quarantine\gsat"; S = os.path.join(G, "scripts")
def run(args, log):
    p = subprocess.run([BAT, G, "QS", *args], capture_output=True, text=True, errors="replace", creationflags=0x08000000)
    open(os.path.join(G, "logs", log), "w", encoding="utf-8").write(p.stdout + p.stderr); return p.returncode
f, base = sys.argv[1], sys.argv[2]; n = os.path.splitext(f)[0]
print("import", run(["-import", os.path.join(G, "bin", f), "-overwrite", "-processor", "SuperH:BE:32:SH-2", "-loader", "BinaryLoader", "-loader-baseAddr", base,
  "-scriptPath", S, "-postScript", "FindSh2FunctionsMem.java", "-postScript", "CreateAt.java", base], "import_%s.log" % n), flush=True)
print("export", run(["-process", f, "-noanalysis", "-readOnly", "-scriptPath", S, "-postScript", "ExportFuncInfo.java", os.path.join(G, "funcinfo_%s.tsv" % n)], "export_%s.log" % n))
print("dump", run(["-process", f, "-noanalysis", "-readOnly", "-scriptPath", S, "-postScript", "CsDumpAll.java", os.path.join(G, "decomp_%s.c" % n)], "dump_%s.log" % n))
t = os.path.join(G, "funcinfo_%s.tsv" % n)
print(f, "F=", sum(1 for l in open(t, encoding="utf-8", errors="replace") if l.startswith("F ")))
