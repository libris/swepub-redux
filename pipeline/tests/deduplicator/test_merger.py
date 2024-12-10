from pipeline.publicationmerger import has_kb_se_affiliation
from pipeline.publicationmerger import has_affiliations
from pipeline.publicationmerger import PublicationMerger

from pipeline.publication import Publication
from pipeline.publication import Contribution
from pipeline.publication import IsPartOf

from pipeline.util import SWEPUB_CLASSIFIER_ID, SSIF_BASE

from flexmock import flexmock

merger = PublicationMerger()


def test_contribution_equality():
    master_contribution_kalle = _get_master_contribution_kalle()
    master_contribution_per = _get_master_contribution_per()
    candidate_contribution_per = _get_candidate_contribution_per()
    assert master_contribution_per == candidate_contribution_per
    assert not master_contribution_kalle == candidate_contribution_per


def test_merge_multiple_contributions():
    master_contribution_kalle = _get_master_contribution_kalle()
    master_contribution_per = _get_master_contribution_per()
    candidate_contribution_per = _get_candidate_contribution_per()
    mocked_master_contributions = flexmock(contributions=[master_contribution_per, master_contribution_kalle])
    mocked_candidate_contributions = flexmock(contributions=[candidate_contribution_per])
    merged_master = merger._merge_contribution(mocked_master_contributions, mocked_candidate_contributions)
    assert len(merged_master.contributions) == 2


def test_merge_contribution_identified_bys():
    master_contribution_per = _get_master_contribution_per()
    candidate_contribution_per = _get_candidate_contribution_per()
    mocked_master_contributions = flexmock(contributions=[master_contribution_per])
    mocked_candidate_contributions = flexmock(contributions=[candidate_contribution_per])
    merged_master = merger._merge_contribution(mocked_master_contributions, mocked_candidate_contributions)
    merged_contribution_per = merged_master.contributions[0]
    assert (merged_contribution_per.identified_bys) == [
        {'@type': 'Local', 'value': 'perlan', 'source': {'@type': 'Source', 'code': 'hig'}},
        {'@type': 'ORCID', 'value': 'ORCID_1'},
        {'@type': 'Local', 'value': 'perlan', 'source': {'@type': 'Source', 'code': 'chalmers.se'}},
        {'@type': 'ORCID', 'value': 'ORCID_2'}
    ]


def test_merge_contribution_affiliations():
    master_contribution_per = _get_master_contribution_per()
    candidate_contribution_per = _get_candidate_contribution_per()
    mocked_master_contributions = flexmock(contributions=[master_contribution_per])
    mocked_candidate_contributions = flexmock(contributions=[candidate_contribution_per])
    merged_master = merger._merge_contribution(mocked_master_contributions, mocked_candidate_contributions)
    merged_contribution_per = merged_master.contributions[0]
    assert merged_contribution_per.affiliations == _get_expected_merged_contribution_per().affiliations


def test_merge_contribution_affiliations_no_master_affiliations():
    master_contribution_kalle = _get_master_contribution_kalle()
    candidate_contribution_kalle = _get_candidate_contribution_kalle()
    assert not has_affiliations(master_contribution_kalle)
    assert has_affiliations(candidate_contribution_kalle)
    mocked_master_contributions = flexmock(contributions=[master_contribution_kalle])
    mocked_candidate_contributions = flexmock(contributions=[candidate_contribution_kalle])
    merged_master = merger._merge_contribution(mocked_master_contributions, mocked_candidate_contributions)
    merged_contribution_kalle = merged_master.contributions[0]
    assert merged_contribution_kalle.affiliations == candidate_contribution_kalle.affiliations


def test_merge_contribution_affiliations_no_master_kb_affiliations():
    master_contribution_kalle = _get_master_contribution_kalle()
    master_contribution_kalle.affiliations = [
        {
            '@type': 'Organization',
            'name': 'University of Ankeborg',
            'language': {
                '@type': 'Language',
                '@id': 'https://id.kb.se/language/eng',
                'code': 'eng'
            },
            'identifiedBy': [
                {
                    '@type': 'Local',
                    'value': 'Ankdammen',
                    'source': {
                        '@type': 'Source',
                        'code': 'jag_ar_inte_kb_se'
                    }
                }
            ]
        }
    ]
    candidate_contribution_kalle = _get_candidate_contribution_kalle()
    assert not has_kb_se_affiliation(master_contribution_kalle)
    assert has_kb_se_affiliation(candidate_contribution_kalle)
    mocked_master_contributions = flexmock(contributions=[master_contribution_kalle])
    mocked_candidate_contributions = flexmock(contributions=[candidate_contribution_kalle])
    merged_master = merger._merge_contribution(mocked_master_contributions, mocked_candidate_contributions)
    merged_contribution_kalle = merged_master.contributions[0]
    assert merged_contribution_kalle.affiliations == candidate_contribution_kalle.affiliations


def test_merge_localid_from_candidate():
    master_without_localid = _get_master_contribution_kalle_without_localid()
    candidate_with_localid = _get_candidate_contribution_kalle_with_localid()

    mocked_master_contributions = flexmock(contributions=[master_without_localid])
    mocked_candidate_contributions = flexmock(contributions=[candidate_with_localid])
    merged_master = merger._merge_contribution(mocked_master_contributions, mocked_candidate_contributions)
    assert len(merged_master.contributions) == 1
    assert merged_master.contributions[0].identified_bys == [
        {'@type': 'ORCID', 'value': 'https://orcid.org/0000-0003-0229-9999'},
        {'@type': 'Local', 'value': 'foobar', 'source': {'@type': 'Source', 'code': 'kth'}}
    ]


