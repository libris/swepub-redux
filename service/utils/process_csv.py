from io import StringIO
import csv


def export(hit, flavor="csv", query=None, handled_at=None, total=0):
    delimiter = ","
    if flavor == "tsv":
        delimiter = "\t"
    list_to_string_delim = "\t" if flavor == "tsv" else ";"

    fieldnames = [
        "record_id",
        "source",
        "publication_year",
        "publication_type",
        "output_type",
        "flag_class",
        "flag_type",
        "flag_code",
        "validation_result",
        "value",
        "old_value",
        "new_value",
        "path",
        "mods_url",
        "repository_url",
    ]

    rows = []
    if "validation" in hit["flags"]:
        for flag_type in hit["flags"]["validation"].keys():
            for flag in hit["flags"]["validation"][flag_type]:
                row = _get_basic_row(hit, "validation", flag_type, flag.get("code", ""))
                if "path" in flag:
                    row["path"] = flag["path"]
                if "value" in flag:
                    row["value"] = flag["value"]
                if "result" in flag:
                    row["validation_result"] = flag["result"]
                rows.append(row)
    if "enrichment" in hit["flags"]:
        for flag_type in hit["flags"]["enrichment"].keys():
            for flag in hit["flags"]["enrichment"][flag_type]:
                row = _get_basic_row(hit, "enrichment", flag_type, flag.get("code", ""))
                if "path" in flag:
                    row["path"] = flag["path"]
                if "old_value" in flag:
                    ov = flag["old_value"]
                    if type(ov) == list:
                        row["old_value"] = list_to_string_delim.join([str(item) for item in ov])
                    else:
                        row["old_value"] = ov
                if "new_value" in flag:
                    nv = flag["new_value"]
                    if type(nv) == list:
                        row["new_value"] = list_to_string_delim.join([str(item) for item in nv])
                    else:
                        row["new_value"] = nv
                rows.append(row)
    if "normalization" in hit["flags"]:
        for flag_type in hit["flags"]["normalization"].keys():
            for flag in hit["flags"]["normalization"][flag_type]:
                row = _get_basic_row(
                    hit, "normalization", flag_type, flag.get("code", "")
                )
                if "path" in flag:
                    row["path"] = flag["path"]
                if "old_value" in flag:
                    row["old_value"] = flag["old_value"]
                if "new_value" in flag:
                    row["new_value"] = flag["new_value"]
                rows.append(row)
    if "audit" in hit["flags"]:
        for flag_type, flag in hit["flags"]["audit"].items():
            row = _get_basic_row(hit, "audit", flag_type, "")
            if "result" in flag:
                row["validation_result"] = flag["result"]
            rows.append(row)
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=delimiter)
    if total == 0:
        writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _get_basic_row(hit, flag_class, flag_type, flag_code):
    basic_row = {
        "record_id": hit["record_id"],
        "source": hit["source"],
        "publication_year": hit["publication_year"],
        "publication_type": hit["publication_type"],
        "output_type": hit["output_type"],
        "flag_class": flag_class,
        "flag_type": flag_type,
        "flag_code": flag_code,
        "mods_url": hit["mods_url"],
        "repository_url": hit["repository_url"],
    }
    return basic_row
