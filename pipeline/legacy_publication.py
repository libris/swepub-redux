import dateutil.parser
from datetime import datetime

genre_form_publication_mappings = {
    "https://id.kb.se/term/swepub/output/publication/editorial-letter": ["art"],
    "https://id.kb.se/term/swepub/output/publication/journal-article": ["art"],
    "https://id.kb.se/term/swepub/output/publication/magazine-article": ["art"],
    "https://id.kb.se/term/swepub/output/publication/newspaper-article": ["art"],
    "https://id.kb.se/term/swepub/output/publication/book": ["bok"],
    "https://id.kb.se/term/swepub/output/publication/doctoral-thesis": ["dok"],
    "https://id.kb.se/term/swepub/output/publication/review-article": ["for"],
    "https://id.kb.se/term/swepub/output/publication/book-chapter": ["kap"],
    "https://id.kb.se/term/swepub/output/publication/encyclopedia-entry": ["kap"],
    "https://id.kb.se/term/swepub/output/publication/foreword-afterword": ["kap"],
    "https://id.kb.se/term/swepub/output/publication/report-chapter": ["kap"],
    "https://id.kb.se/term/swepub/output/artistic-work": ["kfu"],
    "https://id.kb.se/term/swepub/output/artistic-work/original-creative-work": ["kfu"],
    "https://id.kb.se/term/swepub/output/artistic-work/artistic-thesis": ["kfu", "dok"],
    "https://id.kb.se/term/swepub/output/conference": ["kon"],
    "https://id.kb.se/term/swepub/output/conference/other": ["kon"],
    "https://id.kb.se/term/swepub/output/conference/paper": ["kon"],
    "https://id.kb.se/term/swepub/output/conference/poster": ["kon"],
    "https://id.kb.se/term/swepub/output/publication/licentiate-thesis": ["lic"],
    "https://id.kb.se/term/swepub/output/other": ["ovr"],
    "https://id.kb.se/term/swepub/output/other/data-set": ["ovr"],
    "https://id.kb.se/term/swepub/output/other/software": ["ovr"],
    "https://id.kb.se/term/swepub/output/publication": ["ovr"],
    "https://id.kb.se/term/swepub/output/publication/critical-edition": ["ovr"],
    "https://id.kb.se/term/swepub/output/publication/journal-issue": ["ovr"],
    "https://id.kb.se/term/swepub/output/publication/other": ["ovr"],
    "https://id.kb.se/term/swepub/output/publication/preprint": ["ovr"],
    "https://id.kb.se/term/swepub/output/publication/working-paper": ["ovr"],
    "https://id.kb.se/term/swepub/output/intellectual-property": ["pat"],
    "https://id.kb.se/term/swepub/output/intellectual-property/other": ["pat"],
    "https://id.kb.se/term/swepub/output/intellectual-property/patent": ["pat"],
    "https://id.kb.se/term/swepub/output/conference/proceeding": ["pro"],
    "https://id.kb.se/term/swepub/output/publication/report": ["rap"],
    "https://id.kb.se/term/swepub/output/publication/book-review": ["rec"],
    "https://id.kb.se/term/swepub/output/publication/edited-book": ["sam"],
}

publication_type_to_issuance_type = {
    "art": "ComponentPart",
    "for": "ComponentPart",
    "rec": "ComponentPart",
    "kap": "ComponentPart",
    "kon": "ComponentPart",
    "bok": "Monograph",
    "dok": "Monograph",
    "lic": "Monograph",
    "rap": "Monograph",
    "pro": "Monograph",
    "pat": "Monograph",
    "kfu": "Monograph",
    "ovr": "Monograph",
    "sam": "Monograph",
}


def get_publication_types(genre_form):
    return genre_form_publication_mappings.get(genre_form, [])


def get_issuance_type(publication_type):
    return publication_type_to_issuance_type.get(publication_type)


