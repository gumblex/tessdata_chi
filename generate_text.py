#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import math
import random
import string
import textwrap
import itertools
import unicodedata
import collections

random.seed(12345)

LEFT_PUNCTS = "\"'([{‘“〈《「『【〔"
RIGHT_PUNCTS = "\"')]}’”〉》」』】〕"
MIDDLE_PUNCTS = "!&*,./:;?@\\_~·、。々！，：；？—…"
DIGIT_PUNCTS = ("#$¥", "+-*/×÷=≠≈<>≤≥^", "%°")
PUNCT_PATTERN_L = {
    ':': '"\'([{',
    '：': '“〈《「『【〔',
}
PUNCT_PATTERN_R = {
    '"': ('.!?', ',.;'),
    '”': ('。！？', '，。、；'),
    '」': ('。！？', '，。、；'),
    '》': ('', '：，。'),
    ')': ('.!?', ',.;'),
    ']': ('.', ',;'),
    '}': ('.', ',;'),
}

LEFT_MID_PUNCTS = frozenset(LEFT_PUNCTS + MIDDLE_PUNCTS)
ALL_PUNCTS = frozenset(LEFT_PUNCTS + RIGHT_PUNCTS + MIDDLE_PUNCTS)

re_alphanum = re.compile('[A-Za-z0-9]')


class CJKTextWrapper(textwrap.TextWrapper):
    wordsep_simple_re = re.compile(r'(\s+|[%s]*[\u4e00-\u9FFF][%s]*|[¥$+-]*\d+(?:\.\d+)?(?:e[+-]\d+)?)' % (
        re.escape(LEFT_PUNCTS), re.escape(RIGHT_PUNCTS + MIDDLE_PUNCTS.replace('¥', ''))
    ))

    def _split(self, text):
        chunks = self.wordsep_simple_re.split(text)
        return [c for c in chunks if c]


def load_wordlist(bigram_freq_file, char_list):
    total1 = total2 = 0
    max_in_freq2 = 0
    freq1 = {}
    freq1_start = {}
    freq2 = collections.defaultdict(list)
    with open(bigram_freq_file, 'r', encoding='utf-8') as f:
        for ln in f:
            fields = ln.rstrip().split(' ')
            if not fields[1]:
                continue
            word = fields[0]
            freq = int(fields[1])
            if len(word) < 2:
                if word not in char_list:
                    continue
                total1 += freq
                freq1[word] = freq
            elif word[0] == '\uf000':
                if word[1] not in char_list:
                    continue
                total2 += freq
                freq1_start[word[1]] = freq
            elif word[0] not in char_list:
                continue
            else:
                if word[1] not in char_list and word[1] not in LEFT_MID_PUNCTS:
                    freq2[word[0]].append(('', freq))
                else:
                    freq2[word[0]].append((word[1:], freq))
                total2 += freq
                if freq > max_in_freq2:
                    max_in_freq2 = freq
    #print(total1, total2)
    #print(max_in_freq1, max_in_freq2)
    for word in freq1:
        if word in freq1_start:
            freq1[word] = freq1_start[word] / total2
        else:
            freq1[word] /= total1
    for word1 in freq2:
        for i, (word2, freq) in enumerate(freq2[word1]):
            freq2[word1][i] = (word2, freq / total2)
    return freq1, freq2


def load_simplewordlist(filename):
    words = []
    with open(filename, 'r', encoding='utf-8') as f:
        for ln in f:
            words.append(ln.strip())
    return words


