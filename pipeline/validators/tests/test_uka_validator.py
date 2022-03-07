from pipeline.validate import FieldMeta

def test_1_digits_uka(uka_validator):
    _test_uka(uka_validator, "1", "valid", "format")


def test_3_digits_uka(uka_validator):
    _test_uka(uka_validator, "123", "valid", "format")


def test_5_digits_uka(uka_validator):
    _test_uka(uka_validator, "12345", "valid", "format")


def test_4_digits_uka(uka_validator):
    _test_uka(uka_validator, "1234", "invalid", "format")


def test_3_nondigits_uka(uka_validator):
    _test_uka(uka_validator, "abc", "invalid", "format")


def _test_uka(validator, test_data, expected_validation, expected_code):
    field = FieldMeta(None, None, value=test_data)
    result = validator(field)
    assert field.validation_status != "pending"
    assert field.validation_status == expected_validation
    assert field.events[0]["code"] == expected_code
