#!/usr/bin/env bash
# Launch PDSMS (Pokémon DS Map Studio) natively on macOS via Java.
export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"
cd "$HOME/toolchains/pdsms" || exit 1
exec java -cp "lib/*" editor.MainFrame "$@"
