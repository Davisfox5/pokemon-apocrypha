#!/usr/bin/env bash
# bootstrap.sh — set up the asset-pipeline environment on macOS.
#
# What it does:
#   1. Reports Java status (Pokémon DS Map Studio needs Java 8+) — does not install.
#   2. Creates .venv and installs Pillow.
#   3. Reports melonDS / mGBA emulator status via Homebrew.
#   4. Reports Windows-compatibility-layer status (DSPRE and SDSME are
#      Windows .NET tools with no macOS build).
#   5. Installs the ROM-blocking pre-commit hook.
#
# It never downloads anything that requires accepting a license.

set -u
cd "$(dirname "$0")/.." || exit 1

ok()   { printf '  [ok]   %s\n' "$1"; }
miss() { printf '  [MISS] %s\n' "$1"; }
info() { printf '  [info] %s\n' "$1"; }

echo "== Java (Pokemon DS Map Studio needs Java 8+) =="
# /usr/bin/java is a macOS stub that errors when no JDK is installed, so test
# that it actually runs; also check the Homebrew keg tools/launch_pdsms.sh uses.
JAVA_BIN=""
if command -v java >/dev/null 2>&1 && java -version >/dev/null 2>&1; then
    JAVA_BIN=java
elif [ -x /opt/homebrew/opt/openjdk/bin/java ]; then
    JAVA_BIN=/opt/homebrew/opt/openjdk/bin/java
fi
if [ -n "$JAVA_BIN" ]; then
    ok "$("$JAVA_BIN" -version 2>&1 | head -1)  ($JAVA_BIN)"
else
    miss "Java not found. Install it yourself, e.g.:"
    echo "         brew install --cask temurin"
    echo "       (or any JDK 8+; PDSMS is launched via tools/launch_pdsms.sh)"
fi

echo
echo "== Python venv (.venv) + Pillow =="
PY=python3
if ! command -v "$PY" >/dev/null 2>&1; then
    miss "python3 not found — install Xcode command line tools or 'brew install python'"
    exit 1
fi
if [ ! -x .venv/bin/python ]; then
    "$PY" -m venv .venv || { miss "failed to create .venv"; exit 1; }
    ok "created .venv ($(.venv/bin/python --version 2>&1))"
else
    ok "existing .venv ($(.venv/bin/python --version 2>&1))"
fi
if .venv/bin/python -c 'import PIL' 2>/dev/null; then
    ok "Pillow $( .venv/bin/python -c 'import PIL; print(PIL.__version__)' )"
else
    .venv/bin/pip install --quiet --upgrade pip Pillow \
        && ok "installed Pillow $( .venv/bin/python -c 'import PIL; print(PIL.__version__)' )" \
        || { miss "pip install Pillow failed"; exit 1; }
fi

echo
echo "== Emulators (Homebrew) =="
if command -v brew >/dev/null 2>&1; then
    for cask in melonds mgba; do
        if brew list --cask "$cask" >/dev/null 2>&1 || brew list "$cask" >/dev/null 2>&1; then
            ok "$cask installed via Homebrew"
        elif [ -d "/Applications/$(echo "$cask" | sed 's/melonds/melonDS/;s/mgba/mGBA/').app" ]; then
            ok "$cask present in /Applications (not via Homebrew)"
        else
            miss "$cask — install with: brew install --cask $cask"
        fi
    done
    info "note: mGBA is GBA-only (Gen 3 reference material); DS testing uses melonDS/DeSmuME"
else
    miss "Homebrew not found — cannot check emulators (https://brew.sh)"
fi

echo
echo "== Windows compatibility layer (for DSPRE / SDSME — Windows .NET, no macOS build) =="
found_layer=0
if command -v wine64 >/dev/null 2>&1 || command -v wine >/dev/null 2>&1; then
    ok "wine: $(command -v wine64 || command -v wine)"
    found_layer=1
fi
[ -d "$HOME/.wine_dspre" ] && { ok "DSPRE wine prefix at ~/.wine_dspre (used by tools/launch_dspre.sh)"; found_layer=1; }
[ -d "/Applications/Whisky.app" ] && { ok "Whisky.app"; found_layer=1; }
[ -d "/Applications/CrossOver.app" ] && { ok "CrossOver.app"; found_layer=1; }
[ -d "/Applications/Parallels Desktop.app" ] && { ok "Parallels Desktop"; found_layer=1; }
if [ "$found_layer" -eq 0 ]; then
    miss "no wine/Whisky/CrossOver/Parallels found."
    echo "       You still need one of these to run DSPRE or SDSME, e.g.:"
    echo "         brew install --cask whisky        (free, Game Porting Toolkit based)"
    echo "       then install .NET Framework 4.8 inside the prefix."
fi
[ -d "$HOME/toolchains/pdsms" ] \
    && ok "PDSMS found at ~/toolchains/pdsms (tools/launch_pdsms.sh)" \
    || info "PDSMS not found at ~/toolchains/pdsms — download it yourself (see tools/vendor/README.md)"
[ -d "$HOME/toolchains/DSPRE-app" ] \
    && ok "DSPRE found at ~/toolchains/DSPRE-app (tools/launch_dspre.sh)" \
    || info "DSPRE not found at ~/toolchains/DSPRE-app — download it yourself (see tools/vendor/README.md)"

echo
echo "== Git pre-commit hook (blocks ROM extensions) =="
if [ -d .git ]; then
    cp scripts/hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit \
        && ok "installed .git/hooks/pre-commit" \
        || miss "could not install hook"
else
    miss "not a git checkout (?) — hook not installed"
fi

echo
echo "Bootstrap complete. Next: put source art under assets/src/ and run 'make build'."
