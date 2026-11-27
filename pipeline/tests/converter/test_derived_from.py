from pipeline.convert import convert
from pipeline.publication import Publication
from pipeline.publicationmerger import PublicationMerger
from pipeline.util import derived_from_ids, derived_from_orgs, source_org

RECORD = """
    <record xmlns="http://www.openarchives.org/OAI/2.0/">
      <header><identifier>{oai_id}</identifier></header>
      <metadata>
        <mods xmlns="http://www.loc.gov/mods/v3" version="3.2">
          {record_info}
          <titleInfo><title>{title}</title></titleInfo>
        </mods>
      </metadata>
    </record>
"""


def _xml(oai_id, source=None, title="A title"):
    record_info = f"<recordInfo><recordContentSource>{source}</recordContentSource></recordInfo>" if source else ""
    return RECORD.format(oai_id=oai_id, record_info=record_info, title=title)


def _derived_from(oai_id, publisher=None):
    derived_from = {"@type": "Record", "identifiedBy": [{"@type": "Identifier", "value": oai_id}]}
    if publisher:
        derived_from["publisher"] = publisher
    return derived_from


def test_convert_links_known_source():
    doc = convert(_xml("oai:DiVA.org:kth-1", "kth"))
    assert "assigner" not in doc["meta"]
    assert doc["meta"]["derivedFrom"] == [
        _derived_from("oai:DiVA.org:kth-1", {"@id": "https://swepub.kb.se/source/kth"})
    ]
    assert source_org(doc) == "kth"


def test_convert_keeps_unknown_source_as_blank_org():
    doc = convert(_xml("oai:example:1", "nope"))
    assert doc["meta"]["derivedFrom"] == [
        _derived_from("oai:example:1", {"@type": "Organization", "code": "nope"})
    ]
    assert source_org(doc) == "nope"


def test_convert_without_record_content_source():
    doc = convert(_xml("oai:example:1"))
    assert doc["meta"]["derivedFrom"] == [_derived_from("oai:example:1")]
    assert source_org(doc) is None


def test_merge_puts_master_first():
    # The master is the record with most elements; its @id is not the alphabetically first one
    small = Publication(convert(_xml("oai:DiVA.org:aaa-1", "kth")))
    other = Publication(convert(_xml("oai:DiVA.org:bbb-1", "nope")))
    big = Publication(convert(_xml("oai:DiVA.org:zzz-1", "su")))
    big.body["instanceOf"]["subject"] = [{"@type": "Topic", "prefLabel": "x"}]

    merged = PublicationMerger().merge([small, other, big]).body

    assert merged["@id"] == "oai:DiVA.org:aaa-1"
    assert derived_from_ids(merged) == ["oai:DiVA.org:zzz-1", "oai:DiVA.org:aaa-1", "oai:DiVA.org:bbb-1"]
    assert derived_from_orgs(merged) == ["su", "kth", "nope"]
    assert source_org(merged) == "su"
