"""Olivine's element tools (olivine_elements/), loaded by path under their own names, so
Saffron's modules can share names with them (sprites, pack, check) without shadowing.

    OS = olivine.mod('sprites')         # olivine_elements/sprites.py
"""
from __future__ import annotations
import importlib.util, sys
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / 'olivine_elements'
if str(DIR) not in sys.path:
    sys.path.append(str(DIR))           # their own plain imports (hgss_render, hgss_camera, build)

def mod(name):
    key = f'olivine_{name}'
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, DIR / f'{name}.py')
        m = importlib.util.module_from_spec(spec)
        sys.modules[key] = m
        spec.loader.exec_module(m)
    return sys.modules[key]
