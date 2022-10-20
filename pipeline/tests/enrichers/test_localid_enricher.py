from pipeline.util import FieldMeta
from pipeline.enrichers.localid import recover_orcid_from_localid
from pipeline.util import get_localid_cache_key


def test_add_orcid_if_matching_localid():
    source = "foo"
    test_data = {
        "@type": "Local",
        "value": "kalle.ninja",
        "source": {"@type": "Source", "code": "foo"},
    }
    cache_key = get_localid_cache_key(test_data, "bar foo", source)
    cache_data = {cache_key: ["0000-0002-5892-9999", "oai:DiVA.org:foo-123"]}

    expected_addition = {"@type": "ORCID", "value": cache_data[cache_key][0]}
    expected_body = {"instanceOf": {"contribution": [{"agent": {"givenName": "foo", "familyName": "bar", "identifiedBy": [test_data, expected_addition]}}]}}
    expected_codes = ["add_orcid_from_localid"]

    _test_localid_enricher(cache_data, source, test_data, expected_body, expected_codes)


def test_dont_add_orcid_if_no_matching_localid():
    source = "foo"
    test_data = {
        "@type": "Local",
        "value": "kalle.ninja",
        "source": {"@type": "Source", "code": "foo"},
    }
    cache_key = get_localid_cache_key(test_data, "bar foo", "bar")
    cache_data = {cache_key: ["0000-0002-5892-9999", "oai:DiVA.org:foo-123"]}

    expected_body = {"instanceOf": {"contribution": [{"agent": {"givenName": "foo", "familyName": "bar", "identifiedBy": [test_data]}}]}}
    expected_codes = []

    _test_localid_enricher(cache_data, source, test_data, expected_body, expected_codes)


def _test_localid_enricher(cache_data, source, test_data, expected_body, expected_codes):
    harvest_cache = {"localid_to_orcid_static": {}, "localid_to_orcid_new": {}}
    cache_key = get_localid_cache_key(test_data, "bar foo", source)
    harvest_cache["localid_to_orcid_static"] = cache_data
    field = FieldMeta(
        value=test_data, path="instanceOf.contribution.[0].agent.identifiedBy.[0]"
    )
    body = {"instanceOf": {"contribution": [{"agent": {"givenName": "foo", "familyName": "bar", "identifiedBy": [test_data]}}]}}

    recover_orcid_from_localid(body, field, harvest_cache, source)

    assert body == expected_body
    if len(field.events) > 0:
        assert field.events[0]["type"] == "enrichment"
        for event in field.events:
            assert event["initial_value"] == f"{cache_data[cache_key][1]}, {test_data['value']}"
            assert event["code"] in expected_codes
