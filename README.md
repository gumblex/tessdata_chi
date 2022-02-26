Tesseract OCR data trained for Chinese
=========================================

This is another trained tesseract data pack for Chinese OCR,
more accurate than the official ones.

The training fonts includes commonly used fonts for the four font styles:

* Song/Ming (serif)
* Hei (sans-serif)
* Kai
* FangSong

The packs also supports Pinyin (chi_sim) and Bopomofo (chi_tra) characters.

Currently there are data packs for:

* chi_sim: Simplified Chinese (China)
* chi_tra: Traditional Chinese (HK style, TW style, Traditional style)

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

训练集包括常用的宋体、黑体、楷体和仿宋，同时训练了英文短句，并支持拼音字母和注音符号（仅繁体 LSTM 模型）。

目前提供以下模型包：

* chi_sim：v3 版传统模型和 LSTM 模型，支持大陆写法字体
* chi_tra：v3 版传统模型和 LSTM 模型，支持台湾、香港、传承、大陆写法字体

简繁字符集各支持 8000 多个字、标点符号，覆盖《通用规范汉字表》最常用的部分（去除了 Unicode BMP 之外的扩展字符），以及该表中没有的常用汉字。

# 用法

从 [Releases](https://github.com/gumblex/tessdata_chi/releases) 下载模型包，将 `*.traineddata` 文件替换进 Tesseract 所使用的 tessdata 目录。
