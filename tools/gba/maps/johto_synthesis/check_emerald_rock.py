"""Compare packed route metatiles with the untouched Emerald donor pixels."""
from compose import ROOT, SOURCE, OUT, Tileset, Path, np
import json, sys

game = Path(sys.argv[1]).resolve()
layouts = json.loads((game/'data/layouts/layouts.json').read_text())['layouts']
donor = Tileset(SOURCE)
checks = []

def native(mid):
    return np.asarray(donor.render(mid))

def packed(name, secondary):
    m = json.loads((game/'data/maps'/name/'map.json').read_text())
    layout = next(v for v in layouts if v['id'] == m['layout'])
    grid = np.frombuffer((game/layout['blockdata_filepath']).read_bytes(), '<u2')
    return np.asarray(Tileset(game, secondary, 'cherrygrove').map_image(grid, layout['width']))

def verify(image, x, y, expected, label):
    h, w = expected.shape[:2]
    rgb = expected.astype(int)
    # The original lawn is intentionally transparent over our existing ground.
    mask = ~((rgb[...,1] > rgb[...,0]+15) & (rgb[...,1] > rgb[...,2]+15))
    actual = image[y*16:y*16+h, x*16:x*16+w]
    assert np.array_equal(actual[mask], expected[mask]), label
    checks.append(dict(name=label, x=x, y=y, exact_donor_pixels=int(mask.sum())))

r31 = packed('JohtoRoute31', 'route31')
for x in (33, 34):
    for y in (4, 10, 20, 27):
        verify(r31, x, y, native(0x75), 'east-facing cliff')
for x in (40, 41, 50):
    for y in (28, 29):
        verify(r31, x, y, native(0x7c), 'south-facing cliff')
verify(r31, 34, 28, native(0x76), 'inside corner')
verify(r31, 34, 29, native(0x7c), 'corner foot')
verify(r31, 12, 18, native(0x87), 'south jump ledge')
edge, tread = native(0xaf), native(0xcf)
north = np.tile(np.concatenate([edge, tread, tread], axis=1), (2, 1, 1))
east = np.rot90(np.tile(np.concatenate([edge, tread], axis=1), (2, 1, 1)))
verify(r31, 37, 28, north, 'north-south Emerald stairs')
verify(r31, 33, 16, east, 'east-west stairs, quarter turn')
r30 = packed('CherrygroveRoute30Approach', 'claude_route30')
verify(r30, 9, 0, north, 'Route 30 seam stairs')
verify(r30, 12, 0, native(0x7c), 'Route 30 adjoining rock')
verify(r30, 12, 1, native(0x79), 'Route 30 adjoining rock foot')
report = dict(source='Emerald primary/general', original_colors=True,
              resized=False, east_west_stairs_rotation_degrees=90,
              geometry_baseline='522b72e838bfc83f4929274d68fbca89fc95911b',
              checks=checks, passed=True)
(OUT/'evidence/emerald-rock-pixels.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
