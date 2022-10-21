from pipeline.publication import Contribution
from pipeline.publication import Publication
from pipeline.publication import HasSeries
from pipeline.publication import PartOfHasSeries
from pipeline.publication import PartOf
from pipeline.deduplicate import _has_same_publication_date
from pipeline.util import empty_string, has_same_ids


def test_get_id(master):
    assert master.id == 'i_am_master'


def test_main_title(master):
    assert master.main_title == 'Title 1'


def test_sub_title(master):
    assert master.sub_title == 'Subtitle 1'


def test_summary(master):
    assert master.summary == 'Summary 1'


def test_publication_date(master):
    assert master.publication_date == '2016-02-01'


def test_publication_date_old_version():
    entry = {
        "@type": "Publication",
        "date": "2020"
    }
    new_version = {
        "publication": [entry],
        "provisionActivity": [
            {
                "@type": "Availability",
                "date": "2021"
            }
        ]
    }
    new_pub = Publication(new_version)
    assert new_pub.publication_date == "2020"


def test_genre_form(master):
    assert set(master.genre_form) == {'https://id.kb.se/term/swepub/ArtisticWork',
                                      'https://id.kb.se/term/swepub/artistic-work'}
    master.add_genre_form(['https://somewhere'])
    assert set(master.genre_form) == {'https://id.kb.se/term/swepub/ArtisticWork',
                                      'https://id.kb.se/term/swepub/artistic-work',
                                      'https://somewhere'}
    master.add_genre_form(['https://id.kb.se/term/swepub/publication/book-chapter'])
    assert set(master.genre_form) == {'https://id.kb.se/term/swepub/ArtisticWork',
                                      'https://id.kb.se/term/swepub/artistic-work',
                                      'https://somewhere',
                                      'https://id.kb.se/term/swepub/publication/book-chapter'}


def test_has_same_title(master,
                        candidate1_same_title_and_same_doi,
                        candidate2_different_title_and_same_pmid,
                        candidate3_same_title_different_ids_summary,
                        candidate4_same_title_summary_pub_date_but_different_ids):
    assert master.has_same_main_title(candidate1_same_title_and_same_doi)
    assert not master.has_same_main_title(candidate2_different_title_and_same_pmid)
    assert master.has_same_main_title(candidate3_same_title_different_ids_summary)
    assert master.has_same_main_title(candidate4_same_title_summary_pub_date_but_different_ids)


def test_has_same_sub_title(master,
                            candidate1_same_title_and_same_doi,
                            candidate2_different_title_and_same_pmid,
                            candidate3_same_title_different_ids_summary,
                            candidate4_same_title_summary_pub_date_but_different_ids):
    assert master.has_same_sub_title(candidate1_same_title_and_same_doi)
    assert not master.has_same_sub_title(candidate2_different_title_and_same_pmid)
    assert master.has_same_sub_title(candidate3_same_title_different_ids_summary)
    assert master.has_same_sub_title(candidate4_same_title_summary_pub_date_but_different_ids)


def test_has_same_summary(master,
                          candidate1_same_title_and_same_doi,
                          candidate2_different_title_and_same_pmid,
                          candidate3_same_title_different_ids_summary,
                          candidate4_same_title_summary_pub_date_but_different_ids):
    assert master.has_same_summary(candidate1_same_title_and_same_doi)
    assert not master.has_same_summary(candidate2_different_title_and_same_pmid)
    assert not master.has_same_summary(candidate3_same_title_different_ids_summary)
    assert master.has_same_summary(candidate4_same_title_summary_pub_date_but_different_ids)


def test_has_same_genre_form(master,
                             candidate1_same_title_and_same_doi,
                             candidate4_same_title_summary_pub_date_but_different_ids):
    assert set(master.genre_form) == \
           set(['https://id.kb.se/term/swepub/ArtisticWork',
                'https://id.kb.se/term/swepub/artistic-work'])
    assert set(candidate1_same_title_and_same_doi.genre_form) == \
           set(['https://id.kb.se/term/swepub/ArtisticWork',
                'https://id.kb.se/term/swepub/artistic-work',
                'https://id.kb.se/term/swepub/Book'])
    assert set(candidate4_same_title_summary_pub_date_but_different_ids.genre_form) == \
           set(['https://id.kb.se/term/swepub/artistic-work', 'https://id.kb.se/term/swepub/ArtisticWork'])

    assert not master.has_same_genre_form(candidate1_same_title_and_same_doi)
    assert master.has_same_genre_form(candidate4_same_title_summary_pub_date_but_different_ids)


