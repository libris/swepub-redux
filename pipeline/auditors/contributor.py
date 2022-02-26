from auditors import BaseAuditor

class ContributorAuditor(BaseAuditor):
    """An auditor class used to check for duplicate contributor persons."""

    def __init__(self):
        self.name = ContributorAuditor.__name__

    def audit(self, publication, audit_events, _harvest_cache, _session):
        code = 'contributor_duplicate_check'
        result = False
        if publication.has_duplicate_contributor_persons:
            message = 'Publication has duplicate contributor persons'
            result = True
        else:
            message = 'No duplicate contributor persons found'
        #logger.info(message, extra={'auditor': self.name})
        new_audit_events = self._add_audit_event(audit_events, code, result)
        return (publication, new_audit_events)

    def _add_audit_event(self, audit_events, code, result):
        audit_events.add_event(self.name, code, result)
        return audit_events
