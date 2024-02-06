from pipeline.util import FieldMeta, Validation
from pipeline.validators.ssif import validate_ssif


def test_1_digits_ssif():
    _test_ssif("1", Validation.VALID, "format")


def test_3_digits_ssif():
    _test_ssif("123", Validation.VALID, "format")


def test_5_digits_ssif():
    _test_ssif("12345", Validation.VALID, "format")


def test_4_digits_ssif():
    _test_ssif("1234", Validation.INVALID, "format")


def test_3_nondigits_ssif():
    _test_ssif("abc", Validation.INVALID, "format")


def _test_ssif(test_data, expected_validation, expected_code):
    field = FieldMeta(value=test_data)
    result = validate_ssif(field)
    assert field.validation_status != Validation.PENDING
    assert field.validation_status == expected_validation
    assert field.events[0]["code"] == expected_code