class Publication:
    """Abstract publication format and API to access its properties"""

    def __init__(self, body):
        self._body = body

    def __eq__(self, publication):
        """Two publication is considered eq if whole body is equal"""
        return self.body == publication.body

    @property
    def id(self):
        """Return local publication id"""
        return self._body["@id"]

    @property
    def body(self):
        """Return raw publication data"""
        return self._body

    @property
    def meta_assigner_label(self):
        body = self.body
        return body.get("meta", {}).get("assigner", {}).get("label")

    @property
    def body_with_required_legacy_search_fields(self):
        self.add_meta_control_number_001()
        self.add_meta_system_name_003()
        self.add_genre_form_007()
        self.add_meta_created_008()
        self.add_publication_008()
        self.add_meta_duplicate_publications_009()
        self.add_identified_by_024()
        self.add_genre_form_072()
        self.add_meta_description_creator_040()
        self.add_meta_bibliography_sigel_042()
        self.add_instance_of_has_title_240()
        self.add_has_series_490()
        self.add_has_note_500()
        self.add_instance_of_subject_650()
        self.add_instance_of_subject_653()
        self.add_instance_of_contribution_100_and_700_710()
        self.add_is_part_of_773()
        self.add_electronic_locator_and_identified_by_856()
        return self.body

    def add_meta_control_number_001(self):
        """Adds meta.controlNumber from self.id , represents part of marc field 001"""
        body = self.body
        if not body.get("meta"):
            body["meta"] = {}
        body["meta"]["controlNumber"] = self.id

    def add_meta_system_name_003(self):
        """Adds meta.systemName hardcoded to 'SwePub', represents part of marc field 003"""
        body = self.body
        if not body.get("meta"):
            body["meta"] = {}
        body["meta"]["systemName"] = "SwePub"

    def add_genre_form_007(self):
        """Adds issuanceType from instanceOf.genreForm[@id] and genreform_mapper code, represents marc field 007"""
        body = self.body
        genre_forms = body.get("instanceOf", {}).get("genreForm", [])
        for gf in genre_forms:
            if gf.get("@id"):
                p_t = get_publication_types(gf.get("@id"))
                if p_t:
                    issuance_type = get_issuance_type(p_t[0])
                    if issuance_type:
                        body["issuanceType"] = issuance_type
                    break

    def add_meta_created_008(self):
        """Adds meta.created, represent part of marc field 008"""
        body = self.body
        if not body.get("meta"):
            body["meta"] = {}
        created = body.get("meta").get("creationDate")
        if created:
            created = dateutil.parser.parse(created).strftime("%y%m%d")
            body["meta"]["created"] = created
        else:
            body["meta"]["created"] = datetime.today().strftime("%y%m%d")

    def add_meta_description_creator_040(self):
        """Adds meta.descriptionCreator from meta.assigner.label, represents marc field 040"""
        body = self.body
        meta = body.get("meta", {})
        meta["descriptionCreator"] = {
            "@id": "https://libris.kb.se/library/" + str(self.meta_assigner_label),
            "@type": "Library",
            "sigel": "(SwePub)" + str(self.meta_assigner_label),
        }

        if len(self.body.get("_publication_orgs", [])) > 1:
            other_orgs = [
                org
                for org in self.body.get("_publication_orgs", [])
                if org != self.meta_assigner_label
            ]
            if other_orgs:
                # meta.descriptionUpgrader only support one meta_assigner_label in 040d so take first one
                candidate_meta_assigner_label = other_orgs[0]
                meta["descriptionUpgrader"] = {
                    "@id": "https://libris.kb.se/library/" + str(candidate_meta_assigner_label),
                    "@type": "Library",
                    "sigel": "(SwePub)" + str(candidate_meta_assigner_label),
                }

    def add_meta_bibliography_sigel_042(self):
        """Adds meta.bibliography hardcoded Bibliography/Swepub, represents marc field 042"""
        body = self.body
        if body.get("meta"):
            body["meta"]["bibliography"] = [{"@type": "Bibliography", "sigel": "SwePub"}]

    def add_genre_form_072(self):
        """
        Adds instanceOf.genreForm[@type=Concept) using genreform_mapper, represents marc field 072
        1. Suffix of https://id.kb.se/term/swepub/svep/ is added as swepub-contenttype
        2. publication type determined by get_publication_types and added as swepub-publicationtype
        """
        body = self.body
        subjects = body.get("instanceOf", {}).get("subject", [])
        genre_forms = body.get("instanceOf", {}).get("genreForm", [])
        for gf in genre_forms:
            if gf.get("@id"):
                id = gf.get("@id")
                if id and id.startswith("https://id.kb.se/term/swepub/svep/"):
                    label = id.split("/")[-1]
                    code = "swepub-contenttype"
                    contenttype = {
                        "@type": "Concept",
                        "label": label,
                        "inScheme": {"@type": "ConceptScheme", "code": code},
                    }
                    if contenttype not in subjects:
                        subjects.append(contenttype)
                else:
                    for p_t in get_publication_types(id):
                        label = p_t
                        code = "swepub-publicationtype"
                        publicationtype = {
                            "@type": "Concept",
                            "label": label,
                            "inScheme": {"@type": "ConceptScheme", "code": code},
                        }
                        if publicationtype not in subjects:
                            subjects.append(publicationtype)

    def add_has_series_490(self):
        """Adds SeriesMembership from hasSeries, represents marc field 490"""
        body = self.body
        if body.get("hasSeries") and body.get("hasSeries")[0].get("hasTitle"):
            series_member_ships = []
            for serie in body.get("hasSeries"):
                series_member_ship = {
                    "@type": "SeriesMembership",
                    "marc:seriesTracingPolicy": "0",
                }
                if serie.get("hasTitle"):
                    series_statements = []
                    part_number = None
                    for title in serie.get("hasTitle"):
                        if title.get("mainTitle"):
                            series_statements.append(title.get("mainTitle"))
                        if title.get("partNumber"):
                            part_number = title.get("partNumber")
                    if len(series_statements) > 0:
                        series_member_ship["seriesStatement"] = series_statements
                    if part_number:
                        series_member_ship["seriesEnumeration"] = part_number

                if serie.get("identifiedBy"):
                    identified_bys = serie.get("identifiedBy")
                    series_member_ship["inSeries"] = {
                        "@type": "Instance",
                        "identifiedBy": identified_bys,
                    }
                series_member_ships.append(series_member_ship)

            if len(series_member_ships) > 0:
                body["seriesMembership"] = series_member_ships

    def add_has_note_500(self):
        """Adds hasNote[@type=Note] from instanceOf.hasNote[@type=Note], represents marc field 042"""
        body = self.body
        notes = []
        for note in body.get("instanceOf", {}).get("hasNote", []):
            if note.get("@type") == "Note":
                notes.append(note)
        if len(notes) > 0:
            body["hasNote"] = notes

    def add_publication_008(self):
        """
        Remakes publication, represents marc field 008 pos 5
        1. rename @type=Publication to @type=PrimaryPublication
        2. rename date to year
        """
        body = self.body
        if body.get("publication", []):
            for publication in [
                p for p in body.get("publication") if p.get("@type") == "Publication"
            ]:
                publication["@type"] = "PrimaryPublication"
                # Set year as YYYY, if invalid format or missing, year will be current year.
                publication["year"] = _format_date_as_year(publication.pop("date", None))

        if not body.get("meta"):
            body["meta"] = {}
        body["meta"]["recordStatus"] = "marc:New"

    def add_meta_duplicate_publications_009(self):
        """
        Adds meta.marc:relatedIdentifier with any duplicated publications, represents marc field 009""
        """
        duplicated_publications = []
        for duplicated_publication in [
            p for p in self.body.get("_publication_ids", []) if p != self.id
        ]:
            duplicated_publications.append(duplicated_publication)

        if duplicated_publications:
            body = self.body
            if body.get("meta"):
                body["meta"]["marc:relatedIdentifier"] = duplicated_publications

    def add_identified_by_024(self):
        """
        Remakes identifiedBy for types urn, uri and doi, translates to marc field 024
        1. Set @type to identifier
        2. Set typeNote to urn, uri, doi
        3. Remove 'http://urn.kb.se/resolve?urn=' prefix from value (keep urn only)
        """
        body = self.body
        ids_array = body.get("identifiedBy", [])
        for id in ids_array:
            if isinstance(id, dict):
                if id.get("@type") in ["DOI", "URI"]:
                    type_note = dict(id).get("@type")
                    id["@type"] = "Identifier"
                    id["typeNote"] = type_note
                if id.get("value", "").startswith("http://urn.kb.se/resolve?urn="):
                    id["@type"] = "Identifier"
                    id["typeNote"] = "urn"
                    param, value = id.get("value").split("=", 1)
                    id["value"] = value

    def add_instance_of_contribution_100_and_700_710(self):
        """
        Remakes instanceOf.contribution, represents marc fields 100, 700, 710
        1. Remakes first instanceOf.contribution with type aut/cre to type PrimaryContribution
        2. Adds instanceOf.contribution,.@type. to Role and code to last part of @id url
        3. Adds marc:affiliation for each contribution in instanceOf.contribution.agent
        4. Adds marc:titlesAndOtherWordsAssociatedWithAName for each contribution in instanceOf.contribution.agent
        4. Adds new instanceOf.contribution with all organizations needed for marc field 710
        """
        body = self.body
        if body.get("instanceOf"):
            contributions = body["instanceOf"].get("contribution", [])
            contributions = [
                c
                for c in contributions
                if c.get("agent") and c.get("agent").get("@type") == "Person"
            ]
            primary_contribution_is_set = False
            for c in contributions:
                if c.get("role"):
                    for r in c.get("role"):
                        r["@type"] = "Role"
                        if r["@id"]:
                            code = r["@id"].split("/")[-1]
                            r["code"] = code
                            if (code == "aut" or code == "cre") and not primary_contribution_is_set:
                                c["@type"] = "PrimaryContribution"
                                primary_contribution_is_set = True

                if c.get("agent") and c.get("hasAffiliation"):
                    _set_contribution_values(body, c, c.get("hasAffiliation"))
                    if c.get("agent", {}).get("termsOfAddress"):
                        c.get("agent")["marc:titlesAndOtherWordsAssociatedWithAName"] = c.get(
                            "agent"
                        ).get("termsOfAddress")

                    for id_by in c.get("agent", {}).get("identifiedBy", []):
                        if id_by.get("@type") == "Local" and id_by.get("source", {}).get("code"):
                            c.get("agent")["marc:uri"] = (
                                "(Swepub:"
                                + str(id_by.get("source", {}).get("code"))
                                + ")"
                                + str(id_by.get("value"))
                            )

            _move_tmp_global_organizational_contribution_to_instance_of_contribution_for_marc_field_710(
                body
            )

    def add_instance_of_has_title_240(self):
        """Adds hasTitle (from instanceOf.hasTitle) to marc field 240"""
        body = self.body
        if body.get("instanceOf", {}).get("hasTitle"):
            body["hasTitle"] = body.get("instanceOf", {}).pop("hasTitle")

    def add_instance_of_subject_650(self):
        """
        Remakes SSIF instanceOf.classification, represents marc field 650
        1. Rename @id to '(SwePub)'+code, 650_0
        2. Rename inScheme.code to 'hsv//'+ language.code, 650_2
        3. Create termComponentList, 650_a and 650_x
        """
        body = self.body
        work = body.setdefault("instanceOf", {})

        subjects = work.setdefault("subject", [])

        kept_classifications = []

        for term in work.get("classification", []):
            if is_ssif_classification(term):
                for lang, pref_label in term.get("prefLabelByLang").items():
                    langcode = 'eng' if lang == 'en' else 'swe'
                    newterm = {
                        "@id": "(SwePub)" + term.get("code", ""),
                        "code": term.get("code", ""),
                        "prefLabel": term.get("prefLabelByLang", {}).get(lang, ""),
                        "language": {
                            "@type": "Language",
                            "@id": f"https://id.kb.se/language/{langcode}",
                            "code": langcode
                        },
                        "inScheme": {
                            "@id": "https://id.kb.se/term/uka/",
                            "@type": "ConceptScheme",
                            "code": f"hsv//{langcode}"
                        },
                    }
                    if "broader" in term:
                        newterm["@type"] = "ComplexSubject"
                        newterm["termComponentList"] = _get_term_components(
                            term["broader"], pref_label, lang
                        )

                        # SSIF has three levels, so we can have two "broader" at most, so let's
                        # keep it simple here.
                        # TODO: Is still still necessary?
                        broader = {
                            "prefLabel": term.get("broader", {}).get("prefLabelByLang", {}).get(lang, "")
                        }
                        if term.get("broader", {}).get("broader"):
                            broader["broader"] = {
                                "prefLabel": term.get("broader", {}).get("broader", {}).get("prefLabelByLang", {}).get(lang, "")
                            }
                        newterm["broader"] = broader
                    else:
                        newterm["@type"] = "Topic"

                    subjects.append(newterm)
            else:
                kept_classifications.append(term)

        if "classification" in work:
            if kept_classifications:
                work["classification"] = kept_classifications
            else:
                del work["classification"]

    def add_instance_of_subject_653(self):
        """
        Remakes instanceOf.subject, represents marc field 653
        Change prefLabel to label for subjects without inScheme
        (label is used determine if it should be added to 653 instead of 650)
        """
        body = self.body
        for s in body.get("instanceOf", {}).get("subject", []):
            if not is_ssif_classification(s):
                langs = s.get("prefLabelByLang", {}).keys()
                for lang in langs:  # should only be one at ths point
                    langcode = "eng" if lang == "en" else "swe"
                    s["language"] = {
                        "@type": "Language",
                        "@id": f"https://id.kb.se/language/{langcode}",
                        "code": langcode
                    }

                for key, value in _find_by_lang(s, "prefLabel"):
                    s.pop(key)
                    s["label"] = value

    def add_is_part_of_773(self):
        """
        Reconstruct isPartOf, affects marc field 773
        1. Sets @type to Instance for each (is)PartOf
        2. Moves isPartOf.hasInstance.extent to isPartOf.extent. Removes the rest of hasInstance
        3. Creates isPartOf.marc:enumerationAndFirstPage  with volumeNumber and issueNumber
        3. Creates part with volumeNumber and issueNumber
        """
        body = self.body
        if body.get("isPartOf"):
            part = ""
            marc_enumeration_and_first_page = ""

            provision_activity_statement = _get_provision_activity_statement(body)
            # Not all parts of 'isPartOf' should remain in body after conversion.
            # Only take parts that has title and does not have 'genreForm' or 'Dataset' as type, ignore other parts.

            to_add_to_body = []
            before_convert = body.pop("isPartOf", [])

            for is_part in before_convert:

                if (
                    is_part.get("hasTitle")
                    and len(is_part.get("hasTitle")) > 0
                    and not is_part.get("genreForm")
                    and is_part["@type"] != "Dataset"
                ):

                    is_part["@type"] = "Instance"
                    has_title = is_part["hasTitle"][0]
                    volume_number = has_title.pop("volumeNumber", None)
                    if volume_number:
                        part = volume_number
                        marc_enumeration_and_first_page = volume_number
                    issue_number = has_title.pop("issueNumber", None)
                    if issue_number:
                        part = part + ":" + issue_number
                        marc_enumeration_and_first_page = (
                            marc_enumeration_and_first_page + ":" + issue_number
                        )
                    if len(is_part.get("hasInstance", {}).get("extent", [])) > 0:
                        extent_label = is_part.get("hasInstance", {}).get("extent")[0].get("label")
                        part = part + ", s. " + extent_label
                        marc_enumeration_and_first_page = (
                            marc_enumeration_and_first_page + "<" + extent_label
                        )
                    if part:
                        body["part"] = [part]
                    if marc_enumeration_and_first_page:
                        is_part["marc:enumerationAndFirstPage"] = marc_enumeration_and_first_page
                    if provision_activity_statement:
                        is_part["provisionActivityStatement"] = provision_activity_statement

                    to_add_to_body.append(is_part)

            if to_add_to_body:
                body["isPartOf"] = to_add_to_body

    def add_electronic_locator_and_identified_by_856(self):
        """
        Remakes electronicLocator, represent marc field 856.
        """
        body = self.body
        if body.get("electronicLocator"):
            electronic_locators = body.get("electronicLocator", [])
            for e_l in electronic_locators:
                e_l["@type"] = "Document"
                if e_l.get("locator"):
                    e_l["uri"] = [e_l.pop("locator", "")]
                elif e_l.get("uri") and not isinstance(e_l.get("uri"), list):
                    e_l["uri"] = [e_l.get("uri", "")]
                if e_l.get("hasNote"):
                    e_l["cataloguersNote"] = [
                        note.get("label") for note in e_l.pop("hasNote", []) if note.get("label")
                    ]
                if e_l.get("label"):
                    e_l["marc:linkText"] = [e_l.get("label")]

        if body.get("identifiedBy"):
            identified_bys = body.get("identifiedBy", [])
            body["relatedTo"] = []
            for i in identified_bys:
                if i.get("typeNote") in ["URI", "DOI", "urn"]:
                    related_to = body.get("relatedTo", [])
                    new_value = {"@type": "Document"}
                    if i.get("typeNote") == "urn":
                        urn = i.get("value", "")
                        assigner = _get_assigner_from_urn(urn)
                        new_value["marc:linkText"] = ["Till lärosätets (" + assigner + ") databas"]
                        new_value["cataloguersNote"] = ["lärosäteslänk"]
                        new_value["uri"] = ["http://urn.kb.se/resolve?urn=" + urn]
                    elif i.get("typeNote") == "DOI" and not i.get("value", "").startswith("http"):
                        doi = i.get("value", "")
                        new_value["uri"] = ["https://doi.org/" + doi]
                    else:
                        new_value["uri"] = [i.get("value", "")]

                    if new_value not in related_to:
                        related_to.append(new_value)
                    body.update({"relatedTo": related_to})


