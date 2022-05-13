#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import string

re_qs = re.compile('\?\?|[\ufffc\ufffd]|([?？]\s*){2,}')


def load_simplewordlist(filename):
    words = []
    with open(filename, 'r', encoding='utf-8') as f:
        for ln in f:
            words.append(ln.strip())
    return words


if __name__ == '__main__':
    script_dir = os.path.abspath(os.path.dirname(__file__))

    if len(sys.argv) < 2 or sys.argv[1] == 'zhs':
        filename_chlist = 'wordlist/cn_tygfhzb.txt'
    else:
        filename_chlist = 'wordlist/tw_cygzb.txt'

    chlist = load_simplewordlist(
        os.path.join(script_dir, filename_chlist))
    common_chars = set(string.ascii_letters + string.digits)
    common_chars.update(chlist[:5000])

    for raw_ln in sys.stdin.buffer:
        try:
            ln = raw_ln.strip().decode('utf-8')
        except UnicodeError:
            continue
        if not ln or re_qs.search(ln):
            continue
        length = len(ln)
        unusual = sum((ch not in common_chars) for ch in ln)
        if ((len(set(ln)) == 1 and length > 2) or
            (unusual / length > 0.5 and length > 2)
        ):
            continue
        sys.stdout.buffer.write(raw_ln)
