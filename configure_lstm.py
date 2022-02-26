#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import base64
import shutil
import random
import hashlib
import tempfile
import itertools
import subprocess
import contextlib
import multiprocessing

random.seed(12345)

CHARMAP_V = str.maketrans(
    '()-—‘’“”…〈〉《》「」『』【】〔〕（）｛｝',
    '︵︶｜｜﹃﹄﹁﹂︙︿﹀︽︾﹁﹂﹃﹄︻︼︹︺︵︶︷︸'
)

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
LANGDATA_DIR = os.path.join(ROOT_DIR, 'langdata')
FONTS_DIR = os.path.join(ROOT_DIR, 'fonts')
TMP_DIR = '/dev/shm'

TRAINING_BIN = os.path.dirname(shutil.which('tesseract'))
TESSDATA_PREFIX = os.environ.get(
    'TESSDATA_PREFIX', '/usr/share/tesseract-ocr/4.00/tessdata')

re_bold = re.compile(r'Bold|Heavy|W5|W7|W9|W12|Cu|Da|weight')
re_serif = re.compile(r'Song|Ming|Sun|Serif|HanaMin', re.I)
re_light = re.compile(r'Light|BaoSong', re.I)


def grouper_it(n, iterable):
    it = iter(iterable)
    while True:
        chunk_it = itertools.islice(it, n)
        try:
            first_el = next(chunk_it)
        except StopIteration:
            return
        yield itertools.chain((first_el,), chunk_it)


def check_mtime(src, dst):
    if not os.path.isfile(dst):
        return True
    return (os.stat(dst).st_mtime < os.stat(src).st_mtime)


def font_to_filename(x):
    return x.replace(' ', '_')


def generate_txt_from_box(filename_base):
    with open(filename_base + '.box', 'r', encoding='utf-8') as f:
        line = []
        for ln in f:
            ln = ln.rstrip()
            if not ln:
                continue
            ch = ln.split(' ')[0]
            if ch:
                line.append(ch)
            else:
                line.append(' ')
    with open(filename_base + '.txt', 'w', encoding='utf-8') as f:
        f.write(''.join(line))


def generate_line_img(path, font, line, vertical=False):
    line_hash = base64.b32encode(hashlib.blake2b(
        line.encode('utf-8'), digest_size=20).digest()).decode('ascii')
    font_dir = os.path.join(path, font_to_filename(font))
    if not os.path.isdir(font_dir):
        os.makedirs(font_dir, exist_ok=True)
    filename_base = os.path.join(font_dir, line_hash)
    if all(os.path.isfile(filename_base + ext) and
           os.stat(filename_base + ext).st_size > 0
           for ext in ('.txt', '.tif', '.box', '.lstmf')):
        return filename_base
    for ext in ('.txt', '.tif', '.box', '.lstmf'):
        with contextlib.suppress(FileNotFoundError):
            os.remove(filename_base + ext)
    with open(filename_base + '.txt', 'w', encoding='utf-8') as f:
        f.write(line)
    with tempfile.TemporaryDirectory(prefix='t2ifc_', dir=TMP_DIR) as tmpdir:
        if vertical:
            writing_mode = 'vertical'
            ysize = 3600
            xsize = 200
        else:
            writing_mode = 'horizontal'
            xsize = 3600
            ysize = 200
        exposure_level = 0
        if re_bold.search(font):
            exposure_level = -1
        elif re_serif.search(font):
            # make serif bolder
            exposure_level = 1
        if random.random() < 0.3:
            dpi = random.choice((200, 250))
        else:
            dpi = 300
            if exposure_level == 0:
                exposure_level = -1
        exposure = random.choice((exposure_level, 0, 0))
        for i in range(3):
            for ext in ('.tif', '.box', '.lstmf'):
                with contextlib.suppress(FileNotFoundError):
                    os.remove(filename_base + ext)
            try:
                subprocess.run((
                    os.path.join(TRAINING_BIN, 'text2image'),
                    '--text=%s.txt' % filename_base,
                    '--outputbase=%s' % filename_base,
                    '--font=%s' % font,
                    '--fonts_dir=%s' % FONTS_DIR,
                    '--fontconfig_tmpdir=%s' % tmpdir,
                    '--writing_mode=' + writing_mode,
                    '--exposure=%s' % exposure, '--resolution=%d' % dpi,
                    '--margin=50', '--xsize=%d' % xsize, '--ysize=%d' % ysize,
                    '--rotate_image=false', '--strip_unrenderable_words=false'
                ), capture_output=True, check=True)
                if not os.path.isfile(filename_base + '.tif'):
                    continue
                subprocess.run((
                    os.path.join(TRAINING_BIN, 'tesseract'),
                    '%s.tif' % filename_base, filename_base,
                    '--psm', '13', 'lstm.train'
                ), capture_output=True, check=True)
            except subprocess.CalledProcessError as ex:
                print('Command returned %s: %s' % (ex.returncode, ' '.join(ex.cmd)))
                print(ex.stdout.decode('utf-8', errors='replace'))
                print(ex.stderr.decode('utf-8', errors='replace'))
            try:
                generate_txt_from_box(filename_base)
                if all(os.path.isfile(filename_base + ext) and
                       os.stat(filename_base + ext).st_size > 0
                       for ext in ('.txt', '.tif', '.box', '.lstmf')):
                    break
            except (FileNotFoundError, UnicodeError):
                print('Box decode error: %s.box' % filename_base)
        else:
            return None
    return filename_base


