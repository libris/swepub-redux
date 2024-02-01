import re

from pipeline.auditors import BaseAuditor

_is_one_digit = re.compile("^[0-9]$").fullmatch


class UKAAuditor(BaseAuditor):
    """Used to warn for comprehensive classification, i.e. only one 1 digit classification"""

    def __init__(self):
        self.name = UKAAuditor.__name__

    def audit(self, publication, audit_events, _harvest_cache, _session):
        comprehensive = any(_is_one_digit(code) for code in codes)
        audit_events.add_event(self.name, "UKA_comprehensive_check", comprehensive)

        return publication, audit_events
