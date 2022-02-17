from requests.exceptions import Timeout, ReadTimeout
import rfc3987

def _unicode_char_finder(input_string):
        return [(i, c.encode('unicode_escape')) for i, c in enumerate(input_string) if ord(c) > 127]

def validate_base_unicode(value):
    if _unicode_char_finder(value) != []:
        return False
    return True

def _is_valid_uri(url):
    return rfc3987.match(url, 'URI') is not None

def remote_verification(url, session):
    if not _is_valid_uri(url):
        return False

    #r = session.get(url, verify = False, timeout = 8) # Use a timeout and don't waste time veryfing certificates
    #print(f" * got {r.status_code} on call to: {url}")
    try:
        r = session.head(url, timeout=8)
    except Exception: # Timeout, ReadTimeout ?
        return False
    return r.status_code == 200
