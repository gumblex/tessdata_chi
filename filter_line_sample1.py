#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import string
import random
import textwrap
import unicodedata

LEFT_PUNCTS = "\"'(（[{‘“〈《「『【〔"
RIGHT_PUNCTS = "\"')）]}’”〉》」』】〕"
MIDDLE_PUNCTS = "!&*,./:;?@\\_~·、。々！，：；？—…"
DIGIT_PUNCTS = ("#$¥", "+-*/×÷=≠≈<>≤≥^", "%°")
ALL_PUNCTS = (LEFT_PUNCTS + RIGHT_PUNCTS + MIDDLE_PUNCTS + ''.join(DIGIT_PUNCTS))

re_noleft = re.compile(r'^[!%),.:;>?\]}°·’”、。〉》」』】〕！），：；？]+')
re_noright = re.compile(r'[$\(\[{¥·‘“〈《「『【〔（]+$')
re_empty_pair = re.compile(r'[%s]+[%s]*[%s]+' %
    tuple(map(re.escape, (LEFT_PUNCTS[2:], MIDDLE_PUNCTS, RIGHT_PUNCTS[2:]))))
re_qs = re.compile('\?\s*\?|？\s*？|[\ufffc\ufffd]')
re_open = re.compile(r'([%s])\s*[%s]+' % tuple(map(re.escape,
    (LEFT_PUNCTS[2:], MIDDLE_PUNCTS + DIGIT_PUNCTS[2]))))
re_close = re.compile(r'[&*,/:;@\\_·、，：；%s]+\s*([%s])' % tuple(map(re.escape,
    (DIGIT_PUNCTS[0] + DIGIT_PUNCTS[1], RIGHT_PUNCTS[2:]))))
re_dup = re.compile(r'[!,:;?@\\·、。！，：；？ ]{2,}')
re_exqm = re.compile(r'^[!?]{1,5}\s*$|^[！？]{1,5}$')
re_space = re.compile(r'\s+')
re_fwspace_left = re.compile(r'([（‘“〈《「『【〔]+)\s+')
re_fwspace_right = re.compile(r'\s+([）’”〉》」』】〕]+)')
re_fwspace_mid = re.compile(r'\s+([·、。々！，：；？—…]+)\s+')
re_allpuncts = re.compile(r'[%s ]+' % re.escape(''.join(sorted(set(ALL_PUNCTS)))))

random.seed(12345)

class CJKTextWrapper(textwrap.TextWrapper):
    wordsep_simple_re = re.compile(r'(\s+|[%s]*[\u4e00-\u9FFF][%s]*|[¥$+-]*\d+(?:\.\d+)?(?:e[+-]\d+)?)' % (
        re.escape(LEFT_PUNCTS), re.escape(RIGHT_PUNCTS + MIDDLE_PUNCTS.replace('¥', ''))
    ))

    def _split(self, text):
        chunks = self.wordsep_simple_re.split(text)
        return [c for c in chunks if c]

def remove_dup_puncts(match):
    s = match.group(0)
    if s.rstrip() == s[0] and s[0] in '!,:;?':
        return s
    elif re_exqm.match(s):
        return s
    elif not s.strip():
        return ' '
    return s.strip()[0]

def remove_fw_space(x):
    if ' ' not in x:
        return x
    merged = []
    last_width = None
    for frag in x.split():
        this_width = (unicodedata.east_asian_width(frag[0]) in 'FW')
        if last_width is None or this_width == last_width == True:
            merged.append(frag)
        else:
            merged.append(' ' + frag)
        last_width = (unicodedata.east_asian_width(frag[-1]) in 'FW')
    return ''.join(merged)

def load_simplewordlist(filename):
    words = []
    with open(filename, 'r', encoding='utf-8') as f:
        for ln in f:
            words.append(ln.strip())
    return words


