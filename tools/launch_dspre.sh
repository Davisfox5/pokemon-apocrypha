#!/usr/bin/env bash
# Launch DSPRE (DS Pokémon ROM Editor) under GPTK wine + .NET Framework 4.8 on macOS.
export WINEPREFIX="$HOME/.wine_dspre"
export WINEDEBUG=-all
export PATH="$HOME/.omni_winebin:/opt/homebrew/bin:$PATH"
cd "$HOME/toolchains/DSPRE-app/current" || exit 1
exec /opt/homebrew/bin/wine64 DSPRE.exe "$@"
