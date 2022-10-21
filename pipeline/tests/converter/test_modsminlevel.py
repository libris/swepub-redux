from pipeline.validate import _minimum_level_checker

MODS = """
    <record
    xmlns="http://www.openarchives.org/OAI/2.0/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <metadata>
        <mods xmlns="http://www.loc.gov/mods/v3"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:xlink="http://www.w3.org/1999/xlink" version="3.2"
        xsi:schemaLocation="http://www.loc.gov/mods/v3
        http://www.loc.gov/standards/mods/v3/mods-3-2.xsd">
            {}
        </mods>
      </metadata>
    </record>
""".format


def _get_error_names(data):
    errors = _minimum_level_checker(data)
    return [error.text for error in errors.getroot()]


def test_min_level_with_empty_publication():
    data = MODS("")
    error_codes = _get_error_names(data)
    expected_errors = [
        'recordContentSourceViolation', 'nameViolation',
        'titleViolation', 'publicationOrOutputTypeViolation', 'contentTypeViolation',
        'publicationDateViolation', 'uriViolation', 'languageViolation']
    assert error_codes == expected_errors


def test_empty_mods():
    data = """
      <record xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
         <header status="deleted">
            <identifier>oai:publications.lib.chalmers.se:180444</identifier>
            <datestamp>2013-10-02T08:29:10Z</datestamp>
         </header>
      </record>"""

    error_codes = _get_error_names(data)
    expected_results = ['modsDataMissing']
    assert error_codes == expected_results


def test_institution_code_correct():
    data = MODS(
        """
        <recordInfo>
            <recordContentSource>du</recordContentSource>
        </recordInfo>
        """
    )
    errors = _get_error_names(data)
    assert 'recordContentSourceViolation' not in errors


def test_name_correct_with_person():
    create_mods_post = MODS(
        """
        <name authority="muep" type="personal">
            <namePart type="given">John</namePart>
            <namePart type="family">Doe</namePart>
                <role>
                    <roleTerm authority="marcrelator" type="code">aut</roleTerm>
                </role>
        </name>
        """)
    errors = _get_error_names(create_mods_post)
    assert 'nameViolation' not in errors


def test_name_correct_with_organization():
    allowed_role_terms = ['aut', 'edt', 'cre', 'pbl', 'org']
    create_mods_post = MODS(
        """
        <name type="corporate" authority="nationalmuseum">
            <namePart>Nationalmuseum</namePart>
            <role>
                <roleTerm  type="code" authority="marcrelator">{}</roleTerm>
            </role>
        </name>
        """).format
    res = []
    for term in allowed_role_terms:
        errors = _get_error_names(create_mods_post(term))
        res.append('nameViolation' not in errors)
    assert res == [True] * len(allowed_role_terms)


def test_title_correct():
    create_mods_post = MODS(
        """
        <titleInfo>
            <title>Hello world</title>
        </titleInfo>
        """
    )
    errors = _get_error_names(create_mods_post)
    assert 'titleViolation' not in errors


def test_publication_type_correct():
    create_mods_post = MODS("""
        <genre authority="svep" type="publicationType">kon</genre>
    """)
    errors = _get_error_names(create_mods_post)
    assert 'publicationOrOutputTypeViolation' not in errors


def test_output_type_correct():
    create_mods_post = MODS("""
        <genre type="outputType" authority="kb.se">conference</genre>
    """)
    errors = _get_error_names(create_mods_post)
    assert 'publicationOrOutputTypeViolation' not in errors


def test_publication_and_output_type_correct():
    create_mods_post = MODS("""
        <genre authority="kb.se" type="outputType">conference</genre>
        <genre authority="svep" type="publicationType">kon</genre>
    """)
    errors = _get_error_names(create_mods_post)
    assert 'publicationOrOutputTypeViolation' not in errors


def test_allowed_output_types():
    output_types = [
        'artistic-work/artistic-thesis', 'publication/foreword-afterword', 'publication/preprint', 'other/software']
    create_mods_post = MODS("""
        <genre authority="kb.se" type="outputType">{}</genre>
    """).format
    for output_type in output_types:
        errors = _get_error_names(create_mods_post(output_type))
        assert 'publicationOrOutputTypeViolation' not in errors


def test_allowed_content_types():
    allowed_content_types = ['ref', 'vet', 'pop']
    create_mods_post = MODS("""
        <genre type="contentType" authority="svep">{}</genre>
    """).format
    for con in allowed_content_types:
        errors = _get_error_names(create_mods_post(con))
        assert 'contentTypeViolation' not in errors


