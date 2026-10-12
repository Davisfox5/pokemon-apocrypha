#!/usr/bin/env python3
"""Preserve the Route 29 / Route 30 build: patches, playable package, review boards and hashes.

Workbench history expected (tags in the isolated checkout): `preset` (the portable workbench preset) and `town`
(Claude's Cherrygrove from tools/gba/maps/claude_cherrygrove at the current revision); the working tree holds the
routes on top.

- gba/claude-cherrygrove.patch  preset -> town (refreshed: the committed copy predated the generator's last revision)
- gba/claude-routes.patch       town -> routes, checked forward on a clean `town` worktree and in reverse here
- tools/vendor/gba/Routes-claude-preview.zip   ROM + the ordinary save the checks wrote (ignored by git)
- gba/art/claude-routes/evidence/              boards from the in-game captures, comparisons, runtime and build records

    python3 tools/gba/maps/claude_routes/preserve.py tools/vendor/gba/claude-routes tools/vendor/gba/routes-check-NN
"""
from __future__ import annotations
import hashlib, json, platform, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from claude_routes import layouts as L  # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/claude-routes'; EV = ART / 'evidence'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(game, *a, **k): return subprocess.run(['git', '-C', str(game), *a], check=True, capture_output=True, **k)

def board(check, names, out, cols=3, z=2, title=None):
    W, H = 240 * z, 160 * z; rows = (len(names) + cols - 1) // cols; top = 22 if title else 0
    im = Image.new('RGB', (cols * (W + 6) - 6, top + rows * (H + 18)), (24, 26, 30)); d = ImageDraw.Draw(im)
    if title: d.text((4, 4), title, fill=(255, 255, 255))
    for i, (tag, label) in enumerate(names):
        t = Image.open(check / f'{tag}.png').resize((W, H), Image.NEAREST); x = (i % cols) * (W + 6); y = top + (i // cols) * (H + 18)
        im.paste(t, (x, y + 18)); d.text((x + 2, y + 3), label, fill=(230, 230, 230))
    im.save(out)

def compare(route, out):
    """The HGSS render beside this build's packed map, at the same 1:1 scale on the same cell grid."""
    ref = Image.open(ART / f'references/route{route}-hgss.png').convert('RGB'); mine = Image.open(ART / f'route{route}-overview.png').convert('RGB')
    ox, oy = {29: (4, 5), 30: (6, 4)}[route]
    ref = ref.crop((ox, oy, ox + mine.width, oy + mine.height))
    if route == 29: im = Image.new('RGB', (mine.width, mine.height * 2 + 30), (24, 26, 30)); im.paste(ref, (0, 20)); im.paste(mine, (0, mine.height + 30))
    else: im = Image.new('RGB', (mine.width * 2 + 20, mine.height + 20), (24, 26, 30)); im.paste(ref, (0, 20)); im.paste(mine, (mine.width + 20, 20))
    d = ImageDraw.Draw(im); d.text((4, 4), f'HGSS Route {route} (Bulbagarden render, 1:1)', fill=(255, 255, 255))
    d.text((4 if route == 29 else mine.width + 24, (mine.height + 14) if route == 29 else 4), f'This build (packed engine tiles, no characters)', fill=(255, 255, 255))
    im.save(out)

def structure(route):
    g = np.load(ART / f'route{route}-plan.npy'); col = open(ART / f'route{route}-collision.txt').read().split()
    solid = np.array([[c == '#' for c in line] for line in col])
    return dict(width=int(g.shape[1]), height=int(g.shape[0]), passable_cells=int((~solid).sum()), tall_grass_cells=int((g == 'G').sum()),
                ledge_cells=int((g == '_').sum()), path_cells=int((g == 'P').sum()), water_cells=int((g == 'W').sum()))

def main():
    game = Path(sys.argv[1]).resolve(); check = Path(sys.argv[2]).resolve(); EV.mkdir(parents=True, exist_ok=True)
    assert game != ROOT / 'game'
    # Patches.
    town_patch = git(game, 'diff', '--binary', 'preset', 'town').stdout
    git(game, 'add', '-A'); routes_patch = git(game, 'diff', '--cached', '--binary', 'town').stdout; git(game, 'reset', '-q')
    (ROOT / 'gba/claude-cherrygrove.patch').write_bytes(town_patch); (ROOT / 'gba/claude-routes.patch').write_bytes(routes_patch)
    subprocess.run(['git', '-C', str(game), 'apply', '--binary', '--check', '--reverse', str(ROOT / 'gba/claude-routes.patch')], check=True)
    wt = Path(tempfile.mkdtemp(prefix='routes-forward-')) / 'wt'
    git(game, 'worktree', 'add', '-q', '--detach', str(wt), 'town')
    try: subprocess.run(['git', '-C', str(wt), 'apply', '--binary', '--check', str(ROOT / 'gba/claude-routes.patch')], check=True)
    finally: git(game, 'worktree', 'remove', '--force', str(wt))
    stat = lambda p: subprocess.check_output(['git', '-C', str(game), 'apply', '--binary', '--stat', str(p)], text=True).strip().splitlines()[-1]
    # Package.
    zpath = ROOT / 'tools/vendor/gba/Routes-claude-preview.zip'
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(game / 'pokeemerald.gba', 'Routes-claude-preview.gba'); z.write(check / 'routes.sav', 'Routes-claude-preview.sav')
        z.writestr('README.txt', 'Pokemon Apocrypha - Cherrygrove with Route 29 and Route 30 (Claude build). Load the .gba with the .sav beside it and '
                                 'choose CONTINUE: you start at the Route 29 sea lookout. NEW GAME starts outside the player\'s house in Cherrygrove.\n')
    # Boards.
    board(check, [('r29-view-west', 'West end: blossom trees from Cherrygrove'), ('r29-view-lawn', 'Upper lawn, Apricorn tree, ledges'),
                  ('r29-view-centre', 'Centre woods'), ('r29-view-gate', 'Route 46 gate (closed)'), ('r29-view-south', 'South: the coast under the route'),
                  ('r29-view-lookout', 'Sea-view lookout'), ('r29-view-east-grass', 'East tall grass and ledge wall'), ('r29-view-east', 'East sign'),
                  ('route29-east-end', 'East edge (New Bark not built yet)')], EV / 'route29-in-game.png', title='Route 29, real engine captures (headless mGBA, 2x)')
    board(check, [('r30-view-south', 'Low steps above Cherrygrove'), ('r30-view-berry-house', 'Berry house and route sign'), ('r30-view-pond', 'Pond'),
                  ('r30-view-junction', 'Junction sign'), ('r30-view-middle', 'Middle steps'), ('r30-view-corridor', 'North corridor and tall grass'),
                  ('r30-view-plateau', 'Plateau'), ('mr-pokemon-house', "Mr. Pokemon's doorstep"), ('route30-top-steps', 'Steps up to Route 31')],
          EV / 'route30-in-game.png', title='Route 30, real engine captures (headless mGBA, 2x)')
    board(check, [(f'cross29-in-{i}', f'Cherrygrove -> Route 29, step {i}') for i in (0, 2, 4, 6, 8)] + [('seam-town-east', 'Cherrygrove east edge, before crossing')] +
                 [(f'cross29-out-{i}', f'Route 29 -> Cherrygrove, step {i}') for i in (0, 2, 4)] +
                 [(f'cross30-in-{i}', f'Cherrygrove -> Route 30, step {i}') for i in (0, 2, 4, 6)] + [('seam-town-north', 'Cherrygrove north edge, before crossing')] +
                 [(f'cross30-out-{i}', f'Route 30 -> Cherrygrove, step {i}') for i in (0, 2, 4, 6, 8)], EV / 'seams.png', cols=4, z=1,
          title='Walking across both map connections, every other step, both directions')
    board(check, [('sign-route29-west', 'Route 29 west sign'), ('sign-route29-east', 'Route 29 east sign'), ('sign-route30-junction', 'Route 30 junction sign'),
                  ('sign-route30-south', 'Route 30 south sign'), ('potion-found', 'Hidden Potion at the lookout'), ('route46-gate', 'Gate door stays shut'),
                  ('lookout', 'Railing holds'), ('continue-menu', 'Title screen Continue'), ('cold-reload', 'Cold reload at the lookout')],
          EV / 'interactions.png', title='Signs, the hidden Potion, collision and save/continue')
    for r in (29, 30): compare(r, EV / f'compare-route{r}.png')
    res = json.loads((check / 'results.json').read_text())
    (EV / 'runtime.json').write_text(json.dumps([dict(phase=p['phase'], exit_code=p['exit_code'], observations=p['observations']) for p in res], indent=1) + '\n')
    (EV / 'structure.json').write_text(json.dumps({f'route{r}': structure(r) for r in (29, 30)}, indent=2) + '\n')
    rec = dict(workbench_base_commit=git(game, 'rev-parse', 'town', text=True).stdout.strip(), rom_sha256=sha(game / 'pokeemerald.gba'), save_sha256=sha(check / 'routes.sav'),
               town_patch_sha256=sha(ROOT / 'gba/claude-cherrygrove.patch'), town_patch_stat=stat(ROOT / 'gba/claude-cherrygrove.patch'),
               routes_patch_sha256=sha(ROOT / 'gba/claude-routes.patch'), routes_patch_stat=stat(ROOT / 'gba/claude-routes.patch'),
               package=str(zpath.relative_to(ROOT)), package_sha256=sha(zpath), rom_bytes=(game / 'pokeemerald.gba').stat().st_size,
               toolchain=platform.system() + '-' + platform.machine() + ' ARM GNU 14.2.rel1',
               references={f'route{r}-hgss.png': sha(ART / f'references/route{r}-hgss.png') for r in (29, 30)})
    (EV / 'build.json').write_text(json.dumps(rec, indent=2) + '\n'); print(json.dumps(rec, indent=2))

if __name__ == '__main__':
    main()