def test_merge_has_notes_publication_status_unchanged():
    published_publication = Publication(
        {'instanceOf': {'hasNote': [
            {'@type': 'PublicationStatus', '@id': 'https://id.kb.se/term/swepub/Published'},
            {'@type': 'CreatorCount', 'label': '3'},
            {'@type': 'Note', 'label': 'note1'},
            {'@type': 'Note', 'label': 'note2'},
        ]}})

    online_first_publication = Publication(
        {'instanceOf': {'hasNote': [
            {'@type': 'PublicationStatus', '@id': 'https://id.kb.se/term/swepub/EpubAheadOfPrint/OnlineFirst'},
            {'@type': 'CreatorCount', 'label': '2'},
            {'@type': 'Note', 'label': 'note2'},
            {'@type': 'Note', 'label': 'note3'},
        ]}})
    merged_master = merger._merge_has_notes(published_publication, online_first_publication)
    assert merged_master.publication_status == 'https://id.kb.se/term/swepub/Published'
    assert merged_master.creator_count == 3
    assert set(merged_master.notes) == {'note1', 'note2', 'note3'}


def test_merge_has_notes_publication_status_changed():
    published_publication = Publication(
        {'instanceOf': {'hasNote': [
            {'@type': 'PublicationStatus', '@id': 'https://id.kb.se/term/swepub/Published'},
            {'@type': 'CreatorCount', 'label': '3'},
            {'@type': 'Note', 'label': 'note1'},
            {'@type': 'Note', 'label': 'note2'},
        ]}})

    online_first_publication = Publication(
        {'instanceOf': {'hasNote': [
            {'@type': 'PublicationStatus', '@id': 'https://id.kb.se/term/swepub/EpubAheadOfPrint/OnlineFirst'},
            {'@type': 'CreatorCount', 'label': '2'},
            {'@type': 'Note', 'label': 'note2'},
            {'@type': 'Note', 'label': 'note3'},
        ]}})
    merged_master = merger._merge_has_notes(online_first_publication, published_publication)
    assert merged_master.publication_status == 'https://id.kb.se/term/swepub/Published'
    assert merged_master.creator_count == 2
    assert set(merged_master.notes) == {'note1', 'note2', 'note3'}


def test_merge_has_notes_publication_status_unknown():
    online_first_publication = Publication(
        {'instanceOf': {'hasNote': [
            {'@type': 'PublicationStatus', '@id': 'https://id.kb.se/term/swepub/EpubAheadOfPrint/OnlineFirst'},
            {'@type': 'CreatorCount', 'label': '2'},
            {'@type': 'Note', 'label': 'note1'},
            {'@type': 'Note', 'label': 'note2'},
        ]}})
    unknown_publication = Publication(
        {'instanceOf': {'hasNote': [
            {'@type': 'PublicationStatus', '@id': 'https://id.kb.se/term/swepub/FINNS_INTE'},
            {'@type': 'CreatorCount', 'label': '2'},
            {'@type': 'Note', 'label': 'note3'},
            {'@type': 'Note', 'label': 'note4'},
        ]}})
    merged_master = merger._merge_has_notes(online_first_publication, unknown_publication)
    assert merged_master.publication_status == 'https://id.kb.se/term/swepub/EpubAheadOfPrint/OnlineFirst'
    assert merged_master.creator_count == 2
    assert set(merged_master.notes) == {'note1', 'note2', 'note3', 'note4'}


def test_merge_genre_form(master, candidate1_same_title_and_same_doi):
    merged_master = merger._merge_genre_forms(master, candidate1_same_title_and_same_doi)
    assert set(merged_master.genre_form) == {'https://id.kb.se/term/swepub/ArtisticWork',
                                             'https://id.kb.se/term/swepub/output/artistic-work',
                                             'https://id.kb.se/term/swepub/Book'}


def test_merge_subjects(master, candidate1_same_title_and_same_doi,
                        candidate4_same_title_summary_pub_date_but_different_ids):
    merged_master = merger._merge_subjects(master, candidate1_same_title_and_same_doi)
    assert len(merged_master.subjects) == 2
    assert {'@type': 'Topic', 'code': '28177', 'prefLabel': 'prefLabel1', 'language': {'code': 'swe'}} \
        in merged_master.subjects
    assert {'@type': 'Topic', 'prefLabel': 'prefLabel2'} in merged_master.subjects
    merged_master = merger._merge_subjects(master, candidate4_same_title_summary_pub_date_but_different_ids)
    assert len(merged_master.subjects) == 3
    assert {'@type': 'Topic', 'code': '28177', 'prefLabel': 'prefLabel1', 'language': {'code': 'swe'}} \
        in merged_master.subjects
    assert {'@type': 'Topic', 'prefLabel': 'prefLabel2'} in merged_master.subjects
    assert {'@type': 'Topic', 'code': '28177', 'prefLabel': 'prefLabel1_eng', 'language': {'code': 'eng'}} \
        in merged_master.subjects


def test_merge_classifications():
    master = Publication({
        "instanceOf": {
            "classification": [
                {
                    "@id": f"{SSIF_BASE}10606",
                    "@type": "Classification",
                    "prefLabelByLang": {"en": "Microbiology", "sv": "Mikrobiologi"}
                },
                {
                    "@id": f"{SSIF_BASE}10203",
                    "@type": "Classification",
                    "prefLabelByLang": {"en": "Bioinformatics", "sv": "Bioinformatik"}
                }
            ]
        }
    })

    candidate = Publication({
        "instanceOf": {
            "classification": [
                {
                    "@id": f"{SSIF_BASE}10606",
                    "@type": "Classification",
                    "prefLabelByLang": {"en": "Microbiology", "sv": "Mikrobiologi"}
                },
                {
                    "@id": f"{SSIF_BASE}30102",
                    "@type": "Classification",
                    "prefLabelByLang": {"en": "Pharmacology and Toxicology", "sv": "Farmakologi och toxikologi"}
                }
            ]
        }
    })

    merged_master = merger._merge_classifications(master, candidate)

    assert len(merged_master.classifications) == 3

    assert merged_master.classifications == [
        {
            "@id": f"{SSIF_BASE}10606",
            "@type": "Classification",
            "prefLabelByLang": {"en": "Microbiology", "sv": "Mikrobiologi"}
        },
        {
            "@id": f"{SSIF_BASE}10203",
            "@type": "Classification",
            "prefLabelByLang": {"en": "Bioinformatics", "sv": "Bioinformatik"}
        },
        {
            "@id": f"{SSIF_BASE}30102",
            "@type": "Classification",
            "prefLabelByLang": {"en": "Pharmacology and Toxicology", "sv": "Farmakologi och toxikologi"}
        }
    ]

