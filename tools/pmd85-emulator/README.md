# Running the 1991/92 program on a real PMD 85

The green screens on the site (`docs/`) are not drawn — they are captured from a PMD 85-2
running [GPMD85Emulator](https://github.com/mborik/GPMD85Emulator) with the
BASIC-G V2.0 ROM module, with the program typed in one key at a time.

    git clone --depth 1 https://github.com/mborik/GPMD85Emulator.git gpmd
    podman build -t pmd85 .          # docker build works the same
    podman run --rm -v "$PWD/out:/out:Z" pmd85

`out/` then holds window captures of every step: the boot banner, the program as
typed, `LIST`, `RUN`, the whole character set, and the fixed version. Turn a
capture into the image the site uses with:

    python3 ../pmd85-screen.py extract out/02-typed.png ../raster/listing-1992.png
    python3 ../pmd85-screen.py render ../raster/listing-1992.png ../../docs/images/pmd85-screen.jpg

The container builds the emulator (SDL2 + autotools), starts it under `Xvfb`,
and drives it with `xdotool`. Two things make the typing work:

- **Keys are held, not tapped.** The PMD keyboard is a matrix scanned by the
  emulated 8080; an instant press/release is missed. `typist.py` holds each key
  for ~100 ms.
- **The PMD 85 layout is not a PC layout.** Unshifted letter keys give
  *uppercase* and shift gives lowercase; `"` is shift-2, `$` is shift-4, `=` is
  shift-minus, `+` is the key right of L. `typist.py` has the full table, which
  was read off the keyboard tables in the MONITOR ROM and then checked against
  what actually appeared on screen.

## What the machine settled

- The boot screen is exactly `BASIC-G /V2.0`, and the ROM module starts BASIC
  by itself — no `JUMP` needed.
- BASIC-G keeps the spacing you type, so `20 SL = 0` stays as written in the
  notebook.
- The input line lives at the bottom row of the screen; `OK` is the prompt after
  a program ends.
- `CHR$(32)` to `CHR$(127)` is plain ASCII, uppercase *and* lowercase. Every code
  from 128 up prints an empty box: **the machine had no Czech diacritics at all**,
  which is why `Pepo čau` had to be typed as `PEPO CAU`.
- BASIC-G's text screen is 48 characters by **26 lines**, not 32: it spaces
  lines 9 pixels apart, starting 3 pixels down, so about 21 pixels at the bottom
  of the 288x256 raster are never used. `PRINT AT` clamps the row to 25 - print
  at 26 or 35 and it all lands on the last line.
- The fixed version (`RA`, and `GOTO 40` instead of `GOTO 20`) runs: the text
  walks down the screen, one line per `PAUSE`, and fills all 26 lines in about
  30 seconds.
