"""Read Q.EXE globals out of the running DOSBox (ground truth for parity checks).
usage: dosmem.py cam | dosmem.py rd <hexaddr> <n> | dosmem.py wr <hexaddr> <hexbytes>   (addresses = Ghidra/q.bin addresses, file off = addr - 0x10000)
Finds the data object by scanning DOSBox memory for 64 constant bytes at ANCHOR (player start table 0x792e0)."""
import sys, os, ctypes, struct, subprocess, json
from ctypes import wintypes as W
BIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ghidra', 'bin', 'q.bin')
ANCHOR = 0x792e0
k = ctypes.WinDLL('kernel32', use_last_error=True)
class MBI(ctypes.Structure):
    _fields_ = [('Base', ctypes.c_void_p), ('ABase', ctypes.c_void_p), ('AProt', W.DWORD), ('Part', W.WORD), ('Size', ctypes.c_size_t), ('State', W.DWORD), ('Prot', W.DWORD), ('Type', W.DWORD)]
k.OpenProcess.restype = W.HANDLE; k.VirtualQueryEx.argtypes = [W.HANDLE, ctypes.c_void_p, ctypes.POINTER(MBI), ctypes.c_size_t]
k.ReadProcessMemory.argtypes = [W.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
def pid():
    o = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq dosbox.exe', '/FO', 'CSV', '/NH'], capture_output=True, text=True).stdout
    return int(o.split(',')[1].strip('"'))
def rpm(h, a, n):
    b = ctypes.create_string_buffer(n); g = ctypes.c_size_t()
    return b.raw[:g.value] if k.ReadProcessMemory(h, a, b, n, ctypes.byref(g)) else b''
def base(h):
    c = os.path.join(os.environ['TEMP'], 'dosmem_base.json'); p = pid()
    sig = open(BIN, 'rb').read()[ANCHOR - 0x10000:ANCHOR - 0x10000 + 64]
    if os.path.exists(c):
        j = json.load(open(c))
        if j['pid'] == p and rpm(h, j['base'] + ANCHOR, 64) == sig: return j['base']
    a = 0; m = MBI()
    while k.VirtualQueryEx(h, a, ctypes.byref(m), ctypes.sizeof(m)):
        if m.State == 0x1000 and m.Prot in (4, 0x40) and m.Size >= 0x100000:
            d = rpm(h, m.Base, m.Size); i = d.find(sig)
            if i >= 0:
                b = m.Base + i - ANCHOR; json.dump({'pid': p, 'base': b}, open(c, 'w')); return b
        a = (m.Base or 0) + m.Size
    raise SystemExit('anchor not found (game not loaded?)')
def cam():
    h = k.OpenProcess(0x410, False, pid()); b = base(h)
    # 0x83224 = world cam copy kept during the city draw (0x4736c); 0x83230 is overwritten per block while drawing
    x, y, z = struct.unpack('<3i', rpm(h, b + 0x83224, 12)); hd = struct.unpack('<h', rpm(h, b + 0x8362c, 2))[0]
    return {'x': x, 'y': y, 'z': z, 'head': hd, 'deg': hd / 16.0}
if __name__ == '__main__':
    if sys.argv[1] == 'cam': print(json.dumps(cam()))
    elif sys.argv[1] == 'wr':  # dosmem.py wr <hexaddr> <hexbytes>: poke live DOS memory (teleport for parity views)
        k.WriteProcessMemory.argtypes = [W.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        h = k.OpenProcess(0x438, False, pid()); b = base(h); d = bytes.fromhex(sys.argv[3]); g = ctypes.c_size_t(); print(k.WriteProcessMemory(h, b + int(sys.argv[2], 16), d, len(d), ctypes.byref(g)), g.value)
    else:
        h = k.OpenProcess(0x410, False, pid()); b = base(h); print(rpm(h, b + int(sys.argv[2], 16), int(sys.argv[3])).hex())
