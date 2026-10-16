"""Focused background R02 stairs/wall/ordinary save checks. Never opens desktop UI."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_connections import runtime as r
r.MAIN=r.MAIN[:r.MAIN.index('  // Actual east connection')]+r'''
 go(44,13,23);shot("west-approach");
 step(RIGHT,1);at(44,14,23,"west-step-center");shot("step-center");
 step(RIGHT,1);at(44,15,23,"west-stairs-eastward");shot("east-landing");
 step(LEFT,2);at(44,13,23,"west-stairs-westward");shot("west-return");
 go(44,13,22);step(RIGHT,2);at(44,15,22,"upper-row-eastward");shot("upper-row");
 step(LEFT,2);at(44,13,22,"upper-row-westward");
 go(44,13,20);step(RIGHT,1);at(44,13,20,"west-wall-blocks");shot("north-wall");
 go(44,15,20);step(LEFT,1);at(44,15,20,"east-wall-blocks");shot("raised-side");
 go(44,13,24);step(RIGHT,1);at(44,13,24,"lower-wall-blocks");shot("lower-wall");
 go(44,15,23);shot("save-location");
 unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''
r.MAIN=r.MAIN.replace('11,27,18','44,15,23').replace('cold-reload-new-bark','cold-reload-r02')
if __name__=='__main__':r.main()
