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


LEFT_PUNCTS = "\"'([{‘“〈《「『【〔"
RIGHT_PUNCTS = "\"')]}’”〉》」』】〕"
MIDDLE_PUNCTS = "!#$%&*+,-./:;<=>?@\\^_~·、。々！，：；？￥—…"
DOUBLE_PUNCTS = "!#$%&*/\\~！？—…"
ALL_PUNCTS = frozenset(LEFT_PUNCTS + RIGHT_PUNCTS + MIDDLE_PUNCTS + DOUBLE_PUNCTS)
ALPHANUMS = string.ascii_letters + string.digits

EXCLUDE_CHARS = (
'氵冫忄阝刂亻扌犭纟糹牜礻衤訁讠釒钅飠饣丬艹宀冖覀罒罓灬爫丨丿乀乁乄乚丶丷亅丄丅丆乛囗ˇ〥'
)


class CJKTextWrapper(textwrap.TextWrapper):
    wordsep_simple_re = re.compile(r'(\s+|[%s]*[\u4e00-\u9FFF][%s]*|[￥+-]*\d+(?:\.\d+)?(?:e[+-]\d+)?)' % (
        re.escape(LEFT_PUNCTS), re.escape(RIGHT_PUNCTS + MIDDLE_PUNCTS.replace('￥', ''))
    ))

    def _split(self, text):
        chunks = self.wordsep_simple_re.split(text)
        return [c for c in chunks if c]


def load_wordlist(filename, tygfhzb):
    end_punct = '!?。！：；？…'
    total1 = total2 = 0
    max_in_freq1 = max_in_freq2 = 0
    freq1 = []
    freq2 = collections.defaultdict(list)
    with open(filename, 'r', encoding='utf-8') as f:
        for ln in f:
            fields = ln.rstrip().split(' ')
            if not fields[1]:
                continue
            word = fields[0]
            freq = int(fields[1])
            if any(x not in '\uf001\uf002·、。々〇！，：；？￥—…' and (
                unicodedata.category(x) in ('Cn', 'Co', 'Cs')
                or 0x7f <= ord(x) <= 0x3000
                or unicodedata.category(x) == 'Lo' and x not in tygfhzb
                or 0x301d <= ord(x) <= 0x33ff
                # 3400 - 4db5 extA
                or 0x4db6 <= ord(x) <= 0x4dff
                or 0x9fef <= ord(x) <= 0xf000
                or 0xf003 <= ord(x) <= 0xff00
                or x in EXCLUDE_CHARS
            ) for x in word):
                continue
            if len(word) == 1:
                freq1.append((word, freq))
                total1 += freq
                if freq > max_in_freq1:
                    max_in_freq1 = freq
            else:
                freq2[word[0]].append((word[1:], freq))
                total2 += freq
                if freq > max_in_freq2:
                    max_in_freq2 = freq
    #print(total1, total2)
    #print(max_in_freq1, max_in_freq2)
    freq1.sort(key=lambda x: -x[1])
    sum_freq = 0
    for i, (word, freq) in enumerate(freq1):
        freq1[i] = (word, freq / total1)
        sum_freq += freq
        if sum_freq > total1 * 0.9998:
            #print(i, word, freq)
            break
    freq1 = freq1[:i]
    for word1 in freq2:
        for i, (word2, freq) in enumerate(freq2[word1]):
            freq2[word1][i] = (word2, freq / total2)
    return freq1, freq2


def load_engwordlist(filename):
    words = []
    with open(filename, 'r', encoding='utf-8') as f:
        for ln in f:
            words.append(ln.strip())
    return words


