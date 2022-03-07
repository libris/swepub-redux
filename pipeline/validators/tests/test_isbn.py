from pipeline.validate import FieldMeta
from pipeline.validators.isbn import validate_format, validate_checksum


def test_isbn_valid_format():
    isbn = ['9789113073378',  # Correct ISBN13
            '978-911-307-337-8',  # Correct ISBN13
            '978 911-307-337-8',  # Correct ISBN13 with whitespace
            '1-58113-201-8',  # Correct ISBN10
            '1 58113-201-8',  # Correct ISBN10
            '3540291385',  # Correct ISBN10
            '978-0-9981331-0-2'  # ISBN with large field
            ]

    expected_result = [(True, 'format')] * len(isbn)

    result = [validate_format(FieldMeta(value=r)) for r in isbn]
    assert result == expected_result


def test_isbn_invalid_format():
    isbn = ['ISBN 978-911-307-337-8',  # Incorrect prefix on correct ISBN
            '9-789113073378',  # Incorrectly positioned delimiter
            '978-911-307-33-78',  # Incorrectly positioned delimiter
            '978-911 307-33-7 8',  # Too many delimiter
            '978-911-307-337-X',  # ISBN13 with X
            '975-911-307-337-8',  # Incorrect first three digits
            '1234-5678',  # ISSN number
            '10.1205/978-1522-555-43-2',  # DOI
            ]

    expected_result = [(False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format'),
                       (False, 'format')]

    result = [validate_format(FieldMeta(value=r)) for r in isbn]
    assert result == expected_result


def test_isbn_valid_checksum():
    isbn = ['9789113073378',  # Correct ISBN13
            '978-911-307-337-8',  # Correct ISBN13
            '0000000000',  # Correct ISBN10
            ]

    expected_result = [(True, 'checksum'),
                       (True, 'checksum'),
                       (True, 'checksum'),
                       ]

    result = [validate_checksum(FieldMeta(value=r)) for r in isbn]
    assert result == expected_result


def test_isbn_invalid_checksum():
    isbn = ['978-911-307-337-2',  # Incorrect checksum
            '000000000X'  # Incorrect checksum
            ]

    expected_result = [(False, 'checksum'),
                       (False, 'checksum')
                       ]

    result = [validate_checksum(FieldMeta(value=r)) for r in isbn]
    assert result == expected_result
