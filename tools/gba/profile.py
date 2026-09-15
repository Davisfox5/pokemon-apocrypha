#!/usr/bin/env python3
"""Apply or remove a checked-in profile patch, without resets."""
import argparse
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('mode', choices=['apply', 'remove'])
parser.add_argument('--profile', choices=['roster', 'mechanics'], default='roster')
args = parser.parse_args()
command = ['git', '-C', str(root / 'game'), 'apply']
if args.mode == 'remove':
    command.append('--reverse')
patch = str(root / f'gba/{args.profile}-profile.patch')
subprocess.run(command + ['--check', patch], check=True)
subprocess.run(command + [patch], check=True)
print(args.profile.title() + ' patch ' + ('applied' if args.mode == 'apply' else 'removed') + '; rebuild and remeasure before interpreting results.')
