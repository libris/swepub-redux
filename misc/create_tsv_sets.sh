#!/bin/bash

set -eux

if [[ "$#" -lt 5 ]]; then
  echo "Usage: ${0} <language-code> <total> <min-level> <max-level> <output-dir> [suffix]"
  echo "  <language-code>: en or sv"
  echo "  <total>: (maximum) number of records to get. 0 for unlimited."
  echo "  <min-level>: minimum classification level to include (1, 3 or 5)"
  echo "  <max-level>: maxmimum classification level to include (1, 3, or 5)"
  echo "  <output-dir>: directory to write files to (will be created if it doesn't exist)"
  echo "  [suffix]: added before .tsv (optional)" 
  echo ""
  echo "  e.g.:"
  echo "  ${0} en 10000 1 5 /tmp/test foo"
  echo "  => /tmp/test/training_en_foo.tsv"
  echo "     /tmp/test/validation_en_foo.tsv"
  echo "     /tmp/test/testing_en_foo.tsv"
  echo "     /tmp/test/training_and_validation_en_foo.tsv"
  exit 1
fi

LANG=${1}
TOTAL=${2}
MIN_LEVEL=${3}
MAX_LEVEL=${4}
OUTPUT_DIR=${5}
SUFFIX=${6:-""}

if [ -n "${SUFFIX}" ]; then
  SUFFIX="_${SUFFIX}"
fi

mkdir -p "${OUTPUT_DIR}"

TEMP_DIR=$(mktemp -d)

# Write everything to one file
python3 -m misc.export_tsv_annif ${LANG} ${TOTAL} ${MIN_LEVEL} ${MAX_LEVEL} > "${TEMP_DIR}/full_original_${LANG}_${SUFFIX}.tsv"
# Randomize line order
shuf "${TEMP_DIR}/full_original_${LANG}_${SUFFIX}.tsv" > "${TEMP_DIR}/full_shuffled_${LANG}.tsv"
# Split into 10 parts
split -a 1 -d -n l/10 "${TEMP_DIR}/full_shuffled_${LANG}.tsv" "${TEMP_DIR}/tmp_tsv"

# 80% training
cat "${TEMP_DIR}"/tmp_tsv[0-7] > "${TEMP_DIR}/training_${LANG}${SUFFIX}.tsv"
# 10% validation
cat "${TEMP_DIR}"/tmp_tsv8 > "${TEMP_DIR}/validation_${LANG}${SUFFIX}.tsv"
# 10% testing
cat "${TEMP_DIR}"/tmp_tsv9 > "${TEMP_DIR}/testing_${LANG}${SUFFIX}.tsv"
# training+validation
cat "${TEMP_DIR}"/tmp_tsv[0-8] > "${TEMP_DIR}/training_and_validation_${LANG}${SUFFIX}.tsv"

mv "${TEMP_DIR}/training_${LANG}${SUFFIX}.tsv" "${OUTPUT_DIR}"
mv "${TEMP_DIR}/validation_${LANG}${SUFFIX}.tsv" "${OUTPUT_DIR}"
mv "${TEMP_DIR}/testing_${LANG}${SUFFIX}.tsv" "${OUTPUT_DIR}"
mv "${TEMP_DIR}/training_and_validation_${LANG}${SUFFIX}.tsv" "${OUTPUT_DIR}"

rm "${TEMP_DIR}"/tmp_tsv* "${TEMP_DIR}/full_shuffled_${LANG}.tsv" "${TEMP_DIR}/full_original_${LANG}_${SUFFIX}.tsv"
rmdir "${TEMP_DIR}"

wc -l "${OUTPUT_DIR}/training_${LANG}${SUFFIX}.tsv"
wc -l "${OUTPUT_DIR}/validation_${LANG}${SUFFIX}.tsv"
wc -l "${OUTPUT_DIR}/testing_${LANG}${SUFFIX}.tsv"
wc -l "${OUTPUT_DIR}/training_and_validation_${LANG}${SUFFIX}.tsv"
