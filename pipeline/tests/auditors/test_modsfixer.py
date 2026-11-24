from pipeline.auditors.modsfixer import ModsFixer
from pipeline.publication import Publication

modsfixer = ModsFixer()

body = {
    "instanceOf": {
        "contribution": [
            {
                "@type": "Contribution",
                "agent": {
                    "@type": "Person",
                    "familyName": "Bar",
                    "givenName": "Foo",
                },
                "hasAffiliation": [
                    {
                        "@type": "Organization",
                        "identifiedBy": [
                            {
                                "@type": "URI",
                                "source": {"@type": "Source", "code": "kb.se"},
                                "value": "example.com",
                            }
                        ],
                        "nameByLang": {"sv": "authority kb.se, svenska"},
                    },
                    {
                        "@type": "Organization",
                        "identifiedBy": [
                            {
                                "@type": "URI",
                                "source": {"@type": "Source", "code": "kb.se"},
                                "value": "example.com",
                            }
                        ],
                        "nameByLang": {"en": "authority kb.se, English"},
                    },
                    {
                        "@type": "Organization",
                        "identifiedBy": [
                            {"@type": "ROR", "value": "https://ror.org/12345"}
                        ],
                        "nameByLang": {"en": "ROR org in English"},
                    },
                    {
                        "@type": "Organization",
                        "identifiedBy": [
                            {"@type": "ROR", "value": "https://ror.org/12345"}
                        ],
                        "nameByLang": {"sv": "ROR-org på svenska"},
                    },
                    {"@type": "Organization", "name": "Org without language specified"},
                ],
            }
        ]
    }
}


def test_should_merge_identical_ror_ids():
    publication = Publication(
        {
            "instanceOf": {
                "contribution": [
                    {
                        "@type": "Contribution",
                        "agent": {
                            "@type": "Person",
                            "familyName": "Bar",
                            "givenName": "Foo",
                        },
                        "hasAffiliation": [
                            {
                                "@type": "Organization",
                                "identifiedBy": [
                                    {"@type": "ROR", "value": "https://ror.org/12345"}
                                ],
                                "nameByLang": {"en": "ROR org in English"},
                            },
                            {
                                "@type": "Organization",
                                "identifiedBy": [
                                    {"@type": "ROR", "value": "https://ror.org/12345"}
                                ],
                                "nameByLang": {"sv": "ROR-org på svenska"},
                            },
                            {
                                "@type": "Organization",
                                "name": "Org without language specified",
                            },
                        ],
                    }
                ]
            }
        }
    )

    new_publication, _audit_events = modsfixer.audit(publication, [], None, None)

    assert new_publication.contributions[0].affiliations == [
        {
            "@type": "Organization",
            "nameByLang": {"en": "ROR org in English", "sv": "ROR-org på svenska"},
            "identifiedBy": [{"@type": "ROR", "value": "https://ror.org/12345"}],
        },
        {"@type": "Organization", "name": "Org without language specified"},
    ]


def test_should_not_merge_nonidentical_ror_ids():
    publication = Publication(
        {
            "instanceOf": {
                "contribution": [
                    {
                        "@type": "Contribution",
                        "agent": {
                            "@type": "Person",
                            "familyName": "Bar",
                            "givenName": "Foo",
                        },
                        "hasAffiliation": [
                            {
                                "@type": "Organization",
                                "identifiedBy": [
                                    {"@type": "ROR", "value": "https://ror.org/12345"}
                                ],
                                "nameByLang": {"en": "ROR org in English"},
                            },
                            {
                                "@type": "Organization",
                                "identifiedBy": [
                                    {"@type": "ROR", "value": "https://ror.org/67890"}
                                ],
                                "nameByLang": {"sv": "ROR-org på svenska"},
                            },
                        ],
                    }
                ]
            }
        }
    )

    new_publication, _audit_events = modsfixer.audit(publication, [], None, None)

    assert new_publication.contributions[0].affiliations == [
        {
            "@type": "Organization",
            "nameByLang": {"en": "ROR org in English"},
            "identifiedBy": [{"@type": "ROR", "value": "https://ror.org/12345"}],
        },
        {
            "@type": "Organization",
            "nameByLang": {"sv": "ROR-org på svenska"},
            "identifiedBy": [{"@type": "ROR", "value": "https://ror.org/67890"}],
        },
    ]


