from pipeline.storage import *
from pipeline.util import Validation, Enrichment, Normalization

def generate_processing_stats():
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.row_factory = dict_factory
        inner_cursor = connection.cursor()

        # Add stats about records in converted ("duplicated"), per source and year
        for row in cursor.execute("""
            SELECT
                source, date, count(distinct id) AS total, sum(is_open_access) AS open_access, sum(classification_level) AS swedishlist, sum(has_ssif_1) AS ssif_1
            FROM
                converted
            WHERE
                converted.deleted = 0
            GROUP BY
                source, date
            """):
            inner_cursor.execute("""
                INSERT INTO
                    stats_converted(source, date, total, open_access, swedishlist, has_ssif_1)
                VALUES
                    (?, ?, ?, ?, ?, ?)
                """,
                [row["source"], row["date"], row["total"], row["open_access"], row["swedishlist"], row["ssif_1"]])

        # In the stats above we count how many records have SSIF classification at all; here below we count
        # the number of records  _per SSIF category_ and source and year.
        for row in cursor.execute("""
            SELECT
                converted.source, converted.date, converted_ssif_1.value, count(*) AS total
            FROM
                converted
            LEFT JOIN
                converted_ssif_1 ON converted_ssif_1.converted_id=converted.id
            WHERE
                converted_ssif_1.value NOT NULL AND converted.deleted = 0
            GROUP BY
                converted.source, converted.date, converted_ssif_1.value
            """):
            inner_cursor.execute("""
                INSERT INTO
                    stats_ssif_1(source, date, ssif_1, total)
                VALUES
                    (?, ?, ?, ?)
                """,
                [row["source"], row["date"], row["value"], row["total"]])

        # Auditor stats. Note that a couple of auditors, for historical reasons (though we should
        # fix this at some point) should actually go into the _enricher_ category for API/stats purposes.
        for row in cursor.execute("""
            SELECT
                converted_record_info.audit_code,
                converted.source,
                converted.date,
                SUM(CASE WHEN converted_record_info.audit_result == 1 Then 1 else 0 end) AS result_true,
                SUM(CASE WHEN converted_record_info.audit_result == 0 Then 1 else 0 end) AS result_false
            FROM
                converted_record_info
            LEFT JOIN
                converted ON converted_record_info.converted_id=converted.id
            WHERE
                converted.deleted = 0
            AND
                converted_record_info.field_name IS NULL
            GROUP BY
                converted.source, converted_record_info.audit_code, converted.date
            """):
            if row['audit_code'] == 'creator_count_check':
                valid = row['result_true']
                invalid = row['result_false']
            elif row['audit_code'] == 'auto_classify':
                valid = row['result_true']
                invalid = 0
            else:
                valid = row['result_false']
                invalid = row['result_true']

            inner_cursor.execute("""
                INSERT INTO
                    stats_audit_events(source, date, label, valid, invalid)
                VALUES
                    (?, ?, ?, ?, ?)
                """,
                [row['source'], row['date'], row['audit_code'], valid, invalid])

        for row in cursor.execute(f"""
            SELECT
                converted_record_info.field_name,
                converted.source,
                converted.date,
                SUM(CASE WHEN converted_record_info.validation_status == {Validation.VALID} Then 1 else 0 end) AS v_valid,
                SUM(CASE WHEN converted_record_info.validation_status == {Validation.INVALID}  Then 1 else 0 end) AS v_invalid,

                SUM(CASE WHEN converted_record_info.enrichment_status == {Enrichment.ENRICHED} Then 1 else 0 end) AS e_enriched,
                SUM(CASE WHEN converted_record_info.enrichment_status == {Enrichment.UNCHANGED}  Then 1 else 0 end) AS e_unchanged,
                SUM(CASE WHEN converted_record_info.enrichment_status == {Enrichment.UNSUCCESSFUL}  Then 1 else 0 end) AS e_unsuccessful,

                SUM(CASE WHEN converted_record_info.normalization_status == {Normalization.UNCHANGED} Then 1 else 0 end) AS n_unchanged,
                SUM(CASE WHEN converted_record_info.normalization_status == {Normalization.NORMALIZED} Then 1 else 0 end) AS n_normalized
            FROM
                converted_record_info
            LEFT JOIN
                converted ON converted_record_info.converted_id=converted.id
            WHERE
                converted.deleted = 0
            AND
                converted_record_info.audit_code IS NULL
            GROUP BY
                converted.source, converted_record_info.field_name, converted.date
        """):
            inner_cursor.execute("""
                INSERT INTO
                    stats_field_events(
                        field_name, source, date,
                        v_valid, v_invalid,
                        e_enriched, e_unchanged, e_unsuccessful,
                        n_unchanged, n_normalized)
                VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    row['field_name'], row['source'], row['date'],
                    row['v_valid'], row['v_invalid'],
                    row['e_enriched'], row['e_unchanged'], row['e_unsuccessful'],
                    row['n_unchanged'], row['n_normalized']
                ])

        connection.commit()


if __name__ == "__main__":
    generate_processing_stats()
