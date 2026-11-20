#!/usr/bin/env python3
"""Headless mGBA check of the Hidden Grotto mechanic against a built engine.

    python3 tools/gba/grottoes/runtime.py ENGINE OUT

ENGINE is a built pokeemerald-expansion checkout (pokeemerald.gba and pokeemerald.elf present).
Needs the GBA toolchain on PATH (arm-none-eabi-gcc/nm, see tools/gba/portable.py) and libmgba-dev.
Runs runtime.c twice (write, then a cold reload of its save), writes results.json, the frames as
PNG and a contact sheet to OUT. MGBA_FLAGS overrides the libmgba link flags.
"""
from __future__ import annotations
import json, os, shlex, struct, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
RUNTIME_C = HERE.parent / 'maps/runtime.c'
SYMBOLS = ['gMain', 'CB2_Overworld', 'gMapProofState', 'MapProof_ReadState', 'MapProof_Enter', 'MapProof_Boot',
           'MapProof_Resume', 'ArePlayerFieldControlsLocked', 'gSaveBlock3Ptr', 'gSaveBlock2Ptr', 'GetHiddenGrottoState',
           'UpdateHiddenGrottoStepCounter', 'gHiddenGrottoes', 'gParties', 'ScriptGiveMon', 'GetMonData2',
           'GetMonAbility', 'GetAbilityBySpecies', 'GetMonGender', 'CheckBagHasItem', 'TrySavingData',
           'LoadGameSave', 'FlagGet', 'ScriptContext_IsEnabled']
PROBE = r'''
#include "global.h"
#include "pokemon.h"
#include "constants/items.h"
#include "constants/hidden_grotto.h"
extern const u16 sMapProofMaps[];
const int kvals[] = {
  __builtin_offsetof(struct SaveBlock3, hiddenGrottoes), __builtin_offsetof(struct SaveBlock3, hiddenGrottoSteps),
  sizeof(struct Pokemon), MON_DATA_ABILITY_NUM, MON_DATA_SPECIES, MON_DATA_LEVEL, MON_DATA_IS_SHINY,
  MAP_GROUP(MAP_HIDDEN_GROTTO), MAP_NUM(MAP_HIDDEN_GROTTO), MAP_GROUP(MAP_PROOF_JOHTO), MAP_NUM(MAP_PROOF_JOHTO), ITEM_PEARL };
'''
KNAMES = ['K_SB3_GROTTOES', 'K_SB3_STEPS', 'K_MON_SIZE', 'K_MD_ABILITY_NUM', 'K_MD_SPECIES', 'K_MD_LEVEL',
          'K_MD_IS_SHINY', 'K_GROTTO_GROUP', 'K_GROTTO_NUM', 'K_PROOF_GROUP', 'K_PROOF_NUM', 'K_ITEM_PEARL']


def constants(engine: Path, tmp: Path):
    src = tmp / 'probe.c'; obj = tmp / 'probe.o'; raw = tmp / 'probe.bin'
    src.write_text(PROBE)
    subprocess.run(['arm-none-eabi-gcc', '-mthumb', '-mabi=apcs-gnu', '-march=armv4t', '-iquote', 'include', '-DMODERN=1',
                    '-DTESTING=0', '-DEMERALD', '-std=gnu17', '-w', '-c', str(src), '-o', str(obj)], cwd=engine, check=True)
    subprocess.run(['arm-none-eabi-objcopy', '-O', 'binary', '-j', '.rodata', str(obj), str(raw)], check=True)
    vals = struct.unpack(f'<{len(KNAMES)}i', raw.read_bytes()[:4 * len(KNAMES)])
    k = dict(zip(KNAMES, vals))
    # MapProof_Enter takes an index into sMapProofMaps; MAP_PROOF_JOHTO is the list's last entry.
    text = (engine / 'src/apocrypha_map_proof.c').read_text()
    body = text[text.index('sMapProofMaps[] = {') + 19:]; body = body[:body.index('}')]
    entries = [e.strip() for e in body.split(',')]
    k['K_PROOF_INDEX'] = entries.index('MAP_PROOF_JOHTO')
    return k


def symbols(engine: Path):
    out = subprocess.run(['arm-none-eabi-nm', str(engine / 'pokeemerald.elf')], capture_output=True, text=True, check=True).stdout
    table = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2] in SYMBOLS:
            table[parts[2]] = int(parts[0], 16)
    missing = sorted(set(SYMBOLS) - set(table))
    if missing:
        sys.exit('missing symbols: ' + ', '.join(missing))
    return table


def sheet(out: Path, frames: list[str]):
    tiles = [Image.open(out / f'{f}.png') for f in frames]
    cols = 4; w, h = 240, 160 + 14
    im = Image.new('RGB', (cols * w, ((len(tiles) + cols - 1) // cols) * h), 'white')
    d = ImageDraw.Draw(im)
    for i, (t, f) in enumerate(zip(tiles, frames)):
        x, y = (i % cols) * w, (i // cols) * h
        im.paste(t, (x, y + 14)); d.text((x + 3, y + 1), f, fill='black')
    im.save(out / 'contact-sheet.png')


def main(argv):
    if len(argv) != 3:
        print(__doc__); return 2
    engine, out = Path(argv[1]).resolve(), Path(argv[2]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        table = symbols(engine); table.update(constants(engine, tmp))
        symfile = tmp / 'symbols.txt'
        symfile.write_text(''.join(f'{n} {v:x}\n' for n, v in table.items()))
        src = tmp / 'grotto_runtime.c'
        src.write_text((HERE / 'runtime.c').read_text().replace('"RUNTIME_C"', json.dumps(str(RUNTIME_C))))
        exe = tmp / 'grotto_runtime'
        flags = shlex.split(os.environ.get('MGBA_FLAGS', '')) or ['-lmgba']
        subprocess.run(['cc', '-O1', '-w', str(src), '-o', str(exe)] + flags, check=True)
        log = {}
        for phase in ('write', 'read'):
            r = subprocess.run([str(exe), str(engine / 'pokeemerald.gba'), str(symfile), str(out), phase], capture_output=True, text=True)
            log[phase] = {'exit': r.returncode, 'records': [json.loads(l) for l in r.stdout.splitlines() if l.startswith('{')],
                          'stderr': r.stderr.strip()}
            print(f'{phase}: exit {r.returncode}' + (f' ({r.stderr.strip()})' if r.returncode else ''))
            if r.returncode:
                break
    shots = []
    for ppm in sorted(out.glob('*.ppm'), key=lambda p: p.stat().st_mtime):
        Image.open(ppm).save(ppm.with_suffix('.png')); ppm.unlink(); shots.append(ppm.stem)
    rom = (engine / 'pokeemerald.gba').read_bytes()
    import hashlib
    log['rom_sha1'] = hashlib.sha1(rom).hexdigest()
    log['passed'] = all(log[p]['exit'] == 0 for p in ('write', 'read') if p in log) and 'read' in log
    (out / 'results.json').write_text(json.dumps(log, indent=1) + '\n')
    if shots:
        sheet(out, shots)
    print('passed' if log['passed'] else 'FAILED', '->', out / 'results.json')
    return 0 if log['passed'] else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
