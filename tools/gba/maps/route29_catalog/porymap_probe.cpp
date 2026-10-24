#include <QApplication>
#include <QDir>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <cstdio>
#include "project.h"
#include "map.h"
#include "config.h"
#include "loadingscreen.h"
// Porymap 6.3.1's own project loader and layout renderer: open the project, load each named map,
// render its layout as Porymap draws it, and save the image.
int main(int argc,char **argv){
 QApplication app(argc,argv);app.setApplicationName("porymap");app.setApplicationVersion("6.3.1");
 if(argc<4)return 2;
 porysplash=new PorymapLoadingScreen;
 QString root=QString::fromLocal8Bit(argv[1]),out=QString::fromLocal8Bit(argv[2]);QDir().mkpath(out);
 if(!projectConfig.load(root)||!userConfig.load(root))return 3;
 Project p;p.setRoot(root);if(!p.load())return 4;
 QJsonArray maps;
 for(int i=3;i<argc;i++){QString name=QString::fromLocal8Bit(argv[i]);
  Map *m=p.loadMap(name);if(!m)return 5;
  Layout *l=m->layout();l->render(true);if(l->image.isNull()||!l->image.save(out+"/"+name+".png"))return 6;
  maps.append(QJsonObject{{"map",name},{"width_px",l->image.width()},{"height_px",l->image.height()}});
 }
 QByteArray json=QJsonDocument(QJsonObject{{"porymap","6.3.1"},{"maps",maps}}).toJson();fwrite(json.constData(),1,json.size(),stdout);delete porysplash;return 0;
}
