import re
from util import update_at_path, unicode_translate
from log import log_for_OAI_id

    # flake8: noqa W504
isi_regex = re.compile(
    '(?<![/0-9a-zA-Z])' +  # Shouldnt be preceded by chars that it can contain or '/' (prevent doi)
    '((000[0-9]{12})' +  # Accept one of the two valid formats
    '|' +
    '([Aa]19[0-9a-zA-Z]{12}))' +
    '(?:(?![0-9a-zA-Z]))'  # Shouln't be exceded by chars it can contain
)

def recover_isi(isi, body, path, id):
    translated = unicode_translate(isi)
    if translated != isi:
        isi = translated
        update_at_path(body, path, isi)

    hit = isi_regex.search(isi)
    if hit and hit.group() != isi:
        update_at_path(body, path, hit.group())
        log_for_OAI_id(id, 'ISI enrichment: recovery')
    
    if len(isi) == 30 and isi[:15] == isi[15:]:
        update_at_path(body, path, isi[:15])
        log_for_OAI_id(id, 'ISI enrichment: recovery')
