"""Static Nitro display lists with vertex colors retained for native conversion.
The shared reference renderer drops COLOR commands; these colors carry the
cushion joins and lighting of HGSS's small, solid-texture furniture models.
"""
import struct
import numpy as np

def faces(model,decoder):
 for mid,sid in model.pairs:
  dl=model.dls[sid];p=0;pos=(0.,0.,0.);uv=(0.,0.);color=(1.,1.,1.);verts=[];mode=None
  while p+4<=len(dl):
   ops=dl[p:p+4];p+=4
   for op in ops:
    n=decoder._PARAMS.get(op)
    if n is None:raise ValueError(f'Unsupported Nitro opcode {op:x}')
    params=struct.unpack_from('<'+'I'*n,dl,p);p+=n*4;v=params[0] if params else 0;vertex=False
    if op==0x20:color=tuple(((v>>s)&31)/31 for s in (0,5,10))
    elif op==0x40:mode=v&3;verts=[]
    elif op==0x41:mode=None
    elif op==0x22:uv=(decoder._s16(v&65535)/16,decoder._s16(v>>16)/16)
    elif op==0x23:pos=(decoder._s16(v&65535)/4096,decoder._s16(v>>16)/4096,decoder._s16(params[1]&65535)/4096);vertex=True
    elif op==0x24:pos=tuple(decoder._s10(v>>s)/64 for s in (0,10,20));vertex=True
    elif op==0x25:pos=(decoder._s16(v&65535)/4096,decoder._s16(v>>16)/4096,pos[2]);vertex=True
    elif op==0x26:pos=(decoder._s16(v&65535)/4096,pos[1],decoder._s16(v>>16)/4096);vertex=True
    elif op==0x27:pos=(pos[0],decoder._s16(v&65535)/4096,decoder._s16(v>>16)/4096);vertex=True
    elif op==0x28:pos=tuple(pos[k]+decoder._s10(v>>s)/32768 for k,s in enumerate((0,10,20)));vertex=True
    if not vertex or mode is None:continue
    verts.append((tuple(x*model.up_scale for x in pos),uv,color))
    if mode==0 and len(verts)==3:yield mid,verts;verts=[]
    elif mode==1 and len(verts)==4:yield mid,verts;verts=[]
    elif mode==2 and len(verts)>=3:
     a,b,c=verts[-3:];yield mid,[a,b,c] if len(verts)%2 else [b,a,c]
    elif mode==3 and len(verts)>=4 and len(verts)%2==0:
     a,b,d,c=verts[-4:];yield mid,[a,b,c,d]