if __name__ == '__main__':
    script_dir = os.path.abspath(os.path.dirname(__file__))

    char_set = set(ALL_PUNCTS)
    char_set.add(' ')
    unusual_set = set(char_set)
    char_set.update(string.ascii_letters)
    char_set.update(string.digits)

    if len(sys.argv) < 2 or sys.argv[1] == 'zhs':
        lang = 'chi_sim'
        filename_chlist = 'wordlist/zhs_chars.txt'
        filename_phonetic = 'wordlist/pinyin.txt'
    else:
        lang = 'chi_tra'
        filename_chlist = 'wordlist/zht_chars.txt'
        filename_phonetic = 'wordlist/bopomofo.txt'

    chlist = load_simplewordlist(
        os.path.join(script_dir, filename_chlist))
    char_set.update(chlist)
    unusual_set.update(chlist[4000:])
    char_set.add('〇')
    phlist = ''.join(load_simplewordlist(
        os.path.join(script_dir, filename_phonetic)))
    unusual_set.update(set(phlist).difference(string.ascii_letters))
    char_set.update(phlist)

    max_length = 50
    unseen_lengths = {ch: set(range(1, max_length+1)) for ch in char_set}
    seen_lines = set()
    for raw_ln in sys.stdin.buffer:
        try:
            long_ln = raw_ln.strip().decode('utf-8')
        except UnicodeError:
            continue
        if '??' in long_ln:
            continue
        long_ln = re_space.sub(' ', long_ln)
        long_ln = re_fwspace_mid.sub(r'\1', long_ln)
        long_ln = re_fwspace_left.sub(r'\1', long_ln)
        long_ln = re_fwspace_right.sub(r'\1', long_ln)
        long_ln = re_empty_pair.sub('', long_ln)
        long_ln = re_open.sub(r'\1', long_ln)
        long_ln = re_close.sub(r'\1', long_ln)
        long_ln = long_ln.replace('...', '…').replace('… …', '……')
        long_ln = re_dup.sub(remove_dup_puncts, long_ln)
        long_ln = remove_fw_space(long_ln)
        if ' ' in long_ln:
            merged = []
            last_width = None
            for frag in long_ln.split():
                this_width = unicodedata.east_asian_width(frag[0])
                if last_width is None or this_width == last_width == True:
                    merged.append(frag)
                else:
                    merged.append(' ' + frag)
                last_width = this_width
        if len(long_ln) < max_length:
            lns = (long_ln,)
        else:
            wrapper = CJKTextWrapper(width=round(random.triangular(30, max_length, max_length)))
            lns = wrapper.wrap(long_ln)
        for ln in lns:
            if not ln:
                continue
            elif re_qs.search(ln):
                continue
            result = []
            unknown = 0
            unusual = 0
            remove_chars = set()
            for ch in ln:
                if ch not in char_set:
                    unknown += 1
                    category = unicodedata.category(ch)
                    if category[0] == 'Lo':
                        result.append(ch)
                    elif ch == '\u3000' or category[0] in 'PS':
                        result.append(' ')
                    continue
                unusual += (ch in unusual_set)
                result.append(ch)
                remove_chars.add(ch)
            result_line = ''.join(result).strip()
            result_line = re_noright.sub('', re_noleft.sub('', result_line))
            if not result_line:
                continue
            result_length = len(result_line)
            if ((len(set(result_line)) == 1 and result_length > 2) or
                unknown / result_length >= 0.5 or
                (unusual / result_length > 0.5 and result_length > 2)
            ):
                continue
            has_unseen = False
            for ch in remove_chars:
                lengths = unseen_lengths.get(ch, ())
                if result_length in lengths:
                    lengths.remove(result_length)
                    has_unseen = True
            if has_unseen or random.random() < 0.0015:
                result_charonly = re_allpuncts.sub('', result_line)
                if result_charonly in seen_lines:
                    continue
                seen_lines.add(result_charonly)
                print(result_line)
