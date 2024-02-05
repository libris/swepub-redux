import re

from pipeline.auditors import BaseAuditor

_is_three_or_five_digits = re.compile("^(\d{3}|\d{5})$").fullmatch


class UKAAuditor(BaseAuditor):
    """Used to warn for comprehensive classification, i.e. *only* one 1 digit classification"""

    def __init__(self):
        self.name = UKAAuditor.__name__

    def audit(self, publication, audit_events, _harvest_cache, _session):
        # If there's nothing but 1 digit classifications, comprehensive will be True
        comprehensive = not any(_is_three_or_five_digits(code) for code in publication.ukas())
        audit_events.add_event(self.name, "UKA_comprehensive_check", comprehensive)

        return publication, audit_events
