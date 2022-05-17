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

#############################################################################
# Yearly export from 2012
#############################################################################
cur_year=$(date +"%Y")

echo "$(date --utc +%Y-%m-%dT%H:%M:00Z) - INFO: Exporting yearly dumps to ${dump_dir}"

for year in $(seq 2012 "${cur_year}"); do
	echo "$(date --utc +%Y-%m-%dT%H:%M:00Z) - INFO: Preparing export for ${year}"
	for table in duplicated deduplicated; do
		path_no_suffix="${dump_dir}/yearly_${year}-swepub-${table}"
		python3 -m pipeline.export --year "${year}" "${table}" | zip -q > "${path_no_suffix}.zip"
		printf "@ -\n@=%s.jsonl\n" "yearly_${year}-swepub-${table}" | zipnote -w "${path_no_suffix}.zip"
		sha256sum "${path_no_suffix}.zip" | awk '{print $1}' > "${path_no_suffix}.zip.sha256"
		md5sum "${path_no_suffix}.zip" | awk '{print $1}' > "${path_no_suffix}.zip.md5" 
	done
done
