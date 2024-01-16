import os
import json
import pytest
from pipeline.publication import Publication

BODY = """
{{
  "@id": "{}",
  "instanceOf": {{
    "hasTitle": [{{"@type": "Title", "mainTitle": "{}", "subtitle": "{}"}}],
    "summary": [{{"@type": "Summary", "label": "{}"}}],
    "subject": [{}],
    "genreForm": [{}],
    "hasNote": [{}]
  }},
  "identifiedBy": [
      {{"@type": "DOI", "value": "{}"}},
      {{"@type": "PMID", "value": "{}"}},
      {{"@type": "ISI", "value": "{}"}},
      {{"@type": "ScopusID", "value": "{}"}},
      {{"@type": "ISBN", "value": "{}"}},
      {{"@type": "URI", "value": "{}"}}
      ],
  "indirectlyIdentifiedBy": [{{"@type": "ISSN", "value": "{}"}}],
  "publication": [{{"@type": "Publication", "date": "{}"}}],
  "isPartOf": [{}]
}}
""".format

CONTRIBUTION = """
{{
    "@type": "Contribution",
    "agent": {{"@type": "Person", "familyName": "{}","givenName": "{}"}}
}}
""".format

AFFILIATION = """
{{
    "@type": "Organization",
    "name": "{}"
}}
""".format


HAS_SERIES = """
{{
    "@type": "Work",
    "hasTitle": [{{"@type": "Title", "mainTitle": "{}", "partNumber":"{}"}}],
    "identifiedBy": [{{"@type": "ISSN", "value": "{}"}}]
}}
""".format

ELECTRONIC_LOCATOR = """
{{
    "@type": "Resource",
    "uri": "{}",
    "hasNote": [{}]
}}
""".format


@pytest.fixture
def master():
    body = json.loads(BODY('i_am_master',
                           'Title 1',
                           'Subtitle 1',
                           'Summary 1',
                           '{"@type": "Topic", "code": "28177", "prefLabel": "prefLabel1", "language": {"code": "swe"}},'
                           '{"@type": "Topic", "prefLabel": "prefLabel2"}',
                           '{"@id": "https://id.kb.se/term/swepub/ArtisticWork"},'
                           '{"@id": "https://id.kb.se/term/swepub/output/artistic-work"}',
                           '{"@type": "CreatorCount", "label": "3"},'
                           '{"@type": "PublicationStatus", "@id": "https://id.kb.se/term/swepub/Published"},'
                           '{"@type": "Note", "label": "note1"},'
                           '{"@type": "Note", "label": "note2"}',
                           'DOI_1',
                           'PMID_1',
                           'ISI_1',
                           'SCOPUSID_1',
                           'ISBN1_1',
                           'URI_1',
                           'ISSN1_1',
                           '2016-02-01',
                           '{'
                           ' "identifiedBy": [{"@type": "ISSN", "value": "ispartof_1"}],'
                           ' "hasTitle": [{"@type": "Title", "mainTitle": "Beyond professional monologue", "subtitle": "rendering oppressed voices", "volumeNumber": "28", "issueNumber": "4"}],'
                           ' "hasSeries": [{"@type": "Work", "hasTitle": [{"@type": "Title", "mainTitle": "part_of_serie_title", "partNumber":"1"}]}]'
                           '}'
                           ))

    affiliation_asbjorg = json.loads(AFFILIATION('Umeå universitet, Institutionen för språkstudier'))
    contribution_asbjorg = json.loads(CONTRIBUTION('Asbjörg', 'Westum'))
    contribution_asbjorg['hasAffiliation'] = [affiliation_asbjorg]
    contribution_asbjorg['agent']['identifiedBy'] \
        = [{'@type': 'ORCID', 'value': 'ORCID_1'},
           {'@type': 'Local', 'value': 'nla', 'source': {'@type': 'Source', 'code': 'bth'}}]
    affiliation_kalle = json.loads(AFFILIATION('Ankeborg'))
    contribution_kalle = json.loads(CONTRIBUTION('Kalle', 'Kula'))
    contribution_kalle['hasAffiliation'] = [affiliation_kalle]
    body['instanceOf']['contribution'] = [contribution_asbjorg, contribution_kalle]
    has_series = json.loads(HAS_SERIES('hasSeriesTitle1', 'IssueNumber1', 'ISSN_1'))
    body['hasSeries'] = [has_series]
    electronic_locator = json.loads(
        ELECTRONIC_LOCATOR('http://electronic_locator_1', '{"@type": "Note", "label": "free"}'))
    body['electronicLocator'] = [electronic_locator]
    return Publication(body)


