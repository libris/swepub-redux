from pipeline.util import FieldMeta
from pipeline.validators.datetime import validate_format

def test_valid_datetime_format():
    data = ['2001',
            '2001-01-01',
            ]
    expected_result = [(True, 'format'),
                       (True, 'format'), ]
    result = [validate_format(m) for m in data]
    assert result == expected_result


def test_invalid_datetime_format():
    data = ['2012-13-13',
            '2001-01-00',
            '2001-01-32',
            '2001-01',
            '200101',
            '20010101',
            '2000.12.12',
            '2012/12/12',
            '12/12/2001',
            '17/2-2012',
            'date 2001',
            '2001 janbruary',
            '1234-5678']
    expected_result = [(False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format'), ]
    result = [validate_format(m) for m in data]
    assert result == expected_result
