set -e
cd /home/user/pokeemerald-expansion
git checkout HEAD -- data/tilesets/primary/violet_city data/tilesets/secondary/violet_city data/layouts/VioletCity
cd /tmp/claude-0/-home-user/85ee60ab-0025-575e-abae-bfbdaa5ee7ac/scratchpad/gates && python3 build.py /home/user/pokeemerald-expansion | grep -v "^merge" 
cd /home/user/pokeemerald-expansion && python3 /tmp/claude-0/-home-user/85ee60ab-0025-575e-abae-bfbdaa5ee7ac/scratchpad/gates/write.py . 2>/dev/null
for f in $(git diff --name-only | grep '\.pal$'); do sed -i 's/\r*$/\r/' $f; done 2>/dev/null
cd /home/user/pokemon-apocrypha && python3 - <<P 2>&1 | grep -v warning || true
import sys; sys.path.insert(0,'tools/gba/maps/violet_city'); sys.path.insert(0,'tools/gba/maps')
from pathlib import Path
import violet as V, numpy as np
from PIL import Image
S='/tmp/claude-0/-home-user/85ee60ab-0025-575e-abae-bfbdaa5ee7ac/scratchpad/'
img,_,_=V.decode(Path('/home/user/pokeemerald-expansion'))
Image.fromarray(img).save(S+'violet-new.png')
P
