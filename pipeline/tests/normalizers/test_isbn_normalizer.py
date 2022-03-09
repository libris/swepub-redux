from pipeline.validate import FieldMeta
from pipeline.normalize import normalize_isbn


def test_with_lower_case():
    test_data = "97802620360472x"
    expected_result = "97802620360472X"
    _test_isbn_normalizaion(test_data, expected_result, ["format"])


def test_without_lower_case():
    test_data = "97802620360472"
    expected_result = "97802620360472"
    _test_isbn_normalizaion(test_data, expected_result, [])


def test_with_delimeters():
    test_data = "0-1234-5678-9"
    expected_result = "0123456789"
    _test_isbn_normalizaion(test_data, expected_result, ["format"])


def test_with_delimeters_and_lower_case():
    test_data = "978-0-262-03604-72x"
    expected_result = "97802620360472X"
    _test_isbn_normalizaion(test_data, expected_result, ["format"])


def _test_isbn_normalizaion(test_data, expected_result, expected_codes):
    body = {"partOf": [{"identifiedBy": [{"value": test_data}]}]}

    field = FieldMeta(
        value=test_data,
        normalization_status="unchanged",
        validation_status="valid",
        path="partOf.[0].identifiedBy.[0].value",
    )

    normalize_isbn(body, field)
    assert field.value == expected_result
    if len(field.events) > 0:
        assert field.events[0]["type"] == "normalization"
        for event in field.events:
            assert event["code"] in expected_codes