def _set_contribution_values(body, contribution, affiliation):
    if isinstance(affiliation, dict):
        if (affiliation.get("name") or affiliation.get("nameByLang")) and affiliation.get("@type") == "Organization":
            _set_contribution_marc_affiliation(contribution, affiliation)
            _set_global_organizational_contribution_for_marc_field_710(body, affiliation)
        for key, value in affiliation.items():
            _set_contribution_values(body, contribution, value)
    elif isinstance(affiliation, list):
        for key, value in enumerate(affiliation):
            _set_contribution_values(body, contribution, value)


def _set_contribution_marc_affiliation(contribution, affiliation):
    if contribution.get("agent", {}).get("marc:affiliation"):
        marc_affiliations_list = contribution.get("agent", {}).get("marc:affiliation").split(",")
    else:
        marc_affiliations_list = []
    # affiliations can have a single name *or* multiple names in nameByLang...
    marc_affiliations = [affiliation.get("name"), affiliation.get("nameByLang", {}).get("swe"), affiliation.get("nameByLang", {}).get("eng")]

    # ...so add each one of them
    for marc_affiliation in [a for a in marc_affiliations if a is not None]:
        if marc_affiliation not in marc_affiliations_list:
            if _is_kb_se_affiliation(affiliation):
                marc_affiliations_list.insert(0, marc_affiliation)
            else:
                marc_affiliations_list.append(marc_affiliation)
    contribution["agent"]["marc:affiliation"] = ",".join(str(s) for s in marc_affiliations_list)


