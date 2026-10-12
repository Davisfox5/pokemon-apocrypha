#!/usr/bin/env python3
"""Prepare isolated, source-only GBA workspaces on macOS or Linux."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = 'e8bd1cd7b03fc032ea37e3ecd38b379b5d01a1e7'
URL = 'https://github.com/rh-hideout/pokeemerald-expansion.git'

def run(args, **kw):
    subprocess.run([str(x) for x in args], check=True, **kw)

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def install_toolchain():
    locks = json.loads((ROOT / 'tools/gba/portable-toolchains.json').read_text())
    key = platform.system() + '-' + platform.machine()
    if key not in locks:
        raise SystemExit(f'No toolchain lock for {key}; provide --toolchain explicitly.')
    lock = locks[key]
    base = ROOT / 'tools/vendor/gba'
    base.mkdir(parents=True, exist_ok=True)
    directory = base / lock['directory']
    archive = base / (lock['directory'] + '.tar.xz')
    if not archive.exists():
        temporary = archive.with_suffix('.download')
        urllib.request.urlretrieve(lock['url'], temporary)
        temporary.rename(archive)
    if sha(archive) != lock['sha256']:
        raise SystemExit(f'Toolchain checksum mismatch: {archive}')
    if not (directory / 'bin/arm-none-eabi-gcc').exists():
        run(['tar', '-xJf', archive, '-C', base])
    return directory

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--preset', choices=['workbench', 'town', 'preview', 'production'], default='workbench')
    p.add_argument('--output', type=Path, required=True, help='A new isolated directory; never production game/')
    p.add_argument('--build', action='store_true')
    p.add_argument('--toolchain', type=Path, help='Existing complete Arm GNU toolchain; otherwise checksum-pinned download')
    p.add_argument('--jobs', type=int, default=min(os.cpu_count() or 2, 8))
    args = p.parse_args()
    out = args.output.resolve()
    if out == ROOT / 'game' or out.exists():
        raise SystemExit('Use a new isolated output directory. Existing work is never replaced.')
    manifest = json.loads((ROOT / 'gba/source-handoff.json').read_text())
    patches = manifest['presets'][args.preset]
    for spec in patches:
        path = ROOT / spec['path']
        if sha(path) != manifest['patch_sha256'][spec['path']]:
            raise SystemExit(f'Patch differs from handoff snapshot: {path}')
    out.parent.mkdir(parents=True, exist_ok=True)
    run(['git', 'init', '-q', out])
    run(['git', '-C', out, 'remote', 'add', 'origin', URL])
    run(['git', '-C', out, 'fetch', '--depth=1', 'origin', UPSTREAM])
    run(['git', '-C', out, 'checkout', '-q', '--detach', 'FETCH_HEAD'])
    for spec in patches:
        command = ['git', '-C', out, 'apply', '--binary']
        command += ['--exclude=' + item for item in spec.get('exclude', [])]
        path = ROOT / spec['path']
        run(command + ['--check', path])
        run(command + [path])
    # Setup metadata stays outside the source tree and does not affect map compilation.
    record = out.with_name(out.name + '-setup.json')
    data = dict(upstream=UPSTREAM, preset=args.preset, patches=patches, source=str(out), built=False)
    record.write_text(json.dumps(data, indent=2) + '\n')
    if args.build:
        toolchain = args.toolchain.resolve() if args.toolchain else install_toolchain()
        make = shutil.which('gmake') or shutil.which('make')
        if not make:
            raise SystemExit('Install GNU make and the host dependencies listed in docs/GBA_REMOTE_HANDOFF.md.')
        run([toolchain / 'bin/arm-none-eabi-gcc', '--version'])
        env = dict(os.environ, PATH=str(toolchain / 'bin') + os.pathsep + os.environ.get('PATH', ''))
        run([make, '-C', out, '-j' + str(args.jobs), 'TOOLCHAIN=' + str(toolchain)], env=env)
        data.update(built=True, toolchain=str(toolchain), rom_sha256=sha(out / 'pokeemerald.gba'))
        record.write_text(json.dumps(data, indent=2) + '\n')
    print(f'Prepared {args.preset}: {out}\nEvidence: {record}')

if __name__ == '__main__':
    main()
