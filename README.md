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

This data pack uses the old Tesseract 3 model (--oem 0).
The LSTM model is currently broken on PDF output, so the old model is preferred.

# Usage

Replace `tessdata/*.traineddata` into the tessdata directory of your Tesseract installation.

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
