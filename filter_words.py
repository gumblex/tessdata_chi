#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import string
import unicodedata


re_has_eng = re.compile(r'[A-Za-z]+')
re_eng_word = re.compile(r"^[A-Za-z']+$")

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
    if any(unicodedata.category(x) == 'Cn'
        or ord(x) > 0xffff
        or 0x7f <= ord(x) <= 0x3000
        or 0x301d <= ord(x) <= 0x4dff
        or 0x9fef <= ord(x) <= 0xff00
        or x in '氵冫忄阝刂亻扌犭纟糹牜礻衤訁讠釒钅飠饣丬艹宀冖覀罒罓灬爫丨丿乀乁乄乚丶丷亅丄丅丆乛囗ˇ〥‰'
        for x in word):
        continue
    if len(word) > 1 and all(unicodedata.category(x)[0] != 'L' for x in word) and sum_freq > total * 0.5:
        continue
    if re_has_eng.search(word):
        if not re_eng_word.match(word) or eng_words >= 10000:
            continue
        else:
            eng_words += 1
    if len(word) > 1 and sum_freq > total * 0.97:
        continue
    print(word)
