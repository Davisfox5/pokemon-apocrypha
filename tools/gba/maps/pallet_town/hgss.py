#!/usr/bin/env python3
"""Decode and project Pallet's actual HGSS models using the qualified HGSS renderer."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'route29_catalog'))
import hgss_render as R
R.HEADER_ID=49;R.AREA_BANK=18
if __name__=='__main__':R.main(Path(sys.argv[1]),Path(sys.argv[2]))