def test_content_type_validation():
    create_mods_post = MODS("""
        <genre type="contentType" authority="svep">Foo</genre>
    """)
    errors = _get_error_names(create_mods_post)
    assert 'contentTypeViolation' in errors


def test_publication_types_not_requiring_content_type():
    pub_types = ['pat', 'ovr']
    create_mods_post = MODS("""
        <genre authority="svep" type="publicationType">{}</genre>
    """).format
    for pub in pub_types:
        errors = _get_error_names(create_mods_post(pub))
        assert 'contentTypeViolation' not in errors


def test_output_types_not_requiring_content_type():
    output_types = [
        'intellectual-property', 'intellectual-property/patent', 'intellectual-property/other',
        'other', 'other/data-set', 'other/software']
    create_mods_post = MODS("""
        <genre authority="kb.se" type="outputType">{}</genre>
    """).format
    for output_type in output_types:
        errors = _get_error_names(create_mods_post(output_type))
        assert 'contentTypeViolation' not in errors


def test_publication_date_with_published_status_correct():
    create_mods_post = MODS("""
        <originInfo>
            <dateIssued>2014</dateIssued>
        </originInfo>
        <note type="publicationStatus">Published</note>
    """)
    errors = _get_error_names(create_mods_post)
    assert 'publicationDateViolation' not in errors


def test_publication_date_with_non_published_status_correct():
    create_mods_post = MODS("""
        <note type="publicationStatus">In press</note>
    """)
    # TODO
    errors = _get_error_names(create_mods_post)
    assert 'publicationDateViolation' not in errors


def test_publication_date_missing_with_published_status():
    create_mods_post = MODS("""
        <note type="publicationStatus">Published</note>
    """)
    errors = _get_error_names(create_mods_post)
    assert 'publicationDateViolation' in errors


def test_publication_date_correct():
    create_mods_post = MODS("""
        <originInfo>
            <dateIssued>2014</dateIssued>
        </originInfo>
    """)
    errors = _get_error_names(create_mods_post)
    assert 'publicationDateViolation' not in errors


def test_publication_date_for_non_published_correct():
    create_mods_post = MODS("""
        <originInfo>
            <dateIssued>2014</dateIssued>
        </originInfo>
        <note type="publicationStatus">In press</note>
    """)
    errors = _get_error_names(create_mods_post)
    assert 'publicationDateViolation' not in errors


def test_publication_date_missing_with_preprint():
    create_mods_post = MODS("""
            <note type="publicationStatus">Published</note>
            <genre authority="kb.se" type="outputType">publication/preprint</genre>
        """)
    errors = _get_error_names(create_mods_post)
    assert 'publicationDateViolation' not in errors


def test_uri_correct():
    create_mods_post = MODS("""
        <identifier type="uri">dodo.com</identifier>
    """)
    errors = _get_error_names(create_mods_post)
    assert 'uriViolation' not in errors


def test_language_authority_correct():
    create_mods_post = MODS("""
        <language>
            <languageTerm authority="iso639-3" type="code">espiranto</languageTerm>
        </language>
    """)
    errors = _get_error_names(create_mods_post)
    assert 'languageViolation' not in errors


def test_related_item_type_correct():
    create_mods_post = MODS("""
        <genre authority="svep" type="publicationType">art</genre>
        <relatedItem type="host">
            <titleInfo>
                <title>Bamse</title>
            </titleInfo>
        </relatedItem>
    """)
    errors = _get_error_names(create_mods_post)
    assert 'relatedItemTypeMissing' not in errors


def test_related_item_type_missing_for_published():
    create_mods_post = MODS("""
            <genre authority="svep" type="publicationType">art</genre>
            <note type="publicationStatus">Published</note>
        """)
    errors = _get_error_names(create_mods_post)
    assert 'relatedItemTypeMissing' in errors


def test_related_item_type_missing_for_allowed_publication_types():
    allowed_publication_types = ['art', 'for', 'kap', 'rec']
    create_mods_post = MODS("""
            <genre authority="svep" type="publicationType">{}</genre>
        """).format
    for abb in allowed_publication_types:
        errors = _get_error_names(create_mods_post(abb))
        assert 'relatedItemTypeMissing' in errors


def test_related_item_type_non_published_for_all_allowed_publication_types_correct():
    allowed_publication_types = ['art', 'for', 'kap', 'rec']
    create_mods_post = MODS("""
            <genre authority="svep" type="publicationType">{}</genre>
            <note type="publicationStatus">Preprint</note>
        """).format
    for abb in allowed_publication_types:
        errors = _get_error_names(create_mods_post(abb))
        assert 'relatedItemTypeMissing' not in errors


