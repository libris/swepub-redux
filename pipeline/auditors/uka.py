import re

from pipeline.auditors import BaseAuditor

class UKAAuditor(BaseAuditor):
    """A class used to warn for comprehensive classification, i.e only one 1 digit classification"""

    regexp_one_digit = re.compile('^[0-9]$')

    def __init__(self):
        self.name = UKAAuditor.__name__

    def audit(self, publication, audit_events, _harvest_cache, _session):
        comprehensive = False
        ukas = publication.ukas()
        if self._only_1digits(ukas):
            comprehensive = True
            #logger.debug('Comprehensive classification found', extra={'auditor': self.name})
        new_audit_events = self._add_audit_event(audit_events, comprehensive)
        return publication, new_audit_events

    def _add_audit_event(self, audit_events, comprehensive):
        code = 'UKA_comprehensive_check'
        audit_events.add_event(self.name, code, comprehensive)
        return audit_events

    def _only_1digits(self, ukas):
        for uka in ukas:
            if self.regexp_one_digit.fullmatch(uka) is None:
                return False
        return True
