<?xml version="1.0" encoding="UTF-8" ?>

<!--
    Document   : swepub.xsl
    Created on : August 27, 2007, 4:37 PM
    Modified on: September 03, 2009, 08:19 AM
    Modified on: February 27, 2019, 13:11 PM
    Author     : pelle/henrik
    Description: more ktt
        Purpose of transformation follows.

	changed by Jürgen Kerstna, to cope with SwePub analysis, that lighthen restrictions for records
	1. allows publications without "corporate" name
	2. for un-published does not require date nor related item

	Updated by Jacob och Henning March 4, 2019

-->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="2.0"
                xmlns:mods="http://www.loc.gov/mods/v3"
                xmlns:xlink="http://www.w3.org/1999/xlink"
                xmlns:oai="http://www.openarchives.org/OAI/2.0/"
                exclude-result-prefixes="mods xlink oai">
    <xsl:output method="xml" omit-xml-declaration="no" indent="yes" encoding="utf-8"/>

    <xsl:template match="/oai:record">
        <xsl:variable name="errorcodes">
            <xsl:if test="not(oai:metadata/mods:mods)">00modsDataMissing,</xsl:if>
            <xsl:apply-templates select="oai:metadata/mods:mods" mode="validate"/>
        </xsl:variable>
        <xsl:if test="$errorcodes != ''">
            <xsl:attribute name="invalid">true</xsl:attribute>
            <errors>
                <xsl:call-template name="listErrors">
                    <xsl:with-param name="errorList" select="$errorcodes"/>
                </xsl:call-template>
            </errors>
        </xsl:if>
    </xsl:template>

    <!-- Slightly convoluted alternative to for-each-spinners below:
        <xsl:variable name="personal" select="count(mods:name[@type='personal' and count(mods:namePart[normalize-space(translate(., '?-:;.,()[]!#€&#46;/=+$@&quot;', '                    ')) != '']) > 0 and mods:role/mods:roleTerm[@type='code' and @authority='marcrelator' and (. = 'aut' or . = 'edt')]])"/>
    -->
    <xsl:template match="mods:mods" mode="validate">
        <!-- Ansvarigt lärosäte -->
        <xsl:variable name="institutionTmp">
            <!--xsl:for-each select="mods:recordInfo/mods:recordContentSource[. = 'bth' or . = 'cth' or . = 'du' or . = 'esh' or . = 'fhs' or . = 'gih' or . = 'gu' or . = 'hb' or . = 'hh' or . = 'hhs' or . = 'hig' or . = 'his' or . = 'hj' or . = 'hkr' or . = 'hv' or . = 'kau' or . = 'ki' or . = 'kmh' or . = 'konstfack' or . = 'kth' or . = 'liu' or . = 'lnu' or . = 'ltu' or . = 'lu' or . = 'mau' or . = 'mah' or . = 'mdh' or . = 'miun' or . = 'nai' or . = 'nationalmuseum' or . = 'naturvardsverket' or . = 'norden' or . = 'nrm' or . = 'oru' or . = 'polar' or . = 'ri' or . = 'rkh' or . = 'sh' or . = 'shh' or . = 'slu' or . = 'su' or . = 'umu' or . = 'uniart' or . = 'uu' or . = 'vti' or . = 'kkh' or . = 'ra' or . = 'raa' or . = 'ths']"-->
            <xsl:for-each select="mods:recordInfo/mods:recordContentSource">
                <xsl:if test="normalize-space( translate(., '?-:;.,()[]!#€&#46;/=+$@&quot;', '                    ') ) != ''">I</xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:variable name="institution" select="string-length($institutionTmp)"/>
        <!--<xsl:variable name="institution" select="count(mods:recordInfo[mods:recordContentSource[. != '']])"/>-->

        <!-- Upphovsman -->
        <xsl:variable name="personalTmp">
            <xsl:for-each select="mods:name[@type='personal' and mods:role/mods:roleTerm[@type='code' and @authority='marcrelator' and (. = 'aut' or . = 'edt' or . = 'cre')]]/mods:namePart">
                <xsl:if test="normalize-space( translate(., '?-:;.,()[]!#€&#46;/=+$@&quot;', '                    ') ) != ''">I</xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:variable name="personal" select="string-length($personalTmp)"/>

        <xsl:variable name="corporateTmp">
            <!-- corporate w/ namePart -->
            <xsl:for-each select="mods:name[@type='corporate' and @authority != '' and mods:role/mods:roleTerm[@type='code' and @authority='marcrelator' and (. = 'pbl' or . = 'aut' or . = 'edt' or . = 'cre' or . = 'org')]]/mods:namePart">
                <xsl:if test="normalize-space( translate(., '?-:;.,()[]!#€&#46;/=+$@&quot;', '                    ') ) != ''">I</xsl:if>
            </xsl:for-each>
            <!-- corporate w/ affiliation -->
            <xsl:for-each select="mods:name[@type='corporate' and mods:role/mods:roleTerm[@type='code' and @authority='marcrelator' and (. = 'pbl' or . = 'aut' or . = 'edt' or . = 'cre' or . = 'org')]]/mods:affiliation[@authority != '']">
                <xsl:if test="normalize-space( translate(., '?-:;.,()[]!#€&#46;/=+$@&quot;', '                    ') ) != ''">I</xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:variable name="corporate" select="string-length($corporateTmp)"/>

        <xsl:variable name="nameViolationExemption" select="count(mods:genre[@authority = 'kb.se' and @type = 'outputType'][. = 'artistic-work' or . = 'artistic-work/original-creative-work' or . = 'artistic-work/artistic-thesis'])"/>

        <!--<xsl:variable name="corporate" select="count(mods:name[@type='corporate' and @authority != '' and mods:namePart != '' and mods:role/mods:roleTerm[@type='code' and @authority='marcrelator' and . = 'pbl']])"/>-->

        <!-- Titel -->
        <xsl:variable name="titleTmp">
            <xsl:for-each select="mods:titleInfo/mods:title">
                <xsl:if test="normalize-space( translate(., '?-:;.,()[]!#€&#46;/=+$@&quot;', '                    ') ) != ''">I</xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:variable name="title" select="string-length($titleTmp)"/>
        <!--<xsl:variable name="title" select="count(mods:titleInfo[mods:title != ''])"/>-->

        <!-- Publikationstyp -->
        <xsl:variable name="pubtype" select="count(mods:genre[@authority = 'svep' and @type = 'publicationType'][. = 'art' or . = 'bok' or . = 'kfu'  or . = 'for' or . = 'kap' or . = 'rap' or . = 'rec' or . = 'kon' or . = 'sam' or . = 'dok' or . = 'pat' or . = 'ovr' or . = 'lic' or . = 'pro'])"/>
        <xsl:variable name="outtype" select="count(mods:genre[@authority = 'kb.se' and @type = 'outputType'][. = 'publication' or . = 'publication/book' or . = 'publication/edited-book' or . = 'publication/book-chapter' or . = 'publication/report-chapter' or . = 'publication/report' or . = 'publication/journal-article' or . = 'publication/review-article' or . = 'publication/doctoral-thesis' or . = 'publication/licentiate-thesis' or . = 'publication/translation' or . = 'publication/critical-edition' or . = 'publication/working-paper' or . = 'publication/editorial-letter' or . = 'publication/book-review' or . = 'publication/magazine-article' or . = 'publication/newspaper-article' or . = 'publication/encyclopedia-entry' or . = 'publication/journal-issue' or . = 'publication/foreword-afterword' or . = 'publication/preprint' or . = 'publication/other' or . = 'conference' or . = 'conference/poster' or . = 'conference/paper' or . = 'conference/proceeding' or . = 'conference/other' or . = 'intellectual-property' or . = 'intellectual-property/patent' or . = 'intellectual-property/other' or . = 'artistic-work' or . = 'artistic-work/original-creative-work' or . = 'artistic-work/curated-exhibition-or-event' or . = 'other' or . = 'other/data-set' or . = 'other/software' or . = 'ArtisticPerformance/VisualArtworks' or . = 'artistic-work/artistic-thesis'])"/>

        <!-- Innehållsanmärkning -->
        <xsl:variable name="content" select="count(mods:genre[@authority = 'svep' and @type = 'contentType'][. = 'ref' or . = 'vet' or . = 'pop'])"/>
        <xsl:variable name="pubTypeNotRequiringContentType" select="count(mods:genre[@authority = 'svep' and @type = 'publicationType'][. = 'pat' or . = 'ovr' or . = 'kfu'])"/>
        <xsl:variable name="outputTypeNotRequiringContentType" select="count(mods:genre[@authority = 'kb.se' and @type = 'outputType'][. = 'intellectual-property' or . = 'intellectual-property/patent' or . = 'intellectual-property/other' or . = 'other' or . = 'other/data-set' or . = 'other/software' or . = 'artistic-work' or . = 'artistic-work/original-creative-work' or . = 'artistic-work/curated-exhibition-or-event' or . = 'artistic-work/artistic-thesis' or . = 'ArtisticPerformance/VisualArtworks'])"/>
        <xsl:variable name="contentTypeNotRequired" select="number($pubTypeNotRequiringContentType) + number($outputTypeNotRequiringContentType)"/>

        <!-- Utgivningsår -->
        <xsl:variable name="pubyearTmp">
            <xsl:for-each select="mods:originInfo/mods:dateIssued">
                <xsl:if test="normalize-space( translate(., '?-:;.,()[]!#€&#46;/=+$@&quot;', '                    ') ) != ''">I</xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:variable name="pubyear" select="string-length($pubyearTmp)"/>
        <!--<xsl:variable name="pubyear" select="count(mods:originInfo[mods:dateIssued != ''])"/>-->

		<!-- publication Status-->
		<xsl:variable name="pubStatusNotPublished" select="count(mods:note[@type='publicationStatus'][. = 'Preprint' or . = 'Submitted' or . = 'Accepted' or . = 'In press' or . = 'Epub ahead of print/Online first'])"/>

        <!-- output type publication/preprint -->
        <xsl:variable name="publicationPreprint" select="count(mods:genre[@authority = 'kb.se' and @type = 'outputType'][. = 'publication/preprint'])"/>

        <!-- Lokal URL -->
        <xsl:variable name="localurl" select="count(mods:identifier[@type = 'uri' and . != ''])"/>

        <!-- Språk -->
        <xsl:variable name="language" select="count(mods:language[mods:languageTerm[@type = 'code' and ( @authority = 'iso639-2b' or @authority = 'iso639-3') and . != '']])"/>

        <!-- Värdpublikation obligatoriskt för pubtype=art|for|rec|kap-->
        <xsl:variable name="relItemTmp">
            <xsl:for-each select="mods:relatedItem[@type='host']/mods:titleInfo/mods:title">
                <xsl:if test="normalize-space( translate(., '?-:;.,()[]!#€&#46;/=+$@&quot;', '                    ') ) != ''">I</xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:variable name="relatedItem" select="string-length($relItemTmp)"/>

        <!-- Publikationstyp artikel -->
        <xsl:variable name="pubTypeRequiresRelatedItem" select="count(mods:genre[@authority = 'svep' and @type = 'publicationType'][. = 'art' or . = 'for' or . = 'kap' or . = 'rec'])"/>
        <xsl:variable name="excludedGenres" select="count(mods:relatedItem[@type='host']/mods:genre[. = 'project' or . = 'initiative' or . = 'grantAgreement' or . = 'programme' or . = 'event' or . = 'dataset'])"/>
        <xsl:variable name="outputTypeRequiresRelatedItem" select="count(mods:genre[@authority = 'kb.se' and @type = 'outputType'][. = 'publication/book-chapter' or . = 'publication/report-chapter' or . = 'publication/journal-article' or . = 'publication/editorial-letter' or . = 'publication/magazine-article' or . = 'publication/newspaper-article' or . = 'publication/journal-issue' or . = 'publication/book-review' or . = 'publication/review-article' or . = 'publication/foreword-afterword'])"/>
        <xsl:variable name="requiresRelatedItem" select="number($pubTypeRequiresRelatedItem) + number($outputTypeRequiresRelatedItem)"/>

        <!-- Publikationstyp bok -->
        <xsl:variable name="pubTypeRequiresNoRelatedItem" select="count(mods:genre[@authority = 'svep' and @type = 'publicationType'][. = 'bok' or . = 'dok' or . = 'lic' or . = 'pat' or . = 'pro' or . = 'rap'])"/>
        <xsl:variable name="outputTypeRequiresNoRelatedItem" select="count(mods:genre[@authority = 'kb.se' and @type = 'outputType'][. = 'publication/book' or . = 'publication/edited-book' or . = 'publication/report' or . = 'publication/doctoral-thesis' or . = 'publication/licentiate-thesis' or . = 'artistic-work/artistic-thesis' or . = 'conference/proceeding' or . = 'intellectual-property/patent' or . = 'other/software'])"/>
        <xsl:variable name="requiresNoRelatedItem" select="number($pubTypeRequiresNoRelatedItem) + number($outputTypeRequiresNoRelatedItem)"/>

        <xsl:variable name="resultString">
            <xsl:if test="number($institution) = 0">01recordContentSourceViolation,</xsl:if>
            <xsl:if test="number($personal) + number($corporate) + $nameViolationExemption = 0">02nameViolation,</xsl:if>
            <xsl:if test="number($title) = 0">03titleViolation,</xsl:if>
            <!--xsl:if test="number($pubtype) = 0">05publicationTypeViolation,</xsl:if>
            <xsl:if test="number($outtype) = 0">06outputTypeViolation,</xsl:if-->
            <xsl:if test="(number($pubtype) + number($outtype)) = 0">05publicationOrOutputTypeViolation,</xsl:if>
            <xsl:if test="number($content) = 0 and number($contentTypeNotRequired) = 0">07contentTypeViolation,</xsl:if>
            <xsl:if test="number($pubyear) = 0 and number($pubStatusNotPublished) = 0 and number($publicationPreprint) = 0">08publicationDateViolation,</xsl:if> <!-- Status är publicerad men publikationsår saknas samt är inte en preprint publikation -->
            <xsl:if test="number($localurl) = 0">09uriViolation,</xsl:if>
            <xsl:if test="number($language) = 0">10languageViolation,</xsl:if>
            <xsl:if test="number($requiresRelatedItem) > 0 and number($relatedItem) = 0 and number($pubStatusNotPublished) = 0">11relatedItemTypeMissing,</xsl:if>
            <xsl:if test="number($requiresNoRelatedItem) > 0 and number($relatedItem) > 0 and number($excludedGenres) = 0">12relatedItemTypeViolation,</xsl:if> <!-- Det finns related item trots att det inte borde det för vissa publikationstyper, undantaget vissa genrer -->
            <!--xsl:if test="number($corporate) = 0">03Felaktig institution (elementet 'name[@type='corporate']' saknas eller felaktigt),</xsl:if-->

            <!-- Implementera Regel 13, publicationStatusViolation -->

        </xsl:variable>
        <xsl:value-of select="$resultString"/>
     </xsl:template>

    <xsl:template name="listErrors">
        <xsl:param name="errorList"/>
        <xsl:variable name="currentError" select="substring-before($errorList, ',')"/>
        <!--<xsl:variable name="currentError"><xsl:call-template name="mapFilterResult"><xsl:with-param name="result" select="$currentErrorCode"/></xsl:call-template></xsl:variable>-->
        <error type="{substring($currentError, 1, 2)}"><xsl:value-of select="substring($currentError, 3)"/></error>
        <xsl:if test="substring-after($errorList, ',') != ''">
            <xsl:call-template name="listErrors">
                <xsl:with-param name="errorList" select="substring-after($errorList, ',')"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>

    <xsl:template match="*|@*|text()">
        <xsl:copy>
            <xsl:apply-templates select="*|@*|text()"/>
        </xsl:copy>
    </xsl:template>
</xsl:stylesheet>