def test_related_item_type_missing_when_required():
    allowed_output_types = [
        'publication/book-chapter', 'publication/report-chapter', 'publication/journal-article',
        'publication/editorial-letter', 'publication/magazine-article', 'publication/newspaper-article',
        'publication/journal-issue', 'publication/book-review', 'publication/review-article',
        'publication/foreword-afterword']
    create_mods_post = MODS("""
            <genre authority="kb.se" type="outputType">{}</genre>
        """).format
    res = []
    for output_type in allowed_output_types:
        errors = _get_error_names(create_mods_post(output_type))
        res.append('relatedItemTypeMissing' in errors)
    assert res == [True] * len(allowed_output_types)


def test_with_related_item_type_when_required():
    allowed_output_types = [
        'publication/book-chapter', 'publication/report-chapter', 'publication/journal-article',
        'publication/editorial-letter', 'publication/magazine-article', 'publication/newspaper-article',
        'publication/journal-issue', 'publication/book-review', 'publication/review-article',
        'conference', 'publication/forword-afterword']
    create_mods_post = MODS("""
            <genre authority="kb.se" type="outputType">{}</genre>
            <relatedItem type="host">
                <titleInfo>
                    <title>Bamse</title>
                </titleInfo>
            </relatedItem>
            <note type="publicationStatus">Published</note>
        """).format
    for output_type in allowed_output_types:
        errors = _get_error_names(create_mods_post(output_type))
        assert 'relatedItemTypeMissing' not in errors


def test_related_item_violation_for_all_non_allowed_publication_types():
    non_allowed_publication_types = ['bok', 'dok', 'lic', 'pat', 'pro', 'rap']
    create_mods_post = MODS("""
            <genre authority="svep" type="publicationType">{}</genre>
            <relatedItem type="host">
                <titleInfo>
                    <title>Bamse</title>
                </titleInfo>
            </relatedItem>
            <note type="publicationStatus">Published</note>
        """).format
    for abb in non_allowed_publication_types:
        errors = _get_error_names(create_mods_post(abb))
        assert 'relatedItemTypeViolation' in errors


def test_related_item_type_violation_for_all_publication_types_without_related_item():
    allowed_publication_types = ['bok', 'dok', 'lic', 'pat', 'pro', 'rap']
    create_mods_post = MODS("""
            <genre authority="svep" type="publicationType">{}</genre>
        """).format
    for pub in allowed_publication_types:
        errors = _get_error_names(create_mods_post(create_mods_post(pub)))
        assert 'relatedItemTypeViolation' not in errors


def test_related_item_type_violation_for_all_output_types_without_related_item():
    allowed_output_types = [
        'publication/book-chapter', 'publication/report-chapter', 'publication/journal-article',
        'publication/editorial-letter', 'publication/magazine-article', 'publication/newspaper-article',
        'publication/journal-issue', 'publication/book-review', 'publication/review-article',
        'publication/foreword-afterword', 'conference']
    create_mods_post = MODS("""
            <genre authority="kb.se" type="outputType">{}</genre>
        """).format
    for output_type in allowed_output_types:
        errors = _get_error_names(create_mods_post(create_mods_post(output_type)))
        assert 'relatedItemTypeViolation' not in errors


def test_related_item_type_violation_for_all_output_types_with_related_item():
    allowed_output_types = [
        'publication/book-chapter', 'publication/report-chapter', 'publication/journal-article',
        'publication/editorial-letter', 'publication/magazine-article', 'publication/newspaper-article',
        'publication/journal-issue', 'publication/book-review', 'publication/review-article',
        'publication/foreword-afterword', 'conference']
    create_mods_post = MODS("""
            <genre authority="kb.se" type="outputType">{}</genre>
            <relatedItem type="host">
                <titleInfo>
                    <title>Bamse</title>
                </titleInfo>
            </relatedItem>
            <note type="publicationStatus">Published</note>
        """).format
    for output_type in allowed_output_types:
        errors = _get_error_names(create_mods_post(create_mods_post(output_type)))
        assert 'relatedItemTypeViolation' not in errors


def test_no_related_item_type_violation_with_genre_exceptions():
    allowed_genres = ['project', 'initiative', 'grantAgreement', 'programme', 'event', 'dataset']
    create_mods_post = MODS("""
            <genre authority="svep" type="publicationType">bok</genre>
            <relatedItem type="host">
                <genre>{}</genre>
                <titleInfo>
                    <title>Bamse</title>
                </titleInfo>
            </relatedItem>
            <note type="publicationStatus">Published</note>
        """).format
    for allowed_genre in allowed_genres:
        errors = _get_error_names(create_mods_post(allowed_genre))
        assert 'relatedItemTypeViolation' not in errors
