import re
import pytest
from lxml.etree import LxmlError, XMLSyntaxError

MODS = """
    <record xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <metadata>
        <mods xmlns="http://www.loc.gov/mods/v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xlink="http://www.w3.org/1999/xlink" version="3.2" xsi:schemaLocation="http://www.loc.gov/mods/v3 http://www.loc.gov/standards/mods/v3/mods-3-2.xsd">
        {}
        </mods>
      </metadata>
    </record>
""".format


def test_parser(parser):
    raw_xml = re.sub(r"\n\s*", "", """<record xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <header>
        <identifier>oai:DiVA.org:lnu-67642</identifier>
        <datestamp>2017-09-07T07:18:00Z</datestamp>
        <setSpec>lnu</setSpec>
        <setSpec>article</setSpec>
        <setSpec>refereed</setSpec>
    </header>
    <metadata>
        <mods xmlns="http://www.loc.gov/mods/v3" xmlns:xlink="http://www.w3.org/1999/xlink" version="3.2" xsi:schemaLocation="http://www.loc.gov/mods/v3 http://www.loc.gov/standards/mods/v3/mods-3-2.xsd">
            <abstract>Awesome abstract</abstract>
            <genre authority="diva" type="contentTypeCode">refereed</genre>
            <genre authority="svep" type="contentType">ref</genre>
            <genre authority="diva" type="contentType" lang="eng">Refereed</genre>
            <genre authority="diva" type="contentType" lang="swe">Refereegranskat</genre>
            <genre authority="diva" type="contentType" lang="nor">Fagfellevurdert</genre>
            <genre authority="diva" type="publicationTypeCode">article</genre>
            <genre authority="kb.se" type="outputType">publication/journal-article</genre>
            <genre authority="svep" type="publicationType">art</genre>
            <genre authority="diva" type="publicationType" lang="eng">Article in journal</genre>
            <genre authority="diva" type="publicationType" lang="swe">Artikel i tidskrift</genre>
            <genre authority="diva" type="publicationType" lang="nor">Artikkel i tidsskrift</genre>
            <genre authority="kev" type="publicationType" lang="eng">article</genre>
            <name type="personal" authority="lnu">
                <nameIdentifier type="orcid">0000-0002-1825-0097</nameIdentifier>
                <nameIdentifier type="lnu">lolhum</nameIdentifier>
                <nameIdentifier type="lnu" invalid="yes">000</nameIdentifier>
                <namePart type="family">Olsson</namePart>
                <namePart type="given">Lars</namePart>
                <namePart type="date">1945-</namePart>
                <role>
                    <roleTerm type="code" authority="marcrelator">aut</roleTerm>
                </role>
                <affiliation>Lund University</affiliation>
            </name>
            <titleInfo lang="eng">
                <title>"We stand here as sellers and buyers in relation to each other"</title>
                <subTitle>on work, culture and consciousness among Swedish typographers in the late 19th and early 20th centuries</subTitle>
            </titleInfo>
            <subject lang="eng" authority="uka.se" xlink:href="30220">
                <topic>Medical and Health Sciences</topic>
                <topic>Clinical Medicine</topic>
                <topic>Obstetrics, Gynecology and Reproductive Medicine</topic>
            </subject>
            <subject lang="eng" authority="uka.se" xlink:href="30305">
                <topic>Medical and Health Sciences</topic>
                <topic>Health Sciences</topic>
                <topic>Nursing</topic>
            </subject>
            <language>
                <languageTerm type="code" authority="iso639-2b">eng</languageTerm>
            </language>
            <originInfo>
                <publisher>Scandinavian University Press</publisher>
                <dateIssued>1994</dateIssued>
                <dateOther type="available">2017-09-07T09:18:49</dateOther>
                <dateOther type="openAccess" point="start">2017-09-07T09:18:49</dateOther>
                <dateOther type="online">2017-09-07T09:18:49</dateOther>
                <dateOther type="defence">2017-09-07T09:18:49</dateOther>
                <dateOther type="digitized">2017-09-07T09:18:49</dateOther>
                <place>
                    <placeTerm>Ankeborg</placeTerm>
                </place>
                <edition>2nd edition</edition>
            </originInfo>
            <physicalDescription>
                <form authority="marcform">print</form>
            </physicalDescription>
            <identifier type="uri">http://urn.kb.se/resolve?urn=urn:nbn:se:lnu:diva-67642</identifier>
            <identifier type="doi">10.1080/03468759408579279</identifier>
            <identifier type="isi">000071067000025</identifier>
            <typeOfResource>text</typeOfResource>
            <subject lang="swe">
                <topic>Typografer</topic>
            </subject>
            <subject lang="swe">
                <topic>Sverige</topic>
            </subject>
            <subject lang="swe">
                <topic>1800-talet</topic>
            </subject>
            <subject lang="swe">
                <topic>1900-talet</topic>
            </subject>
            <subject lang="eng" authority="hsv" xlink:href="60101">
                <topic>Humanities and the Arts</topic>
                <topic>History and Archaeology</topic>
                <topic>History</topic>
            </subject>
            <subject lang="swe" authority="hsv" xlink:href="60101">
                <topic>Humaniora och konst</topic>
                <topic>Historia och arkeologi</topic>
                <topic>Historia</topic>
            </subject>
            <subject lang="swe" authority="lnu" xlink:href="7304">
                <topic>Historia</topic>
                <genre>Research subject</genre>
            </subject>
            <subject lang="eng" authority="lnu" xlink:href="7304">
                <topic>History</topic>
                <genre>Research subject</genre>
            </subject>
            <relatedItem type="host">
                <genre>dataset</genre>
                <titleInfo>
                    <title>Transfer of bacteriophages between the fingers of volunteers and water or saliva</title>
                </titleInfo>
                <identifier type="doi">10.25678/000099</identifier>
            </relatedItem>
            <relatedItem type="host">
                <titleInfo>
                    <title>Scandinavian Journal of History</title>
                </titleInfo>
                <identifier type="issn">0346-8755</identifier>
                <identifier type="eissn">1502-7716</identifier>
                <part>
                    <detail type="volume">
                        <number>19</number>
                    </detail>
                    <detail type="issue">
                        <number>3</number>
                    </detail>
                    <extent>
                        <start>201</start>
                        <end>221</end>
                    </extent>
                </part>
            </relatedItem>
            <relatedItem type="host">
                <genre>project</genre>
                <genre>programme</genre>
                <genre>grantAgreement</genre>
                <genre>initiative</genre>
                <genre>event</genre>
                <titleInfo>
                    <title>An experimental view on the molecular phase space</title>
                </titleInfo>
                <identifier type="swecris">2017-05336</identifier>
                <identifier type="cordis">2017-05337</identifier>
                <identifier type="lnu">lnu1</identifier>
                <name type="corporate">
                    <namePart lang="swe">Vetenskapsrådet</namePart>
                    <namePart>Swedish Research Council</namePart>
                    <nameIdentifier type="isni">0000 0001 1504 010X</nameIdentifier>
                    <nameIdentifier type="fundref">fundref</nameIdentifier>
                    <nameIdentifier type="grid">grid</nameIdentifier>
                    <nameIdentifier type="ringgold">ringgold</nameIdentifier>
                    <nameIdentifier type="uri">https://example.com</nameIdentifier>
                    <role>
                        <roleTerm type="code" authority="marcrelator">fnd</roleTerm>
                    </role>
                </name>
                <note type="sfo">E-vetenskap</note>
            </relatedItem>
            <note type="publicationStatus" lang="eng">Published</note>
            <accessCondition>gratis</accessCondition>
            <recordInfo>
                <recordOrigin>teguaa</recordOrigin>
                <recordContentSource>lnu</recordContentSource>
                <recordCreationDate>2017-09-07</recordCreationDate>
                <recordChangeDate>2017-09-07</recordChangeDate>
                <recordIdentifier>diva2:1139206</recordIdentifier>
            </recordInfo>
            <location>
                <url note="free/2015-01-01" displayLabel="FULLTEXT">http://hh.divaportal.org/smash/get/diva2:239322/FULLTEXT01</url>
                <url usage="primary" displayLabel="FULLTEXT">http://hh.divaportal.org/smash/get/diva2:239322/FULLTEXT02</url>
                <url usage="primary" displayLabel="FULLTEXT" access="raw object" note="free">http://hh.diva-portal.org/smash/get/diva2:239322/FULLTEXT01</url>
            </location>
            <note>Parallel text in Russian and English</note>
            <note type="creatorCount">3</note>
        </mods>
    </metadata>
</record>""")

    parsed_publication = {
        "@context": "https://id.kb.se/context.jsonld",
        "@id": "oai:DiVA.org:lnu-67642",
        "@type": "Instance",
        "instanceOf": {
            "@type": "Text",
            "genreForm": [
                {'@id': 'https://id.kb.se/term/swepub/svep/ref'},
                {'@id': 'https://id.kb.se/term/swepub/output/publication/journal-article'},
                {'@id': 'https://id.kb.se/term/swepub/JournalArticle'}
            ],
            "language": [
                {
                    '@id': 'https://id.kb.se/language/eng',
                    '@type': 'Language',
                    'code': 'eng',
                    'langCode': 'eng',
                    'source': {'@type': 'Source', 'code': 'iso639-2b'}
                }
            ],
            "hasTitle": [
                {
                    "@type": "Title",
                    "mainTitle": "\"We stand here as sellers and buyers in relation to each other\"",
                    "subtitle": "on work, culture and consciousness among Swedish typographers in the late 19th and early 20th centuries"
                }
            ],
            'summary': [{'@type': 'Summary', 'label': 'Awesome abstract'}],
            "contribution": [
                {
                    "@type": "Contribution",
                    "agent": {
                        "@type": "Person",
                        "familyName": "Olsson",
                        "givenName": "Lars",
                        "lifeSpan": "1945-",
                        "identifiedBy": [
                            {
                                "@type": "ORCID",
                                "value": "0000-0002-1825-0097"
                            },
                            {
                                "@type": "Local",
                                "value": "lolhum",
                                "source": {
                                    "@type": "Source",
                                    "code": "lnu",
                                },
                            },
                        ],
                        "incorrectlyIdentifiedBy": [
                            {
                                "@type": "Local",
                                "value": "000",
                                "source": {
                                    "@type": "Source",
                                    "code": "lnu",
                                },
                            },
                        ],
                    },
                    "role": [{"@id": "http://id.loc.gov/vocabulary/relators/aut"}],
                    "hasAffiliation": [{'@type': 'Organization', 'name': 'Lund University'}]
                }
            ],
            "subject": [
                {
                    "@type": "Topic",
                    "language": {'@type': 'Language', 'code': 'swe', '@id': 'https://id.kb.se/language/swe'},
                    "prefLabel": "Typografer",
                },
                {
                    "@type": "Topic",
                    "language": {'@type': 'Language', 'code': 'swe', '@id': 'https://id.kb.se/language/swe'},
                    "prefLabel": "Sverige",
                },
                {
                    "@type": "Topic",
                    "language": {'@type': 'Language', 'code': 'swe', '@id': 'https://id.kb.se/language/swe'},
                    "prefLabel": "1800-talet",
                },
                {
                    "@type": "Topic",
                    "language": {'@type': 'Language', 'code': 'swe', '@id': 'https://id.kb.se/language/swe'},
                    "prefLabel": "1900-talet",
                },
                {
                    "@type": "Topic",
                    "code": "60101",
                    "inScheme": {"@id": "hsv/eng", "@type": "ConceptScheme", "code": "hsv"},
                    "language": {'@type': 'Language', 'code': 'eng', '@id': 'https://id.kb.se/language/eng'},
                    "prefLabel": "History",
                    'broader': {'prefLabel': 'History and Archaeology',
                                'broader': {'prefLabel': 'Humanities and the Arts'}},
                },
                {
                    "@type": "Topic",
                    "code": "60101",
                    "inScheme": {"@id": "hsv/swe", "@type": "ConceptScheme", "code": "hsv"},
                    "language": {'@type': 'Language', 'code': 'swe', '@id': 'https://id.kb.se/language/swe'},
                    "prefLabel": "Historia",
                    'broader': {'prefLabel': 'Historia och arkeologi',
                                'broader': {'prefLabel': 'Humaniora och konst'}},
                },
                {
                    "@type": "Topic",
                    "code": "7304",
                    "inScheme": {"@id": "lnu/swe", "@type": "ConceptScheme", "code": "lnu"},
                    "language": {'@type': 'Language', 'code': 'swe', '@id': 'https://id.kb.se/language/swe'},
                    "prefLabel": "Historia",
                },
                {
                    "@type": "Topic",
                    "code": '7304',
                    "inScheme": {"@id": "lnu/eng", "@type": "ConceptScheme", "code": "lnu"},
                    "language": {'@type': 'Language', 'code': 'eng', '@id': 'https://id.kb.se/language/eng'},
                    "prefLabel": "History",
                },
                {
                    "@id": "https://id.kb.se/term/uka/30220",
                    "@type": "Topic",
                    "code": "30220",
                    "prefLabel": "Obstetrics, Gynecology and Reproductive Medicine",
                    "language": {
                        "@type": "Language",
                        "@id": "https://id.kb.se/language/eng",
                        "code": "eng"
                    },
                    "inScheme": {
                        "@id": "https://id.kb.se/term/uka/",
                        "@type": "ConceptScheme",
                        "code": "uka.se"
                    },
                    "broader": {
                        "prefLabel": "Clinical Medicine",
                        "broader": {
                            "prefLabel": "Medical and Health Sciences",
                        }
                    }
                },
                {
                    "@id": "https://id.kb.se/term/uka/30305",
                    "@type": "Topic",
                    "code": "30305",
                    "prefLabel": "Nursing",
                    "language": {
                        "@type": "Language",
                        "@id": "https://id.kb.se/language/eng",
                        "code": "eng"
                    },
                    "inScheme": {
                        "@id": "https://id.kb.se/term/uka/",
                        "@type": "ConceptScheme",
                        "code": "uka.se"
                    },
                    "broader": {
                        "prefLabel": "Health Sciences",
                        "broader": {
                            "prefLabel": "Medical and Health Sciences",
                        }
                    }
                }
            ],
            "hasNote": [
                {'@type': 'CreatorCount', 'label': '3'},
                {'@type': 'PublicationStatus', '@id': 'https://id.kb.se/term/swepub/Published'},
                {'@type': 'Note', 'label': 'Parallel text in Russian and English'}
            ]
        },
        "identifiedBy": [
            {
                "@type": "URI",
                "value": "http://urn.kb.se/resolve?urn=urn:nbn:se:lnu:diva-67642"
            },
            {
                "@type": "DOI",
                "value": "10.1080/03468759408579279"
            },
            {
                "@type": "ISI",
                "value": "000071067000025"
            }
        ],
        'meta': {
            '@type': 'AdminMetadata',
            'assigner': {'@type': 'Agent', 'label': 'lnu'},
            'creationDate': '2017-09-07',
            'changeDate': '2017-09-07'
        },
        "isPartOf": [
            {
                "@type": "Dataset",
                "hasTitle": [
                    {
                        "@type": "Title",
                        "mainTitle": "Transfer of bacteriophages between the fingers of volunteers and water or saliva"
                    }
                ],
                "identifiedBy": [
                    {
                        "@type": "DOI",
                        "value": "10.25678/000099"
                    }
                ]
            },
            {
                "@type": 'Work',
                "hasTitle": [
                    {
                        "@type": "Title",
                        'mainTitle': "Scandinavian Journal of History",
                        'issueNumber': '3',
                        'volumeNumber': '19'
                    }
                ],
                "identifiedBy": [
                    {"@type": "ISSN", "value": "0346-8755"},
                    {'@type': 'ISSN', 'value': '1502-7716'}
                ],
                'hasInstance': {
                    '@type': 'Instance',
                    'extent': [{'@type': 'Extent', 'label': '201-221'}]
                }
            },
            {
                "@type": "Work",
                "genreForm": [
                    {
                        "@id": "https://id.kb.se/term/swepub/project"
                    },
                    {
                        "@id": "https://id.kb.se/term/swepub/programme"
                    },
                    {
                        "@id": "https://id.kb.se/term/swepub/grantAgreement"
                    },
                    {
                        "@id": "https://id.kb.se/term/swepub/initiative"
                    },
                    {
                        "@id": "https://id.kb.se/term/swepub/event"
                    }
                ],
                "hasTitle": [
                    {
                        "@type": "Title",
                        "mainTitle": "An experimental view on the molecular phase space"
                    }
                ],
                "identifiedBy": [
                    {
                        "@type": "SweCRIS",
                        "value": "2017-05336"
                    },
                    {
                        "@type": "CORDIS",
                        "value": "2017-05337"
                    },
                    {
                        "@type": "Local",
                        "value": "lnu1",
                        "source": {
                            "@type": "Source",
                            "code": "lnu"
                        }
                    }
                ],
                "contribution": [
                    {
                        "@type": "Contribution",
                        "agent": {
                            "@type": "Organization",
                            "name": "Swedish Research Council",
                            "nameByLang": {
                                "swe": "Vetenskapsrådet"
                            },
                            "identifiedBy": [
                                {
                                    "@type": "ISNI",
                                    "value": "0000 0001 1504 010X"
                                },
                                {
                                    "@type": "FundRef",
                                    "value": "fundref",
                                },
                                {
                                    "@type": "GRID",
                                    "value": "grid"
                                },
                                {
                                    "@type": "Ringgold",
                                    "value": "ringgold"
                                },
                                {
                                    "@type": "URI",
                                    "value": "https://example.com"
                                }
                            ]
                        },
                        "role": [
                            {
                                "@id": "http://id.loc.gov/vocabulary/relators/fnd"
                            }
                        ]
                    }
                ],
                "hasNote": [
                    {
                        "@type": "SFO",
                        "label": "E-vetenskap"
                    }
                ]
            }
        ],
        'carrierType': {
            '@type': 'CarrierType',
            'label': 'print',
            'source': {'@type': 'Source', 'code': 'marcform'}
        },
        'publication': [
            {
                '@type': 'Publication',
                'date': '1994',
                'place': {'@type': 'Place', 'label': 'Ankeborg'},
                'agent': {'@type': 'Agent', 'label': 'Scandinavian University Press'}}
        ],
        'dissertation': [
            {
                "@type": "Dissertation",
                "date": "2017-09-07T09:18:49"
            }
        ],
        'provisionActivity': [
            {
                "@type": "Availability",
                "date": "2017-09-07T09:18:49"
            },
            {
                "@type": "OpenAccessAvailability",
                "startDate": "2017-09-07T09:18:49"
            },
            {
                "@type": "OnlineAvailability",
                "date": "2017-09-07T09:18:49"
            },
            {
                "@type": "Digitization",
                "date": "2017-09-07T09:18:49"
            }
        ],
        "editionStatement": "2nd edition",
        "electronicLocator": [
            {
                '@type': 'Resource',
                'uri': 'http://hh.divaportal.org/smash/get/diva2:239322/FULLTEXT01',
                'label': 'FULLTEXT',
                'hasNote': [{'@type': 'Note', 'label': 'free/2015-01-01'}]
            },
            {
                '@type': 'Resource',
                'uri': 'http://hh.divaportal.org/smash/get/diva2:239322/FULLTEXT02',
                'label': 'FULLTEXT',
                'hasNote': [{'@type': 'Note', 'label': 'primary', 'noteType': 'URL usage'}]
            },
            {
                '@type': 'Resource',
                'uri': 'http://hh.diva-portal.org/smash/get/diva2:239322/FULLTEXT01',
                'label': 'FULLTEXT',
                'hasNote': [
                    {'@type': 'Note', 'label': 'primary', 'noteType': 'URL usage'},
                    {'@type': 'Note', 'label': 'Raw object'},
                    {'@type': 'Note', 'label': 'free'}
                ]
            }
        ],
        'usageAndAccessPolicy': [
            {
                "@type": "AccessPolicy",
                "label": "gratis"
            }
        ]
    }

    assert parsed_publication == parser.parse_mods(raw_xml)


