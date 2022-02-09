from storage import *
from collections import defaultdict


def generate_processing_stats():
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.row_factory = dict_factory
        inner_cursor = connection.cursor()

        for row in cursor.execute("""
            SELECT
                converted_audit_events.step,
                converted.source,
                converted.date,
                SUM(CASE WHEN converted_audit_events.result == 1 Then 1 else 0 end) AS result_true,
                SUM(CASE WHEN converted_audit_events.result == 0 Then 1 else 0 end) AS result_false
            FROM
                converted_audit_events
            LEFT JOIN
                converted ON converted_audit_events.converted_id=converted.id
            GROUP BY
                converted.source, converted_audit_events.step, converted.date
            """):
            if row['step'] == 'creator_count_check':
                valid = row['result_true']
                invalid = row['result_false']
            else:
                valid = row['result_false']
                invalid = row['result_true']

            inner_cursor.execute("""
                INSERT INTO
                    stats_audit_events(source, date, label, valid, invalid)
                VALUES
                    (?, ?, ?, ?, ?)
                """,
                [row['source'], row['date'], row['step'], valid, invalid])

        for row in cursor.execute("""
            SELECT
                converted_record_info.field,
                converted.source,
                converted.date,
                SUM(CASE WHEN converted_record_info.validation_status == 'valid' Then 1 else 0 end) AS v_valid,
                SUM(CASE WHEN converted_record_info.validation_status == 'invalid' Then 1 else 0 end) AS v_invalid,

                SUM(CASE WHEN converted_record_info.enrichment_status == 'enriched' Then 1 else 0 end) AS e_enriched,
                SUM(CASE WHEN converted_record_info.enrichment_status == 'unchanged' Then 1 else 0 end) AS e_unchanged,
                SUM(CASE WHEN converted_record_info.enrichment_status == 'unsuccessful' Then 1 else 0 end) AS e_unsuccessful,

                SUM(CASE WHEN converted_record_info.normalization_status == 'unchanged' Then 1 else 0 end) AS n_unchanged,
                SUM(CASE WHEN converted_record_info.normalization_status == 'normalized' Then 1 else 0 end) AS n_normalized
            FROM
                converted_record_info
            LEFT JOIN
                converted ON converted_record_info.converted_id=converted.id
            GROUP BY
                converted.source, converted_record_info.field, converted.date
            """):
            inner_cursor.execute("""
                INSERT INTO
                    stats_field_events(
                        field, source, date,
                        v_valid, v_invalid,
                        e_enriched, e_unchanged, e_unsuccessful,
                        n_unchanged, n_normalized)
                VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    row['field'], row['source'], row['date'],
                    row['v_valid'], row['v_invalid'],
                    row['e_enriched'], row['e_unchanged'], row['e_unsuccessful'],
                    row['n_unchanged'], row['n_normalized']
                ])

        connection.commit()


if __name__ == "__main__":
    generate_processing_stats()