def _set_global_organizational_contribution_for_marc_field_710(body, affiliation):
    affiliation_name = affiliation.get("name") or affiliation.get("nameByLang", {}).get("swe") or affiliation.get("nameByLang", {}).get("eng")
    if body.get("tmp_global_organizational_contribution"):
        agent = body.get("tmp_global_organizational_contribution").get("agent", {})
        agent_name = agent.get("name", {})
        is_part_of = agent.get("isPartOf", {})
        if not is_part_of and agent_name != affiliation_name:
            is_part_of = {"@type": "Organization", "name": agent.pop("name")}
            agent["isPartOf"] = is_part_of
            if _is_kb_se_affiliation(affiliation):
                marc_subordinate_unit = is_part_of.pop("name")
                is_part_of["name"] = affiliation_name
            else:
                marc_subordinate_unit = affiliation_name
            marc_subordinate_units = agent.get("marc:subordinateUnit", [])

            if (
                marc_subordinate_unit not in marc_subordinate_units
                and marc_subordinate_unit != is_part_of.get("name")
            ):
                marc_subordinate_units.append(marc_subordinate_unit)
                agent["marc:subordinateUnit"] = marc_subordinate_units

    else:
        body["tmp_global_organizational_contribution"] = {
            "@type": "Contribution",
            "agent": {"@type": "Organization", "name": affiliation_name},
            "role": [{"@id": "https://id.kb.se/relator/org", "@type": "Role", "code": "org"}],
        }


