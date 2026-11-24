import sys
from PIL import Image
im=Image.open(sys.argv[1]).convert('RGB'); w=im.width//3; p=im.load()
y0=int(sys.argv[2]) if len(sys.argv)>2 else 0; y1=int(sys.argv[3]) if len(sys.argv)>3 else 200
tot=0
for by in range(y0,y1,8):
    cols={}
    for y in range(by,min(by+8,y1)):
        for x in range(320):
            a=p[x*2,y*2]; b=p[x*2+w,y*2]
            if any(abs(a[k]-b[k])>8 for k in range(3)): cols[x]=cols.get(x,0)+1
    tot+=sum(cols.values())
    xs=sorted(cols); runs=[]
    for x in xs:
        if runs and x-runs[-1][1]<=2: runs[-1][1]=x; runs[-1][2]+=cols[x]
        else: runs.append([x,x,cols[x]])
    print(by, sum(cols.values()), ' '.join('%d-%d:%d'%tuple(r) for r in runs if r[2]>=3))
print('total',tot)