class TextGenerator:
    def __init__(self, freq1, freq2, add_words, eng_words):
        self.chars = []
        self.char_freq = []
        for word, freq in freq1.items():
            self.chars.append(word)
            self.char_freq.append(freq)
        self.chars_set = frozenset(self.chars)
        self.char_cum_weights = tuple(itertools.accumulate(self.char_freq))
        self.bigrams = freq2
        for word1, wl2 in freq2.items():
            wlist2, weights2 = zip(*wl2)
            self.bigrams[word1] = (wlist2, tuple(itertools.accumulate(weights2)))

        # pinyin, bpmf
        self.add_words = list(set(add_words) |
            set(x.upper() for x in eng_words))
        self.eng_words = list(set(eng_words) |
            set(x.lower() for x in eng_words) |
            set(x.upper() for x in eng_words) |
            set(x.title() for x in eng_words))

        self.cur_chars = self.chars.copy()
        self.cur_char_freq = self.char_freq.copy()
        self.cur_char_cum_weights = self.char_cum_weights

        self.unused_chars = list(self.chars) * 2
        self.unused_eng = list(string.ascii_letters) * 2
        self.unused_add = sorted(set(itertools.chain(*add_words))) * 2
        self.unused_digit = list(string.digits + ''.join(DIGIT_PUNCTS)) * 2
        self.unused_punc = sorted(ALL_PUNCTS) * 2

        self.last_char = None
        self.status = 0
        self.left_punc = None

    def get_eng_words(self):
        words = []
        for word in random.choices(self.eng_words, k=random.randint(1, 3)):
            # punc = random.randint(0, ws_weight)
            # ws_weight = 50
            # if not word[-1].isalpha():
                # pass
            # elif punc in (ws_weight + 1, ws_weight + 2):
                # word += ','
            # elif punc == ws_weight + 3:
                # word += '.'
            # elif punc == ws_weight + 4:
                # word += ';'
            # elif punc == ws_weight + 5:
                # word += '?'
            # elif punc == ws_weight + 6:
                # word += '!'
            # elif punc == ws_weight + 7:
                # word += '_'
            # elif punc == ws_weight + 8:
                # word += '&'
            # elif punc == ws_weight + 9:
                # word += '@'
            # elif punc == 13:
                # word = '(%s)' % word
            # elif punc == 14:
                # word = '[%s]' % word
            # elif punc == 15:
                # word = '{%s}' % word
            # elif punc == 16:
                # word = '"%s"' % word
            # elif punc == 17:
                # word = "'%s'" % word
            words.append(word)
        result = ' '.join(words).replace('_ ', '_').replace('@ ', '@')
        return result

    def get_add_words(self):
        result = ' '.join(
            random.choices(self.add_words, k=random.randint(1, 2)))
        if random.randint(0, 1) == 0:
            result = '(%s)' % result
        return result

    def get_digits(self):
        digit_num = random.randint(1, 3)
        if digit_num == 1:
            digit_type = random.randint(0, 2)
            result = '%.5g' % math.exp(random.uniform(0, 16))
            if digit_type == 1:
                result = random.choice(DIGIT_PUNCTS[0]) + result
            elif digit_type == 2:
                result += random.choice(DIGIT_PUNCTS[2])
        else:
            result = ''
            for i in range(digit_num):
                if i > 0:
                    result += ' %s ' % random.choice(DIGIT_PUNCTS[1])
                result += '%.5g' % math.exp(random.uniform(0, 16))
        return result

    def get_char(self):
        get_single = True
        if self.last_char in self.bigrams:
            get_single = False
            wlist2, cw2 = self.bigrams[self.last_char]
            ch = random.choices(wlist2, cum_weights=cw2)[0]
            if not ch:
                get_single = True
        if get_single:
            if not self.cur_chars:
                self.cur_chars = self.chars.copy()
                self.cur_char_freq = self.char_freq.copy()
                self.cur_char_cum_weights = self.char_cum_weights
            ch = random.choices(
                self.cur_chars, cum_weights=self.cur_char_cum_weights)[0]

        if ch in self.unused_chars:
            idx = self.unused_chars.index(ch)
            del self.unused_chars[idx]
            if ch not in self.unused_chars:
                idx = self.cur_chars.index(ch)
                del self.cur_chars[idx]
                del self.cur_char_freq[idx]
                self.cur_char_cum_weights = tuple(
                    itertools.accumulate(self.cur_char_freq))
        return ch

    def get_punc(self, punc_type=None):
        if punc_type is None:
            if self.left_punc is None:
                punc_type = random.choice(('left', 'middle'))
            else:
                punc_type = 'right'
        if punc_type == 'left':
            self.left_punc = random.randrange(len(LEFT_PUNCTS))
            word = LEFT_PUNCTS[self.left_punc]
        elif punc_type == 'middle':
            word = random.choice(MIDDLE_PUNCTS)
            if word in PUNCT_PATTERN_L and random.randint(0, 1):
                word += random.choice(PUNCT_PATTERN_L[word])
            elif word == '…':
                word += '…'
            elif word == ',' and self.last_char in self.chars_set:
                word = '，'
        # elif punc_type == 'right':
        else:
            word = RIGHT_PUNCTS[self.left_punc]
            if word in PUNCT_PATTERN_R and random.randint(0, 1):
                lr = random.randint(0, 1)
                if lr == 0 and PUNCT_PATTERN_R[word][0]:
                    word = random.choice(PUNCT_PATTERN_R[word][0]) + word
                elif lr == 1:
                    word += random.choice(PUNCT_PATTERN_R[word][1])
            self.left_punc = None
        return word

    def get_next_word(self):
        if self.left_punc:
            # left
            if self.status == 0:
                next_types = ('char', 'eng')
            else:
                next_types = ('char', 'eng', 'right')
        elif self.status == 0:
            # start
            next_types = ('char', 'left', 'eng', 'digit')
        elif self.status == 1:
            # char
            next_types = ('char', 'middle', 'left', 'eng', 'add', 'digit')
        elif self.status == 3:
            # eng
            next_types = ('char', 'middle', 'digit')
        elif self.status == 4:
            # add/digit
            next_types = ('char', 'eng')
        elif self.status == 5:
            next_types = ('char',)
        type_cum_weights = tuple(x + 500 for x in (0, 3, 5, 6, 7, 8))
        next_type = random.choices(
            next_types, cum_weights=type_cum_weights[:len(next_types)])[0]
        if next_type == 'char':
            word = self.get_char()
            if not word:
                return word
            elif word in LEFT_MID_PUNCTS:
                if word in LEFT_PUNCTS:
                    self.left_punc = LEFT_PUNCTS.index(word)
                elif word == ',':
                    word = '，'
                self.status = 0
                if word in self.unused_punc:
                    del self.unused_punc[self.unused_punc.index(word)]
                if word == '…':
                    word += '…'
            else:
                self.status = 1
        elif next_type in ('left', 'middle', 'right'):
            word = self.get_punc(next_type)
            self.status = 0
            used_new = set(word).intersection(self.unused_punc)
            for ch in used_new:
                del self.unused_punc[self.unused_punc.index(ch)]
        # elif next_type in ('eng', 'add', 'digit'):
        else:
            if next_type == 'eng':
                unused = self.unused_eng
                fn = self.get_eng_words
                self.status = 3
            elif next_type == 'add':
                unused = self.unused_add
                fn = self.get_add_words
                self.status = 4
            else:
                unused = self.unused_digit
                fn = self.get_digits
                self.status = 4
            if unused:
                while True:
                    word = fn()
                    used_new = set(word).intersection(unused)
                    if used_new:
                        break
                for ch in used_new:
                    del unused[unused.index(ch)]
            else:
                word = fn()
            used_new = set(word).intersection(self.unused_punc)
            for ch in used_new:
                del self.unused_punc[self.unused_punc.index(ch)]
        return word

    def has_space(self, word):
        if not self.last_char or not word:
            return ''
        ch_types = ['fw', 'fw']
        for i, ch in enumerate((self.last_char, word[0])):
            if re_alphanum.match(ch) or unicodedata.category(ch) in ('Ll', 'Lu'):
                ch_types[i] = 'alphanum'
            elif unicodedata.east_asian_width(ch) in 'FWA':
                if ch in ALL_PUNCTS:
                    ch_types[i] = 'fw-p'
                else:
                    ch_types[i] = 'fw'
            elif ch in LEFT_PUNCTS:
                ch_types[i] = 'left'
            elif ch in RIGHT_PUNCTS:
                ch_types[i] = 'right'
            elif ch in '!*,.:;?':
                ch_types[i] = 'stop'
            else:
                ch_types[i] = 'hw'
        #print(self.last_char, word[0], ch_types)
        if tuple(ch_types) in (
            ('alphanum', 'alphanum'),
            ('alphanum', 'fw'),
            ('alphanum', 'left'),
            ('alphanum', 'hw'),
            ('fw', 'alphanum'),
            ('fw', 'left'),
            ('fw', 'hw'),
            ('left', 'right'),
            ('left', 'stop'),
            ('left', 'hw'),
            ('right', 'alphanum'),
            ('right', 'fw'),
            ('right', 'left'),
            ('right', 'hw'),
            ('stop', 'alphanum'),
            ('stop', 'fw'),
            ('stop', 'left'),
            ('stop', 'stop'),
            ('stop', 'hw'),
            ('hw', 'alphanum'),
            ('hw', 'fw'),
            ('hw', 'left'),
            ('hw', 'stop'),
            ('hw', 'hw'),
        ):
            return ' '
        return ''

    def generate_text(self, total_length=250000):
        length = 0
        result = []
        unused_list = (
            (self.unused_chars, self.get_char),
            (self.unused_eng, self.get_eng_words),
            (self.unused_add, self.get_add_words),
            (self.unused_digit, self.get_digits),
            (self.unused_punc, self.get_punc)
        )
        while length < total_length - sum(map(len, unused_list)) * 3:
            word = self.get_next_word()
            if word:
                result.append(self.has_space(word) + word)
                length += len(result[-1])
                self.last_char = word[-1]
        # print(unused_list)
        while self.unused_chars:
            self.status = 5
            self.last_char = None
            for i in range(random.randrange(1, 3)):
                word = self.get_next_word()
                if not word:
                    break
                result.append(self.has_space(word) + word)
                length += len(result[-1])
        while any(x[0] for x in unused_list):
            self.status = 0
            for i in range(random.randrange(1, 10)):
                word = self.get_next_word()
                if not word:
                    continue
                result.append(self.has_space(word) + word)
                length += len(result[-1])
                self.last_char = word[-1]
            unused, fn = random.choice([x for x in unused_list if x[0]])
            while True:
                word = fn()
                used_new = set(word).intersection(unused)
                if used_new:
                    break
            for ch in used_new:
                del unused[unused.index(ch)]
            result.append(self.has_space(word) + word)
            length += len(result[-1])
            self.last_char = word[-1]
        while length < total_length:
            word = self.get_next_word()
            if word:
                result.append(self.has_space(word) + word)
                length += len(result[-1])
                self.last_char = word[-1]
        tw = CJKTextWrapper(width=40)
        return tw.fill(''.join(result))


