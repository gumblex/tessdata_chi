#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import string
import unicodedata


re_has_eng = re.compile(r'[A-Za-z]+')
re_eng_word = re.compile(r"^[A-Za-z']+$")

keep_words = set()
if len(sys.argv) > 2:
    with open(sys.argv[2], 'r', encoding='utf-8') as f:
        for ln in f:
            keep_words.add(ln.strip())

char_list = set(''.join(keep_words))
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    for ln in f:
        char_list.add(ln.strip())
char_list.add('〇')

words = []
total = 0

for ln in sys.stdin:
    word, freq = ln.strip().split(None, 1)
    freq = int(freq)
    total += freq
    words.append((word, freq))

words.sort(key=lambda x: -x[1])

sum_freq = 0
eng_words = 0

for word, freq in words:
    sum_freq += freq
    if word in keep_words:
        print(word)
        keep_words.discard(word)
        continue
    elif any(unicodedata.category(x) == 'Cn'
        or unicodedata.category(x) == 'Lo' and x not in char_list
        or 0x301d <= ord(x) <= 0x33ff
        # 3400 - 4db5 extA
        or 0x4db6 <= ord(x) <= 0x4dff
        or 0x9fef <= ord(x) <= 0xf000
        or 0xf003 <= ord(x) <= 0xff00
        for x in word):
        continue
    elif len(word) > 1 and all(unicodedata.category(x)[0] != 'L' for x in word) and sum_freq > total * 0.5:
        continue
    elif re_has_eng.search(word):
        if not re_eng_word.match(word) or eng_words >= 10000:
            continue
        else:
            eng_words += 1
    if len(word) > 1 and sum_freq > total * 0.97:
        continue
    print(word)

#for word in sorted(keep_words):
    #print(word)
