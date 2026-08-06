#!/usr/bin/env python3
"""validate.py — check converted assets against Gen 4 format budgets.

Checks a file or directory (recursively) for:
  - indexed color mode (PNG mode "P")
  - color count within the asset class budget
  - dimensions a multiple of 8
  - expected size/shape for the asset class

Asset classes and their rules:
  trainer-front      exactly 80x80, <=16 total colors incl. transparent index 0
  trainer-back       multi-frame sheet: one dimension exactly 80, the other a
                     multiple of 80 (HGSS backsprites are ~5-frame animated
                     sheets); <=16 total colors
  trainer-overworld  sheet of 32x32 frames: both dimensions multiples of 32;
                     <=15 NON-transparent colors (+ transparent index 0)
  map-tile           dimensions multiple of 8, <=16 total colors
  map-texture        power-of-two dimensions (typically 32 or 64), palettized;
                     <=256 colors, warns above 16
  generic            indexed, <=16 colors, dimensions multiple of 8

The class is inferred from the path (trainers/front, trainers/back,
trainers/overworld, maps/tiles, maps/textures) or forced with --class.

Exits nonzero if any file fails. Prints a per-file report.
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("error: Pillow is not installed. Run `make setup` (or: .venv/bin/pip install Pillow)")

CLASSES = ("trainer-front", "trainer-back", "trainer-overworld", "map-tile", "map-texture", "generic")


def infer_class(path):
    parts = "/".join(path.parts).lower()
    if "trainers/front" in parts:
        return "trainer-front"
    if "trainers/back" in parts:
        return "trainer-back"
    if "overworld" in parts:
        return "trainer-overworld"
    if "textures" in parts:
        return "map-texture"
    if "tiles" in parts:
        return "map-tile"
    return "generic"


def is_pow2(n):
    return n > 0 and (n & (n - 1)) == 0


def check_file(path, asset_class):
    """Returns (errors, warnings) lists for one file."""
    errors, warnings = [], []
    try:
        img = Image.open(path)
        img.load()
    except OSError as e:
        return [f"unreadable image: {e}"], []

    w, h = img.size

    if img.mode != "P":
        errors.append(f"not indexed: mode is {img.mode}, expected P (palettized)")
        return errors, warnings  # color-count checks below need P mode

    color_entries = img.getcolors(maxcolors=65536) or []
    used = {idx for _count, idx in color_entries}
    n_total = len(used)
    n_opaque = len(used - {0})

    if w % 8 or h % 8:
        errors.append(f"dimensions {w}x{h} not a multiple of 8")

    transparency = img.info.get("transparency")
    if asset_class in ("trainer-front", "trainer-back", "trainer-overworld"):
        if transparency is None:
            warnings.append("no transparency chunk; index 0 should be marked transparent")
        elif transparency != 0:
            errors.append(f"transparent index is {transparency}, must be 0")

    if asset_class == "trainer-front":
        if (w, h) != (80, 80):
            errors.append(f"size {w}x{h}, trainer front sprites must be exactly 80x80")
        if n_total > 16:
            errors.append(f"{n_total} colors used, budget is 16 including transparent index 0")

    elif asset_class == "trainer-back":
        if not ((w == 80 and h % 80 == 0) or (h == 80 and w % 80 == 0)):
            errors.append(f"size {w}x{h}: backsprite sheets are 80x80 frames in a strip "
                          "(one dimension 80, the other a multiple of 80)")
        else:
            frames = max(w, h) // 80
            if frames != 5:
                warnings.append(f"{frames} frame(s); HGSS backsprite sheets are typically ~5 frames")
        if n_total > 16:
            errors.append(f"{n_total} colors used, budget is 16 including transparent index 0")

    elif asset_class == "trainer-overworld":
        if w % 32 or h % 32:
            errors.append(f"size {w}x{h}: overworld sheets are 32x32 frames, dimensions must be multiples of 32")
        if n_opaque > 15:
            errors.append(f"{n_opaque} non-transparent colors used, budget is 15")

    elif asset_class == "map-tile":
        if n_total > 16:
            errors.append(f"{n_total} colors used, budget is 16")

    elif asset_class == "map-texture":
        if not (is_pow2(w) and is_pow2(h)):
            errors.append(f"size {w}x{h}: texture dimensions must be powers of two")
        if n_total > 256:
            errors.append(f"{n_total} colors used, hard maximum is 256")
        elif n_total > 16:
            warnings.append(f"{n_total} colors; 16 (4bpp) is the usual budget for map textures")
        if max(w, h) > 64:
            warnings.append(f"{w}x{h} is large for a map texture; 32x32 or 64x64 is typical")

    else:  # generic
        if n_total > 16:
            errors.append(f"{n_total} colors used, budget is 16")

    return errors, warnings


def collect(target):
    if target.is_file():
        return [target]
    if target.is_dir():
        return sorted(p for p in target.rglob("*.png") if p.is_file())
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", type=Path, help="a PNG file or a directory to scan recursively")
    ap.add_argument("--class", dest="asset_class", choices=CLASSES, default=None,
                    help="force an asset class instead of inferring from the path")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = ap.parse_args()

    files = collect(args.target)
    if files is None:
        sys.exit(f"error: no such file or directory: {args.target}")
    if not files:
        print(f"no PNG files found under {args.target} — nothing to validate")
        return

    n_fail = 0
    for path in files:
        asset_class = args.asset_class or infer_class(path)
        errors, warnings = check_file(path, asset_class)
        if args.strict:
            errors, warnings = errors + warnings, []
        status = "FAIL" if errors else "ok"
        if errors:
            n_fail += 1
        print(f"[{status:4s}] {path}  ({asset_class})")
        for msg in errors:
            print(f"        ERROR: {msg}")
        for msg in warnings:
            print(f"        warn:  {msg}")

    print(f"\n{len(files)} file(s) checked, {n_fail} failed")
    if n_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
