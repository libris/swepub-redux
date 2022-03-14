from pipeline.util import FieldMeta
from pipeline.enrichers.orcid import recover_orcid


def test_orcid_with_prefix_without_delimitet():
    test_data = "ORCID: 0000000216426281"
    expected_result = "0000000216426281"
    _test_orcid_enrichment(test_data, expected_result, ["recovery"])


def test_orcid_with_mssing_http_prefix():
    test_data = "orcid.org/0000-0001-9348-7505"
    expected_result = "0000-0001-9348-7505"
    _test_orcid_enrichment(test_data, expected_result, ["recovery"])


def test_orcid_with_username_as_prefix():
    test_data = "maroh70 0000-0001-9896-4438"
    expected_result = "0000-0001-9896-4438"
    _test_orcid_enrichment(test_data, expected_result, ["recovery"])


def test_orcid_with_bad_prefix():
    test_data = ": 0000-0001-7379-9704"
    expected_result = "0000-0001-7379-9704"
    _test_orcid_enrichment(test_data, expected_result, ["recovery"])


def test_orcid_with_sufix():
    test_data = "0000-0002-2970-5085#sthash.cyjiIYe3.dpuf"
    expected_result = "0000-0002-2970-5085"
    _test_orcid_enrichment(test_data, expected_result, ["recovery"])


def test_orcid_with_faulty_first_char():
    test_data = "/0000-0002-6843-4038"
    expected_result = "0000-0002-6843-4038"
    _test_orcid_enrichment(test_data, expected_result, ["recovery"])


def test_orcid_with_3_digits_in_first_section():
    test_data = "000-0002-8911-4068"
    expected_result = "0000-0002-8911-4068"
    _test_orcid_enrichment(test_data, expected_result, ["extend"])


def test_orcid_with_3_digits_in_first_section_and_x_as_suffix():
    test_data = "000-0002-1642-628X"
    expected_result = "0000-0002-1642-628X"
    _test_orcid_enrichment(test_data, expected_result, ["extend"])


def test_correct_orcid():
    test_data = "0000-0002-1642-6281"
    _test_none_orcid_enrichment(test_data)


def test_orcid_with_missing_delimiter():
    test_data = "0000-0002-07486571"
    _test_none_orcid_enrichment(test_data)


def test_correct_orcid_without_delimiter_and_with_capital_x():
    test_data = "000000021642628X"
    _test_none_orcid_enrichment(test_data)


def test_orcid_non_recoverable_values_faulty_delimiters():
    test_data = "0000 000238483314"
    _test_none_orcid_enrichment(test_data)


def test_orcid_non_recoverable_values_one_digit_too_many_second_section():
    test_data = "0000-00003-2007-3736"
    _test_none_orcid_enrichment(test_data)


def test_orcid_non_recoverable_values_invalid_char():
    test_data = "0000-00A2-1642-6281"
    _test_none_orcid_enrichment(test_data)


def test_orcid_non_recoverable_values_too_short():
    test_data = "25936794100"
    _test_none_orcid_enrichment(test_data)


def _test_orcid_enrichment(test_data, expected_result, expected_codes):
    body = {
        "instanceOf": {
            "contribution": [
                {"agent": {"identifiedBy": [{"@type": "ORCID", "value": test_data}]}}
            ]
        }
    }

    field = FieldMeta(
        value=test_data,
        validation_status="valid",
        enrichment_status="pending",
        path="instanceOf.contribution.[0].agent.identifiedBy.[0].value",
    )

    recover_orcid(body, field)

    assert field.value == expected_result
    if len(field.events) > 0:
        assert field.events[0]["type"] == "enrichment"
        for event in field.events:
            assert event["initial_value"] == test_data
            assert event["code"] in expected_codes
            test_data = event["value"]


def _test_none_orcid_enrichment(test_data):
    body = {
        "instanceOf": {
            "contribution": [
                {"agent": {"identifiedBy": [{"@type": "ORCID", "value": test_data}]}}
            ]
        }
    }

    field = FieldMeta(
        value=test_data,
        validation_status="valid",
        enrichment_status="pending",
        path="instanceOf.contribution.[0].agent.identifiedBy.[0].value",
    )

    recover_orcid(body, field)

    assert field.value == test_data
    assert not field.is_enriched()
    assert len(field.events) == 0