def generate_text(freq1, freq2, eng_words, total_length=200000):
    length = 0
    wlist1 = [x[0] for x in freq1]
    weights1 = [x[1] for x in freq1]
    cum_weights1 = tuple(itertools.accumulate(weights1))
    unused = {x: 2 for x in wlist1}
    unused_alphas = set(string.ascii_letters)
    f2weights = {}
    for word1, wl2 in freq2.items():
        wlist2, weights2 = zip(*wl2)
        f2weights[word1] = (wlist2, tuple(itertools.accumulate(weights2)))

    def get_eng_words():
        result = ' '.join(
            (w.upper() if case == 1 else (w.title() if case == 2 else w)) + punct
            for w, case, punct in ((
                rw, random.randint(0, 2),
                random.choice(('', '', '', ',', '.', ';', '?', '!')
            )) for rw in random.choices(eng_words, k=random.randint(1, 3))
            )
        )
        if not result[-1].isalpha():
            result = result[-1]
        return result

    def get_word(last_word, word):
        nonlocal unused_alphas
        if word == '…' and last_word[-1] != '…':
            return '……'
        elif word == '—' and last_word[-1] != '—':
            return '——'
        # elif last_word in '\uf001\uf002' and word in '\uf001\uf002':
            # return None
        elif word == '\uf001':
            if unused_alphas:
                while True:
                    result = get_eng_words()
                    if set(result) & unused_alphas:
                        break
                unused_alphas -= set(result)
            else:
                result = get_eng_words()
        elif word == '\uf002':
            num_type = random.randint(0, 4)
            if num_type == 0:
                result = str(random.randint(0, 2500))
            elif num_type == 1:
                result = '%.3f' % random.gauss(0, 10000)
            elif num_type == 2:
                result = str(random.randint(1900, 2025))
            elif num_type == 3:
                result = '￥%.2f' % random.gauss(200, 100)
            else:
                result = '%.5g' % math.exp(random.uniform(0, 16))
        else:
            result = word
        ch1 = last_word[-1]
        ch2 = result[0]
        c1_ispunct = (ch1 in ALL_PUNCTS)
        c2_ispunct = (ch2 in ALL_PUNCTS)
        w1 = unicodedata.east_asian_width(ch1)
        w2 = unicodedata.east_asian_width(ch2)
        cat1 = unicodedata.category(ch1)
        cat2 = unicodedata.category(ch2)
        if cat1 == 'Lo' and cat2 == 'Lo':
            return result
        elif cat1 == 'Lo' and ch2 == ',':
            return '，'
        elif c1_ispunct and c2_ispunct:
            if (ch1 == ch2 or
                (ch1 in LEFT_PUNCTS and ch2 not in LEFT_PUNCTS) or
                (ch1 in MIDDLE_PUNCTS and ch2 in MIDDLE_PUNCTS and
                 ch1 not in DOUBLE_PUNCTS or ch2 not in DOUBLE_PUNCTS)):
                return None
            return result
        elif ch1 == '\uf002' and ch2 in '%+-':
            return result
        elif (
            (ch1 in '\uf001\uf002' and ch2 in '\uf001\uf002') or
            (ch1 in '\uf001\uf002' and w2 in 'FWA' and not c2_ispunct) or
            (c1_ispunct and ch1 not in LEFT_PUNCTS
             and not c2_ispunct and w1 not in 'FWA') or
            (not c1_ispunct and w1 in 'FWA' and
             not c2_ispunct and w2 not in 'FWA') or
            (w1 not in 'FWA' and not c1_ispunct and w2 in 'FWA') or
            (w1 in 'FWA' and c2_ispunct and w2 not in 'FWA' and ch2 not in ',.:;!?"\')]}')):
            result = ' ' + result
        return result

    result = []
    last_ch = '啊'
    while length < total_length * 0.75 and unused:
        ch = random.choices(wlist1, cum_weights=cum_weights1)[0]
        if ch not in unused:
            continue
        word = get_word(last_ch, ch)
        if not word:
            continue
        result.append(word)
        unused[ch] -= 1
        if unused[ch] <= 0:
            idx = wlist1.index(ch)
            del wlist1[idx]
            del weights1[idx]
            cum_weights1 = tuple(itertools.accumulate(weights1))
            del unused[ch]
        last_ch = word
        length += 1
        while True:
            try:
                wlist2, cw2 = f2weights[last_ch]
            except KeyError:
                break
            ch = random.choices(wlist2, cum_weights=cw2)[0]
            word = get_word(last_ch, ch)
            if not word:
                break
            result.append(word)
            if ch in unused:
                unused[ch] -= 1
                if unused[ch] <= 0:
                    idx = wlist1.index(ch)
                    del wlist1[idx]
                    del weights1[idx]
                    cum_weights1 = tuple(itertools.accumulate(weights1))
                    del unused[ch]
            last_ch = ch
            length += 1
    while length < total_length and unused:
        ch = random.choices(wlist1, cum_weights=cum_weights1)[0]
        if ch not in unused:
            continue
        word = get_word(last_ch, ch)
        if not word:
            continue
        result.append(word)
        unused[ch] -= 1
        if unused[ch] <= 0:
            idx = wlist1.index(ch)
            del wlist1[idx]
            del weights1[idx]
            cum_weights1 = tuple(itertools.accumulate(weights1))
            del unused[ch]
        last_ch = ch
        length += 1
        try:
            wlist2, cw2 = f2weights[last_ch]
        except KeyError:
            continue
        ch = random.choices(wlist2, cum_weights=cw2)[0]
        word = get_word(last_ch, ch)
        if not word:
            continue
        result.append(word)
        if ch in unused:
            unused[ch] -= 1
            if unused[ch] <= 0:
                idx = wlist1.index(ch)
                del wlist1[idx]
                del weights1[idx]
                cum_weights1 = tuple(itertools.accumulate(weights1))
                del unused[ch]
        last_ch = ch
        length += 1
    tw = CJKTextWrapper(width=40)
    return tw.fill(''.join(result))


if __name__ == '__main__':
    tygfhzb = frozenset(open('wordlist/tygfhzb.txt').read().strip().split())
    freq1, freq2 = load_wordlist('wordlist/bigramfreq_zhs.txt', tygfhzb)
    eng_words = load_engwordlist('wordlist/google-10000-english.txt')
    text = generate_text(freq1, freq2, eng_words)
    print(text)
