import json
import sys
from pathlib import Path

from pipeline.audit import AuditEvents
from pipeline.auditors.subjects import SubjectsAuditor
from pipeline.legacy_publication import Publication as LegacyPublication
from pipeline.publication import Publication

from misc import mods_to_json


def tee(data, outfile):
    with open(outfile, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(outfile, file=sys.stderr)

    return data


if __name__ == '__main__':
    xslt_file = Path(__file__).parent.parent / 'resources'/ 'mods_to_xjsonld.xsl'

    testfile = sys.argv[1]
    outdir = Path(sys.argv[2])

    if not outdir.exists():
        outdir.mkdir(exist_ok=True)

    rname = Path(testfile).with_suffix('').name

    data = tee(
        mods_to_json.process(xslt_file, testfile)['publication'],
        outdir / f'{rname}-out-1.jsonld',
    )

    audit_events = AuditEvents()
    data = tee(
        SubjectsAuditor().audit(Publication(data), audit_events, None, None)[0].body,
        outdir / f'{rname}-out-2-audited.jsonld',
    )
    print('>', audit_events.data, file=sys.stderr)

    tee(
        LegacyPublication(data).body_with_required_legacy_search_fields,
        outdir / f'{rname}-out-3-legacy.jsonld',
    )
