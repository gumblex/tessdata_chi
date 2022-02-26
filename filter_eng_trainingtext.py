#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import string

LEFT_PUNCTS = "\"'(（[{‘“〈《「『【〔"
RIGHT_PUNCTS = "\"')）]}’”〉》」』】〕"
MIDDLE_PUNCTS = "!&*,./:;?@\\_~·、。々！，：；？—…"
DIGIT_PUNCTS = ("#$¥", "+-*/×÷=≠≈<>≤≥^", "%")
ALL_PUNCTS = (LEFT_PUNCTS + RIGHT_PUNCTS + MIDDLE_PUNCTS + ''.join(DIGIT_PUNCTS))


if __name__ == '__main__':
    script_dir = os.path.abspath(os.path.dirname(__file__))

    available_chars = set(
        ALL_PUNCTS +
        string.ascii_letters + string.digits + 'àáèéìíòóùúüāēěīōūǎǐǒǔǘǚǜ')

    for ln in sys.stdin:
        result = ' '.join(
            word for word in ln.strip().split(' ')
            if all(ch in available_chars for ch in word)
        )
        if result:
            print(result)
