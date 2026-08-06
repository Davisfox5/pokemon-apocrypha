# tools/vendor/ — third-party binaries and jars

Everything in this directory **except this README is gitignored**. Drop
third-party tool binaries here (or install them to `~/toolchains/` — the
existing launch scripts in `tools/` expect that location; see below).

## What goes here / what the pipeline expects

| Tool | Kind | Purpose | Notes |
|---|---|---|---|
| Pokémon DS Map Studio (PDSMS) | Java jar | Author 3D map geometry (`.nsbmd`) + textures (`.nsbtx`) | Needs Java 8+. `tools/launch_pdsms.sh` expects it at `~/toolchains/pdsms/` |
| DSPRE (DS Pokémon ROM Editor) | Windows .NET | NARC insertion: trainer sprites, headers, events | No macOS build — runs under wine/GPTK. `tools/launch_dspre.sh` expects `~/toolchains/DSPRE-app/current/` |
| SDSME (Spiky's DS Map Editor) | Windows .NET | Alternative map/NARC editor | No macOS build — needs a Windows compatibility layer |
| Tinke | Windows .NET (runs under mono/wine) | Unpack/repack NARCs, preview Nitro formats | |
| NitroPaint | Windows | NCLR/NCGR/NSCR/NCER editing | |
| apicula | native CLI | Inspect/convert NSBMD/NSBTX | `cargo install apicula` or a release binary dropped here |

Download these yourself — `scripts/bootstrap.sh` deliberately does not fetch
anything that requires accepting a license. It only *reports* what is present.
