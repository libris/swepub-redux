from pipeline.util import FieldMeta
from pipeline.normalize import normalize_orcid


def test_without_prefix_and_with_delimeter():
    test_data = "0000-0002-1642-6281"
    expected_result = "https://orcid.org/0000-0002-1642-6281"
    _test_orcid(test_data, expected_result, ["prefix.add"])


def test_without_prefix_and_without_delimeter():
    test_data = "0000000216426281"
    expected_result = "https://orcid.org/0000-0002-1642-6281"
    _test_orcid(test_data, expected_result, ["prefix.add", "format.delimiters"])


def test_without_prefix_and_without_delimeter_and_x():
    test_data = "000000021642628X"
    expected_result = "https://orcid.org/0000-0002-1642-628X"
    _test_orcid(test_data, expected_result, ["prefix.add", "format.delimiters"])


def test_without_prefix_and_with_delimeter_and_x():
    test_data = "0000-0002-1642-628X"
    expected_result = "https://orcid.org/0000-0002-1642-628X"
    _test_orcid(test_data, expected_result, ["prefix.add"])


def test_with_http_prefix_and_with_delimeter():
    test_data = "http://orcid.org/0000-0002-1642-6281"
    expected_result = "https://orcid.org/0000-0002-1642-6281"
    _test_orcid(test_data, expected_result, ["prefix.update"])


def test_with_http_prefix_and_without_delimeter():
    test_data = "http://orcid.org/0000000216426281"
    expected_result = "https://orcid.org/0000-0002-1642-6281"
    _test_orcid(test_data, expected_result, ["prefix.update", "format.delimiters"])


def _test_orcid(test_data, expected_result, expected_codes):
    body = {
        "instanceOf": {
            "contribution": [{"agent": {"identifiedBy": [{"@type": "ORCID", "value": test_data}]}}]
        }
    }

    field = FieldMeta(
        value=test_data,
        path="instanceOf.contribution.[0].agent.identifiedBy.[0].value",
    )

    normalize_orcid(body, field)
    assert field.value == expected_result
    if len(field.events) > 0:
        assert field.events[0]["type"] == "normalization"
        for event in field.events:
            assert event["code"] in expected_codes
