#!/usr/bin/env python3
"""Boot and cold-process flash-save checks against the current built ordinary ROM."""
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
lock = json.loads((ROOT / 'tools/gba/toolchain.json').read_text())
mgba = Path(subprocess.check_output(['brew', '--prefix', 'mgba'], text=True).strip())
vendor = ROOT / 'tools/vendor/gba'
for tool in ['boot', 'persistence']:
    subprocess.run(['cc', '-I' + str(mgba / 'include'), str(ROOT / f'tools/gba/{tool}.c'),
                    '-L' + str(mgba / 'lib'), '-lmgba', '-o', str(vendor / tool)], check=True)
rom, elf = ROOT / 'game/pokeemerald.gba', ROOT / 'game/pokeemerald.elf'
nm = vendor / lock['directory'] / 'bin/arm-none-eabi-nm'
symbols = {}
for line in subprocess.check_output([str(nm), str(elf)], text=True).splitlines():
    fields = line.split()
    if len(fields) == 3:
        symbols[fields[2]] = int(fields[0], 16)
capacity = json.loads(subprocess.check_output(['python3', str(ROOT / 'tools/gba/measure.py')], text=True))
boot = json.loads(subprocess.check_output([str(vendor / 'boot'), str(rom)], text=True, timeout=60))
with tempfile.TemporaryDirectory(prefix='apocrypha-flash-') as temp:
    command = [str(vendor / 'persistence'), str(rom), str(Path(temp) / 'normal.sav'), 'write']
    command += [str(symbols[name]) for name in ['NewGameInitData', 'TrySavingData', 'LoadGameSave', 'gSaveBlock1Ptr']]
    command += [str(capacity['qualification_var_offset'])]
    write = json.loads(subprocess.check_output(command, text=True, timeout=60))
    command[3] = 'read'
    read = json.loads(subprocess.check_output(command, text=True, timeout=60))
print(json.dumps({'boot': boot, 'fresh_process_write': write, 'fresh_process_read': read,
                  'method': 'mGBA normal ROM engine entry points; separate host processes share only 128 KiB flash; no savestates or menu automation'}, indent=2))