@pytest.fixture
def candidate1_same_title_and_same_doi():
    """Same Title and one ID (DOI) same as master"""
    body = json.loads(BODY('i_am_candiate_1',
                           'Title 1',
                           'Subtitle 1',
                           'Summary 1',
                           '{"@type": "Topic", "prefLabel": "prefLabel2"}',
                           '{"@id": "https://id.kb.se/term/swepub/ArtisticWork"},'
                           '{"@id": "https://id.kb.se/term/swepub/output/artistic-work"},'
                           '{"@id": "https://id.kb.se/term/swepub/Book"}',
                           '{"@type": "CreatorCount", "label": "1"},'
                           '{"@type": "PublicationStatus", "@id": "https://id.kb.se/term/swepub/UnPublished"},'
                           '{"@type": "Note", "label": "note1"},'
                           '{"@type": "Note", "label": "note3"}',
                           'DOI_1',
                           'PMID_2',
                           'ISI_2',
                           'SCOPUSID_2',
                           'ISBN2_1',
                           'URI_2',
                           'ISSN2_2',
                           '2016-02-01',
                           '{'
                           ' "identifiedBy": [{"@type": "ISSN", "value": "ispartof_2"}]'
                           '}'
                           ))

    affiliation_child = json.loads(AFFILIATION('Umeå universitet'))
    affiliation_child['identifiedBy'] = [{'@type': 'URI', 'source': {'@type': 'Source', 'code': 'kb.se'}}]
    affiliation_parent = json.loads(AFFILIATION('Institutionen för språkstudier'))
    affiliation_parent['identifiedBy'] = [{'@type': 'Local', 'source': {'@type': 'Source', 'code': 'umu.se'}}]
    affiliation_parent['hasAffiliation'] = [affiliation_child]
    contribution_asbjorg = json.loads(CONTRIBUTION('Asbjörg', 'Westum'))
    contribution_asbjorg['hasAffiliation'] = [affiliation_parent]
    contribution_asbjorg['agent']['identifiedBy'] \
        = [{'@type': 'ORCID', 'value': 'ORCID_2'},
           {'@type': 'Local', 'value': 'lavnik', 'source': {'@type': 'Source', 'code': 'hj'}}]
    body['instanceOf']['contribution'] = [contribution_asbjorg]
    has_series = json.loads(HAS_SERIES('hasSeriesTitle_not_the_same_as_master', 'IssueNumber1', 'ISSN_1'))
    body['hasSeries'] = [has_series]
    electronic_locator = json.loads(ELECTRONIC_LOCATOR(
        'http://electronic_locator_1', '{"@type": "Note", "noteType": "URL usage", "label": "primary"}'))
    body['electronicLocator'] = [electronic_locator]
    return Publication(body)


@pytest.fixture
def candidate2_different_title_and_same_pmid():
    """Different Title and one ID (PMID_1) same as master"""
    return Publication(json.loads(BODY('i_am_candiate_2',
                                       'I dont have same title',
                                       '',
                                       'I dont have same summary',
                                       '{"@type": "Topic", "code": "28177"}, {"@type": "Topic", "code": "28188"}',
                                       '{"@id": "https://id.kb.se/term/swepub/svep/vet"}',
                                       '',
                                       'DOI_3',
                                       'PMID_1',
                                       'ISI_3',
                                       'SCOPUSID_3',
                                       'ISBN3_1',
                                       'URI_3',
                                       'ISSN3_2',
                                       '2017',
                                       '{'
                                       ' "identifiedBy": [{"@type": "ISSN", "value": "ispartof_1"}, {"@type": "ISBN", "value": "ispartof_2"}, {"@type": "ISBN", "value": "ispartof_3"}],'
                                       ' "hasSeries": [{"@type": "Work", "hasTitle": [{"@type": "Title", "mainTitle": "differenet part_of_serie_title", "partNumber":"2"}]}]'

                                       '}'
                                       )))


@pytest.fixture
def candidate3_same_title_different_ids_summary():
    """Same Title and different ID fields (all), summary and pubdate than master"""
    return Publication(json.loads(BODY('i_am_candiate_3',
                                       'Title 1',
                                       'Subtitle 1',
                                       'Hello World',
                                       '{"@type": "Topic", "code": "28177"}, {"@type": "Topic", "code": "28188"}',
                                       '{'
                                       ' "@id": "https://id.kb.se/term/swepub/svep/vet",'
                                       ' "@id": "https://id.kb.se/term/swepub/ConferencePaper"'
                                       '}',
                                       '',
                                       'DOI_3',
                                       'PMID_3',
                                       'ISI_3',
                                       'SCOPUSID_3',
                                       'ISBN1_3',
                                       'URI_3',
                                       'ISSN2_3',
                                       '2018',
                                       '{'
                                       ' "identifiedBy": [{"@type": "ISSN", "value": "ispartof_2"}],'
                                       ' "hasTitle": [{"@type": "Title", "mainTitle": "ispartof_maintitle_not_the_same_as_master"}]'
                                       '}'
                                       )))


