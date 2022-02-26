#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

for ln in sys.stdin.buffer:
    try:
        sys.stdout.buffer.write(ln.decode('utf-8').encode('utf-8'))
    except UnicodeError:
        pass