def test_parser_handles_invalid_xml(parser):
    with pytest.raises(XMLSyntaxError):
        parser.parse_mods('')
    with pytest.raises(LxmlError):
        parser.parse_mods('<xml><a></xml>')
    with pytest.raises(LxmlError):
        parser.parse_mods('next(self.records).raw')


def test_host_title_is_extracted(parser):
    raw_xml = MODS("""
      <relatedItem type="host">
        <titleInfo>
          <title>ISKO</title>
          <subTitle>Encyclopedia of Knowledge Organization</subTitle>
        </titleInfo>
        <titleInfo>
          <title>Second Title</title>
          <subTitle>Second Subtitle</subTitle>
        </titleInfo>
        <titleInfo type="alternative"><title>baz</title></titleInfo>
        <titleInfo><title>foobar</title></titleInfo>
        <titleInfo><customTitle type="foo">bar</customTitle></titleInfo>
      </relatedItem>
    """)

    expected = [
        {'@type': 'Title', 'mainTitle': 'ISKO', 'subtitle': 'Encyclopedia of Knowledge Organization'},
        {'@type': 'Title', 'mainTitle': 'Second Title', 'subtitle': 'Second Subtitle'},
        {'@type': 'VariantTitle', 'mainTitle': 'baz'},
        {'@type': 'Title', 'mainTitle': 'foobar'},
        {'@type': 'Title', 'foo': 'bar'}
    ]

    assert len(parser.parse_mods(raw_xml)['isPartOf']) == 1
    assert expected == parser.parse_mods(raw_xml)['isPartOf'][0]['hasTitle']


def test_publication_with_series_and_host(parser):
    raw_xml = MODS("""
      <relatedItem type="series">
        <titleInfo><title>ISKO</title></titleInfo>
        <part><detail type="volume">3</detail></part>
      </relatedItem>
      <relatedItem type="host">
        <titleInfo><title>BOSE</title></titleInfo>
        <part><detail type="volume">5</detail></part>
      </relatedItem>
    """)

    expected_has_series = [
        {'@type': 'Work', 'hasTitle': [{'@type': 'Title', 'mainTitle': 'ISKO', 'volumeNumber': '3'}]}
    ]

    expected_is_part_of = [
        {'@type': 'Work', 'hasTitle': [{'@type': 'Title', 'mainTitle': 'BOSE', 'volumeNumber': '5'}],
         'hasSeries': expected_has_series}
    ]

    actual = parser.parse_mods(raw_xml)
    assert actual['isPartOf'] == expected_is_part_of
    assert actual['isPartOf'][0]['hasSeries'] == expected_has_series


def test_series_title_and_part_number_are_extracted(parser):
    raw_xml = MODS("""
      <relatedItem type="series">
        <titleInfo>
          <title>ISKO</title>
          <subTitle>Encyclopedia of Knowledge Organization</subTitle>
        </titleInfo>
        <titleInfo>
          <title>Second Title</title>
          <subTitle>Second Subtitle</subTitle>
        </titleInfo>
        <titleInfo type="alternative"><title>baz</title><partNumber>2</partNumber></titleInfo>
        <titleInfo><title>foobar</title></titleInfo>
        <titleInfo><customTitle type="foo">bar</customTitle></titleInfo>
        <titleInfo><title>Some Title</title><partNumber>3</partNumber></titleInfo>
      </relatedItem>
    """)

    expected = [
        {'@type': 'Title', 'mainTitle': 'ISKO', 'subtitle': 'Encyclopedia of Knowledge Organization'},
        {'@type': 'Title', 'mainTitle': 'Second Title', 'subtitle': 'Second Subtitle'},
        {'@type': 'VariantTitle', 'mainTitle': 'baz', 'partNumber': '2'},
        {'@type': 'Title', 'mainTitle': 'foobar'},
        {'@type': 'Title', 'foo': 'bar'},
        {'@type': 'Title', 'mainTitle': 'Some Title', 'partNumber': '3'},
    ]

    assert len(parser.parse_mods(raw_xml)['hasSeries']) == 1
    assert expected == parser.parse_mods(raw_xml)['hasSeries'][0]['hasTitle']


def test_series_volume_number_is_extracted(parser):
    raw_xml = MODS("""
      <relatedItem type="series">
        <titleInfo><title>.</title></titleInfo>
        <part><detail type="volume">1337</detail></part>
      </relatedItem>
    """)

    assert '1337' == parser.parse_mods(raw_xml)['hasSeries'][0]['hasTitle'][0]['volumeNumber']


def test_series_part_number_is_extracted(parser):
    raw_xml = MODS("""
      <relatedItem type="series">
        <titleInfo><title>Title</title><partNumber>3</partNumber></titleInfo>
      </relatedItem>
    """)

    assert '3' == parser.parse_mods(raw_xml)['hasSeries'][0]['hasTitle'][0]['partNumber']


def test_series_issue_number_identifier_is_extracted_as_part_number(parser):
    raw_xml = MODS("""
      <relatedItem type="series">
        <titleInfo><title>Title</title></titleInfo>
        <identifier type="issue number">4</identifier>
      </relatedItem>
    """)

    assert '4' == parser.parse_mods(raw_xml)['hasSeries'][0]['hasTitle'][0]['partNumber']


def test_series_prefer_mods_part_number_element(parser):
    raw_xml = MODS("""
      <relatedItem type="series">
        <titleInfo><title>Title</title><partNumber>3</partNumber></titleInfo>
        <identifier type="issue number">4</identifier>
      </relatedItem>
    """)

    assert '3' == parser.parse_mods(raw_xml)['hasSeries'][0]['hasTitle'][0]['partNumber']


def test_series_exclude_id_type_issue_number_1(parser):
    raw_xml = MODS("""
      <relatedItem type="series">
        <titleInfo><title>Title</title></titleInfo>
        <identifier type="issue number">4</identifier>
      </relatedItem>
    """)
    expected_identified_by = []

    assert expected_identified_by == parser.parse_mods(raw_xml)['hasSeries'][0]['identifiedBy']


def test_series_exclude_id_type_issue_number_2(parser):
    raw_xml = MODS("""
      <relatedItem type="series">
        <titleInfo><title>Title</title></titleInfo>
        <identifier type="issue number">4</identifier>
        <identifier type="other">1234</identifier>
        <identifier type="issn">5678</identifier>
      </relatedItem>
    """)
    expected_identified_by = [
        {
            "@type": "Local",
            "value": "1234",
            "source": {
                "@type": "Source",
                "code": "other",
            }
        },
        {
            "@type": "ISSN",
            "value": "5678",
        }
    ]

    assert expected_identified_by == parser.parse_mods(raw_xml)['hasSeries'][0]['identifiedBy']


def test_series_no_part_number(parser):
    raw_xml = MODS("""
      <relatedItem type="series">
        <titleInfo><title>Title</title></titleInfo>
      </relatedItem>
    """)

    assert 'partNumber' not in parser.parse_mods(raw_xml)['hasSeries'][0]['hasTitle'][0]


def test_host_volume_number_is_extracted(parser):
    raw_xml = MODS("""
      <relatedItem type="host">
        <titleInfo><title>.</title></titleInfo>
        <part><detail type="volume">1337</detail></part>
      </relatedItem>
    """)

    assert '1337' == parser.parse_mods(raw_xml)['isPartOf'][0]['hasTitle'][0]['volumeNumber']


def test_series_issue_number_is_extracted(parser):
    raw_xml = MODS("""
      <relatedItem type="series">
        <titleInfo><title>.</title></titleInfo>
        <part><detail type="issue">1337</detail></part>
      </relatedItem>
    """)

    assert '1337' == parser.parse_mods(raw_xml)['hasSeries'][0]['hasTitle'][0]['issueNumber']


def test_host_issue_number_is_extracted(parser):
    raw_xml = MODS("""
      <relatedItem type="host">
        <titleInfo><title>.</title></titleInfo>
        <part><detail type="issue">1337</detail></part>
      </relatedItem>
    """)

    assert '1337' == parser.parse_mods(raw_xml)['isPartOf'][0]['hasTitle'][0]['issueNumber']


def test_host_part_number_is_not_extracted(parser):
    raw_xml = MODS("""
      <relatedItem type="host">
        <titleInfo><title>.</title><partNumber>5</partNumber></titleInfo>
        <part><detail type="issue">1337</detail></part>
      </relatedItem>
    """)

    assert 'partNumber' not in parser.parse_mods(raw_xml)['isPartOf'][0]['hasTitle'][0]


def test_host_include_id_type_issue_number(parser):
    raw_xml = MODS("""
      <relatedItem type="host">
        <titleInfo><title>Title</title></titleInfo>
        <identifier type="issue number">4</identifier>
      </relatedItem>
    """)
    expected_identified_by = [
        {
            "@type": "IssueNumber",
            "value": "4",
        }
    ]

    assert expected_identified_by == parser.parse_mods(raw_xml)['isPartOf'][0]['identifiedBy']


def test_handle_empty_detail_type_issue(parser):
    raw_xml = MODS("""
      <relatedItem type="host">
        <titleInfo><title>.</title></titleInfo>
        <part>
            <detail type="issue"/>
        </part>
      </relatedItem>
    """)

    assert {'@type': 'Title', 'mainTitle': '.'} == parser.parse_mods(raw_xml)['isPartOf'][0]['hasTitle'][0]