def _move_tmp_global_organizational_contribution_to_instance_of_contribution_for_marc_field_710(
    body,
):
    if body.get("tmp_global_organizational_contribution"):
        t_g_o_c = body.pop("tmp_global_organizational_contribution")
        if t_g_o_c not in body["instanceOf"].get("contribution"):
            body["instanceOf"].get("contribution").append(t_g_o_c)


def _is_kb_se_affiliation(affiliation):
    for id_by in affiliation.get("identifiedBy", []):
        if (
            id_by.get("@type", "") == "URI"
            and id_by.get("source", {}).get("@type", "") == "Source"
            and id_by.get("source", {}).get("code", "") == "kb.se"
        ):
            return True
    return False


def _get_term_components(broader, pref_label, lang):
    term_components =  []

    for component in _find_components(broader, lang):
        term_components.append(component)

    term_components.append(
        {"@type": "TopicSubdivision", "prefLabel": pref_label}
    )

    return term_components


def _find_components(broader, lang):
    for key, value in _find_by_lang(broader, "prefLabel", [lang]):
        pref_label = value
        break
    else:
        return

    if not broader.get("broader"):
        yield {"@type": "Topic", "prefLabel": pref_label.upper()}
    else:
        yield from _find_components(broader.get("broader"), lang)
        yield {"@type": "TopicSubdivision", "prefLabel": pref_label}