def test_has_same_publication_date(master,
                                   candidate2_different_title_and_same_pmid,
                                   candidate4_same_title_summary_pub_date_but_different_ids):
    assert master.publication_date == '2016-02-01'
    assert candidate2_different_title_and_same_pmid.publication_date == '2017'
    assert candidate4_same_title_summary_pub_date_but_different_ids.publication_date == '2016'
    assert _has_same_publication_date(master.body, candidate4_same_title_summary_pub_date_but_different_ids.body)
    assert not _has_same_publication_date(master.body, candidate2_different_title_and_same_pmid.body)


def test_has_same_ids(master,
                      candidate1_same_title_and_same_doi,
                      candidate3_same_title_different_ids_summary):
    assert has_same_ids(master.body, candidate1_same_title_and_same_doi.body)
    assert not has_same_ids(master.body, candidate3_same_title_different_ids_summary.body)


def test_get_ids(master):
    assert master.get_identifiedby_ids('DOI') == ['DOI_1']
    assert master.get_identifiedby_ids('PMID') == ['PMID_1']
    assert master.get_identifiedby_ids('ISI') == ['ISI_1']
    assert master.get_identifiedby_ids('ScopusID') == ['SCOPUSID_1']
    assert master.get_identifiedby_ids('ISBN') == ['ISBN1_1']
    assert master.get_identifiedby_ids('URI') == ['URI_1']
    assert master.get_indirectly_identifiedby_ids('ISSN') == ['ISSN1_1']
    assert len(master.get_identifiedby_ids()) == 6
    assert {'@type': 'DOI', 'value': 'DOI_1'} in master.identifiedby_ids
    assert {'@type': 'PMID', 'value': 'PMID_1'} in master.identifiedby_ids
    assert {'@type': 'ISI', 'value': 'ISI_1'} in master.identifiedby_ids
    assert {'@type': 'ScopusID', 'value': 'SCOPUSID_1'} in master.identifiedby_ids
    assert {'@type': 'ISBN', 'value': 'ISBN1_1'} in master.identifiedby_ids
    assert {'@type': 'URI', 'value': 'URI_1'} in master.identifiedby_ids
    assert [{'@type': 'ISSN', 'value': 'ISSN1_1'}] == master.indirectly_identifiedby_ids


def test_set_ids(master):
    master.identifiedby_ids = [{'@type': 'DOI', 'value': 'NEW_DOI_IS_ALWAYS_BETTER'}]
    assert len(master.identifiedby_ids) == 1
    master.indirectly_identifiedby_ids = [{'@type': 'ISSN', 'value': 'NEW_ISSN_IS_ALWAYS_BETTER'}]
    assert len(master.indirectly_identifiedby_ids) == 1


def test_elements_size(master, candidate1_same_title_and_same_doi,
                       candidate4_same_title_summary_pub_date_but_different_ids):
    assert master.elements_size > candidate1_same_title_and_same_doi.elements_size
    assert master.elements_size > candidate4_same_title_summary_pub_date_but_different_ids.elements_size


def test_contributions(master):
    # flake8: noqa E127
    assert len(master.contributions) == 2
    master_contribution0 = master.contributions[0]
    master_contribution1 = master.contributions[1]
    assert master_contribution0.agent_family_name == 'Asbjörg'
    assert master_contribution0.agent_given_name == 'Westum'
    assert master_contribution0.agent_name == 'Asbjörg Westum'
    assert master_contribution0.affiliations == \
           [{'@type': 'Organization', 'name': 'Umeå universitet, Institutionen för språkstudier'}]
    assert master_contribution1.agent_family_name == 'Kalle'
    assert master_contribution1.agent_given_name == 'Kula'
    assert master_contribution1.agent_name == 'Kalle Kula'
    assert master_contribution1.affiliations == [{'@type': 'Organization', 'name': 'Ankeborg'}]


def test_set_contributions(master, candidate1_same_title_and_same_doi):
    # flake8: noqa E127
    assert len(master.contributions) == 2
    master.contributions = candidate1_same_title_and_same_doi.contributions
    assert len(master.contributions) == 1
    master_contribution0 = master.contributions[0]
    assert master_contribution0.affiliations == [
        {'@type': 'Organization',
         'name': 'Institutionen för språkstudier',
         'identifiedBy': [{'@type': 'Local', 'source': {'@type': 'Source', 'code': 'umu.se'}}],
         'hasAffiliation': [{'@type': 'Organization', 'name': 'Umeå universitet',
                             'identifiedBy': [{'@type': 'URI', 'source': {'@type': 'Source', 'code': 'kb.se'}}]}]}]


