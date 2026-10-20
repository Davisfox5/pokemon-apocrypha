"""Compile only the two edited native Ecruteak districts from current layers."""
from pathlib import Path
import sys,json,numpy as np
from PIL import Image
from compile_refinement import compile_native
S=Path(__file__).resolve().parents[4]/'gba/art/ecruteak-city/source';E=S.parent/'evidence'
compile_native(Path(sys.argv[1]),Path(sys.argv[2]),S,E,np.array(Image.open(S/'background.png')),np.array(Image.open(S/'foreground.png')),np.load(S/'solid.npy'),np.load(S/'behaviors.npy'),np.load(S/'heritage/above.npy'),json.loads((E/'assembly.json').read_text()))
