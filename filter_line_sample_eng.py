#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import string
import random
import textwrap

LEFT_PUNCTS = "\"'([{‘“"
RIGHT_PUNCTS = "\"')]}’”"
MIDDLE_PUNCTS = "~…!&\',.:;?@\\_¥—"
DIGIT_PUNCTS = ("#$¥", "+-*/×÷=≠≈<>≤≥^", "%°")
ALL_PUNCTS = (LEFT_PUNCTS + RIGHT_PUNCTS + MIDDLE_PUNCTS + ''.join(DIGIT_PUNCTS))

re_noleft = re.compile(r'^[!%),.:;>?\]}°·’”、。〉》」』】〕！），：；？]+')
re_noright = re.compile(r'[$\(\[{¥·‘“〈《「『【〔（]+$')
re_empty_pair = re.compile(r'[%s]+[%s]*[%s]+' %
    tuple(map(re.escape, (LEFT_PUNCTS[2:], MIDDLE_PUNCTS, RIGHT_PUNCTS[2:]))))
re_qs = re.compile('\?\?|(？){3,}|[\ufffc\ufffd]')
re_open = re.compile(r'([%s])\s*[%s]+' % tuple(map(re.escape,
    (LEFT_PUNCTS[2:], MIDDLE_PUNCTS + DIGIT_PUNCTS[2]))))
re_close = re.compile(r'[&*,/:;@\\_·、，：；%s]+\s*([%s])' % tuple(map(re.escape,
    (DIGIT_PUNCTS[0] + DIGIT_PUNCTS[1], RIGHT_PUNCTS[2:]))))
re_dup = re.compile(r'[!,:;?@\\·、。！，：；？ ]{2,}')
re_exqm = re.compile(r'^[!?]{1,5}\s*$')
re_space = re.compile(r'\s+')
re_allpuncts = re.compile(r'[%s ]+' % re.escape(''.join(sorted(set(ALL_PUNCTS)))))

random.seed(12345)

def remove_dup_puncts(match):
    s = match.group(0)
    if s.rstrip() == s[0] and s[0] in '!,:;?':
        return s
    elif re_exqm.match(s):
        return s
    elif not s.strip():
        return ' '
    return s.strip()[0]

if __name__ == '__main__':
    script_dir = os.path.abspath(os.path.dirname(__file__))

    char_set = set(ALL_PUNCTS)
    char_set.update('é')
    unusual_set = set(char_set)
    char_set.add(' ')
    char_set.update(string.ascii_letters)
    char_set.update(string.digits)

    max_length = 100
    min_char_num = 10
    char_count = {}
    seen_lines = set()
    for raw_ln in sys.stdin.buffer:
        try:
            long_ln = raw_ln.strip().decode('utf-8')
        except UnicodeError:
            continue
        if '??' in long_ln:
            continue
        long_ln = re_space.sub(' ', long_ln)
        long_ln = re_empty_pair.sub('', long_ln)
        long_ln = re_open.sub(r'\1', long_ln)
        long_ln = re_close.sub(r'\1', long_ln)
        long_ln = re_dup.sub(remove_dup_puncts, long_ln)
        if len(long_ln) < max_length:
            lns = (long_ln,)
        else:
            wrapper = textwrap.TextWrapper(width=random.randint(50, max_length))
            lns = wrapper.wrap(long_ln)
        for ln in lns:
            if not ln:
                continue
            elif re_qs.search(ln):
                continue
            elif any(x not in char_set for x in ln):
                continue
            unusual = sum(x in unusual_set for x in ln)
            result_line = ln
            result_line = re_noright.sub('', re_noleft.sub('', result_line))
            if not result_line:
                continue
            result_length = len(result_line)
            if (result_length < 40 or
                len(set(result_line)) <= 10 or
                unusual / result_length > 0.5
            ):
                continue
            has_unseen = False
            for ch in set(result_line):
                cnt = char_count.get(ch, 0)
                if cnt < min_char_num:
                    has_unseen = True
                char_count[ch] = cnt + 1
            if has_unseen or random.random() < 0.002:
                result_charonly = re_allpuncts.sub('', result_line)
                if result_charonly in seen_lines:
                    continue
                seen_lines.add(result_charonly)
                print(result_line)
