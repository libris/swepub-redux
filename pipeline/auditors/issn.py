from pipeline.auditors import BaseAuditor

class ISSNAuditor(BaseAuditor):
    """An auditor class used to check for missing or empty ISSN identifier (if publication is a published article)."""

    def __init__(self):
        self.name = ISSNAuditor.__name__

    def audit(self, publication, audit_events, _harvest_cache, _session):
        code = 'ISSN_missing_check'
        result = False
        message = 'ISSN not missing (or publication is not a published article)'
        if publication.is_article and publication.missing_issn_or_any_empty_issn:
            pub_status = publication.get_publication_status_list
            if 'https://id.kb.se/term/swepub/Published' in pub_status or len(pub_status) == 0:
                message = 'Missing ISSN for published article'
                result = True
        #logger.info(message, extra={'auditor': self.name})
        new_audit_events = self._add_audit_event(audit_events, code, result)
        return (publication, new_audit_events)

    def _add_audit_event(self, audit_events, code, result):
        audit_events.add_event(self.name, code, result)
        return audit_events
