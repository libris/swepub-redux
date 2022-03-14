from pipeline.util import FieldMeta
from pipeline.validators.issn import validate_format, validate_checksum


def test_issn_valid_format():
    issn = ['0123-4567',  # Valid format
            '0123-456X',  # Valid format
            '12345678',  # Valid format
            '1234567x',  # Valid format
            ]

    expected_result = [(True, "format"),
                       (True, "format"),
                       (True, "format"),
                       (True, "format")
                       ]

    result = [validate_format(r) for r in issn]

    assert result == expected_result


def test_issn_invalid_format():
    issn = ['0123-4567, 0123-456X',  # Two issn = invalid format
            '1234567Y',  # Invalid checksum digit
            '345678',  # Too few digits
            '122345678',  # Too many digits
            '1234 5232',  # Invalid delimiter
            'ISSN 1234-1344',  # Invalid prefix
            '978-1111-1111-1-1',  # "ISBN" containing "ISSN"
            '10.1234/br.1234-1234-7654',  # Doi containing "ISSN"
            ]

    expected_result = [(False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format')
                       ]

    result = [validate_format(r) for r in issn]

    assert result == expected_result


def test_issn_valid_checksum():
    issn = ['0024-9319',  # Valid checksum
            '00000000',  # Valid checksum
            '0000040X',  # Valid checksum
            ]

    expected_result = [(True, 'checksum'),
                       (True, 'checksum'),
                       (True, 'checksum'),
                       ]

    result = [validate_checksum(r) for r in issn]

    assert result == expected_result


def test_issn_invalid_checksum():
    issn = ['0123-4567',  # Invalid checksum
            '00000001',  # Invalid checksum
            '12345671',  # Invalid checksum
            ]

    expected_result = [(False, 'checksum'),
                       (False, 'checksum'),
                       (False, 'checksum')
                       ]

    result = [validate_checksum(r) for r in issn]

    assert result == expected_result
