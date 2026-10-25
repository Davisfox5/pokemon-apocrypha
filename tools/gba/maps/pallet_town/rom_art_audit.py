#!/usr/bin/env python3
"""Verify real ROM metatiles/attributes and mGBA VRAM/palettes, beyond source labels."""
from pathlib import Path
import json,subprocess,sys,struct,hashlib
import numpy as np
from PIL import Image
from native import Bank,words
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];E=Path(sys.argv[1]);RUN=Path(sys.argv[2]);EV=ROOT/'gba/art/pallet-town/evidence'
symbols={}
for line in subprocess.check_output(['arm-none-eabi-nm',str(E/'pokeemerald.elf')],text=True).splitlines():
 s=line.split()
 if len(s)==3:symbols[s[2]]=int(s[0],16)
rom=(E/'pokeemerald.gba').read_bytes();report=[]
sets=[('PalletOutdoor','palletoutdoor','ApocPallet','pallettown'),('PalletIndoor','palletindoor','PalletRedHouse','palletredhouse'),('PalletIndoor','palletindoor','PalletBedroom','palletbedroom'),('PalletIndoor','palletindoor','PalletOakHouse','palletoakhouse'),('PalletLabPrimary','palletlabprimary','PalletLab','palletlab')]
for mapid,(ps,pr,ss,se) in enumerate(sets,43):
 vram=(RUN/f'vram-{mapid}.bin').read_bytes();pals=(RUN/f'palette-{mapid}.bin').read_bytes();b=Bank(E,'primary/'+pr,'secondary/'+se,False);tiles=0
 for part,(sym,folder) in enumerate([(ps,'primary/'+pr),(ss,'secondary/'+se)]):
  d=E/'data/tilesets'/folder
  for name,p in [('gMetatiles_',d/'metatiles.bin'),('gMetatileAttributes_',d/'metatile_attributes.bin')]:
   expected=p.read_bytes();off=symbols[name+sym]-0x08000000;assert rom[off:off+len(expected)]==expected,(name,sym)
  for idx,tile in enumerate(b.tiles[part]):
   vals=list(tile.getdata());expected=bytes(vals[j]|vals[j+1]<<4 for j in range(0,64,2));off=(idx+part*512)*32;assert vram[off:off+32]==expected,(mapid,part,idx);tiles+=1
 expected=b''.join(struct.pack('<H',(r>>3)|((g>>3)<<5)|((bl>>3)<<10)) for bank in range(13) for r,g,bl in b.pals[bank>=6][bank])
 # The engine explicitly clears global BG backdrop slot 0; Porytiles writes magenta there.
 assert pals[:2]==b'\0\0',(mapid,'engine backdrop')
 assert pals[2:]==expected[2:],(mapid,'actual palette mismatch')
 report.append(dict(map=mapid,rom_metatiles_attributes_equal=True,vram_native_tiles_equal=tiles,background_palette_colors_equal=207,engine_backdrop_slot_0_black=True))
(EV/'rom-art-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
