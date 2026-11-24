# lastwall.sh x y head: teleport, pause, read DOS last-wall s0/s1/div, dump the port's (s0,s1,div) sets at the same cam
cd /c/Games/Quarantine; S="$TEMP"; T=tools
py -3.13 -I tools/dostp.py $1 $2 $3 >/dev/null; py -3.13 -I tools/dbox.py key p wait=0.4 >/dev/null
if [ "$(py -3.13 -I tools/entsync.py paused)" != "1" ]; then py -3.13 -I tools/dbox.py key p wait=0.4 >/dev/null; fi
C=$(py -3.13 -I tools/dosmem.py cam); echo "$C"; echo "dos 98430: $(py -3.13 -I tools/dosmem.py rd 98430 8) div: $(py -3.13 -I tools/dosmem.py rd 79416 2) sx: $(py -3.13 -I tools/dosmem.py rd 984a8 40)"
py -3.13 -I tools/dbox.py key p wait=0.2 >/dev/null
set -- $(echo "$C" | py -3.13 -I -c "import sys,json; c=json.load(sys.stdin); print(c['x'],c['y'],c['head'])")
F="ALBEDO = shadedlv(i, flv >= 0.0 ? flv : sh.y + sh.z * (c - sh.x));"; V="sh = vec3(float(sx[i0]), float(s0), float(ss));"; export BOX=0,37,320,149
for e in "s0" "s1" "wq_div * 64 + cnt" "sx[i0] + 4096" "dx"; do n=$(echo "$e" | tr -dc 'a-z0-9'); OUT=$S/lw_$n.json py -3.13 -I tools/pchk.py port/shots/par_e33.png $1 $2 $3 "$F=>$F if (dw) ALBEDO = (sh + 8.0) / 80.0;" "$V=>int DV = $e; sh = vec3(float(DV & 63), float((DV >> 6) & 63), float((DV >> 12) & 63));" >/dev/null; done
py -3.13 -I -c "
import json, collections
S=r'$S'; L=[json.load(open(S+'/lw_%s.json'%n)) for n in ('s0','s1','wqdiv64cnt','sxi04096','dx')]
C=collections.Counter()
for y in range(112):
    for x in range(320): C[tuple(l[y][x] for l in L)]+=1
for k,n in C.most_common(14):
    if n>=12: print('port s0',k[0],'s1',k[1],'div',k[2]>>6,'cnt',k[2]&63,'sx0',k[3]-4096,'dx',k[4],'px',n)
"
