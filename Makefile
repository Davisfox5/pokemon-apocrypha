# Asset pipeline for the Gen 4 (Platinum / HGSS) ROM hack.
# Source art lives in assets/src/, game-ready output in assets/out/ (gitignored).
# See README.md for the full workflow and docs/gen4-reference.md for format budgets.

PYTHON  := .venv/bin/python
SRC     := assets/src
OUT     := assets/out

.PHONY: setup build validate clean

setup:
	bash scripts/bootstrap.sh

# Full source-to-output conversion. Per asset class:
#   trainers/front     -> 80x80, 16 colors (index 0 transparent)
#   trainers/back      -> 16 colors, dimensions kept (multi-frame sheets are
#                         authored at final size; ~5 frames of 80x80)
#   trainers/overworld -> 16 colors (15 opaque + transparent), dimensions kept
#                         (sheets of 32x32 frames, authored at final size)
#   maps/tiles         -> 16 colors, dimensions kept
#   maps/textures      -> padded to power-of-two, 16 colors
# Platinum front-sprite + VS-mugshot palette sharing is a MANUAL step:
#   $(PYTHON) scripts/shared_palette.py <front.png> <mugshot.png> -o $(OUT)/trainers/front/
build:
	@test -x $(PYTHON) || { echo "error: .venv missing — run 'make setup' first"; exit 1; }
	@for f in $(SRC)/trainers/front/*.png; do [ -e "$$f" ] || continue; \
		$(PYTHON) scripts/quantize.py "$$f" -o $(OUT)/trainers/front/$$(basename "$$f") --size 80x80 --colors 16 || exit 1; done
	@for f in $(SRC)/trainers/back/*.png; do [ -e "$$f" ] || continue; \
		$(PYTHON) scripts/quantize.py "$$f" -o $(OUT)/trainers/back/$$(basename "$$f") --colors 16 || exit 1; done
	@for f in $(SRC)/trainers/overworld/*.png; do [ -e "$$f" ] || continue; \
		$(PYTHON) scripts/quantize.py "$$f" -o $(OUT)/trainers/overworld/$$(basename "$$f") --colors 16 || exit 1; done
	@for f in $(SRC)/maps/tiles/*.png; do [ -e "$$f" ] || continue; \
		$(PYTHON) scripts/quantize.py "$$f" -o $(OUT)/maps/tiles/$$(basename "$$f") --colors 16 || exit 1; done
	@for f in $(SRC)/maps/textures/*.png; do [ -e "$$f" ] || continue; \
		$(PYTHON) scripts/texture_prep.py "$$f" -o $(OUT)/maps/textures/$$(basename "$$f") --colors 16 || exit 1; done
	@echo "build done -> $(OUT)/"

validate:
	@test -x $(PYTHON) || { echo "error: .venv missing — run 'make setup' first"; exit 1; }
	@test -d $(OUT) || { echo "error: $(OUT)/ does not exist — run 'make build' first"; exit 1; }
	$(PYTHON) scripts/validate.py $(OUT)

clean:
	rm -rf $(OUT)