def test_publication_status(master):
    assert master.publication_status == 'https://id.kb.se/term/swepub/Published'
    master.publication_status = 'new value'
    assert master.publication_status == 'new value'


def test_creator_count(master):
    assert master.creator_count == 3
    master.creator_count = 2
    assert master.creator_count == 2


def test_notes(master):
    assert set(master.notes) == {'note1', 'note2'}
    master.add_notes(['note3'])
    assert set(master.notes) == {'note1', 'note2', 'note3'}
    master.add_notes = (['note1'])
    assert set(master.notes) == {'note1', 'note2', 'note3'}


def test_has_higher_publication_status_ranking():
    published_publication = Publication(
        {'instanceOf': {'hasNote': [{'@type': 'PublicationStatus', '@id': 'https://id.kb.se/term/swepub/Published'}]}})
    online_first_publication = Publication(
        {'instanceOf': {'hasNote': [
            {'@type': 'PublicationStatus', '@id': 'https://id.kb.se/term/swepub/EpubAheadOfPrint/OnlineFirst'}]}})
    in_print_publication = Publication(
        {'instanceOf': {'hasNote': [{'@type': 'PublicationStatus', '@id': 'https://id.kb.se/term/swepub/InPrint'}]}})

    accepted_publication = Publication(
        {'instanceOf': {'hasNote': [{'@type': 'PublicationStatus', '@id': 'https://id.kb.se/term/swepub/Accepted'}]}})

    submitted_publication = Publication(
        {'instanceOf': {'hasNote': [{'@type': 'PublicationStatus', '@id': 'https://id.kb.se/term/swepub/Submitted'}]}})

    preprinted_publication = Publication(
        {'instanceOf': {'hasNote': [{'@type': 'PublicationStatus', '@id': 'https://id.kb.se/term/swepub/Preprint'}]}})

    unknown_publication = Publication(
        {'instanceOf': {'hasNote': [{'@type': 'PublicationStatus', '@id': 'https://id.kb.se/term/swepub/FINNS_INTE'}]}})

    assert not published_publication.has_worse_publication_status_ranking(online_first_publication)
    assert not published_publication.has_worse_publication_status_ranking(in_print_publication)
    assert not published_publication.has_worse_publication_status_ranking(accepted_publication)
    assert not published_publication.has_worse_publication_status_ranking(submitted_publication)
    assert not published_publication.has_worse_publication_status_ranking(preprinted_publication)
    assert not published_publication.has_worse_publication_status_ranking(unknown_publication)
    assert not published_publication.has_worse_publication_status_ranking(published_publication)


def test_subjects(master):
    assert len(master.subjects) == 2
    assert {'@type': 'Topic', 'code': '28177', 'prefLabel': 'prefLabel1',
            'language': {'code': 'swe'}} in master.subjects
    assert {'@type': 'Topic', 'prefLabel': 'prefLabel2'} in master.subjects
    master.subjects = [{'foo': 'bar'}]
    assert master.subjects == [{'foo': 'bar'}]


def test_has_series_from_publication(master, candidate1_same_title_and_same_doi,
                    candidate4_same_title_summary_pub_date_but_different_ids):
    assert len(master.has_series) == 1
    has_series_master = master.has_series[0]
    assert has_series_master.main_title == 'hasSeriesTitle1'
    assert has_series_master.issn == 'ISSN_1'
    assert has_series_master.issue_number == 'IssueNumber1'
    has_series_candidate1 = candidate1_same_title_and_same_doi.has_series[0]
    assert has_series_candidate1.main_title == 'hasSeriesTitle_not_the_same_as_master'
    assert has_series_candidate1.issn == 'ISSN_1'
    assert has_series_candidate1.issue_number == 'IssueNumber1'
    has_series_candidate4 = candidate4_same_title_summary_pub_date_but_different_ids.has_series[0]
    assert has_series_candidate4.main_title == 'hasSeriesTitle_not_the_same_as_master'
    assert has_series_candidate4.issn == 'ISSN_2'
    assert has_series_candidate4.issue_number == 'IssueNumber2'
    assert has_series_master == has_series_candidate1
    assert has_series_master != has_series_candidate4


