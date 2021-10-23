#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import shutil

lang = 'chi_sim'

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
LANGDATA_DIR = os.path.join(ROOT_DIR, 'langdata')
BASE_DIR = os.path.join(LANGDATA_DIR, lang)
FONTS_DIR = os.path.join(BASE_DIR, 'fonts')

fonts = []

fontlist = os.path.join(BASE_DIR, lang + '.fontlist.txt')

if not os.path.isfile(fontlist):
    print(fontlist + ' not found')
    sys.exit(1)

with open(fontlist, 'r') as f:
    for ln in f:
        name = ln.rstrip()
        fonts.append((name, name.replace(' ', '_')))

for filename in (
    '.fontlist.txt', '.training_text', '.config', '.unicharambigs',
    '.word', '.freq', '.number', '.punc'
):
    shutil.copy2(os.path.join(BASE_DIR, lang + filename), lang + filename)

trs = ' '.join('%s.%s.exp0.tr' % (lang, r[1]) for r in fonts)

with open('Makefile', 'w') as w:
    w.write('TRAIN_LANG=%s\n' % lang)
    w.write('TESSERACT=tesseract\n')
    w.write('TRAINING_BIN=/usr/bin\n')
    w.write('TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata\n')
    w.write('\n\n.PHONY: clean\n\n')
    w.write('all: %s.traineddata\n\n' % (lang,))
    # w.write('all: %s.unicharset %s.normproto\n\n' % ((lang,)*2))
    w.write('%s.traineddata: %s.unicharset %s.normproto %s.punc-dawg %s.word-dawg %s.freq-dawg %s.number-dawg %s.unicharambigs %s.config\n' % ((lang,)*9))
    w.write('\t$(TRAINING_BIN)/combine_tessdata %s.\n\n' % lang)
    for filename in ('.word', '.freq', '.number', '.punc'):
        w.write('%s%s-dawg: %s%s %s.unicharset\n' % (lang, filename, lang, filename, lang))
        w.write('\t$(TRAINING_BIN)/wordlist2dawg %s%s %s%s-dawg %s.unicharset\n\n' % (lang, filename, lang, filename, lang))
    w.write('%s.normproto: ' % lang)
    w.write(' '.join('%s.%s.exp0.tr' % (lang, x[1]) for x in fonts))
    w.write('\n\t$(TRAINING_BIN)/cntraining %s && \\' % trs)
    w.write('\n\tmv normproto %s.normproto' % lang)
    w.write('\n\n%s.unicharset: unicharset font_properties ' % (lang,))
    w.write(' '.join('%s.%s.exp0.tr' % (lang, x[1]) for x in fonts))
    w.write('\n\tenv TMPDIR=/media/ssdata/gumble $(TRAINING_BIN)/mftraining -F font_properties -U unicharset -O %s.unicharset %s && \\' % (lang, trs))
    w.write('\n\tmv shapetable %s.shapetable && \\' % lang)
    w.write('\n\tmv inttemp %s.inttemp && \\' % lang)
    w.write('\n\tmv pffmtable %s.pffmtable' % lang)
    w.write('\n\nunicharset: ')
    w.write(' '.join('%s.%s.exp0.box' % (lang, x[1]) for x in fonts))
    w.write('\n\t$(TRAINING_BIN)/unicharset_extractor *.box && \\')
    w.write('\n\tmv unicharset unicharset_input && \\')
    w.write('\n\t$(TRAINING_BIN)/set_unicharset_properties -U unicharset_input -O unicharset --script_dir=%s && \\' % (LANGDATA_DIR,))
    w.write('\n\trm unicharset_input')
    w.write('\n\n')
    for fontname, fontfile in fonts:
        outputbase = '%s.%s.exp0' % (lang, fontfile)
        w.write('%s.tr: %s.box %s.tif\n' % ((outputbase,)*3))
        w.write('\tenv TESSDATA_PREFIX=$(TESSDATA_PREFIX) $(TESSERACT) "%s.tif" "%s" box.train "%s.config"\n\n' % (outputbase, outputbase, lang))
        w.write('%s%%box %s%%tif: %s.training_text\n' % (outputbase, outputbase, lang))
        w.write('\t$(TRAINING_BIN)/text2image --text=%s$*training_text --outputbase="%s" --font="%s" --fonts_dir=%s --rotate_image=false --strip_unrenderable_words=false\n\n' % (lang, outputbase, fontname, FONTS_DIR))
    w.write('clean:\n\trm -rf *.tr *.tif *.box %s.inttemp %s.pffmtable %s.unicharset %s.shapetable %s.normproto\n' % ((lang,)*5))

re_bold = re.compile(r'Bold|Heavy|W5|W7|W9|W12|Cu|Da|weight')
re_serif = re.compile(r'Song|Ming|Sun|Serif|HanaMin', re.I)

if os.path.isfile('font_properties') and os.stat(fontlist).st_mtime < os.stat('font_properties').st_mtime:
    print('not generating font_properties')
else:
    with open('font_properties', 'w') as w:
        for fontname, fontfile in fonts:
            w.write('%s 0 %s 0 %s 0\n' % (
                fontname,
                '1' if re_bold.search(fontname) else '0',
                '1' if re_serif.search(fontname) and not 'fangsong' in fontname.lower() else '0',
            ))
