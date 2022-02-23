from functools import reduce
from auditors.swedishlist import Level, SwedishListAuditor
from auditors.creatorcount import CreatorCountAuditor
from auditors.uka import UKAAuditor
from auditors.contributor import ContributorAuditor
from auditors.issn import ISSNAuditor
from auditors.subjects import SubjectsAuditor
from auditors.oa import OAAuditor
from publication import Publication

AUDITORS = [
    SwedishListAuditor(),
    CreatorCountAuditor(),
    ContributorAuditor(),
    UKAAuditor(),
    ISSNAuditor(),
    SubjectsAuditor(),
    OAAuditor(),
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
        audit_event = {'code': code, 'result': result}
        if initial_value:
            audit_event['initial_value'] = initial_value
        if value:
            audit_event['value'] = value
        self._audit_events[name].append(audit_event)
        #self._audit_events.append(make_audit_event(
        #    name=name, type="audit", code=code, step=step, result=result, initial_value=initial_value
        #))

    def get_event_result(self, name, code_name):
        """Get result for specific audit code or None if not found."""
        if name not in self._audit_events:
            return None
        for event in self._audit_events[name]:
            if event['code'] == code_name:
                return event['result']
        return None


def audit(body, harvest_cache):    
    initial_val = (Publication(body), AuditEvents())
    (updated_publication, audit_events) = reduce(lambda acc, auditor: auditor.audit(*acc, harvest_cache), auditors, initial_val)
    return updated_publication, audit_events
