#!/usr/bin/env python3
"""Record real NPC movement, check directions/palettes/collision, and render evidence."""
import argparse, json, struct, subprocess
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
p = argparse.ArgumentParser()
p.add_argument('game', type=Path)
p.add_argument('output', type=Path)
p.add_argument('--toolchain', type=Path, required=True)
p.add_argument('--reuse-recording', action='store_true')
a = p.parse_args()
game, out = a.game.resolve(), a.output.resolve()
assert game == ROOT/'tools/vendor/gba/johto-npc-v1-game'
out.mkdir(parents=True, exist_ok=True)
evidence = ROOT/'gba/art/johto-npc-v1/evidence'
if not a.reuse_recording:
    lines = subprocess.check_output([str(a.toolchain.resolve()/'bin/arm-none-eabi-nm'), str(game/'pokeemerald.elf')], text=True)
    wanted = {'MapProof_Boot', 'MapProof_Enter', 'gObjectEvents', 'gSprites', 'ArePlayerFieldControlsLocked'}
    symbols = {r[2]:r[0] for line in lines.splitlines() if len(r:=line.split()) == 3 and r[2] in wanted}
    assert symbols.keys() == wanted
    (out/'symbols.txt').write_text(''.join(f'{k} {v}\n' for k,v in symbols.items()))
    subprocess.run(['cc', '-I/opt/homebrew/opt/mgba/include', str(ROOT/'tools/gba/maps/johto_npc_runtime.c'), '-L/opt/homebrew/opt/mgba/lib', '-lmgba', '-o', str(out/'runtime')], check=True)
    with (out/'movement.jsonl').open('w') as f:
        subprocess.run([str(out/'runtime'), str(game/'pokeemerald.gba'), str(out/'symbols.txt'), str(out)], stdout=f, check=True, timeout=180)

data = [json.loads(l) for l in (out/'movement.jsonl').read_text().splitlines()]
rows = [r for r in data if 'objects' in r]
assert len(rows) == 360
assert data[-1] == dict(interaction=True, faces_player=True, stops_for_dialogue=True, resumes_walking=True)
layouts = json.loads((game/'data/layouts/layouts.json').read_text())['layouts']
layout = next(l for l in layouts if l['id'] == 'LAYOUT_CHERRYGROVE_CITY')
raw = (game/layout['blockdata_filepath']).read_bytes()
grid = struct.unpack('<'+'H'*(len(raw)//2), raw)
for row in rows:
    objects = row['objects']
    assert {o['gfx'] for o in objects} == {1024,1025,1026}
    assert len({o['palette'] for o in objects}) == 3
    assert len({(o['x'],o['y']) for o in objects}) == 3
    for o in objects:
        assert not o['hflip']
        assert o['anim'] == o['facing'] + 3  # standard walk S/N/W/E = 4/5/6/7
        assert not ((grid[o['y']*layout['width']+o['x']] >> 10) & 3)
summary = []
for gid, name, directions, positions in [
    (1024,'Boy',{3,4},{(46,11),(47,11),(48,11)}),
    (1025,'Girl',{1,2},{(52,11),(52,12)}),
    (1026,'Man',{1,2,3,4},{(49,14),(49,15),(50,14),(50,15)})]:
    objects = [o for r in rows for o in r['objects'] if o['gfx'] == gid]
    assert {o['facing'] for o in objects} == directions
    assert {(o['x'],o['y']) for o in objects} == positions
    commands = {direction:sorted({o['cmd'] for o in objects if o['facing'] == direction}) for direction in directions}
    # One-tile turns may change direction partway through the four-command loop.
    assert all(len(values) >= 2 for values in commands.values())
    assert {o['cmd'] for o in objects} == {0,1,2,3}
    summary.append(dict(name=name, graphics_id=gid, positions=sorted(positions), directions=sorted(directions), commands_by_direction=commands, all_walk_commands_seen_across_route=True))

native = ROOT/'gba/art/johto-npc-v1/native'
for name in ['boy','girl','man','woman','clerk']:
    compiled = game/f'build/assets/graphics/object_events/pics/people/johto/{name}.png_mwidth_4__mheight_4.4bpp'
    palette = game/f'build/assets/graphics/object_events/palettes/johto_{name}.pal.gbapal'
    assert compiled.read_bytes() == (native/f'{name}.4bpp').read_bytes()
    assert palette.read_bytes() == (native/f'{name}.gbapal').read_bytes()

report = dict(samples=len(rows), observed_engine_frames=1440, read_only_struct_probe=True,
              collision_clear=True, distinct_npc_palettes=True, no_horizontal_mirroring=True,
              compiled_assets_exact=True, residents=summary, interaction=data[-1])
(evidence/'movement.json').write_text(json.dumps(report,indent=2)+'\n')
(evidence/'movement.jsonl').write_bytes((out/'movement.jsonl').read_bytes())
# Display scaling only; the ROM keeps native 32x32 animation cells.
frames = [Image.open(out/f'npc-{i:03d}.ppm').resize((720,480),Image.Resampling.NEAREST) for i in range(360)]
frames[0].save(evidence/'walking.gif', save_all=True, append_images=frames[1:], duration=[70,60,70]*120, loop=0, optimize=True)
Image.open(out/'residents.ppm').save(evidence/'residents-native.png')
frames[0].save(evidence/'residents.png')
run = ROOT/'tools/vendor/gba/johto-npc-v1-run'
board = Image.new('RGB',(960,700),'#15262b'); draw=ImageDraw.Draw(board)
for i,(label,file) in enumerate([
    ('Walking resident: stops and faces the player',out/'walking-resident-dialogue.ppm'),
    ('Walking resumes after the conversation',out/'walking-resident-resumed.ppm'),
    ('Waterfront resident: existing dialogue',run/'waterfront-dialogue.ppm'),
    ('Johto shop clerk: functioning shop menu',run/'mart-menu.ppm')]):
    x,y=i%2*480,i//2*350
    board.paste(Image.open(file).resize((480,320),Image.Resampling.NEAREST),(x,y+25))
    draw.text((x+10,y+7),label,fill='white')
board.save(evidence/'interactions.png')
print(json.dumps(report,indent=2))