def generate_imgs(path, fonts, lines, vertical):
    print('Generating images in %s...' % path)
    # shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)
    filenames = []
    total = len(fonts) * len(lines)
    with multiprocessing.Pool(round(os.cpu_count() * 0.5)) as pool:
        for chunk in grouper_it(250, itertools.product(lines, fonts)):
            futures = [
                pool.apply_async(generate_line_img, (path, font, line, vertical))
                for line, font in chunk
            ]
            for future in futures:
                result = future.get()
                if result:
                    filenames.append(result + '.lstmf')
                if len(filenames) % 500 == 0:
                    print(' %d/%d' % (len(filenames), total))
    print('Generated %s images.' % len(filenames))
    return filenames


def main(lang, start_model, v3_model=None):
    fonts = []
    vertical = lang.endswith('_vert')

    BASE_DIR = os.path.join(LANGDATA_DIR, lang)
    fontlist = os.path.join(BASE_DIR, lang + '.fontlist_lstm.txt')

    if not os.path.isfile(fontlist):
        print(fontlist + ' not found')
        sys.exit(1)

    with open(fontlist, 'r') as f:
        for ln in f:
            name = ln.rstrip()
            fonts.append(name)

    for filename in (
        '.fontlist_lstm.txt', '.config', '.unicharambigs',
        '.word', '.freq', '.number', '.punc'
    ):
        shutil.copy2(os.path.join(BASE_DIR, lang + filename), lang + filename)

    if check_mtime(start_model, 'start_%s.traineddata' % lang):
        shutil.copy2(start_model, 'start_%s.traineddata' % lang)
        shutil.rmtree('start_model', ignore_errors=True)
        os.makedirs('start_model', exist_ok=True)
        subprocess.run((
            os.path.join(TRAINING_BIN, 'combine_tessdata'), '-u',
            start_model, 'start_model/%s' % lang
        ), check=True)
        if not os.path.isfile('start_model/%s.lstm-unicharset' % lang):
            shutil.copy2(
                'start_model/%s.unicharset' % lang,
                'start_model/%s.lstm-unicharset' % lang
            )

    if v3_model and check_mtime(v3_model, 'v3_%s.traineddata' % lang):
        shutil.copy2(v3_model, 'v3_%s.traineddata' % lang)
        shutil.rmtree('v3_model', ignore_errors=True)
        os.makedirs('v3_model', exist_ok=True)
        subprocess.run((
            os.path.join(TRAINING_BIN, 'combine_tessdata'), '-u',
            v3_model, 'v3_model/%s' % lang
        ), check=True)

    if (check_mtime(os.path.join(BASE_DIR, lang + '.lstm_train.txt'),
        lang + '.lstmf_train.list') or
        check_mtime(os.path.join(BASE_DIR, lang + '.lstm_test.txt'),
        lang + '.lstmf_test.list')):
        texts = [[], []]
        with open(os.path.join(BASE_DIR, lang + '.lstm_train.txt'), 'r') as f:
            texts[0] = [ln.strip() for ln in f.readlines()]
        with open(os.path.join(BASE_DIR, lang + '.lstm_test.txt'), 'r') as f:
            texts[1] = [ln.strip() for ln in f.readlines()]

        # if vertical:
            # for i in range(2):
                # for j in range(len(texts[i])):
                    # texts[i][j] = texts[i][j].translate(CHARMAP_V)

        random.shuffle(texts[0])
        random.shuffle(texts[1])

        for i, name in enumerate(('train', 'test')):
            with open('%s.lstmf_%s.list' % (lang, name), 'w', encoding='utf-8') as f:
                lstmf = generate_imgs('img_' + name, fonts, texts[i], vertical)
                random.shuffle(lstmf)
                for ln in lstmf:
                    f.write(ln)
                    f.write('\n')
            # with open('%s.lstm_%s.txt' % (lang, name), 'w', encoding='utf-8') as f:
                # for ln in texts[i]:
                    # f.write(ln)
                    # f.write('\n')
        with contextlib.suppress(FileNotFoundError):
            os.remove(lang + '.fake.box')

    if not os.path.isfile(lang + '.fake.box'):
        with open(lang + '.fake.box', 'w', encoding='utf-8') as f:
            line_num = 0
            for i in range(2):
                for ln in texts[i]:
                    for j, ch in enumerate(ln):
                        f.write('%s %d 100 %d 150 %d' % (
                            ch, 100+j*50, 150+j*50, line_num))
                        f.write('\n')
                    line_num += 1

    if check_mtime(fontlist, 'font_properties'):
        with open('font_properties', 'w') as w:
            for fontname in fonts:
                w.write('%s 0 %s 0 %s 0\n' % (
                    fontname,
                    '1' if re_bold.search(fontname) else '0',
                    '1' if re_serif.search(fontname) else '0',
                ))
    else:
        print('not generating font_properties')

    with open('Makefile', 'w') as w:
        w.write(f'TRAIN_LANG={lang}\n')
        w.write(f'TRAINING_BIN={TRAINING_BIN}\n')
        w.write('TESSERACT=$(TRAINING_BIN)/tesseract\n')
        w.write(f'TESSDATA_PREFIX={TESSDATA_PREFIX}\n')
        w.write(f'LANGDATA_DIR={LANGDATA_DIR}\n')
        w.write('\nDEBUG_INTERVAL:=0\n')
        w.write('LEARNING_RATE:=0.0005\n')
        w.write('MAX_ITERATIONS:=5000000\n')
        w.write('TARGET_ERROR_RATE:=0.01\n')
        w.write(f'\nLAST_CHECKPOINT=checkpoints/{lang}_checkpoint\n')
        w.write(f'PROTO_MODEL=proto_model/{lang}.traineddata\n')
        w.write('\n\n.PHONY: clean\n\n')
        w.write('\n\n.PRECIOUS: $(LAST_CHECKPOINT)\n\n')
        w.write(f'all: {lang}.traineddata\n\n')
        w.write(f'traineddata: {lang}.traineddata\n\n')

        # deps = f'{lang}.unicharset {lang}.punc-dawg {lang}.word-dawg {lang}.freq-dawg {lang}.number-dawg {lang}.unicharambigs {lang}.config'
        # if v3_model:
            # deps += f' {lang}.normproto'
        # w.write(f'{lang}.traineddata: {deps}\n')
        # w.write(f'\t$(TRAINING_BIN)/combine_tessdata {lang}.\n\n')
        # for filename in ('.word', '.freq', '.number', '.punc'):
            # w.write('%s%s-dawg: %s%s %s.unicharset\n' % (lang, filename, lang, filename, lang))
            # w.write('\t$(TRAINING_BIN)/wordlist2dawg %s%s %s%s-dawg %s.unicharset\n\n' % (lang, filename, lang, filename, lang))
        if v3_model:
            w.write(f'{lang}.normproto: v3_model/{lang}.normproto\n')
            w.write(f'\tcp v3_model/{lang}.normproto {lang}.normproto\n\n')

        # deps = f'start_model/{lang}.lstm-unicharset'
        deps = ''
        if v3_model:
            deps += f' v3_model/{lang}.unicharset'
        w.write(f'\n\nunicharset: {lang}.fake.box{deps}\n')
        w.write(f'\t$(TRAINING_BIN)/unicharset_extractor --output_unicharset 1.unicharset --norm_mode 2 {lang}.fake.box && \\\n')
        w.write('\t$(TRAINING_BIN)/set_unicharset_properties -U 1.unicharset -O 2.unicharset --script_dir=$(LANGDATA_DIR) && \\\n')
        w.write(f'\t$(TRAINING_BIN)/merge_unicharsets 2.unicharset {deps} 3.unicharset && \\\n')
        w.write("""\tenv LC_ALL=C awk 'NR<5{print $$0; next}{print $$0| "sort -k 1"}' < 3.unicharset > unicharset && \\\n""")
        w.write('\trm 1.unicharset 2.unicharset 3.unicharset\n\n')

        w.write(f'$(PROTO_MODEL): unicharset start_{lang}.traineddata $(LANGDATA_DIR)/radical-stroke.txt\n')
        w.write(f"""\tif false; then \\\n""")
        w.write(f'\t\tmkdir -p proto_model && cp start_{lang}.traineddata $(PROTO_MODEL); \\\n')
        w.write('\telse \\\n')
        w.write(f'\t\t$(TRAINING_BIN)/combine_lang_model --input_unicharset unicharset --script_dir $(LANGDATA_DIR) --numbers {lang}.number --puncs {lang}.punc --words {lang}.word --output_dir . --lang {lang} && \\\n')
        w.write(f'\t\trm -rf proto_model && mv {lang} proto_model; \\\n')
        w.write('\tfi\n\n')

        w.write(f'start_training: $(PROTO_MODEL) start_model/{lang}.lstm {lang}.lstmf_train.list {lang}.lstmf_test.list\n')
        w.write('\t@mkdir -p checkpoints\n')
        w.write(f'\t$(TRAINING_BIN)/lstmtraining --debug_interval $(DEBUG_INTERVAL) --traineddata $(PROTO_MODEL) --old_traineddata start_{lang}.traineddata --continue_from start_model/{lang}.lstm --learning_rate $(LEARNING_RATE) --model_output checkpoints/{lang} --train_listfile {lang}.lstmf_train.list --eval_listfile {lang}.lstmf_test.list --max_iterations $(MAX_ITERATIONS) --target_error_rate $(TARGET_ERROR_RATE) 2>&1 | tee lstmtraining.log\n\n')
        w.write(f'continue: $(PROTO_MODEL) $(LAST_CHECKPOINT) {lang}.lstmf_train.list {lang}.lstmf_test.list\n')
        w.write(f'\t$(TRAINING_BIN)/lstmtraining --debug_interval $(DEBUG_INTERVAL) --traineddata $(PROTO_MODEL) --old_traineddata start_{lang}.traineddata --continue_from $(LAST_CHECKPOINT) --learning_rate $(LEARNING_RATE) --model_output checkpoints/{lang} --train_listfile {lang}.lstmf_train.list --eval_listfile {lang}.lstmf_test.list --max_iterations $(MAX_ITERATIONS) --target_error_rate $(TARGET_ERROR_RATE) 2>&1 | tee -a lstmtraining.log\n\n')
        w.write(f'{lang}.traineddata: $(LAST_CHECKPOINT) $(PROTO_MODEL)\n')
        w.write(f'\tfor i in checkpoints/{lang}_?.*checkpoint; do $(TRAINING_BIN)/lstmtraining --stop_training --continue_from "$$i" --traineddata $(PROTO_MODEL) --model_output $@; break; done\n\n')
        w.write('clean:\n\trm -rf unicharset *.traineddata proto_model/\n')


if __name__ == '__main__':
    main(*sys.argv[1:])
