"""Make an adult Gold battle-back study from the native five-frame GBA template.

The generated concept in gba/art/chapter1-gold establishes Gold's outfit. Native
frame geometry is kept from the editable Red back sprite to avoid distorted
throw frames. This does not register the sprite or change battle mechanics.
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "tools/vendor/gba/opening-house-work/graphics/trainers/back_pics/red.png"
OUTPUT = ROOT / "tools/vendor/gba/opening-house-work/graphics/trainers/back_pics/apoc_gold.png"
PREVIEW = ROOT / "gba/art/chapter1-gold/gold-back-64x320.png"

# Original palette indexes remain stable; only clothing materials change.
RECOLOR = {
    8: (26, 29, 36), 12: (47, 48, 56), 11: (81, 79, 87),
    6: (105, 30, 39), 5: (183, 47, 55), 7: (226, 82, 79),
    14: (50, 53, 58), 13: (165, 166, 157),
}

def main():
    sprite = Image.open(SOURCE)
    if sprite.size != (64, 320) or sprite.mode != "P":
        raise ValueError((sprite.size, sprite.mode))
    palette = sprite.getpalette()
    for index, color in RECOLOR.items():
        palette[index * 3:index * 3 + 3] = color
    sprite.putpalette(palette)
    # A small gold stitch on the cap matches the established overworld sprite.
    for frame in range(5):
        cap = [(x, y) for y in range(frame * 64 + 12, frame * 64 + 35)
               for x in range(64) if sprite.getpixel((x, y)) in (8, 11, 12)]
        if not cap:
            raise ValueError(f"No cap in frame {frame}")
        x = max(x for x, _ in cap) - 11
        y = min(y for _, y in cap) + 5
        for dy in range(2):
            for dx in range(2):
                if sprite.getpixel((x + dx, y + dy)) in (8, 11, 12):
                    sprite.putpixel((x + dx, y + dy), 13)
    sprite.save(OUTPUT)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    sprite.save(PREVIEW)
    print(OUTPUT)

if __name__ == "__main__":
    main()
