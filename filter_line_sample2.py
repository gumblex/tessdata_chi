#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import math
import string
import collections
import unicodedata

LEFT_PUNCTS = "\"'(（[{‘“〈《「『【〔"
RIGHT_PUNCTS = "\"')）]}’”〉》」』】〕"
MIDDLE_PUNCTS = "!&*,./:;?@\\_~·、。々！，：；？—…"
END_PUNCTS = "!?…。！：；？"
CORE_PUNCTS = "、。！，：；？—…‘“〈《「『’”〉》」』（）"

re_digit = re.compile('[0-9]')
re_alpha = re.compile('[A-Za-z]')


def load_simplewordlist(filename):
    words = []
    with open(filename, 'r', encoding='utf-8') as f:
        for ln in f:
            words.append(ln.strip())
    return words


def load_bigram(bigram_freq_file, char_list):
    total = 0
    bigram_freq = {}
    with open(bigram_freq_file, 'r', encoding='utf-8') as f:
        for ln in f:
            fields = ln.rstrip().split(' ')
            if not fields[1]:
                continue
            word = fields[0]
            freq = int(fields[1])
            total += freq
            bigram_freq[word] = freq

    log_total = math.log(total)
    min_freq = 0
    for word, freq in bigram_freq.items():
        bigram_freq[word] = math.log(freq) - log_total
        if bigram_freq[word] < min_freq:
            min_freq = bigram_freq[word]
    return bigram_freq, min_freq


def sentence_score(s, bigram_freq, min_freq, additional_list):
    ch_num = 0
    last_ch = '\uf000'
    score = 0
    for ch in s.strip():
        if ch == ' ':
            continue
        elif unicodedata.category(ch) == 'Lo' or ch in CORE_PUNCTS:
            ch_num += 1
        elif ch.isdigit():
            ch = '\uf002'
        elif ch.isalpha():
            ch = '\uf001'
        if last_ch == ch and ch in '\uf001\uf002':
            continue
        freq = bigram_freq.get(last_ch + ch)
        if freq is None and ch in additional_list:
            freq = bigram_freq.get(last_ch + '\uf001')
        if freq is None:
            freq = min_freq
        score += freq
        if ch in END_PUNCTS:
            last_ch = '\uf000'
        else:
            last_ch = ch
    return ch_num//5, score


if __name__ == '__main__':
    script_dir = os.path.abspath(os.path.dirname(__file__))

    char_list = set(
        " "
        "\"'(（[{‘“〈《「『【〔"
        "\"')）]}’”〉》」』】〕"
        "!&*,./:;?@\\_~·、。々！，：；？—…"
        "#$¥+-*/×÷=≠≈<>≤≥^%°"
    )
    char_list.update(string.ascii_letters)
    char_list.update(string.digits)

    if len(sys.argv) < 2 or sys.argv[1] == 'zhs':
        lang = 'chi_sim'
        char_list.update(load_simplewordlist(
            os.path.join(script_dir, 'wordlist/zhs_chars.txt')))
        char_list.add('〇')
        #additional_list = ()
        additional_list = set(''.join(load_simplewordlist(
            os.path.join(script_dir, 'wordlist/pinyin.txt'))))
        char_list.update(additional_list)
        bigram_freq, min_freq = load_bigram('wordlist/bigramfreq_zhs.txt', char_list)
    else:
        lang = 'chi_tra'
        char_list.update(load_simplewordlist(
            os.path.join(script_dir, 'wordlist/zht_chars.txt')))
        char_list.add('〇')
        #additional_list = ()
        additional_list = set(''.join(load_simplewordlist(
            os.path.join(script_dir, 'wordlist/bopomofo.txt'))))
        char_list.update(additional_list)
        bigram_freq, min_freq = load_bigram('wordlist/bigramfreq_zht.txt', char_list)

    eng_lines = load_simplewordlist(
        os.path.join(script_dir, 'langdata/eng/eng.lstm_all.txt'))

    lines = []
    for line in sys.stdin:
        lines.append(''.join(x for x in line.strip() if x in char_list))
    lines.sort(key=lambda x: (
        sentence_score(x, bigram_freq, min_freq, additional_list) +
        (len(x), len(frozenset(x)), x),
    ), reverse=True)

    train_size = 10
    test_size = 1
    last_test = False
    used_lines_train = set()
    used_lines_test = set()
    line_for_char_train = collections.defaultdict(list)
    line_for_char_test = collections.defaultdict(list)
    line_for_length_train = collections.defaultdict(list)
    line_for_length_test = collections.defaultdict(list)
    for k, line in enumerate(lines):
        if last_test:
            line_for_char = line_for_char_train
            line_for_length = line_for_length_train
            used_lines = used_lines_train
            expect_size = train_size
        else:
            line_for_char = line_for_char_test
            line_for_length = line_for_length_test
            used_lines = used_lines_test
            expect_size = test_size
        length = len(line)
        for ch in line:
            last_test = not last_test
            char_lines = line_for_char[ch]
            if len(char_lines) >= expect_size:
                continue
            elif length < 5 and char_lines and len(lines[char_lines[0]]) > 10:
                continue
            line_for_char[ch].append(k)
            used_lines.add(k)
        if 5 <= length <= 50 and len(line_for_length[length]) < expect_size:
            line_for_length[length].append(k)
            used_lines.add(k)
    for ch in char_list.difference(line_for_char_train.keys()):
        if ch in line_for_char_test:
            line_for_char_train[ch].append(line_for_char_test[ch].pop())
            if not line_for_char_test[ch]:
                del line_for_char_test[ch]
    # for ch in sorted(char_list):
        # ch_lines = line_for_char.get(ch, ())
        # print(ch, len(ch_lines),
            # min(ch_lines, default=None),
            # min((len(lines[x]) for x in ch_lines), default=None),
            # max((len(lines[x]) for x in ch_lines), default=None)
        # )
    print(''.join(sorted(char_list.difference(line_for_char_train.keys()))))
    print(len(char_list))
    print(len(line_for_char_train))
    print(len(line_for_char_test))

    eng_split = int(len(eng_lines) * 0.9)
    with open('%s.lstm_train.txt' % lang, 'w', encoding='utf-8') as f:
        for k in sorted(used_lines_train):
            print(lines[k], file=f)
        for line in eng_lines[:eng_split]:
            print(line, file=f)
    with open('%s.lstm_test.txt' % lang, 'w', encoding='utf-8') as f:
        for k in sorted(used_lines_test):
            print(lines[k], file=f)
        for line in eng_lines[eng_split:]:
            print(line, file=f)
