from auditors import BaseAuditor

class CreatorCountAuditor(BaseAuditor):
    """A class used to verify existance and value of CreatorCount."""

    def __init__(self):
        self.name = CreatorCountAuditor.__name__

    def audit(self, publication, audit_events):
        """Verify existance and value of CreatorCount."""
        cc_exists = False
        msg = 'CreatorCount not found'
        creator_count = publication.creator_count
        if creator_count is not None:
            cc_exists = True
            msg = 'CreatorCount found'

        #logger.info(msg, extra={'auditor': self.name})

        #step = 'Checking if CreatorCount note exists'
        step = 'creator_count_note_exists'
        new_audit_events = self._add_audit_event(
            audit_events, step, cc_exists)

        if creator_count:
            is_valid_count = True
            msg = 'Valid CreatorCount'
            actual_creator_count = publication.count_creators()
            if actual_creator_count > creator_count:
                is_valid_count = False
                msg = (f'Invalid CreatorCount: was {creator_count}, '
                       f'expected at least {actual_creator_count}')
        else:
            is_valid_count = False
            msg = "Invalid CreatorCount: not found"

        #logger.info(msg, extra={'auditor': self.name})

        #step = 'Checking if CreatorCount is valid'
        step = 'creator_count_check'
        new_audit_events = self._add_audit_event(
            new_audit_events, step, is_valid_count)

        return (publication, new_audit_events)

    def _add_audit_event(self, audit_events, step, is_missing):
        audit_events.add_event(self.name, step, is_missing)
        return audit_events
