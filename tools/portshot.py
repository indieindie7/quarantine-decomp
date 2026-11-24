"""Port-only shot at a DOS cam (no DOSBox needed): portshot.py <x> <y> <z> <head> <out.png> [port args..]; prints Godot errors."""
import sys, os, subprocess, re
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
src = open(os.path.join(T, 'parity.py'), encoding='utf-8').read()
GODOT = eval(re.search(r'^GODOT\s*=\s*(.+)$', src, re.M).group(1)); PORT = os.path.join(T, '..', 'port')
x, y, z, hd = map(int, sys.argv[1:5]); out = os.path.abspath(sys.argv[5])
args = ['--path', '.', '--', '--city=KCITY', '--bg', '--res=640x400', '--fov=64', '--nofps', f'--pos={x / 16.0},{-z / 16.0},{y / 16.0}', f'--yaw={hd / 16.0 + 180.0}', f'--shot={out}', '--frames=12'] + sys.argv[6:]
si = subprocess.STARTUPINFO(); si.dwFlags = 1; si.wShowWindow = 7
r = subprocess.run([GODOT, *args], cwd=PORT, startupinfo=si, capture_output=True, text=True)
print('\n'.join(l for l in (r.stdout + r.stderr).splitlines() if re.search('ERROR|error|SHADER|-->|Parse', l))[:3000])
