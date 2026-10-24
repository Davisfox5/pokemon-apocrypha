"""Porymap round trip for Saffron City (KantoSaffronCity): open, export, save, diff.

    python3 tools/gba/maps/saffron/porymap.py ENGINE_CHECKOUT PORYMAP_BINARY

Works on a fresh `git clone` of ENGINE_CHECKOUT's current branch in a temporary
directory, never on the checkout itself (commit the engine first). Under Xvfb it opens
KantoSaffronCity (on its own pair, gTileset_KantoSaffronPrimary and
gTileset_KantoSaffronCity) and its five interiors in Porymap, exports Porymap's own map
image of each, saves the city's tilesets from the tileset editor, saves every map
(File > Save), then reports what Porymap rewrote and how its city image compares with
the native decode (check.render_blocks, which Porymap draws the same way: a bottom
pixel of colour 0 shows the BG3 fill; see frlg.under).

Needs Xvfb, xdotool and ImageMagick `import`. Menu coordinates are Porymap 6.3.1's
Fusion layout with the main window at 1920x1050; keyboard shortcuts do not reach
Porymap without a window manager, so everything goes through menus.
Writes evidence/porymap/{results.json,*.png}.
"""
from __future__ import annotations
import json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EV = ROOT / 'gba/art/saffron-kanto/evidence'
CITY = 'KantoSaffronCity'
INTERIORS = ['KantoSaffronPokemonCenter', 'KantoSaffronCenterUpstairs', 'KantoSaffronMart', 'KantoSaffronDojo', 'KantoSaffronSilphLab']
DISPLAY = ':99'
ENV = dict(os.environ, DISPLAY=DISPLAY)

def sh(*a, check=True):
    return subprocess.run(a, env=ENV, check=check, capture_output=True, text=True).stdout.strip()

def click(x, y, wait=1.0):
    sh('xdotool', 'mousemove', str(x), str(y), 'click', '1'); time.sleep(wait)

def window(pattern, tries=120):
    for _ in range(tries):
        w = sh('xdotool', 'search', '--onlyvisible', '--name', pattern, check=False).split()
        if w:
            return w[0]
        time.sleep(1)
    raise SystemExit(f'no window matching {pattern!r}')

def shot(path):
    sh('import', '-window', 'root', str(path))

def launch(binary, project, cfg, m):
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / 'porymap.cfg').write_text(f'recent_project={project}\nreopen_on_launch=1\nproject_manually_closed=0\n'
                                     'check_for_updates=0\nshow_project_loading_screen=0\nshown_in_game_reload_message=1\n')
    (project / 'porymap.user.cfg').write_text(f'recent_map_or_layout={m}\n')
    p = subprocess.Popen([binary], env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    w = window(f'^{m} - ')
    time.sleep(4)
    sh('xdotool', 'windowsize', w, '1920', '1050'); sh('xdotool', 'windowmove', w, '0', '0'); time.sleep(2)
    return p

def export(item_y, out):
    click(19, 8); click(100, item_y, 3)                     # File > Export Map Image
    geo = dict(l.split('=') for l in sh('xdotool', 'getwindowgeometry', '--shell', window('^Export Map')).splitlines())
    click(int(geo['X']) + 756, int(geo['Y']) + 524, 3)      # Save
    sh('xdotool', 'key', 'ctrl+a'); sh('xdotool', 'type', '--delay', '5', str(out)); sh('xdotool', 'key', 'Return')
    time.sleep(4)

def main(engine, binary):
    native = np.array(Image.open(EV / 'native.png').convert('RGB'))
    out = EV / 'porymap'
    out.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp())
    project = work / 'pokeemerald-expansion'                # Porymap detects the base game from the folder name
    branch = sh('git', '-C', str(engine), 'rev-parse', '--abbrev-ref', 'HEAD')
    sh('git', 'clone', '-q', '-b', branch, str(engine), str(project))
    head = sh('git', '-C', str(project), 'rev-parse', 'HEAD')
    cfg = Path.home() / '.local/share/pret/porymap'
    log = cfg / 'porymap.log'
    log_start = log.stat().st_size if log.exists() else 0
    started = time.time()
    xvfb = subprocess.Popen(['Xvfb', DISPLAY, '-screen', '0', '1920x1080x24'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    try:
        for m in [CITY] + INTERIORS:
            p = launch(binary, project, cfg, m)
            shot(out / f'{m}-porymap.png')
            export(314, work / f'{m}.png')
            if m == CITY:
                click(137, 8); click(180, 171, 5)           # Tools > Tileset Editor
                t = window('^Tileset Editor')
                sh('xdotool', 'windowmove', t, '0', '0'); time.sleep(1)
                shot(out / 'tileset-editor.png')
                click(19, 8); click(60, 31, 5)              # File > Save Tileset
                sh('xdotool', 'windowmove', t, '900', '600'); time.sleep(1)
            click(19, 8); click(49, 125, 4)                 # File > Save
            p.terminate(); p.wait(10)
    finally:
        xvfb.terminate()
    e = np.array(Image.open(work / f'{CITY}.png').convert('RGB'))
    ref = native[:e.shape[0], :e.shape[1]]
    city = dict(size=list(e.shape[1::-1]), differing_pixels=int((e != ref).any(axis=2).sum()))
    shutil.copy(work / f'{CITY}.png', out / f'{CITY}-export.png')
    diff = sh('git', '-C', str(project), 'diff', '-U0')
    changed_lines = [l for l in diff.splitlines() if l[:1] in ('+', '-') and not l.startswith(('+++', '---'))]
    rewritten = [str(p.relative_to(project)) for p in project.rglob('*') if p.is_file() and '.git' not in p.parts
                 and p.stat().st_mtime > started and 'porymap.' not in p.name]
    log_text = log.read_text(errors='replace')[log_start:] if log.exists() else ''
    report = dict(
        porymap=next((l.split('] ', 1)[1] for l in log_text.splitlines() if 'Launching Porymap' in l), 'unknown'),
        engine_commit=head, city_export_vs_native=city,
        saffron_files_rewritten=sorted(r for r in rewritten if 'affron' in r),
        saffron_files_changed=sorted(f for f in sh('git', '-C', str(project), 'diff', '--name-only').splitlines() if 'affron' in f),
        files_changed_by_save=sh('git', '-C', str(project), 'diff', '--name-only').splitlines(),
        changed_lines_mentioning_saffron=[l for l in changed_lines if 'affron' in l or 'AFFRON' in l],
        changed_lines=changed_lines,
        log_errors=[l for l in log_text.splitlines() if '[ERROR]' in l],
        log_warnings=sorted({l.split('] ', 1)[1] for l in log_text.splitlines() if '[WARN]' in l}),
        note='The export is Porymap\'s own render, compared with the native decode. Lines changed by save that do not '
             'mention Saffron are Porymap normalising entries that predate it (key order, \\u escapes).')
    (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    shutil.rmtree(work)
    print(json.dumps({k: v for k, v in report.items() if k != 'changed_lines'}, indent=2))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), str(Path(sys.argv[2]).resolve()))
