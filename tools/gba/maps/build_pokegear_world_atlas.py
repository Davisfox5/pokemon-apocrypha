"""Build the Pokégear's world and five regional views from one supplied image.

This is only cartography for the device. It never changes field maps, collision,
warps, encounters, travel access, or chapter state. All crops share one palette.
"""
from pathlib import Path
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "gba/art/pokegear-world/reference/world-map.jpg"
ART = ROOT / "gba/art/pokegear-world"
OUT = ROOT / "tools/vendor/gba/opening-house-work/graphics/apoc_pokegear"

# Coordinates are in the user's 1091 x 733 source. Each rectangle preserves
# its region's position and nearby context within the original world artwork.
CROPS = {
    "Kanto": (570, 228, 840, 394),
    "Johto": (385, 230, 655, 396),
    "Hoenn": (500, 353, 840, 562),
    "Sinnoh": (500, 8, 830, 211),
    "Unova": (300, 334, 550, 488),
}

# Explicit material palette avoids an adaptive quantizer spending most slots on
# the large ocean, which would flatten towns and remove their red rooftops.
PALETTE = [
    (27, 38, 44), (39, 133, 164), (73, 181, 207), (111, 207, 223),
    (230, 237, 232), (42, 106, 83), (66, 147, 106), (119, 179, 124),
    (128, 100, 83), (179, 137, 104), (217, 178, 139), (143, 57, 66),
    (217, 76, 85), (94, 97, 102), (158, 164, 164), (250, 247, 238),
]

def packed(image):
    pixels = list(image.getdata())
    return bytes(a | b << 4 for a, b in zip(pixels[::2], pixels[1::2]))

def palette_file(colors):
    return "JASC-PAL\n0100\n16\n" + "\n".join(" ".join(map(str, c)) for c in colors) + "\n"

def main():
    ART.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE).convert("RGB")
    if source.size != (1091, 733):
        raise ValueError(f"Unexpected world reference dimensions: {source.size}")
    # GBA 4bpp window art needs exactly 16 colors; a shared palette keeps
    # pan and region transitions stable while preserving each terrain material.
    color_base = source.resize((416, 280), Image.Resampling.LANCZOS)
    master = Image.new("P", (1, 1))
    master.putpalette([v for color in PALETTE for v in color])
    text = palette_file(PALETTE)

    # World view uses a 2x pan canvas (416 x 256); the 12-pixel vertical crop
    # drops only the outer ice border while retaining every named region.
    world = color_base.crop((0, 12, 416, 268)).quantize(
        palette=master, dither=Image.Dither.NONE
    )
    world.save(ART / "world-416x256.png")
    (OUT / "world.bin").write_bytes(packed(world))
    (OUT / "world.pal").write_text(text)

    result = []
    for index, (name, bounds) in enumerate(CROPS.items(), 1):
        detail = source.crop(bounds).resize((208, 128), Image.Resampling.LANCZOS)
        detail = detail.quantize(palette=master, dither=Image.Dither.NONE)
        detail.save(ART / f"atlas-{index}-{name.lower()}.png")
        (OUT / f"atlas{index}.bin").write_bytes(packed(detail))
        (OUT / f"atlas{index}.pal").write_text(text)
        result.append({"index": index, "name": name, "source_crop": bounds})
    (ART / "provenance.json").write_text(json.dumps({
        "source": str(SOURCE.relative_to(ROOT)),
        "source_dimensions": source.size,
        "world_dimensions": world.size,
        "detail_dimensions": [208, 128],
        "palette": PALETTE,
        "regions": result,
        "note": "User-supplied world artwork; visuals only, no travel unlocks.",
    }, indent=2) + "\n")
    print("Built one world atlas and five regional crops from the supplied image")

if __name__ == "__main__":
    main()
