"""dostp.py <x> <y> [head]: teleport the DOS player car. Authoritative state (Q.EXE proc_0003761c, decomp 26826-26833): [0x830a4] = x * 8, [0x830a0] = y * 8, heading short [0x7eae0] (5760 per turn); [0x83230]/[0x83224] are per-frame copies."""
import sys, struct, time, ctypes, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dosmem as D
k = D.k; W = D.W
k.WriteProcessMemory.argtypes = [W.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
h = k.OpenProcess(0x438, False, D.pid()); b = D.base(h); g = ctypes.c_size_t()
x, y = int(sys.argv[1]), int(sys.argv[2])
k.WriteProcessMemory(h, b + 0x830a0, struct.pack('<ii', y * 8, x * 8), 8, ctypes.byref(g))
if len(sys.argv) > 3: k.WriteProcessMemory(h, b + 0x7eae0, struct.pack('<h', int(sys.argv[3])), 2, ctypes.byref(g))
time.sleep(1.5); print(json.dumps(D.cam()))
