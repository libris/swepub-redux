from pipeline.util import FieldMeta
from pipeline.validators.creator import validate_is_numeric

def test_valid_creator_count_numeric():
    data = ['1']
    expected_result = [(True, 'numeric')]
    result = [validate_is_numeric(m) for m in data]
    assert result == expected_result


def test_invalid_datetime_format():
    data = ['a']
    expected_result = [(False, 'numeric')]
    result = [validate_is_numeric(m) for m in data]
    assert result == expected_result
