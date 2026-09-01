#!/bin/bash
# PMD 85-2A: the ROM module boots to a menu - B for BASIC, M for MONITOR,
# P for the PMD 32 disk. Press B, then type the 1991/92 program, LIST it,
# then the fixed version, then dump the character set.
set -u
OUT=/out; mkdir -p "$OUT"; export DISPLAY=:99

Xvfb :99 -screen 0 1000x900x24 -nolisten tcp & XVFB=$!
sleep 2
GPMD85emu -c -m 2A -r -sc 3 -cp 0 -hp 0 -bd 0 -vol 0 -soft >"$OUT/emu.log" 2>&1 &
EMU=$!
sleep 7
WIN=$(xdotool search --name GPMD85 | tail -1)
xdotool windowmove "$WIN" 0 0
xdotool windowfocus --sync "$WIN"
sleep 1

shot() { import -window "$WIN" "$OUT/$1.png"; }
key()  { xdotool keydown "$1"; sleep 0.12; xdotool keyup "$1"; sleep 0.6; }
cls()  { xdotool keydown shift; sleep 0.05; xdotool keydown Home; sleep 0.12
         xdotool keyup Home; sleep 0.05; xdotool keyup shift; sleep 1; }

shot 00-boot-menu
key b                 # B - BASIC
sleep 3
shot 01-basic

python3 /typist.py '10 GCLEAR' '20 SL = 0' '30 TEXT$ = "PEPO CAU"' '40 PAUSE 5' \
                   '50 PRINT AT SL, 0; TEXT$' '60 SL = SL + 1' '70 GOTO 20'
shot 02-typed
cls; python3 /typist.py 'LIST'; sleep 2; shot 03-list

cls
python3 /typist.py 'NEW' '10 GCLEAR' '20 RA = 0' '30 TEXT$ = "PEPO CAU"' '40 PAUSE 5' \
                   '50 PRINT AT RA, 0; TEXT$' '60 RA = RA + 1' '70 GOTO 40'
cls; python3 /typist.py 'LIST'; sleep 2; shot 04-fixed-list
cls; python3 /typist.py 'RUN'; sleep 40; shot 05-fixed-run
xdotool keydown Escape; sleep 0.2; xdotool keyup Escape; sleep 1

cls
python3 /typist.py 'NEW' '10 FOR I = 32 TO 255' '20 PRINT CHR$(I);' '30 NEXT I'
cls; python3 /typist.py 'RUN'; sleep 8; shot 06-charset

kill $EMU 2>/dev/null; kill $XVFB 2>/dev/null; wait 2>/dev/null; echo done