def test_merge_classifications_with_autoclassified_subject():
    master = Publication({
        "instanceOf": {
            "classification": [
                {
                    "@id": f"{SSIF_BASE}10606",
                    "@type": "Classification",
                    "prefLabelByLang": {"en": "Microbiology", "sv": "Mikrobiologi"}
                },
                {
                    "@id": f"{SSIF_BASE}10203",
                    "@type": "Classification",
                    "prefLabelByLang": {"en": "Bioinformatics", "sv": "Bioinformatik"}
                }
            ]
        }
    })

    # Since the master publication is classified, *not* autoclassified, and the candidate has
    # an autoclassified term, the autoclassified term should be dropped when merging.
    candidate = Publication({
        "instanceOf": {
            "classification": [
                {
                    "@id": f"{SSIF_BASE}30105",
                    "@type": "Classification",
                    "prefLabelByLang": {"en": "Neurosciences", "sv": "Neurovetenskaper"},
                    "@annotation": {"assigner": {"@id": SWEPUB_CLASSIFIER_ID}}
                },
                {
                    "@id": f"{SSIF_BASE}30102",
                    "@type": "Classification",
                    "prefLabelByLang": {"en": "Pharmacology and Toxicology", "sv": "Farmakologi och toxikologi"}
                }
            ]
        }
    })

    merged_master = merger._merge_classifications(master, candidate)

    assert len(merged_master.classifications) == 3

    assert merged_master.classifications == [
        {
            "@id": f"{SSIF_BASE}10606",
            "@type": "Classification",
            "prefLabelByLang": {"en": "Microbiology", "sv": "Mikrobiologi"}
        },
        {
            "@id": f"{SSIF_BASE}10203",
            "@type": "Classification",
            "prefLabelByLang": {"en": "Bioinformatics", "sv": "Bioinformatik"}
        },
        {
            "@id": f"{SSIF_BASE}30102",
            "@type": "Classification",
            "prefLabelByLang": {"en": "Pharmacology and Toxicology", "sv": "Farmakologi och toxikologi"}
        }
    ]

def test_merge_has_series(master, candidate1_same_title_and_same_doi):
    merged_master = merger._merge_has_series(master, candidate1_same_title_and_same_doi)
    assert len(merged_master.has_series) == 1
    has_series_master = master.has_series[0]
    has_series_merged_master = merged_master.has_series[0]
    assert has_series_master == has_series_merged_master
    assert has_series_master.main_title == has_series_merged_master.main_title
    assert has_series_master.issn == has_series_merged_master.issn
    assert has_series_master.issue_number == has_series_merged_master.issue_number


def test_merge_has_no_series(master, candidate1_same_title_and_same_doi):
    del master.body['hasSeries']
    del candidate1_same_title_and_same_doi.body['hasSeries']
    merged_master = merger._merge_has_series(master, candidate1_same_title_and_same_doi)
    exists = merged_master.body.get('hasSeries', 'does not exist')
    assert exists == 'does not exist'


def test_merge_identifiedby_ids(master, candidate1_same_title_and_same_doi):
    merged_master = merger._merge_identifiedby_ids(master, candidate1_same_title_and_same_doi)
    assert len(master.identifiedby_ids) == 8
    assert {'@type': 'DOI', 'value': 'DOI_1'} in merged_master.identifiedby_ids
    assert {'@type': 'PMID', 'value': 'PMID_1'} in merged_master.identifiedby_ids
    assert {'@type': 'ISI', 'value': 'ISI_1'} in merged_master.identifiedby_ids
    assert {'@type': 'ScopusID', 'value': 'SCOPUSID_1'} in merged_master.identifiedby_ids
    assert {'@type': 'ISBN', 'value': 'ISBN1_1'} in merged_master.identifiedby_ids
    assert {'@type': 'ISBN', 'value': 'ISBN2_1'} in merged_master.identifiedby_ids
    assert {'@type': 'URI', 'value': 'URI_1'} in merged_master.identifiedby_ids
    assert {'@type': 'URI', 'value': 'URI_2'} in merged_master.identifiedby_ids


def test_merge_identifiedby_ids_qualifier():
    master = Publication({
        "identifiedBy": [
            {"@type": "ISBN", "value": "9789144137605"},
            {"@type": "URI", "value": "https://www.example.com/foobar"}
        ]
    })
    candidate = Publication({
        "identifiedBy": [
            {"@type": "ISBN", "value": "9789144137605", "qualifier": "print"}
        ]
    })
    merged_master = merger._merge_identifiedby_ids(master, candidate)
    assert len(merged_master.identifiedby_ids) == 2
    assert merged_master.identifiedby_ids == [
        {"@type": "ISBN", "value": "9789144137605", "qualifier": "print"},
        {"@type": "URI", "value": "https://www.example.com/foobar"}
    ]


