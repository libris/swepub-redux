#!/bin/bash

set -e

if [ -z ${3} ]; then
  echo "Specify language code (en or sv), number of records and max level (1, 3, 5)"
  exit
fi

LANG=${1}
TOTAL=${2}
MAX_LEVEL=${3}

python3 -m misc.export_tsv_short ${LANG} ${TOTAL} ${MAX_LEVEL} > full_original.tsv
shuf full_original.tsv > full.tsv
split -a 1 -d -n l/10 full.tsv tmp_tsv

cat tmp_tsv[0-7] > training_${LANG}.tsv
cat tmp_tsv8 > validation_${LANG}.tsv
cat tmp_tsv9 > testing_${LANG}.tsv

wc -l training_${LANG}.tsv
wc -l validation_${LANG}.tsv
wc -l testing_${LANG}.tsv

rm tmp_tsv* full.tsv