def test_electronic_locator(master, candidate1_same_title_and_same_doi):
    assert len(master.electronic_locators) == 1
    electronic_locator_master = master.electronic_locators[0]
    assert electronic_locator_master.type == 'Resource'
    assert electronic_locator_master.uri == 'http://electronic_locator_1'
    assert electronic_locator_master.notes == [{"@type": "Note", "label": "free"}]
    electronic_locator_candidate1 = candidate1_same_title_and_same_doi.electronic_locators[0]
    assert electronic_locator_master == electronic_locator_candidate1


def test_set_electronic_locator(master, candidate4_same_title_summary_pub_date_but_different_ids):
    master.electronic_locators = candidate4_same_title_summary_pub_date_but_different_ids.electronic_locators
    electronic_locator_master = master.electronic_locators[0]
    assert electronic_locator_master.type == 'Resource'
    assert electronic_locator_master.uri == 'http://electronic_locator_3'
    assert electronic_locator_master.notes == [{"@type": "Note", "label": "free"},
                                               {"@type": "Note", "noteType": "URL usage", "label": "primary"}]


def test_add_notes_to_electronic_locator(master):
    electronic_locator_master = master.electronic_locators[0]
    assert electronic_locator_master.notes == [{"@type": "Note", "label": "free"}]
    electronic_locator_master.add_notes([{"@type": "Note", "noteType": "URL usage", "label": "primary"}])
    assert electronic_locator_master.notes == [{'@type': 'Note', 'label': 'free'},
                                               {'@type': 'Note', 'noteType': 'URL usage', 'label': 'primary'}]


def test_part_of(master, candidate2_different_title_and_same_pmid,
                 candidate4_same_title_summary_pub_date_but_different_ids):
    part_of_master = master.part_of[0]
    assert part_of_master.main_title == 'Beyond professional monologue'
    assert part_of_master.volume_number == '28'
    assert part_of_master.issue_number == '4'
    assert part_of_master.issns == ['partof_1']
    assert len(part_of_master.has_series) == 1
    part_of_has_serie = part_of_master.has_series[0]
    assert part_of_has_serie.main_title == 'part_of_serie_title'
    assert part_of_has_serie.issue_number == "1"
    candidate2_part_of = candidate2_different_title_and_same_pmid.part_of[0]
    assert candidate2_part_of.issns == ['partof_1']
    assert candidate2_part_of.isbns == ['partof_2', 'partof_3']
    assert part_of_master == candidate2_part_of
    part_of_candidate4 = candidate4_same_title_summary_pub_date_but_different_ids.part_of[0]
    assert part_of_master == part_of_candidate4


def test_set_part_of(master, candidate3_same_title_different_ids_summary):
    master.part_of = candidate3_same_title_different_ids_summary.part_of
    part_of_master = master.part_of[0]
    assert part_of_master.main_title == 'partof_maintitle_not_the_same_as_master'
    assert part_of_master.volume_number is None
    assert part_of_master.issue_number is None
    assert part_of_master.issns == ['partof_2']


def test_contribution_names():
    fname = 'fname'
    gname = 'gname'
    name = 'name'
    no_names_body = {
        'agent': {}
    }
    fname_only_body = {
        'agent': {
            'familyName': fname
        }
    }
    gname_only_body = {
        'agent': {
            'givenName': gname
        }
    }
    fname_and_gname_body = {
        'agent': {
            'familyName': fname,
            'givenName': gname
        }
    }
    name_only_body = {
        'agent': {
            'name': name
        }
    }
    all_names_body = {
        'agent': {
            'familyName': fname,
            'givenName': gname,
            'name': name
        }
    }
    no_names = Contribution(no_names_body)
    fname_only = Contribution(fname_only_body)
    gname_only = Contribution(gname_only_body)
    name_only = Contribution(name_only_body)
    fname_and_gname = Contribution(fname_and_gname_body)
    all_names = Contribution(all_names_body)
    assert no_names.agent_family_name is None
    assert no_names.agent_given_name is None
    assert no_names.agent_name is None

    assert fname_only.body == fname_only_body
    assert fname_only.agent_family_name == fname
    assert fname_only.agent_given_name is None
    assert fname_only.agent_name == fname

    assert gname_only.agent_family_name is None
    assert gname_only.agent_given_name == gname
    assert gname_only.agent_name == gname

    assert name_only.agent_family_name is None
    assert name_only.agent_given_name is None
    assert name_only.agent_name == name

    assert fname_and_gname.agent_family_name == fname
    assert fname_and_gname.agent_given_name == gname
    assert fname_and_gname.agent_name == f"{fname} {gname}"

    assert all_names.agent_family_name == fname
    assert all_names.agent_given_name == gname
    assert all_names.agent_name == name


