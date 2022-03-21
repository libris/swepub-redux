from pipeline.util import FieldMeta
from pipeline.normalize import normalize_doi


def test_prefix_add():
    test_data = "10.5468/ogs.2010.59.10.1"
    expected_result = "https://doi.org/10.5468/ogs.2010.59.10.1"
    _test_doi(test_data, expected_result, ["prefix.add"])


def test_prefix_remove():
    test_data = "doi https://doi.org/10.5468/ogs.2010.59.10.1"
    expected_result = "https://doi.org/10.5468/ogs.2010.59.10.1"
    _test_doi(test_data, expected_result, ["prefix.remove"])


def test_bad_prefix_doi_whitespace():
    test_data = "doi 10.5468/ogs.2010.59.10.1"
    expected_result = "https://doi.org/10.5468/ogs.2010.59.10.1"
    _test_doi(test_data, expected_result, ["prefix.remove", "prefix.add"])


def test_bad_prefix_doi():
    test_data = "DOI:10.5468/ogs.2010.59.10.1"
    expected_result = "https://doi.org/10.5468/ogs.2010.59.10.1"
    _test_doi(test_data, expected_result, ["prefix.remove", "prefix.add"])


def test_faulty_website():
    test_data = "http://goi.org/10.5468/ogs.2010.59.10.1"
    expected_result = "https://doi.org/10.5468/ogs.2010.59.10.1"
    _test_doi(test_data, expected_result, ["prefix.remove", "prefix.add"])


def test_no_normalization():
    test_data = "https://doi.org/10.5468/ogs.2010.59.10.1"
    expected_result = "https://doi.org/10.5468/ogs.2010.59.10.1"
    _test_doi(test_data, expected_result, [])


def test_prefix_update():
    test_data = "http://doi.org/10.5468/ogs.2010.59.10.1"
    expected_result = "https://doi.org/10.5468/ogs.2010.59.10.1"
    _test_doi(test_data, expected_result, ["prefix.update"])


def _test_doi(test_data, expected_result, expected_codes):
    body = {"partOf": [{"identifiedBy": [{"value": test_data}]}]}

    field = FieldMeta(
        value=test_data,
        normalization_status="unchanged",
        validation_status="valid",
        path="partOf.[0].identifiedBy.[0].value",
    )

    normalize_doi(body, field)
    assert field.value == expected_result
    if len(field.events) > 0:
        assert field.events[0]["type"] == "normalization"
        for event in field.events:
            assert event["code"] in expected_codes
