#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import string
import unicodedata

re_has_eng = re.compile(r'[A-Za-z]+')
re_eng_word = re.compile(r"^[A-Za-z'àáèéìíòóùúüāēěīōūǎǐǒǔǘǚǜ]+$")

LEFT_PUNCTS = "\"'([{‘“〈《「『【〔"
RIGHT_PUNCTS = "\"')]}’”〉》」』】〕"
MIDDLE_PUNCTS = "!&*,./:;?@\\_~·、。々！，：；？—…"
DIGIT_PUNCTS = ("#$¥", "+-*/×÷=≠≈<>≤≥^", "%")

MAX_ENG_WORDS = 30000

def load_simplewordlist(filename):
    words = []
    with open(filename, 'r', encoding='utf-8') as f:
        for ln in f:
            words.append(ln.strip())
    return words


char_set = set(
    LEFT_PUNCTS + RIGHT_PUNCTS + MIDDLE_PUNCTS + ''.join(DIGIT_PUNCTS) +
    string.ascii_letters + string.digits + 'àáèéìíòóùúüāēěīōūǎǐǒǔǘǚǜ' + '〇'
)
char_set.update(load_simplewordlist(sys.argv[1]))

eng_words = load_simplewordlist(sys.argv[2])

keep_words = set()
if len(sys.argv) > 3:
    keep_words = set(load_simplewordlist(sys.argv[3]))

words = []
total = 0

for ln in sys.stdin:
    word, freq = ln.strip().split(None, 1)
    freq = int(freq)
    total += freq
    words.append((word, freq))

words.sort(key=lambda x: -x[1])

sum_freq = 0
printed_words = set()

for word, freq in words:
    sum_freq += freq
    if word in keep_words:
        print(word)
        keep_words.discard(word)
        continue
    elif any(x not in char_set for x in word):
        continue
    elif len(word) > 1 and all(unicodedata.category(x)[0] != 'L' for x in word) and sum_freq > total * 0.5:
        continue
    elif re_has_eng.search(word):
        continue
    if len(word) > 1 and sum_freq > total * 0.95:
        continue
    print(word)
    printed_words.add(word)


eng_words_num = 0

for word in eng_words:
    if word in printed_words or any(x not in char_set for x in word):
        continue
    print(word)
    eng_words_num += 1
    if eng_words_num >= MAX_ENG_WORDS:
        break


#for word in sorted(keep_words):
    #print(word)
