Tesseract OCR data trained for Chinese
=========================================

This is another trained tesseract data pack for Chinese OCR,
more accurate than the official ones.

This data pack uses the old Tesseract 3 model (--oem 0).
The LSTM model is currently broken on PDF output, so the old model is preferred.

# Usage

Replace `tessdata/*.traineddata` into the tessdata directory of your Tesseract installation.

# Training

Get the fonts in the fontlist.txt, and put them into the `fonts` folder.

```
mkdir train
cd train
python3 ../configure.py
make
```
