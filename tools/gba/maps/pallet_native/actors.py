"""Enable the two canonical Pallet actors for the Emerald build.
Their existing IDs, graphics, palettes, animation tables and dialogue stay intact.
Only these definitions move outside the FRLG compile guard.
"""
from pathlib import Path
import re,sys
E=Path(sys.argv[1]);root=E/'src/data/object_events'
plans={
 'object_event_graphics.h':[r'const u16 gObjectEventPic_ProfOak\[\] = [^\n]+\n',r'const u16 gObjectEventPic_Blue\[\] = [^\n]+\n'],
 'object_event_pic_tables.h':[r'static const struct SpriteFrameImage sPicTable_ProfOak\[\] = \{.*?\n\};\n',r'static const struct SpriteFrameImage sPicTable_Blue\[\] = \{.*?\n\};\n'],
 'object_event_graphics_info.h':[r'const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_ProfOak = \{.*?\n\};\n',r'const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_Blue = \{.*?\n\};\n'],
 'object_event_graphics_info_pointers.h':[r'    \[OBJ_EVENT_GFX_PROF_OAK\][^\n]+\n',r'    \[OBJ_EVENT_GFX_BLUE\][^\n]+\n'],
}
for name,patterns in plans.items():
 p=root/name;s=p.read_text()
 if '// Pallet actors are used in the Emerald campaign.' in s:continue
 blocks=[]
 for pat in patterns:
  found=list(re.finditer(pat,s,re.S));assert len(found)==1,(name,pat);m=found[0];blocks.append(m[0]);s=s[:m.start()]+s[m.end():]
 marker='#if IS_FRLG';idx=s.index(marker);s=s[:idx]+'// Pallet actors are used in the Emerald campaign.\n'+''.join(blocks)+'\n'+s[idx:];p.write_text(s)
# Their palette registrations were also behind the FRLG guard.
for p,patterns in [
 (root/'object_event_graphics.h',[r'const u16 gObjectEventPal_NpcGreen\[\] = [^\n]+\n',r'const u16 gObjectEventPal_NpcWhite\[\] = [^\n]+\n']),
 (E/'src/event_object_movement.c',[r'    \{gObjectEventPal_NpcGreen,[^\n]+\n',r'    \{gObjectEventPal_NpcWhite,[^\n]+\n'])]:
 s=p.read_text();marker='// Pallet actor palettes are available in Emerald.'
 if marker in s:continue
 chunks=[];insertion=None
 for pat in patterns:
  m=re.search(pat,s);assert m,(p,pat)
  insertion=s.rfind('#if IS_FRLG',0,m.start());assert insertion>=0
  chunks.append(m[0]);s=s[:m.start()]+s[m.end():]
 s=s[:insertion]+marker+'\n'+''.join(chunks)+s[insertion:];p.write_text(s)
