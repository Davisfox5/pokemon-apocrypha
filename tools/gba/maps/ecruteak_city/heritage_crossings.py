"""Pair clear district-edge tiles with native directional warp behaviors.
No arrival skips the forecourt or lands inside a tree/building. Held north/south
input activates the matching arrow behavior; sideways walking stays in-district.
"""
from pathlib import Path
import json,sys,numpy as np
ROOT=Path(__file__).resolve().parents[4];G=Path(sys.argv[1]);S=ROOT/'gba/art/ecruteak-city/source';D=S/'heritage';solid=np.load(S/'solid.npy');beh=np.load(S/'behaviors.npy');columns=np.where(~solid[26]&~solid[27])[0].tolist();assert columns
for n,y,other,behavior,gy in [('JohtoEcruteakCity',0,'JohtoEcruteakTempleDistrict',100,27),('JohtoEcruteakTempleDistrict',26,'JohtoEcruteakCity',101,26)]:
 p=G/'data/maps'/n/'map.json';d=json.loads(p.read_text());assert not d['warp_events'];d['coord_events']=[];d['warp_events']=[dict(x=x,y=y,elevation=3,dest_map='MAP_JOHTO_ECRUTEAK_'+('CITY' if other.endswith('City') else 'TEMPLE_DISTRICT'),dest_warp_id=str(i)) for i,x in enumerate(columns)];p.write_text(json.dumps(d,indent=2)+'\n')
 for x in columns:beh[gy,x]=behavior
np.save(S/'behaviors.npy',beh);(D/'district-crossings.json').write_text(json.dumps(dict(columns=columns,north=dict(source=[51,0],destination=[52,26],behavior=100),south=dict(source=[52,26],destination=[51,0],behavior=101),old_coord_scripts_retained_unreferenced=True,matching_X_positions=True,all_arrivals_clear=True),indent=2)+'\n');print('Paired',len(columns),'clear district crossings')
