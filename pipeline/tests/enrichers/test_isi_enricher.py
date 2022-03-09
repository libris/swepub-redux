from pipeline.validate import FieldMeta
from pipeline.enrichers.isi import recover_isi


def test_correct_isi():
    test_data = "000123456789123"
    _test_none_isi_enrichment(test_data)


def test_correct_isi_with_prefix():
    test_data = "ISI: 000321123456789"
    expected_result = "000321123456789"
    _test_isi_enrichment(test_data, expected_result, ["recovery"])


def test_correct_isi_with_suffix():
    test_data = "A19123456789XYZ checked"
    expected_result = "A19123456789XYZ"
    _test_isi_enrichment(test_data, expected_result, ["recovery"])


def test_correct_isi_with_incorrect_first_sign():
    test_data = ":000321123456789"
    expected_result = "000321123456789"
    _test_isi_enrichment(test_data, expected_result, ["recovery"])


def test_isi_non_recoverable_values_incorrect_prefix_001_instead_of_000():
    test_data = "13978-91-975576-6-5"
    _test_none_isi_enrichment(test_data)


def test_isi_non_recoverable_values_incorrect_prefix_8_instead_of_9():
    test_data = "A18123456789123"
    _test_none_isi_enrichment(test_data)


def test_isi_non_recoverable_values_to_short():
    test_data = "00012345678912"
    _test_none_isi_enrichment(test_data)


def test_isi_non_recoverable_values_to_long():
    test_data = "00012345678912345"
    _test_none_isi_enrichment(test_data)


def test_isi_non_recoverable_values_invalid_characters():
    test_data = "A1912A456!@#$%^"
    _test_none_isi_enrichment(test_data)


def test_isi_non_recoverable_values_incorrect_prefix_000_with_non_numeric_characters():
    test_data = "000A23456789123"
    _test_none_isi_enrichment(test_data)


def _test_isi_enrichment(test_data, expected_result, expected_codes):
    body = {"identifiedBy": [{"value": test_data}]}

    field = FieldMeta(
        value=test_data,
        normalization_status="unchanged",
        validation_status="valid",
        enrichment_status="pending",
        path="identifiedBy.[0].value",
    )

    recover_isi(body, field)

    assert field.value == expected_result
    if len(field.events) > 0:
        assert field.events[0]["type"] == "enrichment"
        for event in field.events:
            assert event["initial_value"] == test_data
            assert event["code"] in expected_codes


def _test_none_isi_enrichment(test_data):
    body = {"identifiedBy": [{"value": test_data}]}

    field = FieldMeta(
        value=test_data,
        normalization_status="unchanged",
        validation_status="valid",
        enrichment_status="pending",
        path="identifiedBy.[0].value",
    )

    recover_isi(body, field)
    assert field.value == test_data
    assert not field.is_enriched()
    assert len(field.events) == 0
