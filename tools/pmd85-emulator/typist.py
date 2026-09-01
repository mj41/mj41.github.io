#!/usr/bin/env python3
"""Type into the emulated PMD 85 keyboard.

The emulator maps host *scancodes* onto the PMD 85 key matrix, and the PMD ROM
decides which character a key produces, so a character has to be spelled as
"physical key + shift or not" according to the PMD 85 layout:

    unshifted digit row:  1 2 3 4 5 6 7 8 9 0 _ }
    shifted digit row:    " # $ % & ' ( ) - = { ]
    key right of L:       + unshifted, ; shifted
    key right of that:    * unshifted, : shifted
    bottom row:           < > ? unshifted, , . / shifted

The matrix is scanned by the emulated CPU, so every key is held down for a
while instead of being tapped, otherwise most presses are missed.
"""

import subprocess
import sys
import time

HOLD = 0.10       # how long a key stays down
GAP = 0.07        # pause between keys
LINE_PAUSE = 0.5  # pause after Enter

PLAIN = {
    ' ': 'space',
    ';': 'semicolon',
    ':': 'apostrophe',
    ',': 'comma',
    '.': 'period',
    '/': 'slash',
    '_': 'minus',
    '@': 'bracketleft',
}
SHIFTED = {
    '!': '1', '"': '2', '#': '3', '$': '4', '%': '5', '&': '6',
    "'": '7', '(': '8', ')': '9', '-': '0',
    '=': 'minus', '{': 'backslash',
    '+': 'semicolon', '*': 'apostrophe',
    '<': 'comma', '>': 'period', '?': 'slash',
}


def x(*args):
    subprocess.run(['xdotool'] + list(args), check=False)


def tap(key, shift=False):
    if shift:
        x('keydown', 'shift')
        time.sleep(0.05)
    x('keydown', key)
    time.sleep(HOLD)
    x('keyup', key)
    if shift:
        time.sleep(0.04)
        x('keyup', 'shift')
    time.sleep(GAP)


def send_char(ch):
    if ch in PLAIN:
        tap(PLAIN[ch])
    elif ch in SHIFTED:
        tap(SHIFTED[ch], shift=True)
    elif ch.isdigit():
        tap(ch)
    elif ch.isalpha():
        tap(ch.lower(), shift=ch.islower())
    else:
        raise SystemExit('no key for %r' % ch)


def send_line(text):
    for ch in text:
        send_char(ch)
    tap('Return')
    time.sleep(LINE_PAUSE)


if __name__ == '__main__':
    for line in sys.argv[1:]:
        send_line(line)
