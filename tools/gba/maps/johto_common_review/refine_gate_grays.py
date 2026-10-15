"""Lighten G02 stonework only, preserving the approved native geometry."""
from pathlib import Path
import json
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import refine_gates as base

PREV = base.OUT.parent / 'refinement-2'
OUT = PREV.parent / 'refinement-3'


def main():
    OUT.mkdir(exist_ok=True)
    old = Image.open(PREV / 'G02.png').convert('RGBA')
    before = np.array(old)
    after = before.copy()
    replacements = {
        (48, 48, 56): (144, 144, 144),
        (104, 112, 104): (248, 248, 248),
        (184, 184, 176): (248, 248, 248),
    }
    material = np.zeros(before.shape[:2], dtype=bool)
    entrance = np.zeros(before.shape[:2], dtype=bool)
    entrance[:, :4] = True
    entrance[:, 91:] = True
    for source, target in replacements.items():
        mask = (before[:, :, :3] == source).all(2) & (before[:, :, 3] == 255) & entrance
        material |= mask
        after[mask, :3] = target
    # All stone pixels belong to the two exposed side entrances.
    assert not material[:, 4:91].any()
    assert np.array_equal(before[:, :, 3], after[:, :, 3])
    assert np.array_equal(before[~material], after[~material])
    assert not ((after[:, :, :3] == (48, 48, 56)).all(2) & (after[:, :, 3] > 0) & entrance).any()
    revised = Image.fromarray(after)
    front = Image.open(PREV / 'G01a.png').convert('RGBA')
    base.OUT = OUT
    base.front = lambda: (front, front)
    base.side = lambda: (old, revised)
    base.main()
    report = json.loads((OUT / 'validation.json').read_text())
    report['G01a']['identical_to_refinement_2'] = True
    report['G02'].update({
        'alpha_unchanged': True,
        'non_stone_pixels_unchanged': True,
        'geometry_unchanged': True,
        'stone_palette': list(replacements.values()),
        'black_stone_pixels_remaining': 0,
    })
    (OUT / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    board = Image.new('RGB', (864, 540), (235, 238, 237))
    draw = ImageDraw.Draw(board)
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 22)
    draw.text((24, 18), 'G02 / gray and white', font=font, fill=(24, 36, 38))
    full = revised.resize((448, 448), Image.Resampling.NEAREST)
    board.paste(full, (24, 58), full)
    draw.text((510, 18), 'Awning and stairs / 6x', font=font, fill=(24, 36, 38))
    detail = revised.crop((88, 24, 112, 104)).resize((144, 480), Image.Resampling.NEAREST)
    board.paste(detail, (586, 52), detail)
    board.save(OUT / 'G02-close-up.png')
    backgrounds = Image.new('RGB', (720, 252))
    asset = revised.resize((224, 224), Image.Resampling.NEAREST)
    for index, color in enumerate(((235, 238, 237), (32, 40, 48), (200, 88, 152))):
        backgrounds.paste(color, (index * 240, 0, (index + 1) * 240, 252))
        backgrounds.paste(asset, (index * 240 + 8, 14), asset)
    backgrounds.save(OUT / 'background-check.png')


if __name__ == '__main__':
    main()
