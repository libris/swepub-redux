from pipeline.validate import FieldMeta
from pipeline.validators.uka import validate_uka

def test_1_digits_uka():
    _test_uka("1", "valid", "format")


def test_3_digits_uka():
    _test_uka("123", "valid", "format")


def test_5_digits_uka():
    _test_uka("12345", "valid", "format")


def test_4_digits_uka():
    _test_uka("1234", "invalid", "format")


def test_3_nondigits_uka():
    _test_uka("abc", "invalid", "format")


def _test_uka(test_data, expected_validation, expected_code):
    field = FieldMeta(value=test_data)
    result = validate_uka(field)
    assert field.validation_status != "pending"
    assert field.validation_status == expected_validation
    assert field.events[0]["code"] == expected_code
