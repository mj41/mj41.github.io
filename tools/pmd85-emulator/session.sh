#!/bin/bash
# Boot a PMD 85-2 with the BASIC-G V2.0 ROM module and drive it:
#  - type the 1991/92 program exactly as the notebook spells it, LIST it, RUN it
#  - dump the whole character set, to see what the machine could actually show
#  - type the fixed 2026 version, LIST it, RUN it
# The emulator window is captured whole; the 864x768 viewport is 3x the real
# 288x256 raster, so the shots can be reduced back to the exact PMD bitmap.
set -u

OUT=/out
mkdir -p "$OUT"
export DISPLAY=:99

Xvfb :99 -screen 0 1000x900x24 -nolisten tcp &
XVFB=$!
sleep 2

GPMD85emu -c -m 2 -r -sc 3 -cp 0 -hp 0 -bd 0 -vol 0 -soft >"$OUT/emu.log" 2>&1 &
EMU=$!
sleep 6

WIN=$(xdotool search --name GPMD85 | tail -1)
xdotool windowmove "$WIN" 0 0
xdotool windowfocus --sync "$WIN"
sleep 1
xdotool getwindowgeometry "$WIN" >"$OUT/geometry.txt"

shot() { import -window "$WIN" "$OUT/$1.png"; }
type_lines() { python3 /typist.py "$@"; }
cls() { xdotool keydown shift; sleep 0.05; xdotool keydown Home; sleep 0.12;
        xdotool keyup Home; sleep 0.05; xdotool keyup shift; sleep 1; }

shot 01-boot

# the notebook spells the program with spaces around = , and ; - does BASIC-G
# keep them?
type_lines '10 GCLEAR' \
           '20 SL = 0' \
           '30 TEXT$ = "PEPO CAU"' \
           '40 PAUSE 5' \
           '50 PRINT AT SL, 0; TEXT$' \
           '60 SL = SL + 1' \
           '70 GOTO 20'
shot 02-typed

cls
type_lines 'LIST'
sleep 2
shot 03-list

type_lines 'RUN'
sleep 6
shot 04-run
xdotool keydown Escape; sleep 0.2; xdotool keyup Escape; sleep 1

# what characters does this machine have at all?
cls
type_lines 'NEW' \
           '10 FOR I=32 TO 255' \
           '20 PRINT CHR$(I);' \
           '30 NEXT I'
cls
type_lines 'RUN'
sleep 6
shot 05-charset
xdotool keydown Escape; sleep 0.2; xdotool keyup Escape; sleep 1

# the fixed version
cls
type_lines 'NEW' \
           '10 GCLEAR' \
           '20 RA = 0' \
           '30 TEXT$ = "PEPO CAU"' \
           '40 PAUSE 5' \
           '50 PRINT AT RA, 0; TEXT$' \
           '60 RA = RA + 1' \
           '70 GOTO 40'
shot 06-fixed-typed
cls
type_lines 'LIST'
sleep 2
shot 07-fixed-list
type_lines 'RUN'
sleep 30
shot 08-fixed-run

kill $EMU 2>/dev/null
kill $XVFB 2>/dev/null
wait 2>/dev/null
echo done