def test_handle_empty_start_and_end_for_extent(parser):
    raw_xml = MODS("""
      <relatedItem type="host">
        <titleInfo><title>.</title></titleInfo>
        <part>
            <extent><start/><end/></extent>
        </part>
      </relatedItem>
    """)

    assert {'@type': 'Title', 'mainTitle': '.'} == parser.parse_mods(raw_xml)['isPartOf'][0]['hasTitle'][0]


def test_series_article_number_is_extracted(parser):
    raw_xml = MODS("""
      <relatedItem type="series">
        <titleInfo><title>.</title></titleInfo>
        <part><detail type="artNo">1337</detail></part>
      </relatedItem>
    """)

    assert '1337' == parser.parse_mods(raw_xml)['hasSeries'][0]['hasTitle'][0]['articleNumber']


@pytest.mark.parametrize("mods_identifier,bibframe_type", [
    ('doi', 'DOI'),
    ('isbn', 'ISBN'),
    ('issn', 'ISSN'),
    ('eissn', 'ISSN'),
    ('issue number', 'IssueNumber')
])
def test_host_identifier_is_extracted(mods_identifier, bibframe_type, parser):
    raw_xml = MODS("""
      <relatedItem type="host">
        <identifier type="{}">foo</identifier>
      </relatedItem>
    """.format(mods_identifier))
    identified_by = [
        {
            "@type": bibframe_type,
            "value": "foo"
        }
    ]

    assert len(parser.parse_mods(raw_xml)['isPartOf']) == 1
    assert identified_by == parser.parse_mods(raw_xml)['isPartOf'][0]['identifiedBy']


def test_host_only_gets_position_information_on_forst_title_instance(parser):
    raw_xml = MODS("""
      <relatedItem type="host">
        <titleInfo><title>First Title</title></titleInfo>
        <titleInfo><title>Second Title</title></titleInfo>
        <part>
            <detail type="volume"><number>1</number></detail>
            <detail type="issue"><number>2</number></detail>
            <detail type="artNo"><number>3</number></detail>
            <detail type="issue number"><number>4</number></detail>
        </part>
      </relatedItem>
    """)

    expected = {
        '@type': 'Work',
        'hasTitle': [
            {
                '@type': 'Title',
                'mainTitle': 'First Title',
                'articleNumber': '3',
                'issueNumber': '4',
                'volumeNumber': '1'
            },
            {
                '@type': 'Title',
                'mainTitle': 'Second Title'
            }
        ]
    }

    assert expected == parser.parse_mods(raw_xml)['isPartOf'][0]


def test_series_only_gets_position_information_on_forst_title_instance(parser):
    raw_xml = MODS("""
      <relatedItem type="series">
        <titleInfo><title>First Title</title></titleInfo>
        <titleInfo><title>Second Title</title></titleInfo>
        <part>
            <detail type="volume"><number>1</number></detail>
            <detail type="issue"><number>2</number></detail>
            <detail type="artNo"><number>3</number></detail>
            <detail type="issue number"><number>4</number></detail>
        </part>
      </relatedItem>
    """)

    expected = {
        '@type': 'Work',
        'hasTitle': [
            {
                '@type': 'Title',
                'mainTitle': 'First Title',
                'articleNumber': '3',
                'issueNumber': '4',
                'volumeNumber': '1'
            },
            {
                '@type': 'Title',
                'mainTitle': 'Second Title'
            }
        ]
    }

    assert expected == parser.parse_mods(raw_xml)['hasSeries'][0]


@pytest.mark.parametrize("mods_identifier,bibframe_type", [
    ('doi', 'DOI'),
    ('isbn', 'ISBN'),
    ('issn', 'ISSN'),
    ('eissn', 'ISSN')
])
def test_series_identifier_is_extracted(mods_identifier, bibframe_type, parser):
    raw_xml = MODS("""
      <relatedItem type="series">
        <identifier type="{}">foo</identifier>
      </relatedItem>
    """.format(mods_identifier))
    identified_by = [
        {
            "@type": bibframe_type,
            "value": "foo"
        }
    ]

    assert len(parser.parse_mods(raw_xml)['hasSeries']) == 1
    assert identified_by == parser.parse_mods(raw_xml)['hasSeries'][0]['identifiedBy']


def test_series_note_is_extracted(parser):
    raw_xml = MODS("""
      <relatedItem type="series">
        <note>foo</note>
        <note>bar</note>
      </relatedItem>
    """)

    notes = [{'@type': 'Note', 'label': 'foo'}, {'@type': 'Note', 'label': 'bar'}]

    assert len(parser.parse_mods(raw_xml)['hasSeries']) == 1
    assert notes == parser.parse_mods(raw_xml)['hasSeries'][0]['hasNote']


def test_host_note_is_extracted(parser):
    raw_xml = MODS("""
      <relatedItem type="host">
        <note>foo</note>
        <note>bar</note>
      </relatedItem>
      <relatedItem type="host">
        <note>arg</note>
      </relatedItem>
    """)

    notes = [
        {'@type': 'Note', 'label': 'foo'},
        {'@type': 'Note', 'label': 'bar'},
        {'@type': 'Note', 'label': 'arg'}
    ]
    assert len(parser.parse_mods(raw_xml)['isPartOf']) == 2
    assert notes[:2] == parser.parse_mods(raw_xml)['isPartOf'][0]['hasNote']
    assert notes[2:] == parser.parse_mods(raw_xml)['isPartOf'][1]['hasNote']


def test_host_with_note_and_citation_is_extracted(parser):
    raw_xml = MODS("""
      <relatedItem type="host">
        <note>foo</note>
        <part>
            <citation><caption>bar</caption></citation>
        </part>
      </relatedItem>
    """)

    notes = [
        {'@type': 'Note', 'label': 'foo'},
        {'@type': 'Note', 'label': 'bar', 'noteType': 'partText'}
    ]

    assert len(parser.parse_mods(raw_xml)['isPartOf']) == 1
    assert notes == parser.parse_mods(raw_xml)['isPartOf'][0]['hasNote']


def test_host_citation_is_extracted(parser):
    raw_xml = MODS("""
      <relatedItem type="host">
        <part>
            <citation><caption>foo</caption></citation>
            <citation><caption>bar</caption></citation>
        </part>
        <part>
            <citation><caption>baz</caption></citation>
        </part>
      </relatedItem>
      <relatedItem type="host">
        <part>
            <citation><caption>arg</caption></citation>
        </part>
      </relatedItem>
    """)

    notes = [
        {'@type': 'Note', 'label': 'foo', 'noteType': 'partText'},
        {'@type': 'Note', 'label': 'bar', 'noteType': 'partText'},
        {'@type': 'Note', 'label': 'baz', 'noteType': 'partText'},
        {'@type': 'Note', 'label': 'arg', 'noteType': 'partText'}
    ]

    assert len(parser.parse_mods(raw_xml)['isPartOf']) == 2
    assert notes[:3] == parser.parse_mods(raw_xml)['isPartOf'][0]['hasNote']
    assert notes[3:] == parser.parse_mods(raw_xml)['isPartOf'][1]['hasNote']


def test_host_with_open_ended_extent(parser):
    raw_xml = MODS("""
      <relatedItem type="host">
        <part>
            <extent><start>234</start></extent>
        </part>
      </relatedItem>
    """)

    assert len(parser.parse_mods(raw_xml)['isPartOf']) == 1
    assert parser.parse_mods(raw_xml)['isPartOf'][0]['hasInstance'] == {
        '@type': 'Instance',
        'extent': [{'@type': 'Extent', 'label': '234-'}]
    }


def test_host_with_empty_part_element(parser):
    raw_xml = MODS("""
      <relatedItem type="host"><part/></relatedItem>
    """)

    assert parser.parse_mods(raw_xml)['isPartOf'] == [{'@type': 'Work'}]


def test_host_with_empty_extent_element(parser):
    raw_xml = MODS("""
      <relatedItem type="host"><part><extent/></part></relatedItem>
    """)

    assert parser.parse_mods(raw_xml)['isPartOf'] == [{'@type': 'Work'}]


def test_series_with_empty_part_element(parser):
    raw_xml = MODS("""
      <relatedItem type="series"><part/></relatedItem>
    """)

    assert parser.parse_mods(raw_xml)['hasSeries'] == [{'@type': 'Work'}]


def test_series_with_empty_extent_element(parser):
    raw_xml = MODS("""
      <relatedItem type="series"><part><extent/></part></relatedItem>
    """)

    assert parser.parse_mods(raw_xml)['hasSeries'] == [{'@type': 'Work'}]


def test_host_with_open_beginning_extent(parser):
    raw_xml = MODS("""
      <relatedItem type="host">
        <part>
            <extent><end>234</end></extent>
        </part>
      </relatedItem>
    """)

    assert len(parser.parse_mods(raw_xml)['isPartOf']) == 1
    assert parser.parse_mods(raw_xml)['isPartOf'][0]['hasInstance'] == {
        '@type': 'Instance',
        'extent': [{'@type': 'Extent', 'label': '-234'}]
    }


def test_empty_start_and_end_are_ignored(parser):
    raw_xml = MODS("""
      <relatedItem type="host">
        <part>
            <extent>
                <start/>
                <end/>
            </extent>
        </part>
      </relatedItem>
    """)
    assert len(parser.parse_mods(raw_xml)['isPartOf']) == 1
    assert 'hasInstance' not in parser.parse_mods(raw_xml)['isPartOf'][0]


def test_host_with_closed_extent(parser):
    raw_xml = MODS("""
      <relatedItem type="host">
        <part>
            <extent>
                <start>123</start>
                <end>234</end>
            </extent>
        </part>
      </relatedItem>
    """)
    assert len(parser.parse_mods(raw_xml)['isPartOf']) == 1
    assert parser.parse_mods(raw_xml)['isPartOf'][0]['hasInstance'] == {
        '@type': 'Instance',
        'extent': [{'@type': 'Extent', 'label': '123-234'}]
    }


def test_host_with_total_extent(parser):
    raw_xml = MODS("""
      <relatedItem type="host">
        <part>
            <extent>
                <total>123</total>
            </extent>
        </part>
      </relatedItem>
    """)

    assert len(parser.parse_mods(raw_xml)['isPartOf']) == 1
    assert parser.parse_mods(raw_xml)['isPartOf'][0]['hasInstance'] == {
        '@type': 'Instance',
        'extent': [{'@type': 'Extent', 'label': '123'}]
    }


def test_host_with_multiple_extents(parser):
    raw_xml = MODS("""
      <relatedItem type="host">
        <part>
            <extent>
                <start>123</start>
                <end>234</end>
                <total>345</total>
            </extent>
            <extent>
                <start>75</start>
            </extent>
            <extent>
                <end>76</end>
            </extent>
            <extent>
                <total>77</total>
            </extent>
        </part>
        <part><extent><start>1</start></extent></part>
      </relatedItem>
      <relatedItem type="host">
        <part><extent><start>2</start></extent></part>
      </relatedItem>
    """)

    actual = parser.parse_mods(raw_xml)['isPartOf']
    assert len(actual) == 2
    assert actual[0]['hasInstance'] == {
        '@type': 'Instance',
        'extent': [
            {'@type': 'Extent', 'label': '123-234'},
            {'@type': 'Extent', 'label': '345'},
            {'@type': 'Extent', 'label': '75-'},
            {'@type': 'Extent', 'label': '-76'},
            {'@type': 'Extent', 'label': '77'},
            {'@type': 'Extent', 'label': '1-'}
        ]
    }
    assert actual[1]['hasInstance'] == {
        '@type': 'Instance',
        'extent': [{'@type': 'Extent', 'label': '2-'}]
    }


@pytest.mark.parametrize("display_label", ['print', 'electronic'])
def test_series_identifier_with_display_label_is_extracted(display_label, parser):
    raw_xml = MODS("""
      <relatedItem type="host">
        <identifier type="issn" displayLabel="{}">0943-7444</identifier>
      </relatedItem>
    """.format(display_label))
    identified_by = [
        {
            "@type": "ISSN",
            "value": "0943-7444",
            "qualifier": display_label
        }
    ]

    assert len(parser.parse_mods(raw_xml)['isPartOf']) == 1
    assert identified_by == parser.parse_mods(raw_xml)['isPartOf'][0]['identifiedBy']


def test_empty_issn_series_identifier_does_not_create_bibframe_field(parser):
    raw_xml = MODS("""
          <relatedItem type="series">
            <identifier type="issn"/>
          </relatedItem>
        """)
    identified_by = []

    assert identified_by == parser.parse_mods(raw_xml)['hasSeries'][0]['identifiedBy']


def test_empty_issn_is_part_of_identifier_does_not_create_bibframe_field(parser):
    raw_xml = MODS("""
          <relatedItem type="host">
            <identifier type="issn"/>
          </relatedItem>
        """)
    identified_by = []

    assert identified_by == parser.parse_mods(raw_xml)['isPartOf'][0]['identifiedBy']


def test_orcid_person_id_is_extracted(parser):
    raw_xml = MODS("""
      <name type="personal">
        <description type="orcid">0000-0003-4169-4777</description>
      </name>
    """)

    identified_by = [{"@type": "ORCID", "value": "0000-0003-4169-4777"}]
    assert identified_by == parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['agent']['identifiedBy']


def test_local_person_id_is_extracted(parser):
    raw_xml = MODS("""<name type="personal" authority="lnu" xlink:href="kogoaa"/> """)
    identified_by = [{"@type": "Local", "value": "kogoaa", "source": {"@type": "Source", "code": "lnu"}}]
    assert identified_by == parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['agent']['identifiedBy']


