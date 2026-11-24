# Quarantine (GameTek / Imagexcel, 1994) reverse-engineering names and tools

Function names for three builds of **Quarantine**, plus the tools that produced them. Every function carries a name (0 `FUN_` placeholders left). All names are provisional: string references and structural rules (size, callees), not verified behaviour. Nothing here has been rebuilt or behaviour-tested.

| Build | Program | Load base | Functions |
|---|---|---|---|
| DOS (DOS4GW LE, Watcom) | `Q.EXE` flattened | 0x10000 | 1443 |
| Sega Saturn JA ("Death Throttle") | `ADT.BIN` + IP.BIN | 0x06004000 / 0x06002000 | 1346 + 7 |
| 3DO | `launchme` (ARM BE) | 0x0 (assumed) | 986 |

## Contents
- `funcinfo_*.tsv`, `work/`: function lists and names.
- `tools/imgdec.py`: DOS `.IMG` ("IMAGEX" header, 256-colour palette, GIF-style LZW) to PNG. 39 of 44 files decode; `MISSIL0-4.IMG` are another variant.
- `tools/cmpdec.py`: Saturn `.CMP` (8bpp, 16x16 blocks of 8x8 tiles, palette at the end) to PNG. Width is not in the header; 320 is the default, other widths are unverified.
- `tools/operafs.py`: 3DO Opera file system extractor (2352-byte sectors).
- `tools/autodecomp/`: `autodecomp.py <game.zip> [--name N] [--out DIR]` does a whole first pass unattended: unzip, detect and extract disc images (Saturn, 3DO, ISO9660), find executables (DOS LE, PE, Saturn first-read SH-2, 3DO ARM), Ghidra headless import and function finding, provisional names, known asset conversion, `REPORT.md`. Tested on the three Quarantine builds above; the PE path is untested. Needs Ghidra (headless launcher path is set at the top of the script) and the Watcom cspec for DOS builds.

Paths inside the scripts are from the author's machine (`C:/Users/USER/...`); adjust them.

No game data is included. Research and preservation only.

## Decompiled code (`src/`)
Raw Ghidra decompiler output with the provisional names applied, one file per program: `src/dos/decomp_q.c`, `src/saturn/decomp_ADT.c` + `decomp_IP.c`, `src/3do/decomp_launchme.c`. It is pseudo-C for reading and study: it does not compile and has not been checked against the running game.

## Godot port, work in progress (`port/`)
A Godot 4.7 project that draws the DOS game's city view from the original data files, compared pixel by pixel with the DOS build running in DOSBox. State on 2026-11-23: 85 stored camera poses in the first city, 84 differing pixels in total (320x200 each), 19 frames fully equal.

- `port/main.gd`, `port/shaders/*.gdshader`: renderer (integer ports of the DOS wall, floor, sprite and entity scalers), dash, radar.
- `port/tests/baseline.json`, `chk.json`: best pixel count and frame checksum per test pose. The DOS screenshots and level data behind them are not included.
- `tools/cityexport.py`, `entexport.py`, `animexport.py`, `areas.py`: build `port/data` and `port/areas` from your own copy of the DOS game. The port does not run without them.
- `tools/parity.py`, `regress.py`, `pp.py`, `chkparity.py`, `sceneparity.py`: the parity tests (DOSBox snapshot at a pose, port render at the same pose, diff, gate).

It is a renderer test bed, not a playable game yet. Script paths are again from the author's machine (`C:\Games\...`).
