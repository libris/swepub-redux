import os
import lxml
import lxml.etree as et

class ModsStylesheet:
    parsed_stylesheets = {}

    def __init__(self, code, url):
        self.url = url
        self.code = code
        self.stylesheet = None

    def apply(self, raw_xml):
        return self._transform(raw_xml)

    def _transform(self, raw_xml):
        self.get_stylesheet()
        if not self.stylesheet:
            return raw_xml
        try:
            parsed_xml = et.fromstring(raw_xml)
        except lxml.etree.XMLSyntaxError:
            print(
                f'Failed to parse XML from "{self.url}" for stylesheet '
                'transform. Continuing harvest without transform, even though '
                'a stylesheet to be applied exists.'
            )
            return raw_xml
        transform = et.XSLT(self.stylesheet)
        transformed_xml = transform(parsed_xml)
        return et.tostring(transformed_xml, encoding='unicode')

    def get_stylesheet(self):
        if self.parsed_stylesheets.get(self.url):
            self.stylesheet = self.parsed_stylesheets.get(self.url)
        else:
            self._get_parsed_xsl()

    def _get_parsed_xsl(self):
        xsl = self._get_xsl_file_path()
        self.stylesheet = et.parse(xsl) if xsl else None
        self._add_to_cache()

    def _get_xsl_file_path(self):
        xsl = f"/app/application/modsstylesheet/{self.code}_stylesheet.xml"
        if os.path.isfile(xsl):
            return xsl

        if 'diva' in self.url:
            return '/app/application/modsstylesheet/general_stylesheet_v3_1.xml'

        return None

    # TODO: Implement remote request for stylesheet
    def _get_xsl_from_remote(self):
        # raw_xsl = urllib.get(..., self.url)
        pass

    def _add_to_cache(self):
        self.parsed_stylesheets[self.url] = self.stylesheet
        print('Stylesheet for "{}" added to cache'.format(self.url))
