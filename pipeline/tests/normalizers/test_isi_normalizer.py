from pipeline.util import FieldMeta
from pipeline.normalize import normalize_isi


def test_with_lower_case_letters():
    test_data = "a19ABCDEFGHIJ12"
    expected_result = "A19ABCDEFGHIJ12"
    _test_isi(test_data, expected_result, ["capitalize"])


def test_without_lower_case_letters():
    test_data = "A19ABCDEFGHIJ12"
    expected_result = "A19ABCDEFGHIJ12"
    _test_isi(test_data, expected_result, [])


def _test_isi(test_data, expected_result, expected_codes):
    body = {"identifiedBy": [{"value": test_data}]}

    field = FieldMeta(
        value=test_data,
        normalization_status="unchanged",
        validation_status="valid",
        path="identifiedBy.[0].value",
    )

    normalize_isi(body, field)
    assert field.value == expected_result
    if len(field.events) > 0:
        assert field.events[0]["type"] == "normalization"
        for event in field.events:
            assert event["code"] in expected_codes
