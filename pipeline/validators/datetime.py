from datetime import datetime
from validators.shared import validate_base_unicode
from util import make_event

def validate_date_time(dt, path, events):
    """Valid date formats are YYYY and YYYY-MM-DD, as specified in Swepub MODS specification.
    """
    if isinstance(dt, str):
        if not validate_base_unicode(dt):
            events.append(make_event("validation", "datetime", path, "unicode", "invalid"))
            return False

        try:
            datetime.strptime(dt, '%Y')
            return True
        except ValueError:
            try:
                datetime.strptime(dt, '%Y-%m-%d')
                return True
            except ValueError:
                events.append(make_event("validation", "datetime", path, "format", "invalid"))
                return False

    events.append(make_event("validation", "datetime", path, "format", "invalid"))
    return False
