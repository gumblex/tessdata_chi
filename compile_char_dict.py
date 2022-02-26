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

base_dir = 'wordlist'
char_list_files = {
    'zhs': ('tygfhzb.txt',),
    'zht': ('tw_cygzb.txt', 'tw_ccygzb.txt', 'hk_cyzzxb.txt')
}
exclude_chars = set('氵冫忄阝刂亻扌犭纟糹牜礻衤訁讠釒钅飠饣丬艹宀冖覀罒罓灬爫丨丿乀乁乄乚丶丷亅丄丅丆乛囗')

if len(sys.argv) < 2 or sys.argv[1] == 'zhs':
    lang = 'zhs'
    other_lang = 'zht'
    conv_file = 'TSCharacters.txt'
    freq_file = 'charfreq_zhs.txt'
    guarantee_list = (('tygfhzb.txt', 3500),)
    guarantee_list2 = 'tygfhzb.txt'
    guarantee_list2_conv = False
else:
    lang = 'zht'
    other_lang = 'zhs'
    conv_file = 'STCharacters.txt'
    freq_file = 'charfreq_zht.txt'
    guarantee_list = (
        ('tw_cygzb.txt', 5000),
        ('hk_cyzzxb.txt', 5000)
    )
    guarantee_list2 = 'tygfhzb.txt'
    guarantee_list2_conv = True


char_lists = {}
for filenames in char_list_files.values():
    for filename in filenames:
        with open(os.path.join(base_dir, filename), 'r', encoding='utf-8') as f:
            char_lists[filename] = [
                unicodedata.normalize('NFKC', x.strip()) for x in f]

conv_table = {}
with open(os.path.join(base_dir, conv_file), 'r', encoding='utf-8') as f:
    for ln in f:
        key, values = ln.rstrip().split('\t', 1)
        conv_table[key] = values.split()

char_set = collections.OrderedDict()

for filename in char_list_files[lang]:
    with open(os.path.join(base_dir, filename), 'r', encoding='utf-8') as f:
        char_set.update({unicodedata.normalize('NFKC', x.strip()): 0
            for x in f})

for filename in char_list_files[other_lang]:
    with open(os.path.join(base_dir, filename), 'r', encoding='utf-8') as f:
        for ln in f:
            ch = unicodedata.normalize('NFKC', ln.strip())
            for conv_ch in conv_table.get(ch, (ch,)):
                char_set[conv_ch] = 0

for ch in exclude_chars:
    if ch in char_set:
        del char_set[ch]

guarantee_chars = set()
for filename, num in guarantee_list:
    guarantee_chars.update(char_lists[filename][:num])

if guarantee_list2_conv:
    guarantee_chars2 = set()
    for ch in char_lists[guarantee_list2]:
        guarantee_chars2.update(conv_table.get(ch, (ch,)))
else:
    guarantee_chars2 = set(char_lists[guarantee_list2])

total_freq = 0
with open(os.path.join(base_dir, freq_file), 'r', encoding='utf-8') as f:
    for ln in f:
        row = ln.strip().split()
        if len(row) < 2:
            continue
        word, freq = row
        if word in char_set:
            freq = int(freq)
            char_set[word] = freq
            total_freq += freq

sorted_chars = sorted(char_set.items(), key=lambda x: (-x[1], x[0]))
all_chars = set(guarantee_chars)
acc_freq = 0
last_freq = None
status = 0
for ch, freq in sorted_chars:
    if ord(ch) > 0xffff:
        continue
    elif freq == 0:
        break
    acc_freq += freq
    if status == 0 and acc_freq / total_freq > 0.999:
        status = 1
    if status == 1 and freq != last_freq:
        status = 2
    if status == 2:
        if len(all_chars) >= 8000:
            status = 3
        if ch not in guarantee_chars2:
            continue
    if status == 3 and freq != last_freq:
        break
    # print(ch, status, freq, acc_freq / total_freq, len(all_chars))
    all_chars.add(ch)
    last_freq = freq

for ch in sorted(all_chars, key=lambda x: (-char_set[x], x)):
    print(ch)