def test_compare_contributions():
    fname = 'fname'
    gname = 'gname'
    name = 'name'
    no_names_body = {
        'agent': {}
    }
    fname_only_body = {
        'agent': {
            'familyName': fname
        }
    }
    gname_only_body = {
        'agent': {
            'givenName': gname
        }
    }
    fname_and_gname_body = {
        'agent': {
            'familyName': fname,
            'givenName': gname
        }
    }
    name_only_body = {
        'agent': {
            'name': name
        }
    }
    all_names_body = {
        'agent': {
            'familyName': fname,
            'givenName': gname,
            'name': name
        }
    }
    no_names = Contribution(no_names_body)
    no_names2 = Contribution(no_names_body)
    fname_only = Contribution(fname_only_body)
    gname_only = Contribution(gname_only_body)
    fname_and_gname = Contribution(fname_and_gname_body)
    name_only = Contribution(name_only_body)
    all_names = Contribution(all_names_body)
    assert no_names != no_names2
    assert no_names != fname_only
    assert no_names != gname_only
    assert no_names != fname_and_gname
    assert no_names != name_only
    assert no_names != all_names
    assert fname_only != gname_only
    assert fname_only != fname_and_gname
    assert fname_only != name_only
    assert fname_only != all_names
    assert gname_only != fname_and_gname
    assert gname_only != name_only
    assert gname_only != all_names
    assert fname_and_gname != name_only
    assert fname_and_gname != all_names

    assert name_only == all_names

    assert no_names == no_names
    assert no_names2 == no_names2
    assert fname_only == fname_only
    assert gname_only == gname_only
    assert fname_and_gname == fname_and_gname
    assert name_only == name_only
    assert all_names == all_names


def test_contribution_agent_name_different_types():
    simple_name_body = {
        'agent': {
            'name': 'simple_name'
        }
    }

    list_name_body = {
        'agent': {
            'name': ['name1', 'name2']
        }
    }

    comma_seperated_name_body = {
        'agent': {
            'name': 'name1, name2'
        }
    }
    simple_name = Contribution(simple_name_body)
    list_name = Contribution(list_name_body)
    comma_seperated_name = Contribution(comma_seperated_name_body)
    assert simple_name.agent_name == 'simple_name'
    assert list_name.agent_name == 'name1, name2'
    assert comma_seperated_name.agent_name == 'name1, name2'
    assert list_name == comma_seperated_name


def test_agent_identified_by():
    agent_with_identified_by_body = {
        'agent': {
            'familyName': 'kula',
            'givenName': 'kalle',
            'identifiedBy': [
                {
                    '@type': 'ORCID',
                    'value': 'https://orcid.org/0000-0002-0535-1761'
                },
                {
                    '@type': 'Local',
                    'value': 'kalkul',
                    'source': {
                        '@type': 'Source',
                        'code': 'hj'
                    }
                }
            ]
        }
    }

    agent_with_identified_by = Contribution(agent_with_identified_by_body)

    assert len(agent_with_identified_by.identified_bys) == 2
    assert {
               '@type': 'ORCID',
               'value': 'https://orcid.org/0000-0002-0535-1761'
           } in agent_with_identified_by.identified_bys
    assert {
               '@type': 'Local',
               'value': 'kalkul',
               'source': {
                   '@type': 'Source',
                   'code': 'hj'
               }
           } in agent_with_identified_by.identified_bys


def test_part_of_add_issn():
    part_of = PartOf({
        'identifiedBy': [{'@type': 'ISSN', 'value': 'issn_1'}]
    })

    part_of_with_new_issn = PartOf({
        'identifiedBy': [{'@type': 'ISSN', 'value': 'issn_2'}]
    })
    part_of.add_issns(part_of_with_new_issn)
    assert {'@type': 'ISSN', 'value': 'issn_1'} in part_of.body['identifiedBy']
    assert {'@type': 'ISSN', 'value': 'issn_2'} in part_of.body['identifiedBy']

    part_of_with_qualifier = PartOf({
        'identifiedBy': [{'@type': 'ISSN', 'value': 'issn_1', 'qualifier': 'print'}]
    })
    part_of.add_issns(part_of_with_qualifier)
    assert {'@type': 'ISSN', 'value': 'issn_1', 'qualifier': 'print'} in part_of.body['identifiedBy']

    part_of_without_qualifier = PartOf({
        'identifiedBy': [{'@type': 'ISSN', 'value': 'issn_1'}]
    })
    #Checks that existing qualifier is not removed
    part_of.add_issns(part_of_without_qualifier)
    assert {'@type': 'ISSN', 'value': 'issn_1', 'qualifier': 'print'} in part_of.body['identifiedBy']


