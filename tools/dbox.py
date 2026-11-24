"""Drive the Quarantine DOSBox in the background. dbox.py start | key <k> [k..] [hold=0.1] | shot | stop
Keys go by PostMessage to the SDL window (no focus needed). shot = Ctrl+F5 (DOSBox Staging default), prints newest file."""
import sys, time, ctypes, subprocess, glob, os
u = ctypes.windll.user32
PLAY = r'C:\Games\QuarantinePlay'; CAP = r'C:\Games\Quarantine\dosshots'
SC = {'enter': (0x0D, 0x1C), 'esc': (0x1B, 0x01), 'space': (0x20, 0x39), 'up': (0x26, 0x148), 'down': (0x28, 0x150), 'left': (0x25, 0x14B), 'right': (0x27, 0x14D),
      'ctrl': (0x11, 0x1D), 'f5': (0x74, 0x3F), 'f1': (0x70, 0x3B), 'tab': (0x09, 0x0F), 'y': (0x59, 0x15), 'n': (0x4E, 0x31), 'alt': (0x12, 0x38), 'p': (0x50, 0x19), 'pause': (0x13, 0x45), 'f11': (0x7A, 0x57), 'f12': (0x7B, 0x58)}
for i, c in enumerate('1234567890'): SC[c] = (0x30 + (i + 1) % 10, 2 + i)
def hwnd():
    res = []
    def cb(h, l):
        b = ctypes.create_unicode_buffer(200); u.GetWindowTextW(h, b, 200)
        if 'DOSBox' in b.value and u.IsWindowVisible(h): res.append(h)
        return True
    u.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(cb), 0)
    return res[0] if res else None
def post(h, k, down):
    vk, sc = SC[k]; lp = 1 | ((sc & 0xFF) << 16) | ((1 << 24) if sc > 0xFF else 0) | (0 if down else 0xC0000000)
    u.PostMessageW(ctypes.c_void_p(h), 0x100 if down else 0x101, vk, lp)
def key(h, k, hold=0.1):
    post(h, k, True); time.sleep(hold); post(h, k, False); time.sleep(0.15)
a = sys.argv[1:]
if a[0] == 'start':
    si = subprocess.STARTUPINFO(); si.dwFlags = 1; si.wShowWindow = 7  # SW_SHOWMINNOACTIVE
    p = subprocess.Popen([PLAY + r'\dosbox\dosbox.exe', '-conf', CAP + r'\test.conf', '-noprimaryconf'], cwd=PLAY, startupinfo=si, stdout=subprocess.DEVNULL, stderr=open(CAP + r'\err.txt', 'w'))
    print('pid', p.pid)
elif a[0] == 'stop': subprocess.run(['taskkill', '/IM', 'dosbox.exe', '/F'], capture_output=True)
else:
    h = hwnd()
    if not h: sys.exit('no DOSBox window')
    if a[0] == 'key':
        hold = 0.1
        for k in a[1:]:
            if k.startswith('hold='): hold = float(k[5:])
            elif k == 'shot': pass
            elif k.startswith('wait='): time.sleep(float(k[5:]))
            else: key(h, k, hold)
    if a[0] == 'shot' or 'shot' in a:
        key(h, 'f11'); time.sleep(1.0)  # dosshots/q.map binds the grab to plain F11: the game never sees it, so its pause holds
        f = sorted(glob.glob(PLAY + r'\capture\*.png'), key=os.path.getmtime); print(f[-1] if f else 'NO SHOT')
