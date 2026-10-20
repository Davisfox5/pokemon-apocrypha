// Run only against a disposable project copy. Exercises native selector and paint/undo.
#include <QApplication>
#include <QFile>
#include <QJsonDocument>
#include <QJsonArray>
#include <QJsonObject>
#include <cstdio>
#include <cstdlib>
#include "project.h"
#include "map.h"
#include "config.h"
#include "loadingscreen.h"
#include "metatileselector.h"
#include "layoutpixmapitem.h"
#include "collisionpixmapitem.h"
static void check(bool v,const char *what){if(!v){fprintf(stderr,"FAIL: %s\n",what);exit(1);}}
class Selector:public MetatileSelector {
public:using MetatileSelector::MetatileSelector;
 void rectangle(QPoint a,QPoint b){
  QGraphicsSceneMouseEvent press(QEvent::GraphicsSceneMousePress);press.setPos(a*16+QPoint(1,1));mousePressEvent(&press);
  QGraphicsSceneMouseEvent move(QEvent::GraphicsSceneMouseMove);move.setPos(b*16+QPoint(1,1));mouseMoveEvent(&move);
 }
};
int main(int argc,char **argv){
 QApplication app(argc,argv);app.setApplicationName("porymap-selector-check");app.setApplicationVersion("6.3.1");
 if(argc!=3)return 2;
 porysplash=new PorymapLoadingScreen;
 QString root=argv[1];check(projectConfig.load(root)&&userConfig.load(root),"config");
 Project p;p.setRoot(root);check(p.load(),"project");auto m=p.loadMap(argv[2]);check(m,"map");auto l=m->layout();fprintf(stderr,"loaded map\n");
 QFile f(root+"/porymap.selector.json");check(f.open(QIODevice::ReadOnly),"catalog");auto raw=f.readAll();f.close();
 auto spec=QJsonDocument::fromJson(raw).object()["layouts"].toObject()[l->id].toObject();auto cells=spec["cells"].toArray();int w=spec["width"].toInt();
 fprintf(stderr,"catalog read\n");Selector s(8,l);s.refresh();check(s.pixmap().width()==w*16,"organized sheet activated");
 fprintf(stderr,"selector ready\n");int count=0;for(int i=0;i<cells.size();i++){int id=cells[i].toInt();if(id<0)continue;s.rectangle(QPoint(i%w,i/w),QPoint(i%w,i/w));auto sel=s.getMetatileSelection();check(sel.metatileItems.size()==1&&sel.metatileItems[0].enabled&&sel.metatileItems[0].metatileId==id,"cell maps to native ID");count++;}
 fprintf(stderr,"cells checked\n");int first=0,last=cells.size()-1;while(cells[first].toInt()<0)first++;while(cells[last].toInt()<0)last--;
 s.rectangle(QPoint(first%w,first/w),QPoint(last%w,last/w));auto sel=s.getMetatileSelection();int x0=qMin(first%w,last%w),y0=qMin(first/w,last/w),holes=0;
 for(int y=0;y<sel.dimensions.height();y++)for(int x=0;x<sel.dimensions.width();x++){int id=cells[(y0+y)*w+x0+x].toInt();auto item=sel.metatileItems[y*sel.dimensions.width()+x];check(item.enabled==(id>=0),"blank cells disabled");if(id<0)holes++;else check(item.metatileId==id,"rectangle native IDs");}
 fprintf(stderr,"rectangle checked\n");check(holes>0,"rectangle covers gaps");auto before=l->blockdata;Settings settings;LayoutPixmapItem painter(l,&s,&settings);l->setLayoutItem(&painter);qreal opacity=0.5;QSpinBox collision,elevation;CollisionPixmapItem collisionView(l,&collision,&elevation,&s,&settings,&opacity);painter.paint_tile_initial_x=0;painter.paint_tile_initial_y=0;painter.paintNormal(0,0);fprintf(stderr,"painted\n");check(l->blockdata!=before,"paint changes memory");l->editHistory.undo();check(l->blockdata==before,"undo restores exact map");
 int hidden=-1;for(int id=0;id<1024;id++)if(l->metatileIsValid(id)&&!cells.contains(id)){hidden=id;break;}
 check(hidden>=0,"hidden ID exists");s.selectFromMap(hidden,1,3);auto picked=s.getMetatileSelection();check(picked.metatileItems[0].metatileId==hidden&&picked.collisionItems[0].elevation==3,"hidden eyedropper preserves ID and movement");
 s.pixmap().save(root+"/selector-native.png");
 auto bad=QJsonDocument::fromJson(raw).object();auto layouts=bad["layouts"].toObject();auto broken=spec;broken["sources"]=QJsonObject{{"missing-file","bad-hash"}};layouts[l->id]=broken;bad["layouts"]=layouts;check(f.open(QIODevice::WriteOnly),"write invalid test catalog");f.write(QJsonDocument(bad).toJson());f.close();s.refresh();check(s.pixmap().width()==8*16,"stale revision falls back to stock selector");check(f.open(QIODevice::WriteOnly),"restore test catalog");f.write(raw);f.close();
 printf("PASS: %d visible cells, %d disabled gaps; paint/undo, hidden eyedropper, stale-catalog fallback\n",count,holes);
 return 0;
}