def test_part_of_add_isbn():
    part_of = PartOf({
        'identifiedBy': [{'@type': 'ISBN', 'value': 'isbn_1'}]
    })

    part_of_with_new_isbn = PartOf({
        'identifiedBy': [{'@type': 'ISBN', 'value': 'isbn_2'}]
    })
    part_of.add_isbns(part_of_with_new_isbn)
    assert {'@type': 'ISBN', 'value': 'isbn_1'} in part_of.body['identifiedBy']
    assert {'@type': 'ISBN', 'value': 'isbn_2'} in part_of.body['identifiedBy']

    part_of_with_qualifier = PartOf({
        'identifiedBy': [{'@type': 'ISBN', 'value': 'isbn_1', 'qualifier': 'print'}]
    })
    part_of.add_isbns(part_of_with_qualifier)
    assert {'@type': 'ISBN', 'value': 'isbn_1', 'qualifier': 'print'} in part_of.body['identifiedBy']

    part_of_without_qualifier = PartOf({
        'identifiedBy': [{'@type': 'ISBN', 'value': 'isbn_1'}]
    })
    #Checks that existing qualifier is not removed
    part_of.add_isbns(part_of_without_qualifier)
    assert {'@type': 'ISBN', 'value': 'isbn_1', 'qualifier': 'print'} in part_of.body['identifiedBy']


def test_part_of_empty_issn_and_isbn():
    empty_part_of = PartOf({})

    part_of_issn = PartOf({
        'identifiedBy': [{'@type': 'ISSN', 'value': 'issn_1'}]
    })
    part_of_issn.add_issns(empty_part_of)
    assert len(part_of_issn.body['identifiedBy']) == 1

    part_of_isbn = PartOf({
        'identifiedBy': [{'@type': 'ISBN', 'value': 'isbn_1'}]
    })
    empty_part_of.add_isbns(part_of_isbn)
    assert len(empty_part_of.body['identifiedBy']) == 1


def test_part_of_empty_titles():
    empty_part_of = PartOf({})
    # Main title must exist for us to match on it
    assert not empty_part_of.has_same_main_title(empty_part_of)
    # Sub title comparison is less strict
    assert empty_part_of.has_same_sub_title(empty_part_of)


def test_has_series():
    has_series = \
        HasSeries(_get_test_data_has_serie_dict(mainTitle='mainTitle',
                                                partNumber='partNumber_1',
                                                identifiedBys=[{'@type': 'ISSN', 'value': 'isnn_1'}]))
    has_series_same_title = \
        HasSeries(_get_test_data_has_serie_dict(mainTitle='mainTitle'))

    has_series_different_title = \
        HasSeries(_get_test_data_has_serie_dict(mainTitle='different'))

    has_series_different_title_same_part_number = \
        HasSeries(_get_test_data_has_serie_dict(mainTitle='different',
                                                partNumber='partNumber_1'))
    has_series_different_title_same_issn = \
        HasSeries(_get_test_data_has_serie_dict(mainTitle='different',
                                                identifiedBys=[{'@type': 'ISSN', 'value': 'isnn_1'}]))
    has_series_different_title_same_part_number_and_issn = \
        HasSeries(_get_test_data_has_serie_dict(mainTitle='different',
                                                partNumber='partNumber_1',
                                                identifiedBys=[{'@type': 'ISSN', 'value': 'isnn_1'}]))

    assert has_series == has_series_same_title
    assert not has_series == has_series_different_title
    assert not has_series == has_series_different_title_same_part_number
    assert not has_series == has_series_different_title_same_issn
    assert has_series == has_series_different_title_same_part_number_and_issn


