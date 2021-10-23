#!/bin/bash
opencc -c t2s.json | awk 'BEGIN {FS="\t"; OFS="\t"}{seen[$1]+=$2} END {for (i in seen) {print i, seen[i]}}' | sort -k 2nr -k 1 -t $'\t'
