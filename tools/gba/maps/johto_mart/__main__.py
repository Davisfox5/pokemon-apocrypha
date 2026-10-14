"""Run with PYTHONPATH=tools/gba/maps python -m johto_mart OUTPUT [--bank N]."""
import argparse
from .assets import export_assets
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('output');parser.add_argument('--bank',type=int,default=9)
args=parser.parse_args()
if not 0<=args.bank<=12:parser.error('bank must be an available scenery palette (0-12)')
export_assets(args.output,args.bank)
