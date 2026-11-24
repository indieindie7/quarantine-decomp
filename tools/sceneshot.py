"""Frame of one scene alone (no main.gd): sceneshot.py <res://scene.tscn> <out.png> px,py,pz tx,ty,tz"""
import os, re, subprocess, sys
T = os.path.dirname(os.path.abspath(__file__)); G = eval(re.search(r'^GODOT\s*=\s*(.+)$', open(os.path.join(T, 'parity.py'), encoding='utf-8').read(), re.M).group(1))
si = subprocess.STARTUPINFO(); si.dwFlags |= subprocess.STARTF_USESHOWWINDOW; si.wShowWindow = 7
r = subprocess.run([G, '--path', '.', '--resolution', '1280x800', '--script', 'res://areas/scene_shot.gd', '--', sys.argv[1], os.path.abspath(sys.argv[2]), sys.argv[3], sys.argv[4]], cwd=os.path.join(T, '..', 'port'), startupinfo=si, capture_output=True, text=True)
print('\n'.join(l for l in (r.stdout + r.stderr).split('\n') if 'scene_shot' in l or 'ERROR' in l or 'error' in l)[:900])