def generate_text(freq1, freq2, additional_list, eng_words, total_length=250000):
    length = 0
    wlist1 = [x[0] for x in freq1]
    wlist1_orig = wlist1.copy()
    weights1 = [x[1] for x in freq1]
    weights1_orig = weights1.copy()
    cum_weights1 = tuple(itertools.accumulate(weights1))
    cum_weights1_orig = cum_weights1
    unused = collections.Counter({x: 2 for x in wlist1})
    unused_alphas = sorted(
        set(string.ascii_letters).union(set(itertools.chain(*additional_list)))
    ) * 2
    f2weights = {}
    for word1, wl2 in freq2.items():
        wlist2, weights2 = zip(*wl2)
        f2weights[word1] = (wlist2, tuple(itertools.accumulate(weights2)))

    def get_eng_words():
        if random.randint(0, 1) == 0:
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
        else:
            result = ' '.join(
                random.choices(additional_list, k=random.randint(1, 2)))
            if random.randint(0, 1) == 0:
                result = '(%s)' % result
        return result

    def get_word(last_word, word):
        nonlocal unused_alphas
        if not word:
            return None
        elif word == '…' and last_word[-1] != '…':
            return '……'
        elif word == '—' and last_word[-1] != '—':
            # return '——'
            return '—'
        # elif last_word in '\uf001\uf002' and word in '\uf001\uf002':
            # return None
        elif word == '\uf001':
            if unused_alphas:
                while True:
                    result = get_eng_words()
                    used_new = set(result).intersection(unused_alphas)
                    if used_new:
                        break
                for ch in used_new:
                    del unused_alphas[unused_alphas.index(ch)]
            else:
                result = get_eng_words()
        elif word == '\uf002':
            num_type = random.randint(0, 5)
            if num_type == 0:
                result = str(random.randint(0, 2500))
            elif num_type == 1:
                result = '%.3f' % random.gauss(0, 10000)
            elif num_type == 2:
                result = str(random.randint(1900, 2025))
            elif num_type == 3:
                result = '¥%.2f' % random.gauss(200, 100)
            elif num_type == 4:
                result = '$%.2f' % random.gauss(200, 100)
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
                (ch1 in MIDDLE_PUNCTS and ch2 in MIDDLE_PUNCTS)): # and
                 # ch1 not in DOUBLE_PUNCTS or ch2 not in DOUBLE_PUNCTS)):
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
    while length < total_length - len(unused) * 3:
        if not wlist1:
            wlist1 = wlist1_orig.copy()
            weights1 = weights1_orig.copy()
            cum_weights1 = cum_weights1_orig
        ch = random.choices(wlist1, cum_weights=cum_weights1)[0]
        if unused and ch not in unused:
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
        length += len(word)
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
            length += len(word)
    while unused_alphas:
        while True:
            result = get_eng_words()
            used_new = set(result).intersection(unused_alphas)
            if used_new:
                break
        for ch in used_new:
            del unused_alphas[unused_alphas.index(ch)]
        result.append(' ' + word)
    while unused:
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
        length += len(word)
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
        length += len(word)
    tw = CJKTextWrapper(width=40)
    return tw.fill(''.join(result))


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] == 'zhs':
        char_list = set(load_simplewordlist('wordlist/zhs_chars.txt'))
        char_list.add('〇')
        freq1, freq2 = load_wordlist('wordlist/bigramfreq_zhs.txt', char_list)
        additional_list = load_simplewordlist('wordlist/pinyin.txt')
    else:
        char_list = set(load_simplewordlist('wordlist/zht_chars.txt'))
        char_list.add('〇')
        freq1, freq2 = load_wordlist('wordlist/bigramfreq_zht.txt', char_list)
        additional_list = load_simplewordlist('wordlist/bopomofo.txt')
    eng_words = load_simplewordlist('wordlist/google-10000-english.txt')
    tg = TextGenerator(freq1, freq2, additional_list, eng_words)
    text = tg.generate_text(250000)
    print(text)