def test_merge_indirectly_identifiedby_ids(master, candidate1_same_title_and_same_doi):
    merged_master = merger._merge_indirectly_identifiedby_ids(master, candidate1_same_title_and_same_doi)
    assert len(master.indirectly_identifiedby_ids) == 2
    assert {'@type': 'ISSN', 'value': 'ISSN1_1'} in merged_master.indirectly_identifiedby_ids
    assert {'@type': 'ISSN', 'value': 'ISSN2_2'} in merged_master.indirectly_identifiedby_ids


def test_merge_electronic_locator_same_locator(master, candidate1_same_title_and_same_doi):
    merged_master = merger._merge_electronic_locators(master, candidate1_same_title_and_same_doi)
    assert len(merged_master.electronic_locators) == 1
    electronic_locator = merged_master.electronic_locators[0]
    assert electronic_locator.type == 'Resource'
    assert electronic_locator.uri == 'http://electronic_locator_1'
    assert electronic_locator.notes == [{"@type": "Note", "label": "free"},
                                        {"@type": "Note", "noteType": "URL usage", "label": "primary"}]


def test_merge_electronic_locator_different_locator(master, candidate4_same_title_summary_pub_date_but_different_ids):
    merged_master = merger._merge_electronic_locators(master, candidate4_same_title_summary_pub_date_but_different_ids)
    assert len(merged_master.electronic_locators) == 2
    electronic_locator_master = merged_master.electronic_locators[0]
    assert electronic_locator_master.type == 'Resource'
    assert electronic_locator_master.uri == 'http://electronic_locator_1'
    assert electronic_locator_master.notes == [{"@type": "Note", "label": "free"}]
    electronic_locator_candidate4 = merged_master.electronic_locators[1]
    assert electronic_locator_candidate4.type == 'Resource'
    assert electronic_locator_candidate4.uri == 'http://electronic_locator_3'
    assert electronic_locator_candidate4.notes == [{"@type": "Note", "label": "free"},
                                                   {"@type": "Note", "noteType": "URL usage", "label": "primary"}]


def test_merge_is_part_of(master, candidate2_different_title_and_same_pmid,
                       candidate3_same_title_different_ids_summary):
    is_part_of_master = master.is_part_of[0]
    assert len(is_part_of_master.has_series) == 1
    is_part_of_candidate2 = candidate2_different_title_and_same_pmid.is_part_of[0]
    assert len(is_part_of_candidate2.has_series) == 1
    merged_master = merger._merge_is_part_of(master, candidate2_different_title_and_same_pmid)
    assert len(merged_master.is_part_of) == 1
    merged_master_is_part_of = merged_master.is_part_of[0]
    assert len(merged_master_is_part_of.has_series) == 2
    assert is_part_of_master.has_series[0] in merged_master_is_part_of.has_series
    assert is_part_of_candidate2.has_series[0] in merged_master_is_part_of.has_series

    is_part_of_candidate3 = candidate3_same_title_different_ids_summary.is_part_of[0]
    assert is_part_of_master != is_part_of_candidate3
    merged_master = merger._merge_is_part_of(master, candidate3_same_title_different_ids_summary)
    assert len(merged_master.is_part_of) == 2
    assert is_part_of_master in merged_master.is_part_of
    assert is_part_of_candidate3 in merged_master.is_part_of


def test_merge_is_part_of_if_title_and_subtitle_are_similar():
    is_part_of_master = _get_master_is_part_of()

    is_part_of_candidate = IsPartOf({
        'identifiedBy': [{'@type': 'ISSN', 'value': 'ispartof_2'}],
        'hasTitle': [{'@type': 'Title', 'mainTitle': 'beyond professional Monologue.',
                      'subtitle': 'Rendering Oppressed Voices', 'volumeNumber': '28', 'issueNumber': '4'}],
    })
    # Same is_part_ofs since mainTitle, subtitle, volume_number and issue_number are the same
    assert is_part_of_master == is_part_of_candidate
    mocked_master_publication = flexmock(is_part_of=[is_part_of_master])
    mocked_candidate_publication = flexmock(is_part_of=[is_part_of_candidate])
    merged_master = merger._merge_is_part_of(mocked_master_publication, mocked_candidate_publication)
    assert len(merged_master.is_part_of) == 1
    is_part_of_merged_master = merged_master.is_part_of[0]
    assert is_part_of_master.main_title == is_part_of_merged_master.main_title
    assert is_part_of_master.sub_title == is_part_of_merged_master.sub_title
    assert not is_part_of_candidate.main_title == is_part_of_merged_master.main_title
    assert not is_part_of_candidate.sub_title == is_part_of_merged_master.main_title


def test_merge_is_part_of_not_merged_when_title_differ():
    is_part_of_master = _get_master_is_part_of()
    is_part_of_candidate_different_title = IsPartOf({
        'identifiedBy': [{'@type': 'ISSN', 'value': 'ispartof_2'}],
        'hasTitle': [{'@type': 'Title', 'mainTitle': 'Before amateur dialogue.',
                      'subtitle': 'Rendering Oppressed Voices', 'volumeNumber': '28', 'issueNumber': '4'}],
    })
    # Different is_part_ofs since mainTitle not the same
    assert is_part_of_master != is_part_of_candidate_different_title
    mocked_master_publication = flexmock(is_part_of=[is_part_of_master])
    mocked_candidate_publication = flexmock(is_part_of=[is_part_of_candidate_different_title])
    merged_master = merger._merge_is_part_of(mocked_master_publication, mocked_candidate_publication)
    assert len(merged_master.is_part_of) == 2
    is_part_of_1_merged_master = merged_master.is_part_of[0]
    is_part_of_2_merged_master = merged_master.is_part_of[1]
    assert is_part_of_master.main_title == is_part_of_1_merged_master.main_title
    assert is_part_of_master.sub_title == is_part_of_1_merged_master.sub_title
    assert is_part_of_candidate_different_title.main_title == is_part_of_2_merged_master.main_title
    assert is_part_of_candidate_different_title.sub_title == is_part_of_2_merged_master.sub_title