@pytest.mark.parametrize("modsform", [
    "abr", "act", "adp", "rcp", "anl", "anm", "ann", "apl", "ape", "app", "arc",
    "arr", "acp", "adi", "art", "ard", "asg", "asn", "att", "auc", "aut", "aqt",
    "aft", "aud", "aui", "ato", "ant", "bnd", "bdd", "blw", "bkd", "bkp", "bjd",
    "bpd", "bsl", "brl", "brd", "cll", "ctg", "cas", "cns", "chr", "cng", "cli",
    "cor", "col", "clt", "clr", "cmm", "cwt", "com", "cpl", "cpt", "cpe", "cmp",
    "cmt", "ccp", "cnd", "con", "csl", "csp", "cos", "cot", "coe", "cts", "ctt",
    "cte", "ctr", "ctb", "cpc", "cph", "crr", "crp", "cst", "cou", "crt", "cov",
    "cre", "cur", "dnc", "dtc", "dtm", "dte", "dto", "dfd", "dft", "dfe", "dgg",
    "dgs", "dln", "dpc", "dpt", "dsr", "drt", "dis", "dbp", "dst", "dnr", "drm",
    "dub", "edt", "edc", "edm", "elg", "elt", "enj", "eng", "egr", "etr", "evp",
    "exp", "fac", "fld", "fds", "fmd", "flm", "fmp", "fmk", "fpy", "frg", "fmo",
    "fnd", "gis", "hnr", "hst", "his", "ilu", "ill", "ins", "itr", "ive", "ivr",
    "inv", "isb", "jud", "jug", "lbr", "ldr", "lsa", "led", "len", "lil", "lit",
    "lie", "lel", "let", "lee", "lbt", "lse", "lso", "lgd", "ltg", "lyr", "mfp",
    "mfr", "mrb", "mrk", "med", "mdc", "mte", "mtk", "mod", "mon", "mcp", "msd",
    "mus", "nrt", "osp", "opn", "orm", "org", "oth", "own", "pan", "ppm", "pta",
    "pth", "pat", "prf", "pma", "pht", "ptf", "ptt", "pte", "plt", "pra", "pre",
    "prt", "pop", "prm", "prc", "pro", "prn", "prs", "pmn", "prd", "prp", "prg",
    "pdr", "pfr", "prv", "pup", "pbl", "pbd", "ppt", "rdd", "rpc", "rce", "rcd",
    "red", "ren", "rpt", "rps", "rth", "rtm", "res", "rsp", "rst", "rse", "rpy",
    "rsg", "rsr", "rev", "rbr", "sce", "sad", "aus", "scr", "scl", "spy", "sec",
    "sll", "std", "stg", "sgn", "sng", "sds", "spk", "spn", "sgd", "stm", "stn",
    "str", "stl", "sht", "srv", "tch", "tcd", "tld", "tlp", "ths", "trc", "trl",
    "tyd", "tyg", "uvp", "vdg", "vac", "wit", "wde", "wdc", "wam", "wac", "wat",
    "wal", "wst", "win", "wpr"
])
def test_person_role_is_extracted(modsform, parser):
    raw_xml = MODS("""
      <name type="personal" authority="lnu" xlink:href="kogoaa">
        <role>
          <roleTerm type="code" authority="marcrelator">{}</roleTerm>
        </role>
      </name>
    """.format(modsform))

    role = [{'@id': 'http://id.loc.gov/vocabulary/relators/{}'.format(modsform)}]
    assert role == parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['role']


def test_corporate_contribution_agent_with_authority_and_xlink(parser):
    raw_xml = MODS("""
      <name type="corporate" authority="lnu" xlink:href="kogoaa"></name>
    """)

    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['agent']
    expected = {
        '@type': 'Organization',
        'identifiedBy': [{'@type': 'Local', 'value': 'kogoaa', 'source': {'@type': 'Source', 'code': 'lnu'}}]
    }
    assert actual == expected


def test_conference_contribution_agent_it_extracted_as_meeting(parser):
    raw_xml = MODS("""<name type="conference"></name> """)
    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['agent']
    expected = {'@type': 'Meeting'}
    assert actual == expected


def test_corporate_contribution_agent_with_xlink(parser):
    raw_xml = MODS("""<name type="corporate" xlink:href="kogoaa"></name> """)

    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['agent']
    expected = {'@type': 'Organization'}
    assert actual == expected


def test_corporate_contribution_agent_without_attributes(parser):
    raw_xml = MODS("""<name type="corporate"></name> """)
    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['agent']
    expected = {'@type': 'Organization'}
    assert actual == expected


def test_corporate_contribution_agent_with_authority(parser):
    raw_xml = MODS("""<name type="corporate" authority="lnu"></name> """)
    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['agent']
    expected = {
        '@type': 'Organization',
    }
    assert actual == expected


def test_corporate_contribution_agent_with_authority_and_single_name(parser):
    raw_xml = MODS("""<name type="corporate" authority="lnu">
    <namePart>foo</namePart>
    </name> """)
    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['agent']
    expected = {
        '@type': 'Organization',
        'name': 'foo',
    }
    assert actual == expected


def test_corporate_contribution_agent_with_authority_and_multiple_names(parser):
    raw_xml = MODS("""<name type="corporate" authority="lnu">
    <namePart>foo</namePart>
    <namePart>bar</namePart>
    </name> """)
    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['agent']
    expected = {
        '@type': 'Organization',
        'name': ['foo', 'bar']
    }
    assert actual == expected


def test_persons_are_is_extracted(parser):
    raw_xml = MODS("""
      <name type="personal" authority="lnu" xlink:href="kogoaa">
        <namePart type="family">Golub</namePart>
        <namePart type="given">Koraljka</namePart>
        <namePart type="date">1945-1997</namePart>
        <namePart type="foo">Other name variant</namePart>
      </name>
    """)

    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['agent']

    assert actual['familyName'] == 'Golub'
    assert actual['givenName'] == 'Koraljka'
    assert actual['lifeSpan'] == '1945-1997'
    assert actual['foo'] == 'Other name variant'


def test_corporate_affiliation_is_extracted(parser):
    raw_xml = MODS("""
      <name type="corporate" authority="lnu" xlink:href="kogoaa">
        <affiliation>Affiliation Name</affiliation>
      </name>
    """)

    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['hasAffiliation']
    assert actual == [{'@type': 'Organization', 'name': 'Affiliation Name'}]


def test_ispartof_is_not_present_when_there_are_no_affiliations(parser):
    raw_xml = MODS("""
      <name type="corporate" authority="lnu" xlink:href="kogoaa">
       <role>
          <roleTerm type="code" authority="marcrelator">edt</roleTerm>
        </role>
      </name>
    """)

    assert 'hasAffiliation' not in parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]


def test_carrier_is_not_present_if_form_is_not_part_of_physical_description(parser):
    raw_xml = MODS("""
      <physicalDescription xmlns:xlink="http://www.w3.org/1999/xlink">
        <extent>536 s.</extent>
      </physicalDescription>
    """)

    assert 'carrier' not in parser.parse_mods(raw_xml)


def test_affiliation_is_extracted(parser):
    raw_xml = MODS("""
      <name type="personal" authority="lnu" xlink:href="kogoaa">
        <affiliation>Affiliation Name</affiliation>
      </name>
    """)

    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['hasAffiliation']
    import json
    print(json.dumps(actual, indent=4))
    assert actual == [{'@type': 'Organization', 'name': 'Affiliation Name'}]