def test_part_of_has_series():
    part_of_has_series = \
        PartOfHasSeries(_get_test_data_has_serie_dict(mainTitle='mainTitle',
                                                      partNumber='partNumber_1',
                                                      identifiedBys=[{'@type': 'ISSN', 'value': 'isnn_1'}]))
    part_of_has_series_same_title = \
        PartOfHasSeries(_get_test_data_has_serie_dict(mainTitle='mainTitle'))

    part_of_has_series_different_title = \
        PartOfHasSeries(_get_test_data_has_serie_dict(mainTitle='different'))

    part_of_has_series_different_title_same_part_number = \
        PartOfHasSeries(_get_test_data_has_serie_dict(mainTitle='different',
                                                      partNumber='partNumber_1'))
    part_of_has_series_different_title_same_issn = \
        PartOfHasSeries(_get_test_data_has_serie_dict(mainTitle='different',
                                                      identifiedBys=[{'@type': 'ISSN', 'value': 'isnn_1'}]))
    part_of_has_series_different_title_same_part_number_and_issn = \
        PartOfHasSeries(_get_test_data_has_serie_dict(mainTitle='different',
                                                      partNumber='partNumber_1',
                                                      identifiedBys=[{'@type': 'ISSN', 'value': 'isnn_1'}]))

    assert part_of_has_series == part_of_has_series_same_title
    assert not part_of_has_series == part_of_has_series_different_title
    assert not part_of_has_series == part_of_has_series_different_title_same_part_number
    # Same ISSN enough for two PartOfHasSeries to be equal
    assert part_of_has_series == part_of_has_series_different_title_same_issn
    assert part_of_has_series == part_of_has_series_different_title_same_part_number_and_issn


def test_right_has_serie_is_returned():
    publication = Publication(
        {
            'hasSeries': [
                _get_test_data_has_serie_dict(mainTitle='Publication hasSerie',
                                              partNumber='partNumber_1',
                                              identifiedBys=[{'@type': 'ISSN', 'value': 'isnn_1'}])
            ],
            'partOf': [{
                'hasSeries': [
                    _get_test_data_has_serie_dict(mainTitle='Publication hasSerie',
                                                  partNumber='partNumber_1',
                                                  identifiedBys=[{'@type': 'ISSN', 'value': 'isnn_1'}])
                ]
            }]
        }
    )
    has_serie_from_publication = publication.has_series[0]
    has_serie_from_part_of = publication.part_of[0].has_series[0]
    assert isinstance(has_serie_from_publication, HasSeries)
    assert isinstance(has_serie_from_part_of, PartOfHasSeries)
    # Since PartOfHasSeries inherit from HasSeries
    assert isinstance(has_serie_from_part_of, HasSeries)
    assert not isinstance(has_serie_from_publication, PartOfHasSeries)


def test_add_series_publication():
    publication = Publication(
        {
            'hasSeries': [
                _get_test_data_has_serie_dict(mainTitle='Publication hasSerie',
                                              partNumber='partNumber_1',
                                              identifiedBys=[{'@type': 'ISSN', 'value': 'isnn_1'}])
            ]
        })

    publication_different_serie = Publication(
        {
            'hasSeries': [
                _get_test_data_has_serie_dict(mainTitle='different',
                                              partNumber='different',
                                              identifiedBys=[{'@type': 'ISSN', 'value': 'isnn_1'}])
            ]
        })
    assert len(publication.has_series) == 1
    publication.add_series(publication_different_serie)
    assert len(publication.has_series) == 2

    publication_same_serie = Publication(
        {
            'hasSeries': [
                _get_test_data_has_serie_dict(mainTitle='different',
                                              partNumber='partNumber_1',
                                              identifiedBys=[{'@type': 'ISSN', 'value': 'isnn_1'}])
            ]
        })
    publication.add_series(publication_same_serie)
    assert len(publication.has_series) == 2


def test_add_series_part_of():
    publication = Publication(
        {
            'partOf': [{
                'hasSeries': [
                    _get_test_data_has_serie_dict(mainTitle='Publication hasSerie',
                                                  partNumber='partNumber_1',
                                                  identifiedBys=[{'@type': 'ISSN', 'value': 'isnn_1'}])
                ]
            }]
        })

    publication_same_serie = Publication(
        {
            'partOf': [{
                'hasSeries': [
                    _get_test_data_has_serie_dict(mainTitle='different',
                                                  partNumber='different',
                                                  identifiedBys=[{'@type': 'ISSN', 'value': 'isnn_1'}])
                ]
            }]
        })
    assert len(publication.part_of[0].has_series) == 1
    publication.part_of[0].add_series(publication_same_serie.part_of[0])
    # Ignoring partNumber for hasSeries in part_of
    assert len(publication.part_of[0].has_series) == 1

    publication_different_serie = Publication(
        {
            'partOf': [{
                'hasSeries': [
                    _get_test_data_has_serie_dict(mainTitle='different',
                                                  identifiedBys=[{'@type': 'ISSN', 'value': 'isnn_2'}])
                ]
            }]
        })
    publication.part_of[0].add_series(publication_different_serie.part_of[0])
    assert len(publication.part_of[0].has_series) == 2


