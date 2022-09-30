#!/bin/bash

set -e

if [ -z ${5} ]; then
  echo "Specify language code (en or sv), number of records, min and max level (1, 3, 5) and filename suffix (e.g. abstracts)"
  exit
fi

LANG=${1}
TOTAL=${2}
MIN_LEVEL=${3}
MAX_LEVEL=${4}
SUFFIX=${5}

python3 -m misc.export_tsv_short ${LANG} ${TOTAL} ${MIN_LEVEL} ${MAX_LEVEL} > full_original_${LANG}_${SUFFIX}.tsv
shuf full_original_${LANG}_${SUFFIX}.tsv > full_shuffled_${LANG}.tsv
split -a 1 -d -n l/10 full_shuffled_${LANG}.tsv tmp_tsv

cat tmp_tsv[0-7] > training_${LANG}_${SUFFIX}.tsv
cat tmp_tsv[0-8] > training_and_validation_${LANG}_${SUFFIX}.tsv
cat tmp_tsv8 > validation_${LANG}_${SUFFIX}.tsv
cat tmp_tsv9 > testing_${LANG}_${SUFFIX}.tsv

wc -l training_${LANG}_${SUFFIX}.tsv
wc -l validation_${LANG}_${SUFFIX}.tsv
wc -l testing_${LANG}_${SUFFIX}.tsv

rm tmp_tsv* full_shuffled_${LANG}.tsv
