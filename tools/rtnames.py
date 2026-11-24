"""rtnames.py <hand.txt> : reads fdigest light lines on stdin, appends a name for every listed function of the DOS Q.EXE
runtime tail (0x5371c and above): KNOWN = read from the digest by hand (11-23), everything else gets <region prefix>_<addr>
(Watcom C runtime rt_, HMI SOS sound driver sos_, x87 emulator fp_, VGA tail vga_). Region names are placeholders with a
meaning for the area only; the comment says so."""
import sys
KNOWN = {
    0x5371c: 'rt_fseek_adjust', 0x5375e: 'rt_fseek', 0x5388a: 'rt_atoi', 0x538e1: 'rt_getsetvect', 0x53915: 'rt_dos_setvect',
    0x53940: 'rt_cstart_entry', 0x539ba: 'rt_cstart', 0x53bd3: 'rt_open_con', 0x53c15: 'rt_inp', 0x53c1d: 'rt_outp',
    0x53c2b: 'rt_stricmp', 0x53c64: 'rt_time', 0x53c91: 'rt_rand_seedptr', 0x53c97: 'rt_rand', 0x53cbb: 'rt_srand',
    0x53ce1: 'sos_TimerInitSystem', 0x53dbd: 'sos_TimerUnInitSystem', 0x53df7: 'sos_TimerRegisterEvent',
    0x53fa1: 'sos_TimerRegisterEventB', 0x54119: 'sos_TimerRemoveEvent', 0x542f2: 'sos_TimerSetRate', 0x54327: 'sos_TimerIrq',
    0x54632: 'rt_strtod', 0x547db: 'rt_fputc', 0x5487f: 'rt_fflush', 0x54d4a: 'rt_read', 0x54e5d: 'rt_open', 0x54e81: 'rt_sopen',
    0x55087: 'rt_ioctl_setraw', 0x550c0: 'sos_DigiStartSample', 0x556d9: 'sos_DigiStopSample', 0x5573f: 'sos_DigiContinueSample',
    0x55ae0: 'sos_DigiSampleDone', 0x55bcb: 'rt_close', 0x55c09: 'rt_stack_overflow', 0x55c2d: 'sos_DetectInit',
    0x55d5b: 'sos_DetectUnInit', 0x55dc6: 'sos_DetectFindHardware', 0x56635: 'sos_DetectGetSettings', 0x568be: 'sos_GetErrorString',
    0x56912: 'sos_LockMemory', 0x56ac0: 'sos_UnlockMemory', 0x56c6e: 'sos_DigiInitSystem', 0x56cd6: 'sos_DigiUnInitSystem',
    0x56d04: 'sos_DigiInitDriver', 0x57568: 'sos_DigiUnInitDriver', 0x57780: 'sos_DigiLoadDriver', 0x57a19: 'rt_int386x',
    0x57f09: 'sos_DigiSetSampleRate', 0x58196: 'rt_set_errno', 0x581cc: 'rt_allocfp', 0x58274: 'rt_freefp', 0x582fc: 'rt_ioalloc',
    0x58398: 'rt_flush', 0x58498: 'rt_close_handle', 0x584ca: 'rt_remove', 0x5851a: 'rt_init_fpu', 0x587ca: 'rt_prtf',
    0x58d63: 'rt_prtf_format', 0x58c81: 'rt_prtf_number', 0x5a1a9: 'rt_pic_mask', 0x5a1d5: 'rt_pic_unmask',
    0x5a642: 'rt_isatty', 0x5a6d9: 'sos_DpmiLockRegion', 0x5a706: 'sos_DpmiUnlockRegion', 0x5a7c2: 'sos_DpmiFreeMem',
    0x5af38: 'sos_FileRead', 0x5b0af: 'sos_LoadDriverFileA', 0x5b348: 'sos_LoadDriverFileB', 0x5bb00: 'rt_init_files',
    0x5bd9d: 'rt_fp_not_loaded', 0x5f146: 'rt_utoa', 0x5f1d0: 'rt_ultoa', 0x5f942: 'rt_tzset', 0x7528d: 'vga_SetStartAddr',
    0x75455: 'vga_CrtcWriteA', 0x754b4: 'vga_CrtcWriteB',
}
REGIONS = ((0x550c0, 'rt'), (0x58100, 'sos'), (0x5a6a1, 'rt'), (0x5b7e8, 'sos'), (0x5c41a, 'rt'), (0x5c4e0, 'fp'), (0x75000, 'rt'), (0x1000000, 'vga'))
def region(a):
    return next(p for top, p in REGIONS if a < top)
def main(a):
    out = []
    for ln in sys.stdin:
        t = ln.split()
        if not t or t[0] == '#' or int(t[0], 16) < 0x5371c: continue
        x = int(t[0], 16)
        if x in KNOWN: out.append('0x%x func %s hand runtime, from digest hints' % (x, KNOWN[x]))
        else: out.append('0x%x func %s_%x hand region name only, not studied' % (x, region(x), x))
    open(a[0], 'a', encoding='utf-8').write('\n'.join(out) + '\n'); print('added', len(out), 'known', sum('from digest' in o for o in out))
if __name__ == '__main__': main(sys.argv[1:])
