class BaseAuditor():
    """
    Base class for all auditor classes.

    All auditors must implement an audit method that takes a Publication and
    an AuditEvents object and returns a tuple with an updated version of
    both.
    """

    def audit(self, publication, audit_events):
        raise NotImplementedError
