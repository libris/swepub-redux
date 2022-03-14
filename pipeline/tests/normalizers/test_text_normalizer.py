from pipeline.util import FieldMeta
from pipeline.normalize import normalize_free_text


def test_text_cleaner_succeeds():
    body = {
        "instanceOf": {
            "subject": [{"prefLabel": "<p>Performance\rEnhancement &amp; Health</p>"}]
        }
    }

    test_data = "<p>Performance\rEnhancement &amp; Health</p>"
    expected_result = "Performance Enhancement & Health"
    field = FieldMeta(
        value=test_data,
        normalization_status="unchanged",
        validation_status="valid",
        path="instanceOf.subject.[0].prefLabel",
    )
    normalize_free_text(body, field)
    assert field.value == expected_result
    assert field.normalization_status == "normalized"
    assert field.events[0]["code"] == "strip_tags"
    assert field.events[1]["code"] == "clean_text"


# TODO: Need to fix so that the cleaner doesn't fail on this
def test_text_tag_cleaner_fail():
    body = {"instanceOf": {"subject": [{"prefLabel": "Id<e om nåt roligt."}]}}

    test_data = "Id<e om nåt roligt."
    expected_result = "Id"
    field = FieldMeta(
        value=test_data,
        normalization_status="unchanged",
        validation_status="valid",
        path="instanceOf.subject.[0].prefLabel",
    )
    normalize_free_text(body, field)
    assert field.value == expected_result
    assert field.normalization_status == "normalized"
    assert field.events[0]["code"] == "strip_tags"
