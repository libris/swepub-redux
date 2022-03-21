from pipeline.util import FieldMeta
from pipeline.validators.orcid import strip_url, validate_format, validate_checksum, validate_span


def test_orcid_valid_format_validation():
    orcid = [
        "0000-0002-1825-0097",  # Valid ORCID
        "0000-0002-9079-593X",  # Valid ORCID
        "0000-0002-9079-593x",  # Valid ORCID
        "https://orcid.org/0000-0002-9079-593X",  # Valid ORCID with prefix
        "http://orcid.org/0000-0002-9079-593X",  # Valid ORCID with prefix
        "http://orcid.org/000000029079593X",  # Valid ORCID with prefix without delimiter
        "0000000218250097",
    ]  # Valid format

    expected_results = [
        (True, "format"),
        (True, "format"),
        (True, "format"),
        (True, "format"),
        (True, "format"),
        (True, "format"),
        (True, "format"),
    ]

    result = [validate_format(r) for r in orcid]

    assert result == expected_results


def test_orcid_invalid_format_validation():
    orcid = [
        "00010002X8250092",  # Containing incorrect char
        "00010002250092",  # Too few och digits
        "000000000218250092",
    ]  # Too many digits

    expected_results = [(False, "format"), (False, "format"), (False, "format")]

    result = [validate_format(r) for r in orcid]

    assert result == expected_results


def test_orcid_valid_checksum_validation():
    orcid = [
        "0000-0002-1825-0097",  # Valid ORCID
        "0000-0002-9079-593X",  # Steven hawkins' ORCID
        "https://orcid.org/0000-0002-2397-0769",
    ]  # ORCID with full URL

    result = [validate_checksum(r) for r in orcid]

    assert result == [(True, "checksum")] * len(orcid)


def test_orcid_invalid_checksum_validation():
    orcid = ["0000-0002-9079-5931"]  # Invalid checksum

    expected_results = [(False, "checksum")]

    result = [validate_checksum(r) for r in orcid]

    assert result == expected_results


def test_orcid_valid_span_validation():
    orcid = ["0000-0002-1825-0097", "0000-0002-9079-593X"]  # Valid ORCID  # Valid ORCID

    expected_results = [(True, "span"), (True, "span")]

    result = [validate_span(r) for r in orcid]

    assert result == expected_results


def test_orcid_invalid_span_validation():
    orcid = [
        "0001-0002-9079-593X",  # Invalid first section
        "0000-0003-5079-593X",  # Value too large
        "0000-0001-4999-9999",  # Value too small
        "0000-0000-0000-0000",
    ]  # Value too small

    expected_results = [(False, "span"), (False, "span"), (False, "span"), (False, "span")]

    result = [validate_span(r) for r in orcid]

    assert result == expected_results


def test_url_stril():
    orcid = [
        "0000-0002-1825-0097",
        "http://orcid.org/0000-0002-9079-593X",  # With http
        "https://orcid.org/0000-0002-9079-5931",
    ]  # With https

    expected_results = ["0000-0002-1825-0097", "0000-0002-9079-593X", "0000-0002-9079-5931"]

    result = [strip_url(m) for m in orcid]

    assert result == expected_results