def test_affiliation_is_split_up_by_language(parser):
    raw_xml = MODS("""
      <name type="personal" authority="lnu" xlink:href="kogoaa">
        <affiliation lang="swe" authority="v1000032" xsi:type="stringPlusLanguagePlusAuthority" valueURI="v1000041">Institutioner</affiliation>
        <affiliation lang="eng" authority="v1000032" xsi:type="stringPlusLanguagePlusAuthority" valueURI="v1000041">Departments</affiliation>
        <affiliation lang="swe" authority="v1000041" xsi:type="stringPlusLanguagePlusAuthority" valueURI="v1000088">Språk- och litteraturcentrum</affiliation>
        <affiliation lang="eng" authority="v1000041" xsi:type="stringPlusLanguagePlusAuthority" valueURI="v1000088">Centre for Languages and Literature</affiliation>
        <affiliation lang="swe" authority="v1000088" xsi:type="stringPlusLanguagePlusAuthority" valueURI="v1000109">Sektion 3</affiliation>
        <affiliation lang="eng" authority="v1000088" xsi:type="stringPlusLanguagePlusAuthority" valueURI="v1000109">Section 3</affiliation>
      </name>
    """)

    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['hasAffiliation']
    expected = [
        {
            "@type": "Organization",
            "nameByLang": {
                "swe": "Sektion 3"
            },
            "identifiedBy": [
                {
                    "@type": "Local",
                    "value": "v1000109",
                    "source": {
                        "@type": "Source",
                        "code": "v1000088"
                    },
                }
            ],
            "hasAffiliation": [
                {
                    "@type": "Organization",
                    "nameByLang": {
                        "swe": "Språk- och litteraturcentrum"
                    },
                    "identifiedBy": [
                        {
                            "@type": "Local",
                            "value": "v1000088",
                            "source": {
                                "@type": "Source",
                                "code": "v1000041"
                            },
                        }
                    ],
                    "hasAffiliation": [
                        {
                            "@type": "Organization",
                            "nameByLang": {
                                "swe": "Institutioner"
                            },
                            "identifiedBy": [
                                {
                                    "@type": "Local",
                                    "value": "v1000041",
                                    "source": {
                                        "@type": "Source",
                                        "code": "v1000032"
                                    },
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "@type": "Organization",
            "nameByLang": {
                "eng": "Section 3"
            },
            "identifiedBy": [
                {
                    "@type": "Local",
                    "value": "v1000109",
                    "source": {
                        "@type": "Source",
                        "code": "v1000088"
                    },
                }
            ],
            "hasAffiliation": [
                {
                    "@type": "Organization",
                    "nameByLang": {
                        "eng": "Centre for Languages and Literature"
                    },
                    "identifiedBy": [
                        {
                            "@type": "Local",
                            "value": "v1000088",
                            "source": {
                                "@type": "Source",
                                "code": "v1000041"
                            },
                        }
                    ],
                    "hasAffiliation": [
                        {
                            "@type": "Organization",
                            "nameByLang": {
                                "eng": "Departments"
                            },
                            "identifiedBy": [
                                {
                                    "@type": "Local",
                                    "value": "v1000041",
                                    "source": {
                                        "@type": "Source",
                                        "code": "v1000032"
                                    },
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]

    assert actual == expected


def test_affiliation_tree_is_extracted(parser):
    raw_xml = MODS("""
      <name type="personal" authority="lnu" xlink:href="kogoaa">
        <affiliation valueURI="X" authority="kb.se">A</affiliation>
        <affiliation valueURI="Y" authority="X">B</affiliation>
        <affiliation valueURI="Z" authority="Y">C</affiliation>
      </name>
    """)

    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['hasAffiliation']
    expected = [
        {
            "@type": "Organization",
            "name": "C",
            "identifiedBy": [
                {
                    "@type": "Local",
                    "value": "Z",
                    "source": {
                        "@type": "Source",
                        "code": "Y"
                    },
                }
            ],
            "hasAffiliation": [
                {
                    "@type": "Organization",
                    "name": "B",
                    "identifiedBy": [
                        {
                            "@type": "Local",
                            "value": "Y",
                            "source": {
                                "@type": "Source",
                                "code": "X"
                            },
                        }
                    ],
                    "hasAffiliation": [
                        {
                            "@type": "Organization",
                            "name": "A",
                            "identifiedBy": [
                                {
                                    "@type": "URI",
                                    "value": "X",
                                    "source": {
                                        "@type": "Source",
                                        "code": "kb.se",
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
    assert actual == expected


def test_affiliation_with_identified_by(parser):
    raw_xml = MODS("""
    <name type="personal" authority="kth" xlink:href="u1qvds70">
        <namePart type="family">Afamilyname</namePart>
        <namePart type="given">Agivenname</namePart>
        <namePart type="date">1990-</namePart>
        <role>
            <roleTerm type="code" authority="marcrelator">aut</roleTerm>
        </role>
        <affiliation lang="swe" authority="kb.se" xsi:type="stringPlusLanguagePlusAuthority" valueURI="kth.se">KTH</affiliation>
        <affiliation lang="swe" xsi:type="stringPlusLanguagePlusAuthority" authority="kth.se" valueURI="Elektronik">Elektronik</affiliation>
        <description xsi:type="identifierDefinition" type="orcid">XX</description>
    </name>
    """)

    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['hasAffiliation']
    expected = [
        {
            "@type": "Organization",
            "nameByLang": {
                "swe": "Elektronik"
            },
            "identifiedBy": [
                {
                    "@type": "Local",
                    "value": "Elektronik",
                    "source": {
                        "@type": "Source",
                        "code": "kth.se"
                    }
                }
            ],
            "hasAffiliation": [
                {
                    "@type": "Organization",
                    "nameByLang": {
                        "swe": "KTH"
                    },
                    "identifiedBy": [
                        {
                            "@type": "URI",
                            "value": "kth.se",
                            "source": {
                                "@type": "Source",
                                "code": "kb.se"
                            }
                        }
                    ]
                }
            ]
        }
    ]
    assert actual == expected


def test_circular_affiliation_are_skipped(parser):
    raw_xml = MODS("""
      <name type="personal" authority="lnu" xlink:href="kogoaa">
        <affiliation valueURI="" authority="">Self reference</affiliation>
        <affiliation valueURI="kb.se" authority="foo">Circular 0</affiliation>
        <affiliation valueURI="foo" authority="kb.se">Circular 1</affiliation>
      </name>
    """)

    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['hasAffiliation']
    assert actual == []


def test_parallell_affiliation_trees_are_extracted(parser):
    raw_xml = MODS("""
      <name type="personal" authority="lnu" xlink:href="kogoaa">
        <affiliation valueURI="X1" authority="kb.se">A1</affiliation>
        <affiliation valueURI="Y1" authority="X1">B1</affiliation>
        <affiliation valueURI="X2" authority="kb.se">A2</affiliation>
        <affiliation valueURI="Y2" authority="X2">B2</affiliation>
      </name>
    """)

    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['hasAffiliation']
    expected = [
        {
            "@type": "Organization",
            "name": "B1",
            "identifiedBy": [
                {
                    "@type": "Local",
                    "value": "Y1",
                    "source": {
                        "@type": "Source",
                        "code": "X1"
                    },
                }
            ],
            "hasAffiliation": [
                {
                    "@type": "Organization",
                    "name": "A1",
                    "identifiedBy": [
                        {
                            "@type": "URI",
                            "value": "X1",
                            "source": {
                                "@type": "Source",
                                "code": "kb.se",
                            }
                        }
                    ]
                }
            ]
        },
        {
            "@type": "Organization",
            "name": "B2",
            "identifiedBy": [
                {
                    "@type": "Local",
                    "value": "Y2",
                    "source": {
                        "@type": "Source",
                        "code": "X2"
                    },
                }
            ],
            "hasAffiliation": [
                {
                    "@type": "Organization",
                    "name": "A2",
                    "identifiedBy": [
                        {
                            "@type": "URI",
                            "value": "X2",
                            "source": {
                                "@type": "Source",
                                "code": "kb.se",
                            }
                        }
                    ]
                }
            ]
        }
    ]
    assert actual == expected


def test_branched_affiliation_trees_are_extracted(parser):
    raw_xml = MODS("""
      <name type="personal" authority="lnu" xlink:href="kogoaa">
        <affiliation valueURI="X1" authority="kb.se">A1</affiliation>
        <affiliation valueURI="Y1" authority="X1">B1</affiliation>
        <affiliation valueURI="Y2" authority="X1">B2</affiliation>
      </name>
    """)

    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['hasAffiliation']
    expected = [
        {
            "@type": "Organization",
            "name": "B1",
            "identifiedBy": [
                {
                    "@type": "Local",
                    "value": "Y1",
                    "source": {
                        "@type": "Source",
                        "code": "X1",
                    },
                }
            ],
            "hasAffiliation": [
                {
                    "@type": "Organization",
                    "name": "A1",
                    "identifiedBy": [
                        {
                            "@type": "URI",
                            "value": "X1",
                            "source": {
                                "@type": "Source",
                                "code": "kb.se",
                            }
                        }
                    ]
                }
            ]
        },
        {
            "@type": "Organization",
            "name": "B2",
            "identifiedBy": [
                {
                    "@type": "Local",
                    "value": "Y2",
                    "source": {
                        "@type": "Source",
                        "code": "X1"
                    },
                }
            ],
            "hasAffiliation": [
                {
                    "@type": "Organization",
                    "name": "A1",
                    "identifiedBy": [
                        {
                            "@type": "URI",
                            "value": "X1",
                            "source": {
                                "@type": "Source",
                                "code": "kb.se",
                            }
                        }
                    ]
                }
            ]
        }
    ]
    assert actual == expected


def test_affiliation_language_is_extracted(parser):
    raw_xml = MODS("""
      <name type="personal" authority="lnu" xlink:href="kogoaa">
        <affiliation lang="swe">Affiliation Name</affiliation>
      </name>
    """)

    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['hasAffiliation']

    assert actual == [
        {
            '@type': 'Organization',
            "nameByLang": {
                "swe": "Affiliation Name"
            },
        }
    ]


def test_affiliation_authority_is_extracted(parser):
    raw_xml = MODS("""
      <name type="personal" authority="lnu" xlink:href="kogoaa">
        <affiliation authority="kb.se">Affiliation Name</affiliation>
      </name>
    """)

    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['hasAffiliation']

    assert actual == [
        {
            '@type': 'Organization',
            'name': 'Affiliation Name',
        }
    ]


def test_affiliation_identifier_is_uri_when_authority_is_kb(parser):
    raw_xml = MODS("""
      <name type="personal" authority="lnu" xlink:href="kogoaa">
        <affiliation authority="kb.se" valueURI="abc123">Affiliation Name</affiliation>
      </name>
    """)

    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['hasAffiliation']

    assert actual == [
        {
            '@type': 'Organization',
            'name': 'Affiliation Name',
            'identifiedBy': [
                {
                    '@type': 'URI',
                    'value': 'abc123',
                    "source": {
                        "@type": "Source",
                        "code": "kb.se",
                    }
                }
            ]
        }
    ]


def test_affiliation_identifier_is_local_when_authority_is_not_kb(parser):
    raw_xml = MODS("""
      <name type="personal" authority="lnu" xlink:href="kogoaa">
        <affiliation authority="lnu.se" valueURI="abc123">Affiliation Name</affiliation>
      </name>
    """)

    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['hasAffiliation']

    assert actual == [
        {
            '@type': 'Organization',
            'name': 'Affiliation Name',
            'identifiedBy': [
                {
                    '@type': 'Local',
                    'value': 'abc123',
                    'source': {
                        '@type': 'Source',
                        'code': 'lnu.se',
                    },
                }
            ]
        }
    ]


def test_affiliation_type_code_is_collaboration(parser):
    raw_xml = MODS("""
      <name type="personal" authority="lnu" xlink:href="kogoaa">
        <affiliation type="code">Affiliation Name</affiliation>
      </name>
    """)

    actual = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['hasAffiliation']

    assert actual == [{'@type': 'Collaboration', 'name': 'Affiliation Name'}]


def test_affiliation_non_organizational(parser):
    raw_xml = MODS("""
    <name type="personal" authority="lnu" xlink:href="xxx">
        <affiliation lang="eng" authority="kb.se/collaboration" valueURI="e-science.se">Affiliation Name</affiliation>
    </name>
    """)
    expected_affiliations = [
        {
            "@type": "Collaboration",
            "nameByLang": {
                "eng": "Affiliation Name"
            },
            "identifiedBy": [
                {
                    "@type": "URI",
                    "value": "e-science.se"
                }
            ]
        }
    ]
    converted_affiliations = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['hasAffiliation']
    assert expected_affiliations == converted_affiliations


def test_affiliation_to_country(parser):
    raw_xml = MODS("""
    <name type="personal" authority="lnu" xlink:href="xxx">
        <affiliation lang="eng" authority="kb.se" valueURI="https://id.kb.se/country/xxx"></affiliation>
    </name>
    """)
    expected_affiliations = [
        {
            "@id": "https://id.kb.se/country/xxx"
        }
    ]
    converted_affiliations = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['hasAffiliation']
    assert expected_affiliations == converted_affiliations


def test_output_type_with_authority_kb_se_is_extracted(parser):
    raw_xml = MODS("""<genre authority="kb.se" type="outputType">dok</genre>""")
    expected = [{'@id': 'https://id.kb.se/term/swepub/output/dok'}]
    actual = parser.parse_mods(raw_xml)['instanceOf']['genreForm']
    assert actual == expected


def test_output_type_with_unknown_authority_is_ignored(parser):
    raw_xml = MODS("""<genre authority="foo" type="outputType">dok</genre>""")
    expected = []
    actual = parser.parse_mods(raw_xml)['instanceOf']['genreForm']
    assert actual == expected


@pytest.mark.parametrize("publicationtype, publicationtype_longform, contenttype, outputtype", [
    ('art', 'JournalArticle', 'ref', 'publication/journal-article'),
    ('art', 'JournalArticle', 'vet', 'publication/magazine-article'),
    ('art', 'JournalArticle', 'pop', 'publication/newspaper-article'),
    ('bok', 'Book', 'vet', 'publication/book'),
    ('kon', 'ConferencePaper', 'vet', 'conference'),
    ('kap', 'BookChapter', 'vet', 'publication/book-chapter'),
    ('dok', 'DoctoralThesis', 'vet', 'publication/doctoral-thesis'),
    ('rap', 'Report', 'vet', 'publication/report'),
    ('rec', 'Review', 'vet', 'publication/book-review'),
    ('sam', 'EditorialCollection', 'vet', 'publication/edited-book'),
    ('for', 'ResearchReview', 'ref', 'publication/review-article'),
    ('kfu', 'ArtisticWork', 'vet', 'artistic-work'),
    ('lic', 'LicentiateThesis', 'vet', 'publication/licentiate-thesis'),
    ('pat', 'Patent', 'vet', 'intellectual-property/patent'),
    ('pro', 'EditorialProceedings', 'vet', 'conference/proceeding'),
    ('ovr', 'OtherPublication', 'vet', 'publication')
])
def test_publication_and_output_type(publicationtype, publicationtype_longform, contenttype, outputtype, parser):
    expected = [{'@id': 'https://id.kb.se/term/swepub/{}'.format(publicationtype_longform)},
                {'@id': 'https://id.kb.se/term/swepub/svep/{}'.format(contenttype)},
                {'@id': 'https://id.kb.se/term/swepub/output/{}'.format(outputtype)}]

    raw_xml_without_outputtype \
        = MODS(f"""<genre authority="svep" type="publicationType">{publicationtype}</genre>
                   <genre authority="svep" type="contentType">{contenttype}</genre>""")
    _test_publication_and_output_type(raw_xml_without_outputtype, expected, parser)

    raw_xml_with_outputtype \
        = MODS(f"""<genre authority="svep" type="publicationType">{publicationtype}</genre>
                   <genre authority="svep" type="contentType">{contenttype}</genre>
                   <genre authority="kb.se" type="outputType">{outputtype}</genre>""")
    _test_publication_and_output_type(raw_xml_with_outputtype, expected, parser)


def _test_publication_and_output_type(raw_xml, expected, parser):
    actual = parser.parse_mods(raw_xml)['instanceOf']['genreForm']
    for e in expected:
        assert e in actual


def test_invalid_publication_type_is_ignored(parser):
    raw_xml = MODS("""<genre authority="svep" type="publicationType">foo</genre>""")
    expected = []
    actual = parser.parse_mods(raw_xml)['instanceOf']['genreForm']
    assert actual == expected


def test_valid_publication_type_with_invalid_authority(parser):
    raw_xml = MODS("""<genre authority="foo" type="publicationType">rap</genre>""")
    expected = []
    actual = parser.parse_mods(raw_xml)['instanceOf']['genreForm']
    assert actual == expected


def test_that_output_type_and_publication_type_can_be_used_together(parser):
    raw_xml = MODS("""
          <genre authority="svep" type="publicationType">ovr</genre>
          <genre authority="svep" type="publicationType">foo</genre>
          <genre authority="kb.se" type="outputType">dok</genre>
          <genre authority="fo.oo" type="outputType">dok</genre>
    """)
    # If we get an outputType in the input, we don't map the publicationType
    expected = [
        {'@id': 'https://id.kb.se/term/swepub/output/dok'},
        {'@id': 'https://id.kb.se/term/swepub/OtherPublication'},
    ]
    actual = parser.parse_mods(raw_xml)['instanceOf']['genreForm']
    assert actual == expected


def test_primary_electronic_locator_is_extracted(parser):
    raw_xml = MODS("""
        <location>
            <url note="free/2015-01-01" usage="primary" displayLabel="FULLTEXT">
                http://hh.divaportal.org/smash/get/diva2:239322/FULLTEXT01
            </url>
        </location>
    """)
    expected = [
        {
            '@type': 'Resource',
            'uri': 'http://hh.divaportal.org/smash/get/diva2:239322/FULLTEXT01',
            'label': 'FULLTEXT',
            'hasNote': [
                {'@type': 'Note', 'noteType': 'URL usage', 'label': 'primary'},
                {'@type': 'Note', 'label': 'free/2015-01-01'}
            ]
        }
    ]
    actual = parser.parse_mods(raw_xml)['electronicLocator']
    assert actual == expected


def test_multiple_locations_are_extracted_as_resource_locator(parser):
    raw_xml = MODS("""
        <location>
            <url note="free/2015-01-01" displayLabel="FULLTEXT1">
                http://hh.divaportal.org/smash/get/diva2:239322/FULLTEXT01
            </url>
            <url usage="primary" displayLabel="FULLTEXT2">
                http://hh.divaportal.org/smash/get/diva2:239322/FULLTEXT02
            </url>
        </location>
    """)
    expected = [
        {
            '@type': 'Resource',
            'uri': 'http://hh.divaportal.org/smash/get/diva2:239322/FULLTEXT01',
            'label': 'FULLTEXT1',
            'hasNote': [{'@type': 'Note', 'label': 'free/2015-01-01'}]
        },
        {
            '@type': 'Resource',
            'uri': 'http://hh.divaportal.org/smash/get/diva2:239322/FULLTEXT02',
            'label': 'FULLTEXT2',
            'hasNote': [{'@type': 'Note', 'noteType': 'URL usage', 'label': 'primary'}]
        }
    ]

    actual = parser.parse_mods(raw_xml)['electronicLocator']
    assert actual == expected


def test_electronic_locator_is_extracted_without_notes(parser):
    raw_xml = MODS("""
        <location>
            <url>http://hh.divaportal.org/smash/get/diva2:239322/FULLTEXT01</url>
        </location>
    """)
    expected = [
        {
            '@type': 'Resource',
            'uri': 'http://hh.divaportal.org/smash/get/diva2:239322/FULLTEXT01'
        }
    ]
    actual = parser.parse_mods(raw_xml)['electronicLocator']
    assert actual == expected


def test_uka_subjects_with_href(parser):
    raw_xml = MODS("""
        <subject lang="swe" authority="uka.se" xlink:href="60203">
            <topic>Humaniora</topic>
            <topic>Språk och litteratur</topic>
            <topic>Litteraturvetenskap</topic>
        </subject>
        <subject lang="eng" authority="uka.se" xlink:href="60203">
            <topic>Humanities</topic>
            <topic>Languages and Literature</topic>
            <topic>Literature</topic>
        </subject>
      """)
    expected = [
        {
            '@id': 'https://id.kb.se/term/uka/60203',
            '@type': 'Topic',
            'code': '60203',
            'inScheme': {
                '@id': 'https://id.kb.se/term/uka/',
                '@type': 'ConceptScheme',
                'code': 'uka.se'
            },
            'language': {'@type': 'Language', 'code': 'swe', '@id': 'https://id.kb.se/language/swe'},
            'prefLabel': 'Litteraturvetenskap',
            "broader": {
                "prefLabel": "Spr\u00e5k och litteratur",
                "broader": {
                    "prefLabel": "Humaniora",
                }
            }
        },
        {
            '@id': 'https://id.kb.se/term/uka/60203',
            '@type': 'Topic',
            'code': '60203',
            'inScheme': {
                '@id': 'https://id.kb.se/term/uka/',
                '@type': 'ConceptScheme',
                'code': 'uka.se'
            },
            'language': {'@type': 'Language', 'code': 'eng', '@id': 'https://id.kb.se/language/eng'},
            'prefLabel': 'Literature',
            "broader": {
                "prefLabel": "Languages and Literature",
                "broader": {
                    "prefLabel": "Humanities",
                }
            }
        },
    ]

    actual = parser.parse_mods(raw_xml)['instanceOf']['subject']
    assert actual == expected


def test_uka_subject_once_per_level(parser):
    raw_xml = MODS("""
        <subject lang="swe" authority="uka.se" xlink:href="6">
            <topic>Humaniora</topic>
        </subject>
        <subject lang="swe" authority="uka.se" xlink:href="602">
            <topic>Språk och litteratur</topic>
        </subject>
        <subject lang="swe" authority="uka.se" xlink:href="60203">
            <topic>Litteraturvetenskap</topic>
        </subject>
      """)
    expected = [
        {
            '@id': 'https://id.kb.se/term/uka/6',
            '@type': 'Topic',
            'code': '6',
            'inScheme': {
                '@id': 'https://id.kb.se/term/uka/',
                '@type': 'ConceptScheme',
                'code': 'uka.se'
            },
            'language': {'@type': 'Language', 'code': 'swe', '@id': 'https://id.kb.se/language/swe'},
            'prefLabel': 'Humaniora',
        },
        {
            '@id': 'https://id.kb.se/term/uka/602',
            '@type': 'Topic',
            'code': '602',
            'inScheme': {
                '@id': 'https://id.kb.se/term/uka/',
                '@type': 'ConceptScheme',
                'code': 'uka.se'
            },
            'language': {'@type': 'Language', 'code': 'swe', '@id': 'https://id.kb.se/language/swe'},
            'prefLabel': 'Spr\u00e5k och litteratur',
        },
        {
            '@id': 'https://id.kb.se/term/uka/60203',
            '@type': 'Topic',
            'code': '60203',
            'inScheme': {
                '@id': 'https://id.kb.se/term/uka/',
                '@type': 'ConceptScheme',
                'code': 'uka.se'
            },
            'language': {'@type': 'Language', 'code': 'swe', '@id': 'https://id.kb.se/language/swe'},
            'prefLabel': 'Litteraturvetenskap',
        },
    ]

    actual = parser.parse_mods(raw_xml)['instanceOf']['subject']
    assert actual == expected


def test_non_uka_subject(parser):
    raw_xml = MODS("""
        <subject lang="swe" authority="lnu.se" xlink:href="60203">
            <topic>Humaniora</topic>
        </subject>
      """)
    expected = [
        {
            '@type': 'Topic',
            'code': '60203',
            'inScheme': {
                '@id': 'lnu.se/swe',
                '@type': 'ConceptScheme',
                'code': 'lnu.se'
            },
            'language': {'@type': 'Language', 'code': 'swe', '@id': 'https://id.kb.se/language/swe'},
            'prefLabel': 'Humaniora',
        }
    ]
    actual = parser.parse_mods(raw_xml)['instanceOf']['subject']
    assert actual == expected


def test_non_uka_subject_without_language_property(parser):
    raw_xml = MODS("""
        <subject authority="lnu.se" xlink:href="60203">
            <topic>Humaniora</topic>
        </subject>
      """)
    expected = [
        {
            '@type': 'Topic',
            'code': '60203',
            'inScheme': {
                '@id': 'lnu.se',
                '@type': 'ConceptScheme',
                'code': 'lnu.se'
            },
            'prefLabel': 'Humaniora',
        }
    ]
    actual = parser.parse_mods(raw_xml)['instanceOf']['subject']
    assert actual == expected


def test_non_uka_subject_without_href_or_authority_extract_only_basic_information(parser):
    raw_xml = MODS("""
        <subject lang="swe">
            <topic>Humaniora</topic>
        </subject>
      """)
    expected = [
        {
            '@type': 'Topic',
            'prefLabel': 'Humaniora',
            'language': {'@type': 'Language', 'code': 'swe', '@id': 'https://id.kb.se/language/swe'}
        }
    ]
    actual = parser.parse_mods(raw_xml)['instanceOf']['subject']
    assert actual == expected


def test_non_uka_subject_without_href(parser):
    raw_xml = MODS("""
        <subject lang="swe" authority="lnu.se">
            <topic>Humaniora</topic>
        </subject>
      """)
    expected = [
        {
            '@type': 'Topic',
            'inScheme': {
                '@id': 'lnu.se/swe',
                '@type': 'ConceptScheme',
                'code': 'lnu.se'
            },
            'language': {'@type': 'Language', 'code': 'swe', '@id': 'https://id.kb.se/language/swe'},
            'prefLabel': 'Humaniora',
        }
    ]
    actual = parser.parse_mods(raw_xml)['instanceOf']['subject']
    assert actual == expected


def test_uka_subjects_without_href_are_ignored(parser):
    raw_xml = MODS("""
        <subject lang="swe" authority="uka.se">
            <topic>Humaniora</topic>
            <topic>Språk och litteratur</topic>
            <topic>Litteraturvetenskap</topic>
        </subject>
      """)
    expected = []
    actual = parser.parse_mods(raw_xml)['instanceOf']['subject']
    assert actual == expected


def test_single_title_element_is_converted_as_main_title(parser):
    raw_xml = MODS("""
    <titleInfo>
        <title>Twenty years to nowhere : does land use affect regeneration perspectives?</title>
    </titleInfo>
      """)
    expected = [
        {
            '@type': 'Title',
            'mainTitle': 'Twenty years to nowhere : does land use affect regeneration perspectives?'
        }
    ]
    actual = parser.parse_mods(raw_xml)['instanceOf']['hasTitle']
    assert actual == expected


def test_title_part_number_is_ignored(parser):
    raw_xml = MODS("""
    <titleInfo>
        <title>Twenty years to nowhere : does land use affect regeneration perspectives?</title>
        <partNumber>3</partNumber>
    </titleInfo>
      """)
    assert 'partNumber' not in parser.parse_mods(raw_xml)['instanceOf']['hasTitle'][0]


def test_multiple_title_elements_are_converted(parser):
    raw_xml = MODS("""
    <titleInfo>
        <title>Twenty years to nowhere</title>
        <subTitle>does land use affect regeneration perspectives?</subTitle>
        <customTitleField type="foo">bar</customTitleField>
    </titleInfo>
      """)
    expected = [
        {
            '@type': 'Title',
            'mainTitle': 'Twenty years to nowhere',
            'subtitle': 'does land use affect regeneration perspectives?',
            'foo': 'bar'
        }
    ]
    actual = parser.parse_mods(raw_xml)['instanceOf']['hasTitle']
    assert actual == expected


def test_titleInfo_can_be_repeated(parser):
    raw_xml = MODS("""
    <titleInfo>
        <title>Twenty years to nowhere</title>
    </titleInfo>
    <titleInfo>
        <title>does land use affect regeneration perspectives?</title>
    </titleInfo>
      """)
    expected = [
        {'@type': 'Title', 'mainTitle': 'Twenty years to nowhere'},
        {'@type': 'Title', 'mainTitle': 'does land use affect regeneration perspectives?'}
    ]
    actual = parser.parse_mods(raw_xml)['instanceOf']['hasTitle']
    assert actual == expected


def test_alternative_title(parser):
    raw_xml = MODS("""
    <titleInfo>
        <title>Twenty years to nowhere</title>
    </titleInfo>
    <titleInfo type="alternative">
        <title>does land use affect regeneration perspectives?</title>
    </titleInfo>
      """)
    expected = [
        {'@type': 'Title', 'mainTitle': 'Twenty years to nowhere'},
        {'@type': 'VariantTitle', 'mainTitle': 'does land use affect regeneration perspectives?'}
    ]
    actual = parser.parse_mods(raw_xml)['instanceOf']['hasTitle']
    assert actual == expected


@pytest.mark.parametrize("mods_type,bibframe_type", [
    ('text', 'Text'),
    ('stillimage', 'StillImage'),
    ('sound recording - nonmusical', 'NonMusicalAudio'),
    ('sound recording - musical', 'Music'),
    ('sound recording', 'Audio'),
    ('software, multimedia', 'Multimedia'),
    ('notated music', 'NotatedMusic'),
    ('mixed material', 'MixedMaterial'),
    ('cartographic', 'Cartography'),
    ('three dimensional object', 'Object'),
    ('moving image', 'MovingImage')
])
def test_type_of_resources(mods_type, bibframe_type, parser):
    raw_xml = MODS("""<typeOfResource>{}</typeOfResource>""".format(mods_type))
    actual = parser.parse_mods(raw_xml)['instanceOf']
    assert actual['@type'] == bibframe_type


def test_missing_or_empty_type_of_resources_defaults_to_text(parser):
    raw_xml = MODS("""<note>foo</note>""")
    actual = parser.parse_mods(raw_xml)['instanceOf']
    expected_type = 'Text'
    assert actual['@type'] == expected_type
    raw_xml = MODS("""<typeOfResource/>""")
    assert parser.parse_mods(raw_xml)['instanceOf']['@type'] == expected_type


def test_notes_with_different_types_can_be_mixed(parser):
    raw_xml = MODS("""
        <note>Parallel text in Russian and English</note>
        <note type="creatorCount">3</note>
        <note type="publicationStatus">Published</note>
        <note>Some other note</note>
        <note><p>leaky html</p></note>
        <note type="foo">ignored because unknown type foo</note>
    """)
    expected = [
        {'@type': 'CreatorCount', 'label': '3'},
        {'@type': 'PublicationStatus', '@id': 'https://id.kb.se/term/swepub/Published'},
        {'@type': 'Note', 'label': 'Parallel text in Russian and English'},
        {'@type': 'Note', 'label': 'Some other note'},
        {'@type': 'Note', 'label': 'leaky html'}
    ]
    actual = parser.parse_mods(raw_xml)['instanceOf']['hasNote']
    assert actual == expected


@pytest.mark.parametrize("mods_type,bibframe_type", [
    ('Published', 'Published'),
    ('Preprint', 'Preprint'),
    ('Submitted', 'Submitted'),
    ('Accepted', 'Accepted'),
    ('In press', 'InPress'),
    ('Epub ahead of print/Online first', 'EpubAheadOfPrintOnlineFirst'),
    ('Retracted', 'Retracted'),
])
def test_publication_status(mods_type, bibframe_type, parser):
    raw_xml = MODS("""<note type="publicationStatus">{}</note>""".format(mods_type))
    actual = parser.parse_mods(raw_xml)['instanceOf']['hasNote']
    expected = [{'@type': 'PublicationStatus', '@id': 'https://id.kb.se/term/swepub/{}'.format(bibframe_type)}]
    assert actual == expected


def test_default_publication_status_is_published(parser):
    raw_xml = MODS("""<originInfo/>""")
    actual = parser.parse_mods(raw_xml)['instanceOf']['hasNote']
    expected = [{'@type': 'PublicationStatus', '@id': 'https://id.kb.se/term/swepub/Published'}]
    assert actual == expected


def test_publication_place(parser):
    raw_xml = MODS("""
        <originInfo>
            <place>
                <placeTerm>Ankeborg</placeTerm>
            </place>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['publication']
    expected = [
        {
            '@type': 'Publication',
            'place': {
                '@type': 'Place',
                'label': 'Ankeborg'
            }
        }
    ]

    assert actual == expected


def test_date_issued_without_encoding_defaults_to_iso8601_uri(parser):
    raw_xml = MODS("""
        <originInfo>
            <dateIssued>1986-05-30</dateIssued>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['publication']
    expected = [
        {
            '@type': 'Publication',
            'date': '1986-05-30'
        }
    ]

    assert actual == expected


@pytest.mark.parametrize("date_encoding,encoding_uri", [
    ('iso8601', 'http://id.loc.gov/datatypes/edtf'),
    ('w3cdtf', 'https://www.w3.org/TR/NOTE-datetime'),
])
def test_date_encodings_are_translated_to_uri(date_encoding, encoding_uri, parser):
    raw_xml = MODS("""
        <originInfo>
            <dateIssued encoding="{}">1986-05-30</dateIssued>
        </originInfo>
    """.format(date_encoding))

    actual = parser.parse_mods(raw_xml)['publication']
    expected = [
        {
            '@type': 'Publication',
            'date': '1986-05-30'
        }
    ]

    assert actual == expected


def test_date_issued_with_explicit_encoding(parser):
    raw_xml = MODS("""
        <originInfo>
            <dateIssued encoding="foo">1986-05-30</dateIssued>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['publication']
    expected = [
        {
            '@type': 'Publication',
            'date': '1986-05-30'
        }
    ]

    assert actual == expected


def test_agent_is_extracted_as_provision_activity_agent(parser):
    raw_xml = MODS("""
        <originInfo>
            <publisher>Cambridge University Press</publisher>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['publication']
    expected = [
        {
            '@type': 'Publication',
            'agent': {
                '@type': 'Agent',
                'label': 'Cambridge University Press'
            }
        }
    ]

    assert actual == expected


def test_complete_origin_info(parser):
    raw_xml = MODS("""
        <originInfo>
            <publisher>Cambridge University Press</publisher>
            <dateIssued>1986-05-30</dateIssued>
            <place>
                <placeTerm>Ankeborg</placeTerm>
            </place>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['publication']
    expected = [
        {
            '@type': 'Publication',
            'date': '1986-05-30',
            'place': {'@type': 'Place', 'label': 'Ankeborg'},
            'agent': {'@type': 'Agent', 'label': 'Cambridge University Press'}
        }
    ]

    assert actual == expected


def test_date_other_defence(parser):
    raw_xml = MODS("""
        <originInfo>
            <dateOther type="defence">1986-05-30</dateOther>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['dissertation']
    expected = [
        {
            '@type': 'Dissertation',
            'date': '1986-05-30'
        }
    ]

    assert actual == expected


def test_date_other_availability(parser):
    raw_xml = MODS("""
        <originInfo>
            <dateOther type="available">1986-05-30</dateOther>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['provisionActivity']
    expected = [
        {
            '@type': 'Availability',
            'date': '1986-05-30'
        }
    ]

    assert actual == expected


def test_date_other_open_access(parser):
    raw_xml = MODS("""
        <originInfo>
            <dateOther type="openAccess">1986-05-30</dateOther>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['provisionActivity']
    expected = [
        {
            '@type': 'OpenAccessAvailability',
            'date': '1986-05-30'
        }
    ]

    assert actual == expected


def test_date_other_open_access_with_start_date(parser):
    raw_xml = MODS("""
        <originInfo>
            <dateOther type="openAccess" point="start">1986-05-30</dateOther>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['provisionActivity']
    expected = [
        {
            '@type': 'OpenAccessAvailability',
            'startDate': '1986-05-30'
        }
    ]

    assert actual == expected


@pytest.mark.parametrize("form", ['print', 'electronic'])
def test_form_is_extracted_as_carrier_label(form, parser):
    raw_xml = MODS("""
        <physicalDescription>
            <form>{}</form>
        </physicalDescription>
    """.format(form))

    actual = parser.parse_mods(raw_xml)['carrierType']
    expected = {'@type': 'CarrierType', 'label': form}

    assert actual == expected


@pytest.mark.parametrize("form", ['print', 'electronic'])
def test_marcform_is_extracted_as_carrier_source_label(form, parser):
    raw_xml = MODS("""
        <physicalDescription>
            <form authority="marcform">{}</form>
        </physicalDescription>
    """.format(form))

    actual = parser.parse_mods(raw_xml)['carrierType']
    expected = {'@type': 'CarrierType', 'label': form, 'source': {'@type': 'Source', 'code': 'marcform'}}

    assert actual == expected


def test_physical_description_extent_is_extracted(parser):
    raw_xml = MODS("""
        <physicalDescription>
            <extent>1 bordsduk : gul- och vitrutig ; 90 x 90 cm</extent>
        </physicalDescription>
    """)

    actual = parser.parse_mods(raw_xml)['extent']
    expected = {'@type': 'Extent', 'label': '1 bordsduk : gul- och vitrutig ; 90 x 90 cm'}

    assert actual == expected


def test_record_content_source_is_extracted_to_admin_meta_data(parser):
    raw_xml = MODS("""
        <recordInfo xmlns:xlink="http://www.w3.org/1999/xlink">
            <recordContentSource authority="my-test-authority">lu</recordContentSource>
        </recordInfo>
    """)

    actual = parser.parse_mods(raw_xml)['meta']
    expected = {
        '@type': 'AdminMetadata',
        'assigner': {'@type': 'Agent', 'label': 'lu'},
        'source': {'@type': 'Source', 'value': 'my-test-authority'},
    }

    assert actual == expected


def test_record_content_source_is_extracted_to_admin_meta_data_when_authority_is_missing(parser):
    raw_xml = MODS("""
        <recordInfo xmlns:xlink="http://www.w3.org/1999/xlink">
            <recordContentSource>lu</recordContentSource>
        </recordInfo>
    """)

    actual = parser.parse_mods(raw_xml)['meta']
    expected = {
        '@type': 'AdminMetadata',
        'assigner': {'@type': 'Agent', 'label': 'lu'}
    }

    assert actual == expected


@pytest.mark.parametrize("date_encoding,encoding_uri", [
    ('iso8601', 'http://id.loc.gov/datatypes/edtf'),
    ('w3cdtf', 'https://www.w3.org/TR/NOTE-datetime'),
])
def test_record_creation_date(date_encoding, encoding_uri, parser):
    raw_xml = MODS("""
        <recordInfo xmlns:xlink="http://www.w3.org/1999/xlink">
            <recordCreationDate encoding="{}">2016-12-23T11:16:21+1:00</recordCreationDate>
        </recordInfo>
    """.format(date_encoding))

    actual = parser.parse_mods(raw_xml)['meta']
    expected = {
        '@type': 'AdminMetadata',
        'creationDate': '2016-12-23T11:16:21+1:00'
    }

    assert actual == expected


@pytest.mark.parametrize("date_encoding,encoding_uri", [
    ('iso8601', 'http://id.loc.gov/datatypes/edtf'),
    ('w3cdtf', 'https://www.w3.org/TR/NOTE-datetime'),
])
def test_record_changed_date(date_encoding, encoding_uri, parser):
    raw_xml = MODS("""
        <recordInfo xmlns:xlink="http://www.w3.org/1999/xlink">
            <recordChangeDate encoding="{}">2018-05-29T11:56:32+2:00</recordChangeDate>
        </recordInfo>
    """.format(date_encoding))

    actual = parser.parse_mods(raw_xml)['meta']
    expected = {
        '@type': 'AdminMetadata',
        'changeDate': '2018-05-29T11:56:32+2:00'
    }

    assert actual == expected


def test_record_changed_and_created_date_encodings_default_to_iso8601_when_not_specified(parser):
    raw_xml = MODS("""
        <recordInfo xmlns:xlink="http://www.w3.org/1999/xlink">
            <recordCreationDate>2016-12-23T11:16:21+1:00</recordCreationDate>
            <recordChangeDate>2018-05-29T11:56:32+2:00</recordChangeDate>
        </recordInfo>
    """)

    actual = parser.parse_mods(raw_xml)['meta']
    expected = {
        '@type': 'AdminMetadata',
        'changeDate': '2018-05-29T11:56:32+2:00',
        'creationDate': '2016-12-23T11:16:21+1:00'
    }

    assert actual == expected


def test_newer_output_type_for_artistic_work_as_publication(parser):
    raw_xml = MODS("""
        <genre authority="svep" type="publicationType">bok</genre>
        <genre authority="svep" type="publicationType">kfu</genre>
    """)

    expected = [
        {'@id': 'https://id.kb.se/term/swepub/Book'},
        {'@id': 'https://id.kb.se/term/swepub/output/publication/book'},
        {'@id': 'https://id.kb.se/term/swepub/ArtisticWork'},
        {'@id': 'https://id.kb.se/term/swepub/output/artistic-work'},
    ]
    actual = parser.parse_mods(raw_xml)['instanceOf']['genreForm']
    assert actual == expected


@pytest.mark.parametrize("givenoutputtype, convertedoutputtype", [
    ('ArtisticPerformance/VisualArtworks', 'ArtisticWork'),
])
def test_changed_outputtypes_are_converted(givenoutputtype, convertedoutputtype, parser):
    raw_xml = MODS(f"""
        <genre authority="kb.se" type="outputType">{givenoutputtype}</genre>
    """)

    expected = [
        {'@id': 'https://id.kb.se/term/swepub/{}'.format(convertedoutputtype)}
    ]
    actual = parser.parse_mods(raw_xml)['instanceOf']['genreForm']
    assert actual == expected


@pytest.mark.parametrize("givenoutputtype, convertedoutputtype", [
    ('artistic-work/curated-exhibition-or-event', 'artistic-work/original-creative-work'),
    ('publication/translation', 'publication/critical-edition'),
])
def test_changed_outputtypes_are_converted_2(givenoutputtype, convertedoutputtype, parser):
    raw_xml = MODS(f"""
        <genre authority="kb.se" type="outputType">{givenoutputtype}</genre>
    """)

    expected = [
        {'@id': 'https://id.kb.se/term/swepub/output/{}'.format(convertedoutputtype)}
    ]
    actual = parser.parse_mods(raw_xml)['instanceOf']['genreForm']
    assert actual == expected


def test_conferance_publication_type(parser):
    raw_xml = MODS("""<genre authority="svep" type="publicationType">kon</genre>""")
    expected = [
        {'@id': 'https://id.kb.se/term/swepub/ConferencePaper'},
        {'@id': 'https://id.kb.se/term/swepub/output/conference'},
    ]
    actual = parser.parse_mods(raw_xml)['instanceOf']['genreForm']
    assert actual == expected

    raw_xml = MODS("""
        <genre authority="svep" type="publicationType">kon</genre>
        <genre authority="kb.se" type="outputType">conference/paper</genre>
    """)
    expected = [
        {'@id': 'https://id.kb.se/term/swepub/output/conference/paper'},
        {'@id': 'https://id.kb.se/term/swepub/ConferencePaper'},
    ]
    actual = parser.parse_mods(raw_xml)['instanceOf']['genreForm']
    print(actual)
    assert actual == expected


@pytest.mark.parametrize("display_label", ['print', 'electronic'])
def test_publication_identifier_with_display_label_is_extracted(display_label, parser):
    raw_xml = MODS("""
        <identifier type="isbn" displayLabel="{}">9789129703771</identifier>
    """.format(display_label))
    identified_by = [
        {
            "@type": "ISBN",
            "value": "9789129703771",
            "qualifier": display_label
        }
    ]

    assert identified_by == parser.parse_mods(raw_xml)['identifiedBy']


@pytest.mark.parametrize("mods_type, bibframe_type", [
    ('hdl', 'Hdl'),
    ('isbn', 'ISBN'),
    ('doi', 'DOI'),
    ('issn', 'ISSN'),
    ('eissn', 'ISSN'),
    ('local', 'Local'),
    ('uri', 'URI'),
    ('urn', 'URN'),
    ('urn:nbn', 'URN'),
    ('isi', 'ISI'),
    ('scopus', 'ScopusID'),
    ('pmid', 'PMID'),
    ('patent_number', 'PatentNumber'),
    ('orcid', 'ORCID'),
    ('se-libr', 'LibrisNumber'),
    ('libris', 'LibrisNumber'),
    ('ocolc', 'WorldCatNumber'),
    ('worldcat', 'WorldCatNumber'),
    ('articleId', 'Local'),
    ('foo', 'Local'),
])
def test_mods_identifier_types_are_mapped_to_appropriate_identifier_subclasses_in_bibframe(mods_type, bibframe_type, parser):
    raw_xml = MODS("""
        <identifier type="{}" >9789129703771</identifier>
    """.format(mods_type))
    identified_by = [
        {
            "@type": bibframe_type,
            "value": "9789129703771"
        }
    ]

    if bibframe_type == 'Local':
        identified_by[0]['source'] = {
            "@type": "Source",
            "code": mods_type,
        }

    assert identified_by == parser.parse_mods(raw_xml)['identifiedBy']


def test_multiple_languageTerms_with_authority_are_extracted(parser):
    raw_xml = MODS("""
    <language>
        <languageTerm type="code" authority="iso639-2b">eng</languageTerm>
        <languageTerm type="code" authority="iso639-3">swe</languageTerm>
    </language>
    """)
    expected = [
        {
            "@type": "Language",
            "@id": "https://id.kb.se/language/eng",
            "code": "eng",
            "langCode": "eng",
            "source": {
                '@type': 'Source',
                'code': "iso639-2b"
            }
        },
        {
            "@type": "Language",
            "@id": "https://id.kb.se/language/swe",
            "code": "swe",
            "langCode": "swe",
            "source": {
                '@type': 'Source',
                'code': "iso639-3"
            }
        },
    ]

    assert expected == parser.parse_mods(raw_xml)['instanceOf']['language']


def test_multiple_language_elements_with_authority_are_extracted(parser):
    raw_xml = MODS("""
    <language>
        <languageTerm type="code" authority="iso639-2b">eng</languageTerm>
    </language>
    <language>
        <languageTerm type="code" authority="iso639-3">swe</languageTerm>
    </language>
    """)
    expected = [
        {
            "@type": "Language",
            "@id": "https://id.kb.se/language/eng",
            "code": "eng",
            "langCode": "eng",
            "source": {
                '@type': 'Source',
                'code': "iso639-2b"
            }
        },
        {
            "@type": "Language",
            "@id": "https://id.kb.se/language/swe",
            "code": "swe",
            "langCode": "swe",
            "source": {
                '@type': 'Source',
                'code': "iso639-3"
            }
        },
    ]

    assert expected == parser.parse_mods(raw_xml)['instanceOf']['language']


def test_multiple_unauthorized_language_elements_are_extracted(parser):
    raw_xml = MODS("""
    <language>
        <languageTerm>foo</languageTerm>
        <languageTerm>bar</languageTerm>
    </language>
    <language>
        <languageTerm>baz</languageTerm>
    </language>
    """)
    expected = [
        {"@type": "Language", "code": "foo", '@id': 'https://id.kb.se/language/foo'},
        {"@type": "Language", "code": "bar", '@id': 'https://id.kb.se/language/bar'},
        {"@type": "Language", "code": "baz", '@id': 'https://id.kb.se/language/baz'},
    ]

    assert expected == parser.parse_mods(raw_xml)['instanceOf']['language']


def test_single_abstract_without_language(parser):
    raw_xml = MODS("""
    <abstract>foobar</abstract>
    """)
    expected = [
        {"@type": "Summary", "label": "foobar"}
    ]

    assert expected == parser.parse_mods(raw_xml)['instanceOf']['summary']


def test_single_abstract_with_language(parser):
    raw_xml = MODS("""
    <abstract lang="eng">foobar</abstract>
    """)
    expected = [
        {"@type": "Summary", "label": "foobar", "language": {"@type": "Language", "code": "eng", '@id': 'https://id.kb.se/language/eng'}}
    ]

    assert expected == parser.parse_mods(raw_xml)['instanceOf']['summary']


def test_multiple_abstracts_with_language(parser):
    raw_xml = MODS("""
    <abstract lang="eng">foobar</abstract>
    <abstract lang="swe">skrutt</abstract>
    """)
    expected = [
        {"@type": "Summary", "label": "foobar", "language": {"@type": "Language", "code": "eng", '@id': 'https://id.kb.se/language/eng'}},
        {"@type": "Summary", "label": "skrutt", "language": {"@type": "Language", "code": "swe", '@id': 'https://id.kb.se/language/swe'}},
    ]

    assert expected == parser.parse_mods(raw_xml)['instanceOf']['summary']


def test_invalid_identifiers(parser):
    raw_xml = MODS("""
    <identifier type="doi">10.1080/03468759408579279</identifier>
    <identifier type="uri">https://research.chalmers.se/publication/254409</identifier>
    <identifier type="isbn">9789129703771</identifier>
    <identifier type="isi">000071067000025</identifier>
    <identifier type="issn">1532-6349</identifier>
    <identifier type="doi" invalid='yes'>invalid_doi</identifier>
    <identifier type="uri" invalid='yes'>invalid_uri</identifier>
    <identifier type="isbn" invalid='yes'>invalid_isbn</identifier>
    <identifier type="isi" invalid='yes'>invalid_isi</identifier>
    <identifier type="issn" invalid='yes'>invalid_issn</identifier>

    <relatedItem type="host">
        <identifier type="doi">10.1080/03468759408579279</identifier>
        <identifier type="uri">https://research.chalmers.se/publication/254409</identifier>
        <identifier type="isbn">9789129703771</identifier>
        <identifier type="isi">000071067000025</identifier>
        <identifier type="issn">1532-6349</identifier>
        <identifier type="doi" invalid='yes'>invalid_doi</identifier>
        <identifier type="uri" invalid='yes'>invalid_uri</identifier>
        <identifier type="isbn" invalid='yes'>invalid_isbn</identifier>
        <identifier type="isi" invalid='yes'>invalid_isi</identifier>
        <identifier type="issn" invalid='yes'>invalid_issn</identifier>
    </relatedItem>
    """)
    expectedIdentifiedBy = [
        {'@type': 'DOI', 'value': '10.1080/03468759408579279'},
        {'@type': 'URI', 'value': 'https://research.chalmers.se/publication/254409'},
        {'@type': 'ISBN', 'value': '9789129703771'}, {'@type': 'ISI', 'value': '000071067000025'},
        {'@type': 'ISSN', 'value': '1532-6349'}
    ]
    assert expectedIdentifiedBy == parser.parse_mods(raw_xml)['identifiedBy']

    expectedIncorrectlyIdentifiedBy = [
        {'@type': 'DOI', 'value': 'invalid_doi'},
        {'@type': 'URI', 'value': 'invalid_uri'},
        {'@type': 'ISBN', 'value': 'invalid_isbn'},
        {'@type': 'ISI', 'value': 'invalid_isi'},
        {'@type': 'ISSN', 'value': 'invalid_issn'}
    ]
    assert expectedIncorrectlyIdentifiedBy == parser.parse_mods(raw_xml)['incorrectlyIdentifiedBy']

    expectedIsPartOfIdentifiedBy = [
        {'@type': 'DOI', 'value': '10.1080/03468759408579279'},
        {'@type': 'URI', 'value': 'https://research.chalmers.se/publication/254409'},
        {'@type': 'ISBN', 'value': '9789129703771'}, {'@type': 'ISI', 'value': '000071067000025'},
        {'@type': 'ISSN', 'value': '1532-6349'}
    ]
    assert expectedIsPartOfIdentifiedBy == parser.parse_mods(raw_xml)['isPartOf'][0]['identifiedBy']

    expectedIsPartOfIncorrectlyIdentifiedBy = [
        {'@type': 'DOI', 'value': 'invalid_doi'},
        {'@type': 'URI', 'value': 'invalid_uri'},
        {'@type': 'ISBN', 'value': 'invalid_isbn'},
        {'@type': 'ISI', 'value': 'invalid_isi'},
        {'@type': 'ISSN', 'value': 'invalid_issn'}
    ]
    assert expectedIsPartOfIncorrectlyIdentifiedBy == parser.parse_mods(raw_xml)['isPartOf'][0]['incorrectlyIdentifiedBy']


def test_name_identifiers_swpmods_2(parser):
    raw_xml = MODS("""
    <name type="personal" authority="lnu" xlink:href="lolhum">
        <description xsi:type="identifierDefinition" type="orcid">0000-0002-1825-0097</description>
    </name>
    """)

    expected_identified_by = [
        {
            "@type": "ORCID",
            "value": "0000-0002-1825-0097"
        },
        {
            "@type": "Local",
            "value": "lolhum",
            "source": {
                "@type": "Source",
                "code": "lnu",
            },
        },
    ]

    assert expected_identified_by == parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['agent']['identifiedBy']


def test_name_identifiers_swpmods_3(parser):
    raw_xml = MODS("""
    <name type="personal">
        <nameIdentifier type="orcid">0000-0002-1825-0097</nameIdentifier>
        <nameIdentifier type="lnu">lolhum</nameIdentifier>
        <nameIdentifier type="lnu" invalid="yes">000</nameIdentifier>
    </name>
    """)

    expected_identified_by = [
        {
            "@type": "ORCID",
            "value": "0000-0002-1825-0097"
        },
        {
            "@type": "Local",
            "value": "lolhum",
            "source": {
                "@type": "Source",
                "code": "lnu",
            },
        },
    ]
    expected_incorrectly_identified_by = [
        {
            "@type": "Local",
            "value": "000",
            "source": {
                "@type": "Source",
                "code": "lnu",
            },
        },
    ]

    parsed_agent = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['agent']

    assert expected_identified_by == parsed_agent['identifiedBy']
    assert expected_incorrectly_identified_by == parsed_agent['incorrectlyIdentifiedBy']


def test_name_identifiers_swpmods_3_invalid(parser):
    raw_xml = MODS("""
    <name type="personal">
        <nameIdentifier type="orcid" invalid="yes">000</nameIdentifier>
    </name>
    """)

    expected_incorrectly_identified_by = [
        {
            "@type": "ORCID",
            "value": "000",
        },
    ]

    assert expected_incorrectly_identified_by == parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['agent']['incorrectlyIdentifiedBy']


def test_ignore_swpmods2_if_name_identifier_present(parser):
    raw_xml = MODS("""
    <name type="personal" authority="lnu" xlink:href="ignorethis">
        <description xsi:type="identifierDefinition" type="orcid">ignorethistoo</description>
        <nameIdentifier type="issn">this-is-an-issn-i-promise</nameIdentifier>
        <nameIdentifier type="lnu">lolhum</nameIdentifier>
        <nameIdentifier type="lnu" invalid="yes">000</nameIdentifier>
    </name>
    """)

    expected_identified_by = [
        {
            "@type": "ISSN",
            "value": "this-is-an-issn-i-promise",
        },
        {
            "@type": "Local",
            "value": "lolhum",
            "source": {
                "@type": "Source",
                "code": "lnu",
            },
        },
    ]
    expected_incorrectly_identified_by = [
        {
            "@type": "Local",
            "value": "000",
            "source": {
                "@type": "Source",
                "code": "lnu",
            },
        },
    ]

    parsed_agent = parser.parse_mods(raw_xml)['instanceOf']['contribution'][0]['agent']

    assert expected_identified_by == parsed_agent['identifiedBy']
    assert expected_incorrectly_identified_by == parsed_agent['incorrectlyIdentifiedBy']


def test_usage_and_access_policy_gratis(parser):
    raw_xml = MODS("""
    <accessCondition>gratis</accessCondition>
    """)
    expected_usage_and_access_policy = [
        {
            "@type": "AccessPolicy",
            "label": "gratis"
        }
    ]
    parsed_policy = parser.parse_mods(raw_xml)['usageAndAccessPolicy']
    assert expected_usage_and_access_policy == parsed_policy


def test_usage_and_access_policy_license(parser):
    raw_xml = MODS("""
    <accessCondition
    type="use and reproduction"
    xlink:href="http://creativecommons.org/licenses/by/3.0"></accessCondition>
    """)
    expected_usage_and_access_policy = [
        {
            "@id": "http://creativecommons.org/licenses/by/3.0"
        }
    ]
    parsed_policy = parser.parse_mods(raw_xml)['usageAndAccessPolicy']
    assert expected_usage_and_access_policy == parsed_policy


def test_usage_and_access_policy_embargo(parser):
    raw_xml = MODS("""
    <accessCondition type="restriction on access" displayLabel="embargo">2019-01-01</accessCondition>
    """)
    expected_usage_and_access_policy = [
        {
            "@type": "Embargo",
            "endDate": "2019-01-01"
        }
    ]
    parsed_policy = parser.parse_mods(raw_xml)['usageAndAccessPolicy']
    assert expected_usage_and_access_policy == parsed_policy


def test_several_access_policies(parser):
    raw_xml = MODS("""
    <accessCondition>xxx</accessCondition>
    <accessCondition type="restriction on access" displayLabel="embargo">2019-01-01</accessCondition>
    """)
    expected_usage_and_access_policy = [
        {
            "@type": "AccessPolicy",
            "label": "xxx"
        },
        {
            "@type": "Embargo",
            "endDate": "2019-01-01"
        }
    ]
    parsed_policy = parser.parse_mods(raw_xml)['usageAndAccessPolicy']
    print(f"{parsed_policy}")
    assert expected_usage_and_access_policy == parsed_policy


# Tests related to changes in Swepub MODS 4.0 below

def test_origininfo_eventtype_publication_1(parser):
    raw_xml = MODS("""
        <originInfo eventType="publication">
            <agent>
                <namePart>Cambridge University Press</namePart>
                <role>
                    <roleTerm authority="marcrelator" valueURI="http://id.loc.gov/vocabulary/relators/pbl">pbl</roleTerm>
                </role>
            </agent>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['publication']
    expected = [
        {
            '@type': 'Publication',
            'agent': {
                '@type': 'Agent',
                'label': 'Cambridge University Press'
            }
        }
    ]

    assert actual == expected


def test_origininfo_eventtype_publication_2(parser):
    raw_xml = MODS("""
        <originInfo eventType="publication">
            <agent>
                <namePart>Cambridge University Press</namePart>
                <role>
                    <roleTerm authority="marcrelator">pbl</roleTerm>
                </role>
            </agent>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['publication']
    expected = [
        {
            '@type': 'Publication',
            'agent': {
                '@type': 'Agent',
                'label': 'Cambridge University Press'
            }
        }
    ]

    assert actual == expected


def test_origininfo_eventtype_publication_3(parser):
    raw_xml = MODS("""
        <originInfo eventType="publication">
            <agent>
                <namePart>Cambridge University Press</namePart>
                <role>
                    <roleTerm authority="marcrelator" valueURI="http://id.loc.gov/vocabulary/relators/pbl"></roleTerm>
                </role>
            </agent>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['publication']
    expected = [
        {
            '@type': 'Publication',
            'agent': {
                '@type': 'Agent',
                'label': 'Cambridge University Press'
            }
        }
    ]

    assert actual == expected


def test_origininfo_eventtype_publication_4(parser):
    raw_xml = MODS("""
        <originInfo eventType="publication">
            <agent>
                <namePart>Cambridge University Press</namePart>
                <role>
                    <roleTerm authority="marcrelator" valueURI="http://id.loc.gov/vocabulary/relators/foo">bar</roleTerm>
                </role>
            </agent>
        </originInfo>
    """)

    assert "publication" not in parser.parse_mods(raw_xml)


def test_origininfo_eventtype_manufacture(parser):
    raw_xml = MODS("""
        <originInfo eventType="manufacture">
            <agent>
                <namePart>Cambridge University Press</namePart>
                <role>
                    <roleTerm authority="marcrelator" valueURI="http://id.loc.gov/vocabulary/relators/mfr">mfr</roleTerm>
                </role>
            </agent>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['manufacture']
    expected = [
        {
            '@type': 'Manufacture',
            'agent': {
                '@type': 'Agent',
                'label': 'Cambridge University Press'
            }
        }
    ]

    assert actual == expected


def test_origininfo_eventtype_distribution(parser):
    raw_xml = MODS("""
        <originInfo eventType="distribution">
            <agent>
                <namePart>Cambridge University Press</namePart>
                <role>
                    <roleTerm authority="marcrelator" valueURI="http://id.loc.gov/vocabulary/relators/dst">dst</roleTerm>
                </role>
            </agent>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['distribution']
    expected = [
        {
            '@type': 'Distribution',
            'agent': {
                '@type': 'Agent',
                'label': 'Cambridge University Press'
            }
        }
    ]

    assert actual == expected


def test_origininfo_eventtype_production(parser):
    raw_xml = MODS("""
        <originInfo eventType="production">
            <agent>
                <namePart>Cambridge University Press</namePart>
                <role>
                    <roleTerm authority="marcrelator" valueURI="http://id.loc.gov/vocabulary/relators/pro">pro</roleTerm>
                </role>
            </agent>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['production']
    expected = [
        {
            '@type': 'Production',
            'agent': {
                '@type': 'Agent',
                'label': 'Cambridge University Press'
            }
        }
    ]

    assert actual == expected


def test_origininfo_other(parser):
    raw_xml = MODS("""
        <originInfo>
            <agent>
                <namePart>Cambridge University Press</namePart>
                <role>
                    <roleTerm authority="marcrelator" valueURI="http://id.loc.gov/vocabulary/relators/prt">prt</roleTerm>
                </role>
            </agent>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['contribution']
    expected = [
        {
            '@type': 'Contribution',
            'agent': {
                '@type': 'Agent',
                'label': 'Cambridge University Press',
                'role': [
                    {
                        '@id': 'http://id.loc.gov/vocabulary/relators/prt'
                    }
                ]
            }
        }
    ]

    assert actual == expected


def test_origininfo_other_2(parser):
    raw_xml = MODS("""
        <originInfo eventType="somethingelse">
            <agent>
                <namePart>Cambridge University Press</namePart>
                <role>
                    <roleTerm valueURI="http://id.loc.gov/vocabulary/relators/something" />
                </role>
            </agent>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['contribution']
    expected = [
        {
            '@type': 'Contribution',
            'agent': {
                '@type': 'Agent',
                'label': 'Cambridge University Press',
                'role': [
                    {
                        '@id': 'http://id.loc.gov/vocabulary/relators/something'
                    }
                ]
            }
        }
    ]

    assert actual == expected


def test_complete_origin_info_2(parser):
    raw_xml = MODS("""
        <originInfo eventType="publication">
            <agent>
                <namePart>Cambridge University Press</namePart>
                <role>
                    <roleTerm authority="marcrelator" valueURI="http://id.loc.gov/vocabulary/relators/pbl">pbl</roleTerm>
                </role>
            </agent>
            <dateIssued>1986-05-30</dateIssued>
            <place>
                <placeTerm>Ankeborg</placeTerm>
            </place>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['publication']
    expected = [
        {
            '@type': 'Publication',
            'date': '1986-05-30',
            'place': {'@type': 'Place', 'label': 'Ankeborg'},
            'agent': {'@type': 'Agent', 'label': 'Cambridge University Press'}
        }
    ]

    assert actual == expected


def test_complete_origin_info_3(parser):
    raw_xml = MODS("""
        <originInfo eventType="publication">
            <agent>
                <namePart>Elsevier</namePart>
                <role>
                    <roleTerm authority="marcrelator" valueURI="http://id.loc.gov/vocabulary/relators/pbl">pbl</roleTerm>
                </role>
            </agent>
            <dateIssued>1986-05-30</dateIssued>
            <dateOther type="available">2017-09-28T11:03:29</dateOther>
            <place>
                <placeTerm>Ankeborg</placeTerm>
            </place>
        </originInfo>
        <originInfo eventType="manufacture">
            <agent>
                <namePart>Cambridge University Press</namePart>
                <role>
                    <roleTerm authority="marcrelator" valueURI="http://id.loc.gov/vocabulary/relators/mfr">mfr</roleTerm>
                </role>
            </agent>
            <dateOther type="digitized">2022-07-25T20:05:30</dateOther>
        </originInfo>
        <originInfo eventType="distribution">
            <agent>
                <namePart>Cambridge University Press</namePart>
                <role>
                    <roleTerm authority="marcrelator" valueURI="http://id.loc.gov/vocabulary/relators/pbl">pbl</roleTerm>
                </role>
            </agent>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)
    expected_publication = [
        {
            '@type': 'Publication',
            'date': '1986-05-30',
            'place': {
                '@type': 'Place',
                'label': 'Ankeborg'
            },
            'agent': {
                '@type': 'Agent',
                'label': 'Elsevier'
            }
        }
    ]
    expected_manufacture = [
        {
            '@type': 'Manufacture',
            'agent': {
                '@type': 'Agent',
                'label': 'Cambridge University Press'
            }
        }
    ]
    expected_provisionactivity = [
        {
            "@type": "Availability",
            "date": "2017-09-28T11:03:29"
        },
        {
            "@type": "Digitization",
            "date": "2022-07-25T20:05:30"
        }
    ]

    assert actual["publication"] == expected_publication
    assert actual["manufacture"] == expected_manufacture
    assert actual["provisionActivity"] == expected_provisionactivity


def test_origininfo_copyrightdate(parser):
    raw_xml = MODS("""
        <originInfo>
            <copyrightDate>1999</copyrightDate>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['copyright']
    expected = [
        {
            '@type': 'Copyright',
            'date': '1999'
        }
    ]

    assert actual == expected


# copyrightDate is not repeatable in Swepub MODS 4.0; use the first one
def test_origininfo_copyrightdate(parser):
    raw_xml = MODS("""
        <originInfo>
            <copyrightDate>1999</copyrightDate>
            <copyrightDate>2000</copyrightDate>
        </originInfo>
    """)

    actual = parser.parse_mods(raw_xml)['copyright']
    expected = [
        {
            '@type': 'Copyright',
            'date': '1999'
        }
    ]

    assert actual == expected
