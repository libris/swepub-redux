#!/bin/bash

if [[ -z "${1}" ]]; then
	echo "$(date --utc +%Y-%m-%dT%H:%M:00Z) - ERROR: dump directory not specified"
	exit 1
fi

dump_dir="${1}"
mkdir -p "${dump_dir}"

# Assumes there's a working venv in swepub-redux/venv
# (see README.txt)
cd "${BASH_SOURCE%/*}/.." || (echo "swepub-redux directory not detected" && exit 1)
source venv/bin/activate

for table in duplicated deduplicated; do
	echo "$(date --utc +%Y-%m-%dT%H:%M:00Z) - INFO: Exporting ${table} to ${dump_dir}"
	path_no_suffix="${dump_dir}/swepub-${table}"
	python3 -m pipeline.export "${table}" | zip -q > "${path_no_suffix}.zip-tmp"
	printf "@ -\n@=%s.jsonl\n" "swepub-${table}" | zipnote -w "${path_no_suffix}.zip-tmp"
	sha256sum "${path_no_suffix}.zip-tmp" | awk '{print $1}' > "${path_no_suffix}.zip-tmp.sha256"
	md5sum "${path_no_suffix}.zip-tmp" | awk '{print $1}' > "${path_no_suffix}.zip-tmp.md5"

	mv "${path_no_suffix}.zip-tmp" "${path_no_suffix}.zip"
	mv "${path_no_suffix}.zip-tmp.sha256" "${path_no_suffix}.zip.sha256"
	mv "${path_no_suffix}.zip-tmp.md5" "${path_no_suffix}.zip.md5"
done