def test_should_merge_kb_se_authority_if_different_languages():
    publication = Publication(
        {
            "instanceOf": {
                "contribution": [
                    {
                        "@type": "Contribution",
                        "agent": {
                            "@type": "Person",
                            "familyName": "Bar",
                            "givenName": "Foo",
                        },
                        "hasAffiliation": [
                            {
                                "@type": "Organization",
                                "identifiedBy": [
                                    {
                                        "@type": "URI",
                                        "source": {"@type": "Source", "code": "kb.se"},
                                        "value": "example.com",
                                    }
                                ],
                                "nameByLang": {"sv": "authority kb.se, svenska"},
                            },
                            {
                                "@type": "Organization",
                                "identifiedBy": [
                                    {
                                        "@type": "URI",
                                        "source": {"@type": "Source", "code": "kb.se"},
                                        "value": "example.com",
                                    }
                                ],
                                "nameByLang": {"en": "authority kb.se, English"},
                            },
                        ],
                    }
                ]
            }
        }
    )

    new_publication, _audit_events = modsfixer.audit(publication, [], None, None)

    assert new_publication.contributions[0].affiliations == [
        {
            "@type": "Organization",
            "nameByLang": {
                "sv": "authority kb.se, svenska",
                "en": "authority kb.se, English",
            },
            "identifiedBy": [
                {
                    "@type": "URI",
                    "source": {"@type": "Source", "code": "kb.se"},
                    "value": "example.com",
                }
            ],
        }
    ]


def test_should_not_merge_kb_se_authority_if_same_language():
    publication = Publication(
        {
            "instanceOf": {
                "contribution": [
                    {
                        "@type": "Contribution",
                        "agent": {
                            "@type": "Person",
                            "familyName": "Bar",
                            "givenName": "Foo",
                        },
                        "hasAffiliation": [
                            {
                                "@type": "Organization",
                                "identifiedBy": [
                                    {
                                        "@type": "URI",
                                        "source": {"@type": "Source", "code": "kb.se"},
                                        "value": "example.com",
                                    }
                                ],
                                "nameByLang": {"sv": "en institution"},
                            },
                            {
                                "@type": "Organization",
                                "identifiedBy": [
                                    {
                                        "@type": "URI",
                                        "source": {"@type": "Source", "code": "kb.se"},
                                        "value": "example.com",
                                    }
                                ],
                                "nameByLang": {"sv": "en annan institution"},
                            },
                        ],
                    }
                ]
            }
        }
    )

    new_publication, _audit_events = modsfixer.audit(publication, [], None, None)

    assert new_publication.contributions[0].affiliations == [
        {
            "@type": "Organization",
            "identifiedBy": [
                {
                    "@type": "URI",
                    "source": {"@type": "Source", "code": "kb.se"},
                    "value": "example.com",
                }
            ],
            "nameByLang": {"sv": "en institution"},
        },
        {
            "@type": "Organization",
            "identifiedBy": [
                {
                    "@type": "URI",
                    "source": {"@type": "Source", "code": "kb.se"},
                    "value": "example.com",
                }
            ],
            "nameByLang": {"sv": "en annan institution"},
        },
    ]


def test_should_merge_multiple_orgs_split_by_language():
    publication = Publication(
        {
            "instanceOf": {
                "contribution": [
                    {
                        "@type": "Contribution",
                        "agent": {
                            "@type": "Person",
                            "familyName": "Bar",
                            "givenName": "Foo",
                        },
                        "hasAffiliation": [
                            {
                                "@type": "Organization",
                                "identifiedBy": [
                                    {
                                        "@type": "URI",
                                        "source": {"@type": "Source", "code": "kb.se"},
                                        "value": "example.com",
                                    }
                                ],
                                "nameByLang": {"swe": "Exempeluniversitetet"},
                            },
                            {
                                "@type": "Organization",
                                "identifiedBy": [
                                    {
                                        "@type": "URI",
                                        "source": {"@type": "Source", "code": "kb.se"},
                                        "value": "example.com",
                                    }
                                ],
                                "nameByLang": {"eng": "Example University"},
                            },
                            {
                                "@type": "Organization",
                                "identifiedBy": [
                                    {
                                        "@type": "URI",
                                        "source": {"@type": "Source", "code": "kb.se"},
                                        "value": "other.com",
                                    }
                                ],
                                "nameByLang": {"swe": "Annat universitet"},
                            },
                            {
                                "@type": "Organization",
                                "identifiedBy": [
                                    {
                                        "@type": "URI",
                                        "source": {"@type": "Source", "code": "kb.se"},
                                        "value": "other.com",
                                    }
                                ],
                                "nameByLang": {"eng": "Other University"},
                            },
                        ],
                    }
                ]
            }
        }
    )

    new_publication, _audit_events = modsfixer.audit(publication, [], None, None)

    assert new_publication.contributions[0].affiliations == [
        {
            "@type": "Organization",
            "nameByLang": {"swe": "Exempeluniversitetet", "eng": "Example University"},
            "identifiedBy": [
                {
                    "@type": "URI",
                    "source": {"@type": "Source", "code": "kb.se"},
                    "value": "example.com",
                }
            ],
        },
        {
            "@type": "Organization",
            "nameByLang": {"swe": "Annat universitet", "eng": "Other University"},
            "identifiedBy": [
                {
                    "@type": "URI",
                    "source": {"@type": "Source", "code": "kb.se"},
                    "value": "other.com",
                }
            ],
        },
    ]
