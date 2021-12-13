import lxml.etree as et
from io import StringIO
from log import log_for_OAI_id

MINIMUM_LEVEL_FILTER = et.XSLT(et.parse('./pipeline/minimumlevelfilter.xsl'))

def _should_be_rejected(raw_xml, body):
    error_list = []

    #errors = _minimum_level_checker(body['source_version'])
    parsed_xml = et.parse(StringIO(raw_xml))
    errors = MINIMUM_LEVEL_FILTER(parsed_xml)
    
    if errors.getroot():
        for error in errors.getroot():
            error_list.append(error.text)
        min_level_errors = {'bibliographical_minimum_level_error': error_list}
        #body['system_events']['converter'] = min_level_errors
        log_for_OAI_id(body["@id"], min_level_errors)
    return bool(error_list)

def validate(raw_xml, body):
    if _should_be_rejected(raw_xml, body):
        return False
    else:
        log_for_OAI_id(body["@id"], "Converted OK! Does this thing work?")