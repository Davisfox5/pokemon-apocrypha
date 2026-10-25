"""Full gameplay plus fixture-count checks after menu return and Continue."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import runtime
r=runtime.r
probe=r'''
static void fixture_counts(const char *tag){
 unsigned base=sym("gObjectEvents");int shrine=0,counter=0;
 // include/global.fieldmap.h: ObjectEvent size 0x24, graphicsId at 4.
 for(int i=0;i<16;i++){
  unsigned p=base+i*0x24;
  if(!(c->busRead8(c,p)&1)||c->busRead8(c,p+9)!=51||c->busRead8(c,p+10)!=80)continue;
  unsigned gfx=c->busRead16(c,p+4);shrine+=gfx==1037;counter+=gfx==1038;
 }
 observe(tag);need(shrine==1&&counter==1,tag);
}
'''
r.MAIN=probe+r.MAIN
r.MAIN=r.MAIN.replace('shot("cold-reload");','shot("cold-reload");fixture_counts("reload-exactly-two-fixtures");').replace('shot("title-continue");','shot("title-continue");fixture_counts("Continue-exactly-two-fixtures");')
r.MAIN=r.MAIN.replace(' go(51,41,8);shot("save-Ecruteak");',' go(51,41,8);shot("save-Ecruteak");fixture_counts("new-map-exactly-two-fixtures");frames(1,8);frames(120,0);frames(1,B);frames(240,0);at(51,41,8,"menu-return-same-position");fixture_counts("menu-return-no-duplicates");')
if __name__=='__main__':r.main()
