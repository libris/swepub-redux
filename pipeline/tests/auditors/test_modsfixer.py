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
                        "nameByLang": {"swe": "authority kb.se, svenska"},
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
                        "nameByLang": {"eng": "authority kb.se, English"},
                    },
                    {
                        "@type": "Organization",
                        "identifiedBy": [
                            {"@type": "ROR", "value": "https://ror.org/12345"}
                        ],
                        "nameByLang": {"eng": "ROR org in English"},
                    },
                    {
                        "@type": "Organization",
                        "identifiedBy": [
                            {"@type": "ROR", "value": "https://ror.org/12345"}
                        ],
                        "nameByLang": {"swe": "ROR-org på svenska"},
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
                                "nameByLang": {"eng": "ROR org in English"},
                            },
                            {
                                "@type": "Organization",
                                "identifiedBy": [
                                    {"@type": "ROR", "value": "https://ror.org/12345"}
                                ],
                                "nameByLang": {"swe": "ROR-org på svenska"},
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
            "nameByLang": {"eng": "ROR org in English", "swe": "ROR-org på svenska"},
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
                                "nameByLang": {"eng": "ROR org in English"},
                            },
                            {
                                "@type": "Organization",
                                "identifiedBy": [
                                    {"@type": "ROR", "value": "https://ror.org/67890"}
                                ],
                                "nameByLang": {"swe": "ROR-org på svenska"},
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
            "nameByLang": {"eng": "ROR org in English"},
            "identifiedBy": [{"@type": "ROR", "value": "https://ror.org/12345"}],
        },
        {
            "@type": "Organization",
            "nameByLang": {"swe": "ROR-org på svenska"},
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
                                "nameByLang": {"swe": "authority kb.se, svenska"},
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
                                "nameByLang": {"eng": "authority kb.se, English"},
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
                "swe": "authority kb.se, svenska",
                "eng": "authority kb.se, English",
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
                                "nameByLang": {"swe": "en institution"},
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
                                "nameByLang": {"swe": "en annan institution"},
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
            "nameByLang": {"swe": "en institution"},
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
            "nameByLang": {"swe": "en annan institution"},
        },
    ]