@pytest.fixture
def candidate4_same_title_summary_pub_date_but_different_ids():
    """Same Title, Subtitle, summary (lower case S), pubdate, genreform and different ID fields (all) than master"""
    body = json.loads(BODY('i_am_candiate_4',
                           'Title 1',
                           'Subtitle 1',
                           'Summary 1',
                           '{"@type": "Topic", "code": "28177", "prefLabel": "prefLabel1_eng", "language": {"code": "eng"}}',
                           '{"@id": "https://id.kb.se/term/swepub/ArtisticWork"},'
                           '{"@id": "https://id.kb.se/term/swepub/output/artistic-work"}',
                           '',
                           '',
                           'PMID_3',
                           'ISI_3',
                           'SCOPUSID_3',
                           'ISBN1_3',
                           'URI_3',
                           'ISSN2_3',
                           '2016',
                           '{'
                           ' "identifiedBy": [{"@type": "ISSN", "value": "ispartof_2"}],'
                           ' "hasTitle": [{"@type": "Title", "mainTitle": "Beyond Professional Monologue.", "subtitle": "Rendering Oppressed Voices", "volumeNumber": "28", "issueNumber": "4"}]'
                           '}'
                           ))
    has_series = json.loads(HAS_SERIES('hasSeriesTitle_not_the_same_as_master', 'IssueNumber2', 'ISSN_2'))
    body['hasSeries'] = [has_series]
    electronic_locator = json.loads(ELECTRONIC_LOCATOR(
        'http://electronic_locator_3', '{"@type": "Note", "label": "free"},'
                                       '{"@type": "Note", "noteType": "URL usage", "label": "primary"}'))
    body['electronicLocator'] = [electronic_locator]
    return Publication(body)


@pytest.fixture
def candidate5_updated_publication():
    body = json.loads(BODY('i_am_master',
                           'Title 1',
                           'Subtitle 1',
                           'Summary 1 - updated',
                           '{"@type": "Topic", "code": "28177", "prefLabel": "prefLabel1", "language": {"code": "swe"}},'
                           '{"@type": "Topic", "prefLabel": "prefLabel2"}',
                           '{"@id": "https://id.kb.se/term/swepub/ArtisticWork"},'
                           '{"@id": "https://id.kb.se/term/swepub/output/artistic-work"}',
                           '{"@type": "CreatorCount", "label": "3"},'
                           '{"@type": "PublicationStatus", "@id": "https://id.kb.se/term/swepub/Published"},'
                           '{"@type": "Note", "label": "note1"},'
                           '{"@type": "Note", "label": "note2"}',
                           'DOI_1',
                           'PMID_1',
                           'ISI_1',
                           'SCOPUSID_1',
                           'ISBN1_1',
                           'URI_1',
                           'ISSN1_1',
                           '2016-02-01',
                           '{'
                           ' "identifiedBy": [{"@type": "ISSN", "value": "ispartof_1"}],'
                           ' "hasTitle": [{"@type": "Title", "mainTitle": "Beyond professional monologue", "subtitle": "rendering oppressed voices", "volumeNumber": "28", "issueNumber": "4"}],'
                           ' "hasSeries": [{"@type": "Work", "hasTitle": [{"@type": "Title", "mainTitle": "part_of_serie_title", "partNumber":"1"}]}]'
                           '}'
                           ))

    affiliation_asbjorg = json.loads(AFFILIATION('Umeå universitet, Institutionen för språkstudier'))
    contribution_asbjorg = json.loads(CONTRIBUTION('Asbjörg', 'Westum'))
    contribution_asbjorg['hasAffiliation'] = [affiliation_asbjorg]
    contribution_asbjorg['agent']['identifiedBy'] \
        = [{'@type': 'ORCID', 'value': 'ORCID_1'},
           {'@type': 'Local', 'value': 'nla', 'source': {'@type': 'Source', 'code': 'bth'}}]
    affiliation_kalle = json.loads(AFFILIATION('Ankeborg'))
    contribution_kalle = json.loads(CONTRIBUTION('Kalle', 'Kula'))
    contribution_kalle['hasAffiliation'] = [affiliation_kalle]
    body['instanceOf']['contribution'] = [contribution_asbjorg, contribution_kalle]
    has_series = json.loads(HAS_SERIES('hasSeriesTitle1', 'IssueNumber1', 'ISSN_1'))
    body['hasSeries'] = [has_series]
    electronic_locator = json.loads(
        ELECTRONIC_LOCATOR('http://electronic_locator_1', '{"@type": "Note", "label": "free"}'))
    body['electronicLocator'] = [electronic_locator]
    return Publication(body)


@pytest.fixture
def deleted():
    body = {"status": "deleted", "source_publication_id": "123"}
    return Publication(body)
