"""In-process DOSBox memory reader (fast). R = Reader(); R.rd(ghidra_addr, n); R.p(live_ptr, n); R.u32/u16/s16."""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dosmem
DELTA = 0x1c7000  # live pointer - DELTA = Ghidra-space address (measured 11-22 from reloc at 0x76ca0)
class Reader:
    def __init__(s):
        s.h = dosmem.k.OpenProcess(0x410, False, dosmem.pid()); s.b = dosmem.base(s.h)
    def rd(s, a, n): return dosmem.rpm(s.h, s.b + a, n)
    def p(s, ptr, n): return s.rd(ptr - DELTA, n)
    def u32(s, a): return struct.unpack('<I', s.rd(a, 4))[0]
    def s16(s, a): return struct.unpack('<h', s.rd(a, 2))[0]