def _get_test_data_has_serie_dict(mainTitle='', partNumber='', identifiedBys=[]):
    has_serie_dict = {
        '@type': 'Work',
        'hasTitle': [
            {
                '@type': 'Title',
                'mainTitle': mainTitle,
                'partNumber': partNumber,
            }
        ],
        'identifiedBy': identifiedBys
    }

    if empty_string(partNumber):
        del has_serie_dict['hasTitle'][0]['partNumber']
    if len(identifiedBys) == 0:
        del has_serie_dict['identifiedBy']

    return has_serie_dict


def test_title_and_subtitle():
    publication_main_and_sub_title = Publication(
        {'instanceOf': {'hasTitle': [{'@type': 'Title',
                                      'mainTitle': 'This is the main title',
                                      'subtitle': 'This is the sub title'}
                                     ]}})
    assert publication_main_and_sub_title.main_title == 'This is the main title'
    assert publication_main_and_sub_title.sub_title == 'This is the sub title'


def test_title_only():
    publication_main_title_only = Publication(
        {'instanceOf': {'hasTitle': [{'@type': 'Title',
                                      'mainTitle': 'This is the main title'}
                                     ]}})
    assert publication_main_title_only.main_title == 'This is the main title'
    assert publication_main_title_only.sub_title is None


def test_splited_title_only():
    publication_main_title_mixed_with_sub_title = Publication(
        {'instanceOf': {'hasTitle': [{'@type': 'Title',
                                      'mainTitle': 'This is the main title:This is the sub title'}
                                     ]}})
    assert publication_main_title_mixed_with_sub_title.main_title == 'This is the main title'
    assert publication_main_title_mixed_with_sub_title.sub_title == 'This is the sub title'


def test_splited_title_and_subtitle():
    publication_main_title_mixed_with_sub_title_and_subtitle = Publication(
        {'instanceOf': {'hasTitle': [{'@type': 'Title',
                                      'mainTitle': 'This is the main title:This is NOT the sub title',
                                      'subtitle': 'This is the sub title'}
                                     ]}})
    assert publication_main_title_mixed_with_sub_title_and_subtitle.main_title == 'This is the main title:This is NOT the sub title'
    assert publication_main_title_mixed_with_sub_title_and_subtitle.sub_title == 'This is the sub title'


def test_publication_with_publication_information():
    publication_with_publication_information = Publication(
       {'publication': [{'@type': 'Publication',
                         'agent': {'@type': 'Agent', 'label': 'Kalle Anka'},
                         'place': {'@type': 'Place', 'label': 'Ankeborg'},
                         'date': '2011'}
                        ]})

    assert publication_with_publication_information.publication_date == '2011'
    publication_information = publication_with_publication_information.publication_information
    assert publication_information.agent == {'@type': 'Agent', 'label': 'Kalle Anka'}
    assert publication_information.place == {'@type': 'Place', 'label': 'Ankeborg'}


def test_publication_without_publication_information():
    publication_without_publication_information = Publication({})
    assert publication_without_publication_information.publication_date is None
    assert publication_without_publication_information.publication_information is None


def test_usage_and_access_policy():
    expected = [
        {"@type": "AccessPolicy", "label": "gratis"},
        {"@type": "Embargo", "endDate": "2020-01-01"},
        {"@id": "https://example.com"}
    ]
    publication = Publication({"usageAndAccessPolicy": expected})
    assert expected == publication.usage_and_access_policy


def test_usage_and_access_policy_setter():
    expected = [
        {"@type": "AccessPolicy", "label": "gratis"},
        {"@type": "Embargo", "endDate": "2020-01-01"},
        {"@id": "https://example.com"}
    ]
    publication = Publication({})
    assert not publication.usage_and_access_policy
    publication.usage_and_access_policy = expected
    assert expected == publication.usage_and_access_policy


def test_usage_and_access_policy_by_type():
    policies = [
        {"@type": "AccessPolicy", "label": "gratis"},
        {"@type": "Embargo", "endDate": "2020-01-01"},
        {"@type": "AccessPolicy", "label": "restricted"},
        {"@id": "https://example.com"},
        {"other": "policy"}
    ]
    access_policies = [
        {"@type": "AccessPolicy", "label": "gratis"},
        {"@type": "AccessPolicy", "label": "restricted"}
    ]
    embargoes = [{"@type": "Embargo", "endDate": "2020-01-01"}]
    links = [{"@id": "https://example.com"}]
    others = [{"other": "policy"}]
    expected = (access_policies, embargoes, links, others)
    publication = Publication({"usageAndAccessPolicy": policies})
    assert expected == publication.usage_and_access_policy_by_type