def test_merge_is_part_of_identified_bys():
    is_part_of_master = _get_master_is_part_of()
    is_part_of_candidate_additional_identified_bys = IsPartOf({
        'identifiedBy': [{'@type': 'ISSN', 'value': 'ispartof_1', 'qualifier': 'print'},
                         {'@type': 'ISSN', 'value': 'ispartof_2'},
                         {'@type': 'ISBN', 'value': 'isbn_1'}],
        'hasTitle': [{'@type': 'Title', 'mainTitle': 'Before amateur dialogue.',
                      'subtitle': 'Rendering Oppressed Voices', 'volumeNumber': '28', 'issueNumber': '4'}],
    })
    # Same is_part_ofs since issn ispartof_1 are the same
    assert is_part_of_master == is_part_of_candidate_additional_identified_bys
    mocked_master_publication = flexmock(is_part_of=[is_part_of_master])
    mocked_candidate_publication = flexmock(is_part_of=[is_part_of_candidate_additional_identified_bys])
    merged_master = merger._merge_is_part_of(mocked_master_publication, mocked_candidate_publication)
    assert len(merged_master.is_part_of) == 1
    is_part_of_merged_master = merged_master.is_part_of[0]
    assert {'@type': 'ISSN', 'value': 'ispartof_1', 'qualifier': 'print'} in is_part_of_merged_master.body['identifiedBy']
    assert {'@type': 'ISSN', 'value': 'ispartof_2'} in is_part_of_merged_master.body['identifiedBy']
    # assert {'@type': 'ISBN', 'value': 'isbn_1'} in is_part_of_merged_master.issns


def test_merge_is_part_of_has_series_same_title():
    is_part_of_master = _get_master_is_part_of()
    is_part_of_candidate_same_hasseries_title = IsPartOf({
        'identifiedBy': [{'@type': 'ISSN', 'value': 'ispartof_2'}],
        'hasTitle': [{'@type': 'Title', 'mainTitle': 'Beyond professional monologue',
                      'subtitle': 'Rendering Oppressed Voices', 'volumeNumber': '28', 'issueNumber': '4'}],
        'hasSeries': [{'@type': 'Work',
                       'hasTitle': [{'@type': 'Title', 'mainTitle': 'is_part_of_serie_title_master'}]}]
    })
    # Same is_part_ofs since mainTitle, subtitle, volume_number and issue_number are the same
    assert is_part_of_master == is_part_of_candidate_same_hasseries_title
    mocked_master_publication = flexmock(is_part_of=[is_part_of_master])
    mocked_candidate_publication = flexmock(is_part_of=[is_part_of_candidate_same_hasseries_title])
    merged_master = merger._merge_is_part_of(mocked_master_publication, mocked_candidate_publication)
    assert len(merged_master.is_part_of) == 1
    is_part_of_merged_master = merged_master.is_part_of[0]
    # Same hasSerie (isPartOf) since same mainTitle
    assert len(is_part_of_merged_master.has_series) == 1
    is_part_of_merged_master_has_series = is_part_of_merged_master.has_series[0]
    assert is_part_of_master.has_series[0].main_title == is_part_of_merged_master_has_series.main_title


def test_merge_is_part_of_has_series_same_issn():
    is_part_of_master = _get_master_is_part_of()
    is_part_of_candidate_same_hasseries_issn_and_issue_number = IsPartOf({
        'identifiedBy': [{'@type': 'ISSN', 'value': 'ispartof_2'}],
        'hasTitle': [{'@type': 'Title', 'mainTitle': 'Beyond professional monologue',
                      'subtitle': 'Rendering Oppressed Voices', 'volumeNumber': '28', 'issueNumber': '4'}],
        'hasSeries': [{'@type': 'Work',
                       'hasTitle': [{'@type': 'Title', 'mainTitle': 'is_part_of_serie_title_candidate',
                                     'partNumber': 'issue_numer_1'}],
                       'identifiedBy': [{'@type': 'ISSN', 'value': 'has_serie_issn_1'}]
                       }
                      ]
    })
    # Same is_part_ofs since mainTitle, subtitle, volume_number and issue_number are the same
    assert is_part_of_master == is_part_of_candidate_same_hasseries_issn_and_issue_number
    mocked_master_publication = flexmock(is_part_of=[is_part_of_master])
    mocked_candidate_publication = flexmock(is_part_of=[is_part_of_candidate_same_hasseries_issn_and_issue_number])
    merged_master = merger._merge_is_part_of(mocked_master_publication, mocked_candidate_publication)
    assert len(merged_master.is_part_of) == 1
    is_part_of_merged_master = merged_master.is_part_of[0]
    # Same hasSerie (isPartOf) since same same issn (different mainTitle)
    assert len(is_part_of_merged_master.has_series) == 1
    is_part_of_merged_master_has_series = is_part_of_merged_master.has_series[0]
    assert is_part_of_master.has_series[0].main_title == is_part_of_merged_master_has_series.main_title


