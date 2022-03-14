import unicodedata
import sys

from pipeline.util import FieldMeta
from pipeline.validators.doi import validate_unicode, validate_format


def test_valid_doi_unicode():
    invalid_doi_unicode_categories = {'Cc', 'Cf', 'Zl', 'Zp', 'Zs'}
    # Create a string of all unicode chars not of invalid category.
    all_valid_unicode_chars = ''.join((c for c in (chr(i) for i in range(sys.maxunicode))
                                       if unicodedata.category(c) not in invalid_doi_unicode_categories))
    assert validate_unicode(all_valid_unicode_chars) == (True, 'unicode', None)


def test_invalid_doi_unicode():
    invalid_unicode = [
        '10.1/Category_Cc_TAB:\t',
        '10.1/Category_Cf_ZERO_WIDTH_SPACE:\u200b',
        '10.1/Category_Zl_LINE_SEPARATOR:\u2028',
        '10.1/Category_Zl_PARAGRAPH_SEPARATOR:\u2029',
        '10.1/Category_Zs_SPACE: ',
        '10.1/Category_Zs_NO-BREAK_SPACE:\xa0',
    ]
    expected_result = [
        (False, 'unicode', None),
        (False, 'unicode', None),
        (False, 'unicode', None),
        (False, 'unicode', None),
        (False, 'unicode', None),
        (False, 'unicode', None),
    ]
    result = [validate_unicode(doi) for doi in invalid_unicode]
    assert result == expected_result


def test_valid_doi_format():
    valid_doi = [
        '10.1000/doi:whatever',
        'https://doi.org/10.1000/whatever',
        'http://doi.org/10.1000/whatever',
        '10.text_is_allowed!/{åäö}',
        '10.100.10/sub-element-in-registrant-code-is-ok',
    ]
    expected_result = [
        (True, 'format'),
        (True, 'format'),
        (True, 'format'),
        (True, 'format'),
        (True, 'format'),
    ]
    result = [validate_format(doi)[0:2] for doi in valid_doi]
    assert result == expected_result


def test_invalid_doi_format():
    invalid_doi = [
        'doi:10.1/100',  # Prefix other than 'https://doi.org' or 'http://doi.org' not allowed.
        'not/ok',
        '10./missing-registrant-code',
        '10.missing-suffix/',
        '100.100/incorrect-prefix',
        'https://doi.org/',
        '10.1⁄fraction-slash-not-allowed',  # Fraction slash \u2044
        '',
    ]
    expected_result = [
        (False, 'format'),
        (False, 'format'),
        (False, 'format'),
        (False, 'format'),
        (False, 'format'),
        (False, 'format'),
        (False, 'format'),
        (False, 'format'),
    ]
    result = [validate_format(doi)[0:2] for doi in invalid_doi]
    assert result == expected_result

