from pipeline.util import FieldMeta
from pipeline.enrichers.doi import recover_doi


def test_doi_enrich_remove_whitespace():
    test_data = "10.5468 /ogs.2010.59.10.1"
    expected_result = "10.5468/ogs.2010.59.10.1"
    _test_doi_enrichment(test_data, expected_result, ["recovery"])


def test_doi_enrich_remove_unicode_cat_cc():
    # Test removal of tab from unicode category Cc.
    test_data = "10.10/invalid\t"
    expected_result = "10.10/invalid"
    _test_doi_enrichment(test_data, expected_result, ["recovery"])


def test_doi_enrich_remove_unicode_cat_cf():
    # Test removal of zero width space from unicode category Cf.
    test_data = "10.10/invalid\u200b"
    expected_result = "10.10/invalid"
    _test_doi_enrichment(test_data, expected_result, ["recovery"])


def test_doi_enrich_remove_unicode_cat_zl():
    # Test removal of line separator from unicode category Zl.
    test_data = "10.10/invalid\u2028"
    expected_result = "10.10/invalid"
    _test_doi_enrichment(test_data, expected_result, ["recovery"])


def test_doi_enrich_remove_unicode_cat_zp():
    # Test removal of paragraph separator from unicode category Zp.
    test_data = "10.10/invalid\u2029"
    expected_result = "10.10/invalid"
    _test_doi_enrichment(test_data, expected_result, ["recovery"])


def test_doi_enrich_remove_unicode_cat_zs():
    # Test removal of white space (no-break space) from unicode category Zs.
    # Regular space also belongs in this category.
    test_data = "10.10/invalid\xa0"
    expected_result = "10.10/invalid"
    _test_doi_enrichment(test_data, expected_result, ["recovery"])


def test_doi_enrich_replace_fraction_slash():
    # Test replacement of fractional slash with regular slash.
    test_data = "10.10\u2044invalid"
    expected_result = "10.10/invalid"
    _test_doi_enrichment(test_data, expected_result, ["recovery"])


def test_doi_enrich_remove_prefix():
    # Test removal of invalid prefixes.
    test_data = "Doi:10.10/valid"
    expected_result = "10.10/valid"
    _test_doi_enrichment(test_data, expected_result, ["recovery"])


def test_doi_enrich_valid_prefixes():
    # Test valid prefixes left untouched.
    test_data = "https://doi.org/10.10/valid"
    expected_result = "https://doi.org/10.10/valid"
    body = {"partOf": [{"identifiedBy": [{"value": test_data}]}]}

    field = FieldMeta(
        value=test_data,
        normalization_status="unchanged",
        validation_status="valid",
        path="partOf.[0].identifiedBy.[0].value",
    )

    recover_doi(body, field)
    assert field.value == expected_result
    assert field.events == []

    test_data = "http://doi.org/10.10/valid"
    expected_result = "http://doi.org/10.10/valid"
    body = {"partOf": [{"identifiedBy": [{"value": test_data}]}]}

    field = FieldMeta(
        value=test_data,
        normalization_status="unchanged",
        validation_status="valid",
        path="partOf.[0].identifiedBy.[0].value",
    )

    recover_doi(body, field)
    assert field.value == expected_result
    assert field.events == []


def _test_doi_enrichment(test_data, expected_result, expected_codes):
    body = {"partOf": [{"identifiedBy": [{"value": test_data}]}]}

    field = FieldMeta(
        value=test_data,
        normalization_status="unchanged",
        validation_status="valid",
        path="partOf.[0].identifiedBy.[0].value",
    )

    recover_doi(body, field)

    assert field.value == expected_result
    if len(field.events) > 0:
        assert field.events[0]["type"] == "enrichment"
        for event in field.events:
            assert event["initial_value"] == test_data
            assert event["code"] in expected_codes