def test_merge_is_part_of_has_series_not_merged_when_title_and_issn_differ():
    is_part_of_master = _get_master_is_part_of()
    is_part_of_candidate_different_hasseries_issn = IsPartOf({
        'identifiedBy': [{'@type': 'ISSN', 'value': 'ispartof_2'}],
        'hasTitle': [{'@type': 'Title', 'mainTitle': 'Beyond professional monologue',
                      'subtitle': 'Rendering Oppressed Voices', 'volumeNumber': '28', 'issueNumber': '4'}],
        'hasSeries': [{'@type': 'Work',
                       'hasTitle': [{'@type': 'Title', 'mainTitle': 'is_part_of_serie_title_candidate',
                                     'partNumber': 'issue_numer_1'}],
                       'identifiedBy': [{'@type': 'ISSN', 'value': 'has_serie_issn_2'}]
                       }
                      ]
    })
    # Same is_part_ofs since mainTitle, subtitle, volume_number and issue_number are the same
    assert is_part_of_master == is_part_of_candidate_different_hasseries_issn
    mocked_master_publication = flexmock(is_part_of=[is_part_of_master])
    mocked_candidate_publication = flexmock(is_part_of=[is_part_of_candidate_different_hasseries_issn])
    merged_master = merger._merge_is_part_of(mocked_master_publication, mocked_candidate_publication)
    assert len(merged_master.is_part_of) == 1
    is_part_of_merged_master = merged_master.is_part_of[0]
    assert len(is_part_of_merged_master.has_series) == 2
    assert is_part_of_master.has_series[0].main_title == is_part_of_merged_master.has_series[0].main_title
    assert is_part_of_candidate_different_hasseries_issn.has_series[0].main_title == is_part_of_merged_master.has_series[1].main_title


def test_merge_publication_information_place_from_candidate():
    master_with_agent_only = Publication(
        {'publication': [{'@type': 'Publication',
                          'agent': {'@type': 'Agent', 'label': 'Master Agent'},
                          'date': '2011'}
                         ]})
    candidate_with_place_only = Publication(
        {'publication': [{'@type': 'Publication',
                          'place': {'@type': 'Place', 'label': 'Candidate Place'},
                          'date': '2011'}
                         ]})
    merged_master = merger._merge_publication_information(master_with_agent_only, candidate_with_place_only)
    assert merged_master.publication_information.agent == {'@type': 'Agent', 'label': 'Master Agent'}
    assert merged_master.publication_information.place == {'@type': 'Place', 'label': 'Candidate Place'}


def test_merge_publication_information_agent_from_candidate():
    master_without_agent_and_place = Publication(
        {'publication': [{'@type': 'Publication',
                          'date': '2011'}
                         ]})

    candidate_with_agent_only = Publication(
        {'publication': [{'@type': 'Publication',
                          'agent': {'@type': 'Agent', 'label': 'Candidate Agent'},
                          'date': '2011'}
                         ]})
    merged_master = merger._merge_publication_information(master_without_agent_and_place, candidate_with_agent_only)
    assert merged_master.publication_information.agent == {'@type': 'Agent', 'label': 'Candidate Agent'}
    assert merged_master.publication_information.place is None


def test_merge_publication_information_no_agent_and_no_place_in_both():
    master_without_agent_and_place = Publication(
        {'provisionActivity': [{'@type': 'Publication',
                                'date': '2011'}
                               ]})

    candidate_without_agent_and_place = Publication(
        {'provisionActivity': [{'@type': 'Publication',
                                'date': '2011'}
                               ]})
    merged_master = merger._merge_publication_information(master_without_agent_and_place,
                                                          candidate_without_agent_and_place)

    assert merged_master.publication_information is None


def test_merge_publication_information_agent_and_place_in_master():
    master_with_both_agent_and_place = Publication(
        {'publication': [{'@type': 'Publication',
                          'agent': {'@type': 'Agent', 'label': 'Master Agent'},
                          'place': {'@type': 'Place', 'label': 'Master Place'},
                          'date': '2011'}
                         ]})
    candidate_with_both_agent_and_place = Publication(
        {'publication': [{'@type': 'Publication',
                          'agent': {'@type': 'Agent', 'label': 'Candidate Agent'},
                          'place': {'@type': 'Place', 'label': 'Candidate Place'},
                          'date': '2011'}
                         ]})
    merged_master = merger._merge_publication_information(master_with_both_agent_and_place,
                                                          candidate_with_both_agent_and_place)
    assert merged_master.publication_information.agent == {'@type': 'Agent', 'label': 'Master Agent'}
    assert merged_master.publication_information.place == {'@type': 'Place', 'label': 'Master Place'}


def test_merge_usage_and_access_policy():
    master_policies = [
        {"@type": "Embargo", "endDate": "2020-01-01"},
        {"@type": "AccessPolicy", "label": "restricted"}
    ]
    master = Publication({"usageAndAccessPolicy": master_policies})
    candidate_policies = [
        {"@id": "https://example.com"},
        {"@type": "AccessPolicy", "label": "gratis"},
        {"@type": "Embargo", "endDate": "2019-01-01"},
        {"@type": "AccessPolicy", "label": "restricted"}
    ]
    candidate = Publication({"usageAndAccessPolicy": candidate_policies})
    expected = [
        {"@type": "AccessPolicy", "label": "gratis"},
        {"@type": "AccessPolicy", "label": "restricted"},
        {"@type": "Embargo", "endDate": "2020-01-01"},
        {"@id": "https://example.com"}
    ]

    merged_master = merger._merge_usage_and_access_policy(master, candidate)
    assert expected == merged_master.usage_and_access_policy


def test_merge_copyright_from_candidate():
    master_without_copyright = Publication({})
    candidate_with_copyright = Publication({'copyright': [{'@type': 'Copyright', 'date': '1999'}]})

    merged_master = merger._merge_copyright_date(master_without_copyright, candidate_with_copyright)
    assert merged_master.copyright_date == [{'@type': 'Copyright', 'date': '1999'}]


def test_merge_copyright_prefer_master():
    master_with_copyright = Publication({'copyright': [{'@type': 'Copyright', 'date': '2010'}]})
    candidate_with_copyright = Publication({'copyright': [{'@type': 'Copyright', 'date': '2020'}]})

    merged_master = merger._merge_copyright_date(master_with_copyright, candidate_with_copyright)
    assert merged_master.copyright_date == [{'@type': 'Copyright', 'date': '2010'}]


