#!/usr/bin/env python3
"""Install the checksum-pinned complete Arm toolchain in ignored tools/vendor/gba."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
lock = json.loads((ROOT / 'tools/gba/toolchain.json').read_text())
if f'{platform.system()}-{platform.machine()}' != lock['platform']:
    raise SystemExit('This lock qualifies Apple Silicon macOS only; use upstream OS instructions and qualify other hosts.')
base = ROOT / 'tools/vendor/gba'
base.mkdir(parents=True, exist_ok=True)
archive = base / 'arm-toolchain.tar.xz'
if not archive.exists():
    temporary = archive.with_suffix('.download')
    urllib.request.urlretrieve(lock['url'], temporary)
    temporary.rename(archive)
if hashlib.sha256(archive.read_bytes()).hexdigest() != lock['sha256']:
    raise SystemExit('Toolchain checksum mismatch; archive was not extracted.')
compiler = base / lock['directory'] / 'bin/arm-none-eabi-gcc'
if not compiler.exists():
    subprocess.run(['tar', '-xJf', str(archive), '-C', str(base)], check=True)
subprocess.run([str(compiler), '--version'], check=True)
print('Verified toolchain. Host prerequisites: Homebrew make, libpng, pkgconf, Python 3 and Xcode command-line tools.')
