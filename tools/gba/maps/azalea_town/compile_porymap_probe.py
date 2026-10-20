"""Link the headless exporter against an installed, already-built Porymap tree."""
from pathlib import Path
import sys,re,shlex,subprocess
root,out=map(Path,sys.argv[1:3]);text=(root/'Makefile').read_text();source=Path(__file__).with_name('porymap_probe.cpp').resolve()
def var(name):return re.search(r'^'+name+r'\s*=\s*(.*)$',text,re.M)[1]
defines=var('DEFINES');flags=shlex.split(var('CXXFLAGS').replace('$(DEFINES)',defines));includes=shlex.split(var('INCPATH'));libs=shlex.split(var('LIBS').replace('$(SUBLIBS)',''));objects=[str(p) for p in root.glob('*.o') if p.name not in ['main.o','probe.o']];subprocess.run(['g++',*flags,*includes,str(source),*objects,'-L/workspace/deps/root/usr/lib/x86_64-linux-gnu',*libs,'-o',str(out)],cwd=root,check=True)
