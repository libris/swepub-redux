from pipeline.validate import FieldMeta
from pipeline.enrichers.isbn import recover_isbn


def test_isbn_with_prefix():
    test_data = "ISBN 978-91-86857-16-5"
    expected_result = "978-91-86857-16-5"
    _test_isbn_enrichment(test_data, expected_result, ["recovery"])


def test_isbn_with_prefix_and_suffix():
    test_data = "ISBN: 978-91-7740-107-0 (pdf)"
    expected_result = "978-91-7740-107-0"
    _test_isbn_enrichment(test_data, expected_result, ["recovery"])


def test_isbn10_with_prefix_and_numeric_control():
    test_data = "ISBN 0415579961"
    expected_result = "0415579961"
    _test_isbn_enrichment(test_data, expected_result, ["recovery"])


def test_isbn10_with_prefix_and_lowercase_x_control():
    test_data = "ISBN 041557996x"
    expected_result = "041557996x"
    _test_isbn_enrichment(test_data, expected_result, ["recovery"])


def test_isbn10_with_prefix_and_capital_X_control():
    test_data = "ISBN: 917291341X"
    expected_result = "917291341X"
    _test_isbn_enrichment(test_data, expected_result, ["recovery"])


def test_isbn13_with_prefix():
    test_data = "ISBN: 9172-91-341-X"
    expected_result = "9172-91-341-X"
    _test_isbn_enrichment(test_data, expected_result, ["recovery"])


def test_isbn13_with_numerical_prefix():
    test_data = "13 9780853583080"
    expected_result = "9780853583080"
    _test_isbn_enrichment(test_data, expected_result, ["recovery"])


# TODO: Fix split in enricher
# def test_dual_isbn():
#    test_data = '0415579961, 9780415579964'
#    original_field_data = {'value': test_data, 'enrichment_status': 'pending', 'path': '<path>',
#                           'validation_status': 'true', 'events': []}
#    field, actions = isbn_enricher(FieldMetadata(original_field_data))
#    assert field.value == '0415579961'
#    action1 = actions[0]
#    event1 = field.events[0]
#    assert isinstance(action1, DuplicateFieldAction)
#    assert action1.field_type == 'isbn'
#    assert event1['new_value'] == '0415579961'
#    assert event1['old_value'] == '0415579961, 9780415579964'
#    assert event1['code'] == 'recovery'
#    action2 = actions[1]
#    event2 = field.events[1]
#    assert isinstance(action2, ChangeAction)
#    assert action2.field_type == 'isbn'
#    assert event2['created_value'] == '9780415579964'
#    assert event2['old_value'] == '0415579961, 9780415579964'
#    assert event2['code'] == 'split'


def test_isbn_non_recoverable_wrong_length_and_strange_prefix():
    test_data = "2-s2.0-84863732124"
    _test_none_isbn_enrichment(test_data)


def test_isbn_non_recoverable_issn():
    test_data = "0022-2380"
    _test_none_isbn_enrichment(test_data)


def test_isbn_non_recoverable_doi():
    test_data = "10.1046/j.1365-2834.1999.00138.x"
    _test_none_isbn_enrichment(test_data)


def test_isbn_non_recoverable_to_many_digits():
    test_data = "12345678901234567890"
    _test_none_isbn_enrichment(test_data)


def test_isbn_non_recoverable_doi_containing_isbn():
    test_data = "10.1046/j.978-91-86857-16-5"
    _test_none_isbn_enrichment(test_data)


def test_isbn_non_recoverable_numerical_prefix_without_delimiter():
    test_data = "13978-91-975576-6-5"
    _test_none_isbn_enrichment(test_data)


def _test_isbn_enrichment(test_data, expected_result, expected_codes):
    body = {"identifiedBy": [{"value": test_data}]}

    field = FieldMeta(
        value=test_data,
        normalization_status="unchanged",
        validation_status="valid",
        enrichment_status="pending",
        path="identifiedBy.[0].value",
    )

    recover_isbn(body, field)

    assert field.value == expected_result
    if len(field.events) > 0:
        assert field.events[0]["type"] == "enrichment"
        for event in field.events:
            assert event["initial_value"] == test_data
            assert event["code"] in expected_codes


def _test_none_isbn_enrichment(test_data):
    body = {"identifiedBy": [{"value": test_data}]}

    field = FieldMeta(
        value=test_data,
        normalization_status="unchanged",
        validation_status="valid",
        enrichment_status="pending",
        path="identifiedBy.[0].value",
    )

    recover_isbn(body, field)

    assert field.value == test_data
    assert not field.is_enriched()
    assert len(field.events) == 0