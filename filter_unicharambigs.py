#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

with open(sys.argv[1], 'r', encoding='utf-8') as f:
    charset = frozenset(f.read())

lines = iter(sys.stdin)

sys.stdout.write(next(lines))

for ln in sys.stdin:
    row = ln.split('\t')
    chars = set(row[1].replace(' ', '') + row[3].replace(' ', ''))
    if chars.difference(charset):
        continue
    sys.stdout.write(ln)
