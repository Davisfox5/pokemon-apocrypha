"""Complete-route walking tour, original ledges, material barriers, signs and ordinary save/Continue."""
from pathlib import Path
import sys,json
from collections import deque
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from johto_connections import runtime as r
S=ROOT/'gba/art/routes3839-complete/source'
T={n:json.loads((S/f'route{n}/traversal.json').read_text()) for n in [38,39]};M={n:np.fromfile(Path(sys.argv[1])/f'data/layouts/JohtoRoute{n}/map.bin','<u2').reshape(len(T[n]),-1) for n in T}
D=[('UP',0,-1),('RIGHT',1,0),('DOWN',0,1),('LEFT',-1,0)];J={'ledge_south':(0,1),'ledge_east':(1,0),'ledge_west':(-1,0)}
def cell(p):
 n,x,y=p
 return T[n][y][x] if 0<=y<len(T[n]) and 0<=x<len(T[n][0]) else None
def move(p,dx,dy):
 n,x,y=p;x+=dx;y+=dy
 if n==38 and x<0:n,x=39,31
 elif n==39 and x==32:n,x=38,0
 c=cell((n,x,y))
 if c and c['foot'] in J and J[c['foot']]==(dx,dy):x+=dx;y+=dy;c=cell((n,x,y))
 return (n,x,y) if c and c['foot']=='open' else None
def path(a,b):
 q=deque([a]);prev={a:None}
 while q:
  p=q.popleft()
  if p==b:break
  for key,dx,dy in D:
   z=move(p,dx,dy)
   if z and z not in prev:prev[z]=(p,key);q.append(z)
 assert b in prev,('unreachable',a,b)
 out=[];p=b
 while prev[p]:old,key=prev[p];out.append((key,p));p=old
 return out[::-1]
def at(p,label):return 'at(%d,%d,%d,"%s");'%(p[0]+15,p[1],p[2],label)
steps='go(54,23,62);shot("route39-south");\n';p=(39,23,62);tour=[]
for i,target in enumerate([(39,23,55),(39,14,50),(39,14,38),(39,19,29),(39,19,24),(39,9,30),(39,9,13),(39,9,5),(39,19,12),(38,2,12),(38,12,5),(38,20,6),(38,20,20),(38,21,25),(38,34,21),(38,52,12),(38,58,7),(38,62,7),(38,52,12),(39,28,12)]):
 route=path(p,target);tour+=route
 for key,z in route:steps+=f'step({key},1);'
 steps+=at(target,f'tour-{i:02}')+f'shot("tour-{i:02}");\n';p=target
# Every original jump ledge with valid approach and landing; check reverse blocking too.
ledge_count=0
for n,rows in T.items():
 for y,row in enumerate(rows):
  for x,c in enumerate(row):
   if c['foot'] not in J:continue
   dx,dy=J[c['foot']];a=(n,x-dx,y-dy);b=(n,x+dx,y+dy)
   if cell(a) and cell(b) and cell(a)['foot']==cell(b)['foot']=='open':
    key=next(k for k,xx,yy in D if (xx,yy)==(dx,dy));rev=next(k for k,xx,yy in D if (xx,yy)==(-dx,-dy));tag=f'ledge-{n}-{x}-{y}'
    steps+='go(%d,%d,%d);step(%s,1);'%(n+15,a[1],a[2],key)+at(b,tag)+f'step({rev},1);'+at(b,tag+'-reverse')+'\n';ledge_count+=1
# Cover each distinct native obstacle metatile/direction at an accessible boundary.
cases=[];seen=set()
for n,rows in T.items():
 for y,row in enumerate(rows):
  for x,c in enumerate(row):
   if c['foot']!='open':continue
   for key,dx,dy in D:
    z=(n,x+dx,y+dy);o=cell(z)
    if o and o['foot']=='blocked':
     k=(int(M[n][z[2],z[1]])&1023,key)
     if k in seen:continue
     seen.add(k);cases.append(dict(route=n,x=x,y=y,direction=key,obstacle=[z[1],z[2]],code=o['code']))
# Main run representative barriers; exhaustive distinct-art probes in a second invocation.
if '--boundaries' in sys.argv:
 sys.argv.remove('--boundaries');steps=''
 for i,c in enumerate(cases):steps+='go(%d,%d,%d);step(%s,1);'%(c['route']+15,c['x'],c['y'],c['direction'])+at((c['route'],c['x'],c['y']),f'boundary-{i}')+'\n'
else:
 for i,c in enumerate(cases[::max(1,len(cases)//24)]):steps+='go(%d,%d,%d);step(%s,1);'%(c['route']+15,c['x'],c['y'],c['direction'])+at((c['route'],c['x'],c['y']),f'barrier-{i}')+'\n'
 for n in T:
  for e in json.loads((S/f'route{n}/events.json').read_text())['signs']:
   if e['bg_type']==1:
    x,y=e['cell'];steps+=f'read_sign({n+15},{x},{y},"sign-{n}-{x}-{y}");\n'
 steps+='read_sign(54,9,4,"farmhouse-label");read_sign(54,4,4,"stable-label");\n'
 for n,x,y,key,count in [(38,20,6,'DOWN',12),(39,7,36,'DOWN',10)]:steps+=f'go({n+15},{x},{y});step({key},{count});need(overworld()&&!locked(),"grass-walk-{n}");shot("grass-{n}");\n'
steps+='go(53,59,5);shot("northeast-boulder");\n'
steps+='go(54,19,23);'+at((39,19,23),'save-route39')+'shot("save-route39");\n'
start=r.MAIN[:r.MAIN.index('  // Actual east connection')];end=r.MAIN[r.MAIN.index('  unsigned status=call("TrySavingData"'):]
r.MAIN=(start+steps+end).replace('at(11,27,18','at(54,19,23').replace('cold-reload-new-bark','cold-reload-route39')
E=S.parent/'evidence';(E/'runtime-plan.json').write_text(json.dumps(dict(tour_steps=len(tour),ledge_pairs=ledge_count,boundary_cases=cases),indent=2)+'\n')
if __name__=='__main__':r.main()
