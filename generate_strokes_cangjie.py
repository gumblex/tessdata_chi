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

started = False
with open('wordlist/cangjie5.dict.yaml', 'r', encoding='utf-8') as f:
    for ln in f:
        ln = ln.rstrip()
        if not ln:
            continue
        elif started:
            row = ln.split()
            if len(row[0]) > 1:
                continue
            elif row[1][0] in 'zx':
                continue
            elif row[1].startswith('yyy'):
                continue
            elif row[0] == '、':
                continue
            ch = ord(row[0])
            code = [ord(x) - ord('a') + 1 for x in row[1]]
            orig_code = code[:]
            if len(code) > 4:
                code[3] = code[-1]
                code = code[:4]
                if tuple(code) in used_codes:
                    code[2:4] = orig_code[-2:]
                    #if tuple(code) in used_codes:
                        #code[1:4] = orig_code[-3:]
                        #print(row, code)
            elif len(code) < 4:
                code.extend([0] * (4-len(code)))
            ch_id = ord(row[0])
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
        elif ln == '...':
            started = True


with open('wordlist/original-radical-stroke.txt', 'r', encoding='utf-8') as f:
    for ln in f:
        row = tuple(map(int, ln.strip().split()))
        if row[0] not in strokes:
            strokes[row[0]] = row[1:]


for k, v in sorted(strokes.items()):
    print(' '.join(map(str, (k,) + v)))

# seen = set()
# dup = 0
# for v in strokes.values():
    # if v in seen:
        # dup += 1
    # else:
        # seen.add(v)
# print(dup, len(strokes))
