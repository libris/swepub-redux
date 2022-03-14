from pipeline.util import FieldMeta
from pipeline.validators.isi import validate_format


def test_valid_isi():
    isi = ['000123456789123',  # Correct ISI
           '000321123456789',  # Correct ISI
           'A1994PR35700005',  # Correct ISI
           'A1997WE83100014',  # Correct ISI
           'A19123456789123',  # 'Correct' ISI
           'A19XY3456789123',  # 'Correct' ISI
           'A1993BB56U00028',  # 'Correct' ISI
           ]

    expected_result = [(True, 'format')] * len(isi)

    result = [validate_format(FieldMeta(value=r)) for r in isi]
    assert result == expected_result


def test_invalid_isi_format():
    isi = ['001123456789123',  # Incorrect prefix
           'A18123456789123',  # Incorrect prefix
           '00012345678912',  # Incorrect length
           '0001234567891234',  # Incorrect length
           '000A23456789123',  # Incorrect characters
           'ISI: 000000000000000'  # Preceding characters
           ]

    expected_result = [(False, 'format')] * len(isi)

    result = [validate_format(FieldMeta(value=r)) for r in isi]
    assert result == expected_result
