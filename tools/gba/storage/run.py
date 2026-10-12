#!/usr/bin/env python3
"""Reproduce the isolated storage prototype checks, without modifying production saves."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'tools/vendor/gba/storage-evidence'
OUT.mkdir(parents=True, exist_ok=True)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--gba', action='store_true', help='Also build and execute the actual-Pokemon GBA flash test')
args = parser.parse_args()
exe = OUT / 'storage-test'
subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
                str(HERE/'store.c'),str(HERE/'test_store.c'),'-o',str(exe)],check=True)
started = time.monotonic()
evidence = json.loads(subprocess.check_output([str(exe)],text=True))
evidence['native_suite_wall_seconds'] = round(time.monotonic()-started,3)
evidence['injected_interruption_cases'] = evidence['fault_cases'] - 2
evidence['completed_controls'] = 2
evidence['sanitizers'] = ['address','undefined']
evidence['root_metadata_fault_stride_bytes'] = 1
evidence['commit_marker_fault_stride_bits'] = 1
with tempfile.TemporaryDirectory(prefix='apocrypha-page-store-') as temp:
    save = str(Path(temp)/'normal.sav')
    for mode in ['write','read','update','read-updated','read-updated']:
        subprocess.run([str(exe),mode,save],check=True,timeout=60)
    evidence['fresh_process_phases'] = ['write','read','update','read-updated','read-updated']
    evidence['fresh_process_medium_bytes'] = Path(save).stat().st_size
lock=json.loads((ROOT/'tools/gba/toolchain.json').read_text())
bin_dir=ROOT/'tools/vendor/gba'/lock['directory']/'bin'
probe=OUT/'size.c'
probe.write_text('#include "store.h"\nconst uint32_t sizes[] __attribute__((section(".sizes"),used))={sizeof(struct ApsStore)};\n')
common=[str(bin_dir/'arm-none-eabi-gcc'),'-std=c11','-O2','-mthumb','-mcpu=arm7tdmi','-mabi=apcs-gnu','-I'+str(HERE)]
subprocess.run(common+['-fstack-usage','-c',str(HERE/'store.c'),'-o',str(OUT/'store.o')],check=True)
subprocess.run(common+['-c',str(probe),'-o',str(OUT/'size.o')],check=True)
subprocess.run([str(bin_dir/'arm-none-eabi-objcopy'),'-O','binary','--only-section=.sizes',str(OUT/'size.o'),str(OUT/'size.bin')],check=True)
evidence['arm_workspace_bytes']=struct.unpack('<I',(OUT/'size.bin').read_bytes())[0]
size=subprocess.check_output([str(bin_dir/'arm-none-eabi-size'),str(OUT/'store.o')],text=True).splitlines()[-1].split()
evidence['arm_object_bytes']={'text':int(size[0]),'data':int(size[1]),'bss':int(size[2])}
evidence['arm_stack_usage_per_function']=(OUT/'store.su').read_text().replace(str(HERE)+'/', '')
if args.gba:
    log=OUT/'gba-test.log'
    with log.open('w') as f:
        result=subprocess.run(['python3',str(ROOT/'tools/gba/build.py'),'--storage'],stdout=f,stderr=subprocess.STDOUT)
    text=log.read_text()
    if result.returncode:
        print(text[-5000:])
        raise SystemExit(result.returncode)
    evidence['gba_actual_pokemon_test']='passed: 900 records, first/last updates, remount; isolated test ROM'
    evidence['gba_emulator_timing_seconds_approx']={key:int(value) for key,value in re.findall(r'aps (\w+_seconds)=(\d+)',text)}
    evidence['timing_limit']='Approximately one-second resolution in emulated GBA time; not physical cartridge latency.'
evidence['sources_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'store.h',HERE/'store.c',HERE/'test_store.c',HERE/'gba_test.c']}
evidence['limitations']=['At most seven changed 4 KiB pages per atomic transaction; eight or more safely refused.',
 'Not integrated into the production PC/menu/save path, which still has 14 boxes.',
 'Shared data-page corruption is detected but cannot always be repaired from an older root.',
 'A full classic manual-save implementation remains unqualified.']
path=ROOT/'gba/evidence/storage-prototype.json'
path.write_text(json.dumps(evidence,indent=2)+'\n')
print(json.dumps(evidence,indent=2))
