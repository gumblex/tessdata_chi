#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import sqlite3
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import fontTools.ttLib


CJK_RANGES = (
    (0x2E80, 0x2EFF), # CJK Radicals Supplement
    (0x2F00, 0x2FDF), # Kangxi Radicals
    (0x31C0, 0x31EF), # CJK Strokes
    (0x3400, 0x4DBF), # CJK Unified Ideographs Extension A
    (0x4E00, 0x9FFF), # CJK Unified Ideographs
    (0x20000, 0x2A6DF), # CJK Unified Ideographs Extension B
    (0x2A700, 0x2B73F), # CJK Unified Ideographs Extension C
    (0x2B740, 0x2B81F), # CJK Unified Ideographs Extension D
    (0x2B820, 0x2CEAF), # CJK Unified Ideographs Extension E
    (0x2CEB0, 0x2EBEF), # CJK Unified Ideographs Extension F
    (0x30000, 0x3134F), # CJK Unified Ideographs Extension G
)


def font_cjk_codepoints(font_file):
    with fontTools.ttLib.TTFont(
        font_file, 0, allowVID=0, ignoreDecompileErrors=True, fontNumber=0
    ) as ttf:
        for x in ttf["cmap"].tables:
            for cid, name in x.cmap.items():
                if any(rstart <= cid <= rend for rstart, rend in CJK_RANGES):
                    yield cid


def main(dbname, font_files):
    db = sqlite3.connect(dbname)
    cur = db.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS char_image ("
        "ch TEXT,"
        "font TEXT,"
        "img BLOB,"
        "PRIMARY KEY (ch, font)"
    ")")
    db.commit()
    for font_file in font_files:
        try:
            chars = list(map(chr, font_cjk_codepoints(font_file)))
        except Exception as ex:
            print(ex)
            continue
        chars.sort()
        font = ImageFont.FreeTypeFont(font_file, 18)
        font_name = ' '.join(font.getname())
        print(font_name)
        cur.execute("SELECT 1 FROM char_image WHERE font=?", (font_name,))
        if cur.fetchone():
            continue
        for char in chars:
            im = Image.new('L', (24, 24), color=255)
            draw = ImageDraw.Draw(im)
            draw.multiline_text((12, 12), char, font=font, anchor='mm', fill=0)
            data = np.asarray(im).flatten('C').tobytes()
            cur.execute("REPLACE INTO char_image VALUES (?,?,?)",
                (char, font_name, data))
        db.commit()


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
