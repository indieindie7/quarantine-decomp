"""cdump.py: dump Ghidra decompiler C for the DOS and 3DO programs (Saturn already has gsat/decomp_*.c). One job at a time."""
import os, subprocess
H = os.path.expanduser("~"); BAT = os.path.join(H, "Documents", "Tools", "ghidra-headless.bat")
Q = os.path.join(H, "Documents", "Quarantine"); S = os.path.join(H, "Documents", "Tools", "decomp", "scripts")
for g, proj, f, out in (("ghidra", "Q", "q.bin", "decomp_q.c"), ("g3do", "QA", "launchme.bin", "decomp_launchme.c")):
    G = os.path.join(Q, g)
    p = subprocess.run([BAT, G, proj, "-process", f, "-noanalysis", "-readOnly", "-scriptPath", S, "-postScript", "CsDumpAll.java", os.path.join(G, out)],
                       capture_output=True, text=True, errors="replace", creationflags=0x08000000)
    o = os.path.join(G, out); print(out, os.path.getsize(o) if os.path.exists(o) else "MISSING " + (p.stdout + p.stderr)[-400:], flush=True)
