import csv
from os import path

from pipeline.auditors import BaseAuditor
from pipeline.util import Level


DEFAULT_FILE_PATH = path.join(
    path.dirname(path.abspath(__file__)), "../../resources/swedish_list.csv"
)


class SwedishListAuditor(BaseAuditor):
    """A class used to audit a publication according to the Swedish List."""

    def __init__(self, file_path=DEFAULT_FILE_PATH, list=None):
        self.file_path = file_path
        self.name = SwedishListAuditor.__name__
        if list is None:
            self.list = self._read_swedish_list_from_file()
        else:
            self.list = list

    def audit(self, publication, audit_events, _harvest_cache, _session):
        """Check and set the publication's level according to the Swedish List."""
        level = Level.NONE
        year = publication.year

        # Publications with invalid year are considered not audited
        if year and year in self.list:
            for issn in publication.issns:
                if isinstance(issn, str):
                    issn = issn.upper()
                    if issn in self.list[year]:
                        new_level = self.list[year][issn]
                        # We try our best to find an audited level
                        if new_level is not Level.NONE:
                            level = new_level
                        # If we find a peer-reviewed level, we stop looking
                        if level == Level.PEERREVIEWED:
                            break

        new_audit_events = self._add_audit_event(audit_events, level)
        new_publication = self._set_publication_level(publication, level)
        return new_publication, new_audit_events

    def _read_swedish_list_from_file(self):
        swedish_list = {}
        if self.file_path:
            with open(self.file_path) as csv_file:
                csv_reader = csv.DictReader(csv_file, delimiter=";")
                for row in csv_reader:
                    self._parse_row(swedish_list, row)
        return swedish_list

    def _parse_row(self, swedish_list, row):
        year = row["Year"]
        identifier = row["Identifier"].upper()
        level = row["Level"]
        if year not in swedish_list:
            swedish_list[year] = {}
        if identifier in swedish_list[year]:
            # logger.warning(('Duplicate identifier/year combo for Swedish list: '
            #                '{} occurred more than once for year {}').format(identifier, year))
            print(
                (
                    "Duplicate identifier/year combo for Swedish list: {} occurred more than once for year {}"
                ).format(identifier, year)
            )
            exit(-1)
        swedish_list[year][identifier] = self._parse_level(level)

    @staticmethod
    def _parse_level(level):
        if level == "1":
            return Level.PEERREVIEWED
        elif level == "0":
            return Level.NONPEERREVIEWED
        else:
            return Level.NONE

    @staticmethod
    def _add_audit_event(audit_events, level):
        name = SwedishListAuditor.__name__
        code = "set_publication_level"
        audit_events.add_event(name, code, level.value)
        return audit_events

    @staticmethod
    def _set_publication_level(publication, level):
        publication.level = level
        return publication
