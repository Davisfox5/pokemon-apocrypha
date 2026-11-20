import sys
from PIL import Image
def readpal(p):
    l=open(p).read().split('\n')[3:]
    return [tuple(int(v) for v in x.split()) for x in l if x.strip()]
def decode(b,w=30,h=20):
    px=[[0]*(w*8) for _ in range(h*8)]
    for t in range(w*h):
        tx,ty=t%w,t//w
        for i in range(32):
            v=b[t*32+i]; y=i//4; x=(i%4)*2
            px[ty*8+y][tx*8+x]=v&15; px[ty*8+y][tx*8+x+1]=v>>4
    return px
def encode(px,w=30,h=20):
    out=bytearray(w*h*32)
    for t in range(w*h):
        tx,ty=t%w,t//w
        for i in range(32):
            y=i//4; x=(i%4)*2
            out[t*32+i]=px[ty*8+y][tx*8+x]|(px[ty*8+y][tx*8+x+1]<<4)
    return bytes(out)
def toimg(px,pal,scale=1):
    h=len(px);w=len(px[0]);im=Image.new('RGB',(w,h))
    im.putdata([pal[c] if c<len(pal) else (255,0,255) for row in px for c in row])
    return im.resize((w*scale,h*scale),Image.NEAREST)
if __name__=='__main__':
    b=open(sys.argv[1],'rb').read();pal=readpal(sys.argv[2])
    toimg(decode(b),pal,int(sys.argv[4])).save(sys.argv[3])