def _get_assigner_from_urn(url):
    if url and url.startswith("urn:nbn:se"):
        return url.split(":", 4)[3].split("-")[0]
    return ""


def _get_provision_activity_statement(body):
    provision_activity_statement = ""

    for publication in body.get("publication", []):
        if publication.get("place", {}).get("label"):
            provision_activity_statement = publication.get("place", {}).get("label")
        if publication.get("agent", {}).get("label"):
            provision_activity_statement = (
                provision_activity_statement + " : " + publication.get("agent", {}).get("label")
            )
        break
    return provision_activity_statement


def is_ssif_classification(term):
    return term.get("inScheme", {}).get("@id", "").startswith(("https://id.kb.se/term/ssif", "https://id.kb.se/term/uka"))


def _format_date_as_year(date):
    year = None
    if isinstance(date, str):
        try:
            year = datetime.strptime(date, "%Y").year
        except ValueError:
            try:
                year = datetime.strptime(date, "%Y-%m-%d").year
            except ValueError:
                pass

    if year is None:
        year = datetime.today().year
    return str(year)


def _find_by_lang(item, key, by_lang_pref_order=['sv', 'en']):
    bylangkey = f"{key}ByLang"
    bylang = item.get(bylangkey)

    if bylang:
        for lang in by_lang_pref_order:
            if lang in bylang:
                yield bylangkey, bylang[lang]
                return
        for value in bylang.values():
            yield bylangkey, value
            return

    if key in item:
        yield key, item[key]


if __name__ == '__main__':
    import json
    import sys

    indata = json.load(sys.stdin)['result']
    outdata = Publication(indata).body_with_required_legacy_search_fields
    json.dump(outdata, sys.stdout, indent=2, ensure_ascii=False)
