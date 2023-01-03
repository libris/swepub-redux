from unittest.mock import MagicMock

from pipeline.util import FieldMeta
from pipeline.enrichers.localid import recover_orcid_from_localid
from pipeline.util import get_localid_cache_key

# TODO: These tests are a mess. Should probably be replaced with integration tests
# at some point.

def test_add_orcid_if_matching_localid():
    source = "foo"
    test_data = {
        "@type": "Local",
        "value": "kalle.ninja",
        "source": {"@type": "Source", "code": "foo"},
    }
    cache_key = get_localid_cache_key(test_data, "BarFoo", source)
    cache_data = {"source_oai_id": "oai:DiVA.org:foo-123", "orcid": "0000-0002-5892-9999"}

    expected_addition = {"@type": "ORCID", "value": cache_data["orcid"]}
    expected_body = {"@id": "foo", "instanceOf": {"contribution": [{"agent": {"givenName": "foo", "familyName": "bar", "identifiedBy": [test_data, expected_addition]}}]}}
    expected_codes = ["add_orcid_from_localid"]

    _test_localid_enricher(cache_data, source, test_data, expected_body, expected_codes)


def test_dont_add_orcid_if_no_matching_localid():
    source = "zzz"
    test_data = {
        "@type": "Local",
        "value": "kalle.ninja",
        "source": {"@type": "Source", "code": "foo"},
    }
    cache_key = get_localid_cache_key(test_data, "BarFoo", "bar")
    cache_data = {"source_oai_id": "oai:DiVA.org:foo-123", "orcid": "0000-0002-5892-9999"}

    expected_body = {"@id": "foo", "instanceOf": {"contribution": [{"agent": {"givenName": "foo", "familyName": "bar", "identifiedBy": [test_data]}}]}}
    expected_codes = []

    _test_localid_enricher(cache_data, source, test_data, expected_body, expected_codes)


def _test_localid_enricher(cache_data, source, test_data, expected_body, expected_codes):
    harvest_cache = {"localid_to_orcid": {}, "enriched_from_other_record": {}, "localid_without_orcid": {}}
    cache_key = get_localid_cache_key(test_data, "BarFoo", source)

    harvest_cache["localid_to_orcid"] = cache_data
    field = FieldMeta(
        value=test_data, path="instanceOf.contribution.[0].agent.identifiedBy.[0]"
    )
    body = {"@id": "foo", "instanceOf": {"contribution": [{"agent": {"givenName": "foo", "familyName": "bar", "identifiedBy": [test_data]}}]}}

    mocked_cursor = MagicMock(name="mocked_cursor")
    if cache_key == "foo_foo_kalle.ninja_barfoo":
        mocked_cursor.execute.return_value.fetchone.return_value = cache_data
    else:
        mocked_cursor.execute.return_value.fetchone.return_value = {}

    recover_orcid_from_localid(body, field, harvest_cache, source, {}, mocked_cursor)

    assert body == expected_body
    if len(field.events) > 0:
        assert field.events[0]["type"] == "enrichment"
        for event in field.events:
            assert event["initial_value"] == f"{cache_data['source_oai_id']}, {test_data['value']}"
            assert event["code"] in expected_codes
