from pipeline.util import FieldMeta
from pipeline.normalize import normalize_issn


def test_without_delimeter():
    test_data = "00249319"
    expected_result = "0024-9319"
    _test_issn(test_data, expected_result, ["format"])


def test_without_delimeter_and_x_suffix():
    test_data = "0024-9319x"
    expected_result = "0024-9319X"
    _test_issn(test_data, expected_result, ["format"])


def test_with_delimeter():
    test_data = "0024-9319"
    expected_result = "0024-9319"
    _test_issn(test_data, expected_result, [])


def test_with_delimeterand_x_suffix():
    test_data = "0024-9319x"
    expected_result = "0024-9319X"
    _test_issn(test_data, expected_result, ["format"])


def _test_issn(test_data, expected_result, expected_codes):
    body = {"partOf": [{"identifiedBy": [{"value": test_data}]}]}

    field = FieldMeta(
        value=test_data,
        normalization_status="unchanged",
        validation_status="valid",
        path="partOf.[0].identifiedBy.[0].value",
    )

    normalize_issn(body, field)
    assert field.value == expected_result
    if len(field.events) > 0:
        assert field.events[0]["type"] == "normalization"
        for event in field.events:
            assert event["code"] in expected_codes