def _get_master_is_part_of():
    return IsPartOf({
        'identifiedBy': [{'@type': 'ISSN', 'value': 'ispartof_1'}],
        'hasTitle': [{'@type': 'Title', 'mainTitle': 'Beyond professional monologue',
                      'subtitle': 'rendering oppressed voices', 'volumeNumber': '28', 'issueNumber': '4'}],
        'hasSeries': [{'@type': 'Work',
                       'hasTitle': [{'@type': 'Title', 'mainTitle': 'is_part_of_serie_title_master',
                                     'partNumber': 'issue_numer_1'}],
                       'identifiedBy': [{'@type': 'ISSN', 'value': 'has_serie_issn_1'}]
                       }
                      ]
    })


def _get_master_contribution_per():
    return Contribution(
        {
            '@type': 'Contribution',
            'agent': {
                '@type': 'Person',
                'familyName': 'Landin',
                'givenName': 'Per',
                'identifiedBy': [
                    {
                        '@type': 'Local',
                        'value': 'perlan',
                        'source': {
                            '@type': 'Source',
                            'code': 'hig'
                        }
                    },
                    {
                        '@type': 'ORCID',
                        'value': 'ORCID_1'
                    }
                ]
            },
            'role': [
                {
                    '@id': 'http://id.loc.gov/vocabulary/relators/aut'
                }
            ],
            'hasAffiliation': [
                {
                    '@type': 'Organization',
                    'name': 'Elektronik',
                    'language': {
                        '@type': 'Language',
                        '@id': 'https://id.kb.se/language/swe',
                        'code': 'swe'
                    },
                    'identifiedBy': [
                        {
                            '@type': 'Local',
                            'value': 'Elektronik',
                            'source': {
                                '@type': 'Source',
                                'code': 'hig.se'
                            }
                        }
                    ],
                    'hasAffiliation': [
                        {
                            '@type': 'Organization',
                            'name': 'Högskolan i Gävle',
                            'language': {
                                '@type': 'Language',
                                '@id': 'https://id.kb.se/language/swe',
                                'code': 'swe'
                            },
                            'identifiedBy': [
                                {
                                    '@type': 'URI',
                                    'value': 'hig.se',
                                    'source': {
                                        '@type': 'Source',
                                        'code': 'kb.se'
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    '@type': 'Organization',
                    'name': 'Chalmers'
                }
            ]
        },
    )


def _get_candidate_contribution_per():
    return Contribution(
        {
            '@type': 'Contribution',
            'agent': {
                '@type': 'Person',
                'givenName': 'Per',
                'familyName': 'Landin',
                'lifeSpan': '1983',
                'identifiedBy': [
                    {
                        '@type': 'Local',
                        'value': 'perlan',
                        'source': {
                            '@type': 'Source',
                            'code': 'chalmers.se'
                        }
                    },
                    {
                        '@type': 'ORCID',
                        'value': 'ORCID_1'
                    },
                    {
                        '@type': 'ORCID',
                        'value': 'ORCID_2'
                    }
                ]
            },
            'role': [
                {
                    '@id': 'http://id.loc.gov/vocabulary/relators/aut'
                }
            ],
            'hasAffiliation': [
                {
                    "@type": "Collaboration",
                    "name": "Affiliation Name",
                    "language": {
                        "@type": "Language",
                        "code": "eng",
                        "@id": "https://id.kb.se/language/eng"
                    },
                    "identifiedBy": [
                        {
                            "@type": "URI",
                            "value": "e-science.se"
                        }
                    ]
                },
                {
                    "@id": "https://id.kb.se/country/xxx"
                },
                {
                    '@type': 'Organization',
                    'name': 'Högskolan i Gävle',
                    'language': {
                        '@type': 'Language',
                        '@id': 'https://id.kb.se/language/swe',
                        'code': 'swe'
                    },
                    'identifiedBy': [
                        {
                            '@type': 'URI',
                            'value': 'hig.se',
                            'source': {
                                '@type': 'Source',
                                'code': 'kb.se'
                            }
                        }
                    ]
                },
                {
                    '@type': 'Organization',
                    'name': 'Chalmers tekniska högskola',
                    'language': {
                        '@type': 'Language',
                        '@id': 'https://id.kb.se/language/swe',
                        'code': 'swe'
                    },
                    'identifiedBy': [
                        {
                            '@type': 'URI',
                            'value': 'chalmers.se',
                            'source': {
                                '@type': 'Source',
                                'code': 'kb.se'
                            }
                        }
                    ]
                },
                {
                    '@type': 'Organization',
                    'name': 'University of Gävle',
                    'language': {
                        '@type': 'Language',
                        '@id': 'https://id.kb.se/language/eng',
                        'code': 'eng'
                    },
                    'identifiedBy': [
                        {
                            '@type': 'URI',
                            'value': 'hig.se',
                            'source': {
                                '@type': 'Source',
                                'code': 'kb.se'
                            }
                        }
                    ]
                },
                {
                    '@type': 'Organization',
                    'name': 'Chalmers University of Technology',
                    'language': {
                        '@type': 'Language',
                        '@id': 'https://id.kb.se/language/eng',
                        'code': 'eng'
                    },
                    'identifiedBy': [
                        {
                            '@type': 'URI',
                            'value': 'chalmers.se',
                            'source': {
                                '@type': 'Source',
                                'code': 'kb.se'
                            }
                        }
                    ]
                }
            ]
        })


def _get_expected_merged_contribution_per():
    return Contribution(
        {
            '@type': 'Contribution',
            'agent': {
                '@type': 'Person',
                'familyName': 'Landin',
                'givenName': 'Per',
                'identifiedBy': [
                    {
                        '@type': 'Local',
                        'value': 'perlan',
                        'source': {
                            '@type': 'Source',
                            'code': 'hig'
                        }
                    }
                ]
            },
            'role': [
                {
                    '@id': 'http://id.loc.gov/vocabulary/relators/aut'
                }
            ],
            'hasAffiliation': [
                {
                    '@type': 'Organization',
                    'name': 'Elektronik',
                    'language': {
                        '@type': 'Language',
                        '@id': 'https://id.kb.se/language/swe',
                        'code': 'swe'
                    },
                    'identifiedBy': [
                        {
                            '@type': 'Local',
                            'value': 'Elektronik',
                            'source': {
                                '@type': 'Source',
                                'code': 'hig.se'
                            }
                        }
                    ],
                    'hasAffiliation': [
                        {
                            '@type': 'Organization',
                            'name': 'Högskolan i Gävle',
                            'language': {
                                '@type': 'Language',
                                '@id': 'https://id.kb.se/language/swe',
                                'code': 'swe'
                            },
                            'identifiedBy': [
                                {
                                    '@type': 'URI',
                                    'value': 'hig.se',
                                    'source': {
                                        '@type': 'Source',
                                        'code': 'kb.se'
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    '@type': 'Organization',
                    'name': 'Chalmers'
                },
                {
                    "@type": "Collaboration",
                    "name": "Affiliation Name",
                    "language": {
                        "@type": "Language",
                        "code": "eng",
                        "@id": "https://id.kb.se/language/eng"
                    },
                    "identifiedBy": [
                        {
                            "@type": "URI",
                            "value": "e-science.se"
                        }
                    ]
                },
                {
                    "@id": "https://id.kb.se/country/xxx"
                },
                {
                    '@type': 'Organization',
                    'name': 'Högskolan i Gävle',
                    'language': {
                        '@type': 'Language',
                        '@id': 'https://id.kb.se/language/swe',
                        'code': 'swe'
                    },
                    'identifiedBy': [
                        {
                            '@type': 'URI',
                            'value': 'hig.se',
                            'source': {
                                '@type': 'Source',
                                'code': 'kb.se'
                            }
                        }
                    ]
                },
                {
                    '@type': 'Organization',
                    'name': 'Chalmers tekniska högskola',
                    'language': {
                        '@type': 'Language',
                        '@id': 'https://id.kb.se/language/swe',
                        'code': 'swe'
                    },
                    'identifiedBy': [
                        {
                            '@type': 'URI',
                            'value': 'chalmers.se',
                            'source': {
                                '@type': 'Source',
                                'code': 'kb.se'
                            }
                        }
                    ]
                },
                {
                    '@type': 'Organization',
                    'name': 'University of Gävle',
                    'language': {
                        '@type': 'Language',
                        '@id': 'https://id.kb.se/language/eng',
                        'code': 'eng'
                    },
                    'identifiedBy': [
                        {
                            '@type': 'URI',
                            'value': 'hig.se',
                            'source': {
                                '@type': 'Source',
                                'code': 'kb.se'
                            }
                        }
                    ]
                },
                {
                    '@type': 'Organization',
                    'name': 'Chalmers University of Technology',
                    'language': {
                        '@type': 'Language',
                        '@id': 'https://id.kb.se/language/eng',
                        'code': 'eng'
                    },
                    'identifiedBy': [
                        {
                            '@type': 'URI',
                            'value': 'chalmers.se',
                            'source': {
                                '@type': 'Source',
                                'code': 'kb.se'
                            }
                        }
                    ]
                }
            ]
        }
    )


def _get_master_contribution_kalle():
    return Contribution(
        {
            '@type': 'Contribution',
            'agent': {
                '@type': 'Person',
                'familyName': 'Kula',
                'givenName': 'Kalle',
                'identifiedBy': [
                    {
                        '@type': 'Local',
                        'value': 'kalkul',
                        'source': {
                            '@type': 'Source',
                            'code': 'ankeborg'
                        }
                    }
                ]
            },
            'role': [
                {
                    '@id': 'http://id.loc.gov/vocabulary/relators/aut'
                }
            ],
        },
    )


def _get_candidate_contribution_kalle():
    return Contribution(
        {
            '@type': 'Contribution',
            'agent': {
                '@type': 'Person',
                'familyName': 'Kula',
                'givenName': 'Kalle',
                'identifiedBy': [
                    {
                        '@type': 'Local',
                        'value': 'kalkul',
                        'source': {
                            '@type': 'Source',
                            'code': 'ankeborg'
                        }
                    }
                ]
            },
            'role': [
                {
                    '@id': 'http://id.loc.gov/vocabulary/relators/aut'
                }
            ],
            'hasAffiliation': [
                {
                    '@type': 'Organization',
                    'name': 'University of Gävle',
                    'language': {
                        '@type': 'Language',
                        '@id': 'https://id.kb.se/language/eng',
                        'code': 'eng'
                    },
                    'identifiedBy': [
                        {
                            '@type': 'URI',
                            'value': 'hig.se',
                            'source': {
                                '@type': 'Source',
                                'code': 'kb.se'
                            }
                        }
                    ]
                },
            ]
        },
    )


def _get_master_contribution_kalle_without_localid():
    return Contribution(
        {
            "@type": "Contribution",
            "agent": {
                "@type": "Person",
                "familyName": "Ninja",
                "givenName": "Kalle",
                "identifiedBy": [
                    {
                        "@type": "ORCID",
                        "value": "https://orcid.org/0000-0003-0229-9999"
                    }
                ]
            }
        }
    )


def _get_candidate_contribution_kalle_with_localid():
    return Contribution(
        {
            "@type": "Contribution",
            "agent": {
                "@type": "Person",
                "familyName": "Ninja",
                "givenName": "Kalle",
                "identifiedBy": [
                    {
                        "@type": "Local",
                        "value": "foobar",
                        "source": {
                            "@type": "Source",
                            "code": "kth"
                        }
                    },
                    {
                        "@type": "ORCID",
                        "value": "https://orcid.org/0000-0003-0229-9999"
                    }
                ]
            }
        }
    )
