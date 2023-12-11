from pipeline.util import FieldMeta, Enrichment
from pipeline.enrichers.issn import recover_issn
from pipeline.enrichers.isbn import recover_isbn


def test_issn_with_prefix():
    test_data = "ISSN: 2148-130X"
    expected_result = "2148-130X"
    _test_issn_enrichment(recover_issn, test_data, expected_result, ["recovery"])


def test_issn_with_trailing_chars():
    test_data = "0081-9816f"
    expected_result = "0081-9816"
    _test_issn_enrichment(recover_issn, test_data, expected_result, ["recovery"])


def test_issn_with_whitespace_before_check():
    test_data = "0281-014 X"
    expected_result = "0281-014X"
    _test_issn_enrichment(recover_issn, test_data, expected_result, ["recovery"])


def test_issn_with_weird_signs():
    test_data = "2045â€“4902"
    expected_result = "20454902"
    _test_issn_enrichment(recover_issn, test_data, expected_result, ["unicode", "recovery"])


def test_issn_with_trailing_code():
    test_data = "0044-0477:134"
    expected_result = "0044-0477"
    _test_issn_enrichment(recover_issn, test_data, expected_result, ["recovery"])


def test_issn_with_text_prefix_and_no_whitespace():
    test_data = "Test12345678"
    expected_result = "12345678"
    _test_issn_enrichment(recover_issn, test_data, expected_result, ["recovery"])


def test_issn_with_multiple_delimiter_signs_and_unicode():
    test_data = "0255 – 0644"
    expected_result = "02550644"
    _test_issn_enrichment(recover_issn, test_data, expected_result, ["unicode", "recovery"])


def test_non_recoverable_issn_from_isbn():
    test_data = "978-1-57146-285-5"
    _test_none_issn_enrichment(recover_isbn, test_data)


def test_non_recoverable_with_to_many_numbers():
    test_data = "00255-0644"
    _test_none_issn_enrichment(recover_isbn, test_data)


def test_non_recoverable_with_invalid_check_number():
    test_data = "1234567y"
    _test_none_issn_enrichment(recover_isbn, test_data)


def test_non_recoverable_with_too_many_signs_before_control_number():
    test_data = "1234  567  8"
    _test_none_issn_enrichment(recover_isbn, test_data)


def test_non_recoverable_issn_from_isbn10_with_delimiters():
    test_data = "99-0562125-5"
    _test_none_issn_enrichment(recover_isbn, test_data)


def test_non_recoverable_issn_from_isbn10_with_withespace():
    test_data = "91 3456 789 X"
    _test_none_issn_enrichment(recover_isbn, test_data)


def test_non_recoverable_issn_from_isbn10_with_delimiter_and_withespace():
    test_data = "1234-4562 44"
    _test_none_issn_enrichment(recover_isbn, test_data)


def test_dual_issn():
    test_data = '0256-4718 (Print), 1753-5387 (Online)'

    body = {"isPartOf": [{"identifiedBy": [{"value": test_data}]}]}

    field = FieldMeta(
        value=test_data,
        path="isPartOf.[0].identifiedBy.[0].value",
    )

    created_fields = recover_issn(body, field)

    assert field.value == "0256-4718"
    assert field.enrichment_status == Enrichment.ENRICHED

    assert len(created_fields) == 1
    assert field.events[1]["code"] == "split"
    assert created_fields[0].value == "1753-5387"


def _test_issn_enrichment(enricher, test_data, expected_result, expected_codes):
    body = {"isPartOf": [{"identifiedBy": [{"value": test_data}]}]}

    field = FieldMeta(
        value=test_data,
        path="isPartOf.[0].identifiedBy.[0].value",
    )

    enricher(body, field)

    assert field.value == expected_result
    if len(field.events) > 0:
        assert field.events[0]["type"] == "enrichment"
        for event in field.events:
            assert event["initial_value"] == test_data
            assert event["code"] in expected_codes
            test_data = event["value"]


def _test_none_issn_enrichment(enricher, test_data):
    body = {"isPartOf": [{"identifiedBy": [{"value": test_data}]}]}

    field = FieldMeta(
        value=test_data,
        path="isPartOf.[0].identifiedBy.[0].value",
    )

    enricher(body, field)

    assert field.value == test_data
    assert not field.is_enriched()
    assert len(field.events) == 0
