#!/usr/bin/env python3
"""Build the pinned GBA checkout without changing the legacy root Makefile."""
import argparse
import json
import os
import re
import sys
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
LOCK = json.loads((ROOT / 'tools/gba/toolchain.json').read_text())
TOOLCHAIN = ROOT / 'tools/vendor/gba' / LOCK['directory']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', nargs='?', default='all', choices=['all', 'release', 'clean', 'check'])
    parser.add_argument('--jobs', type=int, default=min(os.cpu_count() or 2, 8))
    parser.add_argument('--tests', help='Upstream runtime test-name filter')
    parser.add_argument('--qualification', action='store_true', help='Run the tracked normal-save qualification test')
    parser.add_argument('--storage', action='store_true', help='Run the isolated 900-record page-store prototype test')
    parser.add_argument('--mechanics', action='store_true', help='Run the tracked mechanics regression tests')
    args = parser.parse_args()
    if args.mechanics and (args.storage or args.qualification):
        parser.error('--mechanics cannot be combined with --storage or --qualification')
    if args.mechanics:
        args.qualification = True
    if args.storage:
        args.qualification = True
    if args.qualification:
        args.target = 'check'
        args.tests = 'test/apocrypha_baseline.c'
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    if not (TOOLCHAIN / 'bin/arm-none-eabi-gcc').exists():
        parser.error('Run python3 tools/gba/setup.py first (Apple Silicon macOS).')
    head = subprocess.check_output(['git', '-C', str(ROOT / 'game'), 'rev-parse', 'HEAD'], text=True).strip()
    if head != LOCK['upstream_commit']:
        parser.error('game/ is not at the qualified upstream pin; qualify a new pin explicitly.')
    make = shutil.which('gmake') or shutil.which('make')
    command = [make, '-C', str(ROOT / 'game'), f'-j{args.jobs}', f'TOOLCHAIN={TOOLCHAIN}', args.target]
    if args.target == 'check':
        # The upstream Makefile only embeds TESTS when linking this generated ELF.
        (ROOT / 'game/pokeemerald-test.elf').unlink(missing_ok=True)
    if args.tests:
        command.append(f'TESTS={args.tests}')
    injected = ROOT / 'game/test/apocrypha_baseline.c'
    copies = []
    if args.qualification:
        source = 'mechanics_test.c' if args.mechanics else ('storage/gba_test.c' if args.storage else 'save_roundtrip.c')
        copies = [(ROOT / 'tools/gba' / source, injected)]
        if args.storage:
            copies += [(ROOT / 'tools/gba/storage/store.c', ROOT / 'game/test/apocrypha_store.inc.c'),
                       (ROOT / 'tools/gba/storage/store.h', ROOT / 'game/test/store.h')]
        if any(dst.exists() for src, dst in copies):
            parser.error('Refusing to overwrite existing qualification source.')
    created = []
    try:
        for src, dst in copies:
            shutil.copyfile(src, dst)
            created.append(dst)
        if args.target != 'check':
            raise SystemExit(subprocess.call(command))
        # Upstream exits successfully for an unmatched filter; that is not a pass.
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        total = 0
        for line in process.stdout:
            sys.stdout.write(line)
            plain = re.sub(r"\x1b\[[0-9;]*m", "", line)
            match = re.search(r"Tests TOTAL:\s+(\d+)", plain)
            if match:
                total = int(match.group(1))
        code = process.wait()
        if code == 0 and total == 0:
            print('No tests executed; refusing to report qualification success.', file=sys.stderr)
            code = 1
        raise SystemExit(code)
    finally:
        for dst in created:
            dst.unlink()


if __name__ == '__main__':
    main()
