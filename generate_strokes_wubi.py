#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import math
import random
import string
import textwrap
import itertools
import unicodedata
import collections

strokes = {}
used_codes = set()

codebook = []
started = False
with open('wordlist/wubi86.dict.yaml', 'r', encoding='utf-8') as f:
    for k, ln in enumerate(f):
        ln = ln.rstrip()
        if not ln:
            continue
        elif started:
            row = ln.lstrip('#').split()
            if len(row[0]) > 1:
                continue
            elif row[1][0] == 'z':
                continue
            ch = ord(row[0])
            if ch < 0x3400:
                continue
            code = [ord(x) - ord('a') + 1 for x in row[1]]
            freq = float(row[2]) if len(row) > 2 else 0
            codebook.append((ch, code, freq, k))
        elif ln == '...':
            started = True
codebook.sort(key=lambda x: (-len(x[1]), -x[2], x[3]))

for ch_id, code, freq, k in codebook:
    orig_code = code[:]
    if len(code) > 4:
        code = code[:4]
    elif len(code) < 4:
        code.extend([0] * (4-len(code)))
        while tuple(code) in used_codes:
            if code[-1] < 26:
                code[-1] = 26
            elif code[-1] < 28:
                code[-1] += 1
            else:
                break
    # print(row[0], code)
    if (ch_id not in strokes or
        any(x >= 26 or x == 0 for x in strokes.get(ch_id, [0])) and
        not any(x >= 26 or x == 0 for x in code)):
        if ch_id in strokes:
            old_code = strokes[ch_id]
            #print(chr(ch_id), old_code, tuple(code))
            if sum(x == old_code for x in strokes.values()) == 1:
                used_codes.remove(old_code)
        strokes[ch_id] = tuple(code)
        used_codes.add(tuple(code))


with open('wordlist/original-radical-stroke.txt', 'r', encoding='utf-8') as f:
    for ln in f:
        row = tuple(map(int, ln.strip().split()))
        if row[0] not in strokes:
            strokes[row[0]] = row[1:]


for k, v in sorted(strokes.items()):
    print(' '.join(map(str, (k,) + v)))
