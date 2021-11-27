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


zht_chars = collections.OrderedDict()

for filename in ('wordlist/tw_cygzb.txt', 'wordlist/tw_ccygzb.txt', 'wordlist/hk_cyzzxb.txt'):
    with open(filename, 'r', encoding='utf-8') as f:
        zht_chars.update({unicodedata.normalize('NFKC', x.strip()): 0
            for x in f.readlines()})


with open('wordlist/charfreq_zht.txt') as f:
    for ln in f:
        row = ln.strip().split()
        if len(row) < 2:
            continue
        word, freq = row
        if word in zht_chars:
            zht_chars[word] = int(freq)

sorted_chars = sorted(zht_chars.items(), key=lambda x: -x[1])
last_freq = None
for i, (ch, freq) in enumerate(sorted_chars):
    if i >= 8500:
        if freq == last_freq:
            print(ch)
        else:
            break
    else:
        last_freq = freq
        print(ch)


