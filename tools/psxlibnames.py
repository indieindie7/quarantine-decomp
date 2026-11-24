"""psxlibnames.py <hand.txt> : reads fdigest light lines on stdin, appends a name for every listed function of the
Hard Rock Cab PSX exe PsyQ library tail (0x80071a4c and above) that psyqsig.py did not match. KNOWN = named from the
library's own debug strings in the digest (11-23); everything else gets <region prefix>_<addr> (libetc interrupt code
etc_, libgpu gpu_, libspu spu_, libpress/MDEC mdec_). Region names are placeholders for the area only; the comment says so."""
import sys
KNOWN = {
    0x80071b84: 'etc_ResetCallback_impl', 0x80071c44: 'etc_IntrDispatch', 0x800720e0: 'etc_DmaBusError',
    0x800726bc: 'ResetGraph', 0x8007288c: 'SetGraphReverse', 0x8007299c: 'SetGraphDebug', 0x80072a04: 'SetGraphQueue',
    0x80072ac0: 'DrawSyncCallback', 0x80072b1c: 'SetDispMask', 0x80072b94: 'DrawSync', 0x80072c00: 'gpu_CheckRect',
    0x80072d18: 'ClearImage', 0x80072dac: 'LoadImage', 0x80072e10: 'StoreImage', 0x80072e74: 'MoveImage',
    0x80072f18: 'ClearOTag', 0x80072fc4: 'ClearOTagR', 0x800730a4: 'DrawOTag', 0x80073114: 'PutDrawEnv',
    0x8007326c: 'PutDispEnv', 0x80074b60: 'gpu_ExeQue', 0x800751fc: 'gpu_Timeout', 0x800754a8: 'DumpTPage',
    0x80075544: 'DumpClut', 0x800758dc: 'DumpDrawEnv', 0x80075a2c: 'DumpDispEnv', 0x800767f0: 'spu_Init',
    0x80076e44: 'spu_Write', 0x800776f4: 'spu_Ioctl', 0x8007f858: 'mdec_Reset', 0x8007fa84: 'mdec_InSync',
    0x8007fb1c: 'mdec_OutSync', 0x8007fbb4: 'mdec_Timeout', 0x8007ff38: 'mdec_Vlc',
}
REGIONS = ((0x80072600, 'etc'), (0x80075d20, 'gpu'), (0x8007f000, 'spu'), (0x90000000, 'mdec'))
def region(a):
    return next(p for top, p in REGIONS if a < top)
def main(a):
    out = []
    for ln in sys.stdin:
        t = ln.split()
        if not t or t[0] == '#' or int(t[0], 16) < 0x80071a4c: continue
        x = int(t[0], 16)
        if x in KNOWN: out.append('0x%x func %s hand psyq, from the debug string in the function' % (x, KNOWN[x]))
        else: out.append('0x%x func %s_%x hand region name only, not studied' % (x, region(x), x))
    open(a[0], 'a', encoding='utf-8').write('\n'.join(out) + '\n'); print('added', len(out), 'known', sum('debug string' in o for o in out))
if __name__ == '__main__': main(sys.argv[1:])
