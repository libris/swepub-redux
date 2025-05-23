from functools import reduce

from pipeline.auditors.modsfixer import ModsFixer
from pipeline.auditors.swedishlist import SwedishListAuditor
from pipeline.auditors.creatorcount import CreatorCountAuditor
from pipeline.auditors.ssif import SSIFAuditor
from pipeline.auditors.contributor import ContributorAuditor
from pipeline.auditors.issn import ISSNAuditor
from pipeline.auditors.legacy_ssif import LegacySSIFAuditor
from pipeline.auditors.subjects import SubjectsAuditor
from pipeline.auditors.oa import OAAuditor
from pipeline.auditors.autoclassifier import AutoclassifierAuditor
from pipeline.auditors.crossref import CrossrefAuditor
from pipeline.publication import Publication

AUDITORS = [
    ModsFixer(),
    SwedishListAuditor(),
    CreatorCountAuditor(),
    ContributorAuditor(),
    SSIFAuditor(),
    ISSNAuditor(),
    LegacySSIFAuditor(),
    SubjectsAuditor(),
    OAAuditor(),
    AutoclassifierAuditor(),
    CrossrefAuditor(),
]

auditors = AUDITORS


class AuditEvents:
    """An encapsulated representation of the audit event log."""

    def __init__(self, data=None):
        if data is None:
            data = {}
        self._audit_events = data

    @property
    def data(self):
        """Return the underlying audit event data."""
        return self._audit_events

    def add_event(self, name, code, result, initial_value=None, value=None):
        """Add an audit event."""
        if name not in self._audit_events:
            self._audit_events[name] = []
        audit_event = {"code": code, "result": result}
        if initial_value:
            audit_event["initial_value"] = initial_value
        if value:
            audit_event["value"] = value
        self._audit_events[name].append(audit_event)

    def get_event_result(self, name, code_name):
        """Get result for specific audit code or None if not found."""
        if name not in self._audit_events:
            return None
        for event in self._audit_events[name]:
            if event["code"] == code_name:
                return event["result"]
        return None


def audit(body, harvest_cache, session):
    initial_val = (Publication(body), AuditEvents())
    (updated_publication, audit_events) = reduce(
        lambda acc, auditor: auditor.audit(*acc, harvest_cache, session),
        auditors,
        initial_val,
    )
    return updated_publication, audit_events
