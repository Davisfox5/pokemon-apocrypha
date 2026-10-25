"""Pack locally authored heritage layers exactly; preserve foreground priority."""
from pathlib import Path
import json,sys,shutil
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/ecruteak-city/source';E=S.parent/'evidence';D=S/'heritage';B=D/'baseline';G=Path(sys.argv[1]);PT=Path(sys.argv[2]);bg=np.array(Image.open(S/'background.png'));fg=np.array(Image.open(S/'foreground.png'));solid=np.load(S/'solid.npy');above=np.load(D/'above.npy');r=json.loads((E/'assembly.json').read_text())
for short in (['city','temple'] if len(sys.argv)>3 else []):shutil.copyfile(Path(sys.argv[3])/('heritage-'+short+'-cover/exact-palette-cover.json'),D/(short+'-flexible-cover.json'))
from tree_layers import encode,finish
protect=(~solid)|(above&solid&np.vstack([~solid[1:],np.zeros((1,72),bool)]));pm=protect.repeat(16,0).repeat(16,1);before=fg.copy();a=encode(S,bg,fg,solid,[(0,0,1152,832)],covers_dir=D,preserve_existing=True);b=finish(S,bg,fg,solid);assert np.array_equal(fg[pm],before[pm])
for n,v in [('background',bg),('foreground',fg)]:Image.fromarray(v).save(S/(n+'.png'))
from palette_order import preserve
orders={bank:preserve(G,S,B,bank) for bank in ['ecruteak_city','ecruteak_temple']};(D/'packing.json').write_text(json.dumps(dict(exact_layer_changes=a,finish=b,palette_slot_orders=orders),indent=2)+'\n')
print('Exact layer packing and palette order complete; compile only after hidden-glyph reuse and native fixture registration.')
