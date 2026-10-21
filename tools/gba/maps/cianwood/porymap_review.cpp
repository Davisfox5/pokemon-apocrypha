#include "mainwindow.h"
#include "loadingscreen.h"

#include <QApplication>
#include <QDir>
#include <QDebug>

template<class Tag, typename Tag::type Member> struct ReviewAccess { friend typename Tag::type access(Tag) { return Member; } };
struct ReviewOpen { using type=bool(MainWindow::*)(QString,bool); friend type access(ReviewOpen); };
template struct ReviewAccess<ReviewOpen, &MainWindow::openProject>;

int main(int argc, char *argv[])
{
    QGuiApplication::setHighDpiScaleFactorRoundingPolicy(Qt::HighDpiScaleFactorRoundingPolicy::Round);
    QCoreApplication::setAttribute(Qt::AA_UseStyleSheetPropagationInWidgetStyles, true);

    QApplication a(argc, argv);
    a.setStyle("fusion");

    porysplash = new PorymapLoadingScreen;

    QObject::connect(&a, &QCoreApplication::aboutToQuit, [=]() { delete porysplash; });

    MainWindow w(nullptr);
    w.initialize();

    if (argc == 3) {
        if (!(w.*access(ReviewOpen{}))(QString::fromLocal8Bit(argv[1]),true)) return 10;
        QDir().mkpath(QString::fromLocal8Bit(argv[2]));
        for (const QString &name : {QString("CianwoodCity"),QString("CianwoodPokemonCenter"),QString("CianwoodCenterUpstairs")}) {
            if (!w.editor->setMap(name)) return 11;
            if (!w.editor->layout->render(true).save(QString::fromLocal8Bit(argv[2])+"/"+name+".png")) return 12;
            qInfo() << "PORYMAP_EXPORT" << name << w.editor->layout->getWidth() << w.editor->layout->getHeight();
        }
        return 0;
    }
    return a.exec();
}
