Tesseract OCR data trained for Chinese
=========================================

This is another trained tesseract data pack for Chinese OCR,
more accurate than the official ones.

The training fonts includes commonly used fonts for the four font styles:

* Song/Ming (serif)
* Hei (sans-serif)
* Kai
* FangSong

Currently there are data packs for:

* chi_sim: Simplified Chinese (China)
* chi_tra: Traditional Chinese (HK style, TW style, Traditional style)
* chi_all: Combined Simplified and Traditional Chinese (CN, HK, TW, Traditional style)

The LSTM packs also supports Pinyin (chi_sim) and Bopomofo (chi_tra) characters.

# Usage

Download from [Releases](https://github.com/gumblex/tessdata_chi/releases), and replace `*.traineddata` into the tessdata directory of your Tesseract installation.

# Training

Get the fonts in the fontlist.txt, and put them into the `fonts` folder.

```
mkdir train_chi_sim
cd train_chi_sim
python3 ../configure.py chi_sim
make

mkdir train_chi_tra
cd train_chi_tra
python3 ../configure.py chi_tra
make
```

---

Tesseract OCR 中文模型
=========================================

比官方更准确的 Tesseract 中文模型。

训练集包括常用的宋体、黑体、楷体和仿宋，同时训练了英文短句。其中 LSTM 模型支持拼音字母和注音符号。

目前提供以下模型包：

* chi_sim：简体，v3 版传统模型（7000字）和 LSTM 模型（8000字），支持大陆写法字体
* chi_tra：繁体，v3 版传统模型（7000字）和 LSTM 模型（8000字），支持台湾、香港、传承、大陆写法字体
* chi_all：简繁通用，v3 版传统模型（8000字）和 LSTM 模型（10000字），支持大陆、台湾、香港、传承写法字体

字符集覆盖常用标点符号、〇、《通用规范汉字表》以及其他字表最常用的部分（按字频、去除了 Unicode BMP 之外的扩展字符），以及规范字表中没有的其他常用汉字。

# 用法

从 [Releases](https://github.com/gumblex/tessdata_chi/releases) 下载模型包，将 `*.traineddata` 文件替换进 Tesseract 所使用的 tessdata 目录。
