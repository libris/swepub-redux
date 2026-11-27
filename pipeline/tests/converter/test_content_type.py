import pytest

from pipeline.bibframesource import BibframeSource
from pipeline.convert import convert
from pipeline.legacy_publication import Publication as LegacyPublication
from service.utils.process import _get_url

RECORD = """
    <record xmlns="http://www.openarchives.org/OAI/2.0/">
      <header><identifier>oai:example:1</identifier></header>
      <metadata>
        <mods xmlns="http://www.loc.gov/mods/v3" version="3.2">
          <titleInfo><title>A title</title></titleInfo>
          <genre authority="svep" type="publicationType">art</genre>
          {genre}
        </mods>
      </metadata>
    </record>
"""


SVEP = "https://id.kb.se/term/swepub/svep/"


def _convert(content_type=None, as_uri=False):
    if not content_type:
        genre = ""
    elif as_uri:
        genre = f'<genre authority="svep" type="contentType" valueURI="{SVEP}{content_type}">{content_type}</genre>'
    else:
        genre = f'<genre authority="svep" type="contentType">{content_type}</genre>'
    return convert(RECORD.format(genre=genre))


@pytest.mark.parametrize("as_uri", [False, True])
@pytest.mark.parametrize("content_type", ["ref", "vet", "pop"])
def test_content_marking(content_type, as_uri):
    doc = _convert(content_type, as_uri)
    assert BibframeSource(doc).content_marking == content_type


def test_content_marking_missing():
    doc = _convert()
    assert "swepub:contentType" not in doc["instanceOf"]
    assert BibframeSource(doc).content_marking is None


@pytest.mark.parametrize("as_uri", [False, True])
def test_content_type_not_an_output_type(as_uri):
    doc = _convert("ref", as_uri)
    assert BibframeSource(doc).output_types == ["https://id.kb.se/term/swepub/output/publication/journal-article"]


@pytest.mark.parametrize("as_uri", [False, True])
def test_legacy_category_072(as_uri):
    doc = _convert("ref", as_uri)
    legacy = LegacyPublication(doc)
    legacy.add_category_072()
    subjects = legacy.body["instanceOf"]["subject"]
    assert {
        "@type": "Concept",
        "label": "ref",
        "inScheme": {"@type": "ConceptScheme", "code": "swepub-contenttype"},
    } in subjects
    assert all(s["inScheme"]["code"] != "swepub-publicationtype" or s["label"] != "ref" for s in subjects)


@pytest.mark.parametrize("as_uri", [False, True])
def test_export_urls_ignore_content_type(as_uri):
    doc = _convert("ref", as_uri)
    for pub_type in ("output", "publication"):
        assert "/svep/" not in (_get_url(doc, pub_type) or "")
