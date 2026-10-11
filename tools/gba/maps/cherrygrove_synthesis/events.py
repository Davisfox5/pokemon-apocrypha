"""Small reviewed corrections to the frozen E event snapshot; keep warp IDs stable."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[4]
SNAPSHOT=ROOT/'gba/art/cherrygrove-synthesis/references/E'
CHANGED={'CherrygroveCity','CherrygroveTransplantHouse'}
def expected_events(name):
    data=json.loads((SNAPSHOT/f'data/maps/{name}/map.json').read_text())
    if name=='CherrygroveCity':
        # Keep the three-cell stroll entirely in the lane west of GardenHouse.
        npc=next(e for e in data['object_events'] if e['local_id']=='LOCALID_COMPARE_UNOVA')
        assert npc['x']==62 and npc['y']==29
        npc['x']=61
    if name=='CherrygroveTransplantHouse':
        # Obsolete room has no exterior entrance. Old saves/test entry must still
        # escape safely: use the visible harbor house instead of the forest.
        for warp in data['warp_events']:
            assert warp['dest_map']=='MAP_CHERRYGROVE_CITY' and warp['dest_warp_id']=='3'
            warp['dest_warp_id']='6'
    return data
def apply_events(game):
    for name in sorted(CHANGED):
        (game/f'data/maps/{name}/map.json').write_text(json.dumps(expected_events(name),indent=2)+'\n')
if __name__=='__main__':
    import sys
    apply_events(Path(sys.argv[1]))
