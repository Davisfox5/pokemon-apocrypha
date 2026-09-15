#!/usr/bin/env python3
"""Measure save and RAM struct sizes with the pinned ARM ABI, without game edits."""
import json
from pathlib import Path
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
lock = json.loads((ROOT / 'tools/gba/toolchain.json').read_text())
bin_dir = ROOT / 'tools/vendor/gba' / lock['directory'] / 'bin'
keys = ['box_pokemon_bytes', 'party_pokemon_bytes', 'saveblock1_bytes', 'saveblock2_bytes',
        'saveblock3_bytes', 'storage_bytes', 'boxes', 'slots_per_box', 'sector_payload_bytes',
        'saveblock3_bytes_per_sector', 'sectors_per_slot', 'flash_sector_count',
        'storage_sectors_per_slot', 'proposed_30_box_storage_bytes', 'flag_bytes',
        'persistent_var_count', 'badges', 'simultaneous_object_events', 'internal_species_count', 'qualification_var_offset']
with tempfile.TemporaryDirectory(prefix='apocrypha-capacity-') as temp:
    obj, raw = Path(temp) / 'capacity.o', Path(temp) / 'capacity.bin'
    subprocess.run([str(bin_dir / 'arm-none-eabi-gcc'), '-mthumb', '-mcpu=arm7tdmi',
                    '-mabi=apcs-gnu', '-std=gnu17', '-DMODERN=1', '-DEMERALD', '-DTESTING=0',
                    '-iquote', str(ROOT / 'game/include'), '-c', str(ROOT / 'tools/gba/capacity.c'),
                    '-o', str(obj)], check=True)
    subprocess.run([str(bin_dir / 'arm-none-eabi-objcopy'), '-O', 'binary',
                    '--only-section=.apocrypha_capacity', str(obj), str(raw)], check=True)
    values = struct.unpack('<' + 'I' * len(keys), raw.read_bytes())
result = dict(zip(keys, values))
result['upstream_commit'] = subprocess.check_output(['git', '-C', str(ROOT / 'game'), 'rev-parse', 'HEAD'], text=True).strip()
result['storage_payload_capacity_bytes'] = result['storage_sectors_per_slot'] * result['sector_payload_bytes']
result['storage_30_box_excess_bytes'] = result['proposed_30_box_storage_bytes'] - result['storage_payload_capacity_bytes']
result['measurement'] = 'ARM-compiled struct sizes; not an emulator persistence test'
print(json.dumps(result, indent=2))
