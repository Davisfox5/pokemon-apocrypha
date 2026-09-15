#!/usr/bin/env python3
"""Run the map proof against an already-built disposable checkout (macOS/mGBA)."""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser()
parser.add_argument("game", type=Path)
parser.add_argument("output", type=Path, help="new directory for disposable flash and captures")
parser.add_argument("--toolchain", type=Path, required=True)
parser.add_argument("--mgba", type=Path, default=Path("/opt/homebrew/opt/mgba"))
args = parser.parse_args()
game, out = args.game.resolve(), args.output.resolve()
if game == ROOT / "game" or not (game / ".git").is_dir():
    parser.error("requires an independent disposable Git checkout, never production game/")
out.mkdir(parents=True, exist_ok=False)
binary = out / "runtime"
subprocess.run(["cc", "-I" + str(args.mgba / "include"),
                str(ROOT / "tools/gba/maps/runtime.c"),
                "-L" + str(args.mgba / "lib"), "-lmgba", "-o", str(binary)], check=True)
nm = subprocess.check_output([str(args.toolchain / "bin/arm-none-eabi-nm"),
                              str(game / "pokeemerald.elf")], text=True)
wanted = {"MapProof_Boot", "MapProof_Enter", "MapProof_ReadState", "MapProof_Resume",
          "gMapProofState", "TrySavingData", "LoadGameSave"}
symbols = {}
for line in nm.splitlines():
    parts = line.split()
    if len(parts) == 3 and parts[2] in wanted:
        symbols[parts[2]] = parts[0]
assert symbols.keys() == wanted, "missing qualification symbols"
symbol_file = out / "symbols.txt"
symbol_file.write_text("".join(f"{key} {value}\n" for key, value in symbols.items()))
results = []
expected_regions = [3, 2, 1, 4, 5]
for region in range(5):
    for phase in ["write", "read"]:
        proc = subprocess.run([str(binary), str(game / "pokeemerald.gba"),
                               str(symbol_file), str(out), phase, str(region)],
                              capture_output=True, text=True, timeout=120)
        (out / f"{phase}-{region}.jsonl").write_text(proc.stdout)
        observations = [json.loads(line) for line in proc.stdout.splitlines()]
        results.append(dict(phase=phase, region_index=region, exit_code=proc.returncode,
                            stderr=proc.stderr, observations=observations))
        (out / "results.json").write_text(json.dumps(results, indent=2) + "\n")
        assert proc.returncode == 0 and not proc.stderr, results[-1]
        if phase == "read":
            saved = observations[-1]
            expected = dict(region=expected_regions[region], group=75 + region, map=0,
                            x=11 if region == 1 else 10, y=11,
                            frlg_layout=int(region == 2),
                            width=80 if region == 4 else 24,
                            height=80 if region == 4 else 20, mapsec=209 + region)
            for key, value in expected.items():
                assert saved[key] == value, (region, key, saved[key], value)
        print(f"{phase} {region}: PASS", flush=True)
print("All ten runtime processes and cold-reload fields passed.")
