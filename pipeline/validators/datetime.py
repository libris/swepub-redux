from datetime import datetime
from validators.shared import validate_base_unicode
from log import log_for_OAI_id

def validate_date_time(dt, id):
    """Valid date formats are YYYY and YYYY-MM-DD, as specified in Swepub MODS specification.
    """
    if isinstance(dt, str):
        if not validate_base_unicode(dt):
            log_for_OAI_id(id, 'DATETIME validation failed: unicode')
            return False

        try:
            datetime.strptime(dt, '%Y')
            return True
        except ValueError:
            try:
                datetime.strptime(dt, '%Y-%m-%d')
                return True
            except ValueError:
                log_for_OAI_id(id, 'DATETIME validation failed: format')
                return False

    log_for_OAI_id(id, 'DATETIME validation failed: format')
    return False
