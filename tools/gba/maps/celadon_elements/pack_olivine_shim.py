"""Olivine's packer module (olivine_elements/pack.py) under its own name, for its exact_banks:
Celadon's pack.py would shadow it as `pack`."""
import importlib.util
import common as C

_spec = importlib.util.spec_from_file_location('olivine_pack', C.OLIVINE / 'pack.py')
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
exact_banks = _mod.exact_banks
