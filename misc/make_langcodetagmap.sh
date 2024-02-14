#!/bin/bash
curl -s https://libris.kb.se/sparql -HAccept:application/sparql-results+xml --data-urlencode 'query=
PREFIX : <https://id.kb.se/vocab/>
SELECT DISTINCT (STR(?langcode) AS ?code) (STR(?langtag) AS ?tag) {
  GRAPH ?g { ?g :mainEntity ?s . ?s a :Language }
  FILTER(isIRI(?s)) .
  ?s :code ?langtag, ?langcode .
  FILTER(datatype(?langtag) = :ISO639-1)
  FILTER(datatype(?langcode) = :ISO639-2)
} ORDER BY ?langcode
' | xsltproc <(cat <<END
<langmap xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
         xmlns:sr="http://www.w3.org/2005/sparql-results#"
         xsl:version="1.0">
    <xsl:for-each select="/sr:sparql/sr:results/sr:result">
        <lang code="{sr:binding[@name='code']/sr:literal}"
              tag="{sr:binding[@name='tag']/sr:literal}"/>
    </xsl:for-each>
</langmap>
END
) - | xmllint --format -
