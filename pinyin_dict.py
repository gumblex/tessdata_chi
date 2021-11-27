#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import collections

import pypinyin
from pypinyin.pinyin_dict import pinyin_dict

re_bpmf_tones = re.compile('[ˉˊˇˋ˙]')
re_special_py = re.compile("(ń|ň|ǹ|m̄|ḿ|m̀|ê̄|ế|ê̌|ề)")

all_py = set()
all_bpmf = set()

for ch, pys in pinyin_dict.items():
    for py in pys.split(','):
        if re_special_py.search(py):
            continue
        all_py.add(pypinyin.style.convert(py, pypinyin.NORMAL, strict=True))
        all_py.add(pypinyin.style.convert(py, pypinyin.TONE, strict=True))
        bpmf = pypinyin.style.convert(py, pypinyin.BOPOMOFO, strict=True)
        all_bpmf.add(bpmf)
        all_bpmf.add(re_bpmf_tones.sub('', bpmf))


with open('pinyin.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(sorted(all_py)))
    f.write('\n')


with open('bopomofo.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(sorted(all_bpmf)))
    f.write('\n')

