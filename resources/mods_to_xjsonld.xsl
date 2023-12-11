<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:mods="http://www.loc.gov/mods/v3"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    version="1.0"
    xmlns:exsl="http://exslt.org/common"
    xmlns:set="http://exslt.org/sets"
    extension-element-prefixes="exsl set">

    <xsl:output indent="yes" encoding="UTF-8"/>

    <xsl:template match="/">
        <xsl:apply-templates select="*"/>
    </xsl:template>

    <xsl:template match="mods:mods">
        <dict>
            <string key="@context">https://id.kb.se/context.jsonld</string>
            <string key="@id"></string>
            <string key="@type">Instance</string>
            <dict key="instanceOf">
                <xsl:choose>
                    <xsl:when test="mods:typeOfResource = 'text'">
                        <string key="@type">Text</string>
                    </xsl:when>
                    <xsl:when test="mods:typeOfResource = 'stillimage'">
                        <string key="@type">StillImage</string>
                    </xsl:when>
                    <xsl:when test="mods:typeOfResource = 'sound recording - nonmusical'">
                        <string key="@type">NonMusicalAudio</string>
                    </xsl:when>
                    <xsl:when test="mods:typeOfResource = 'sound recording - musical'">
                        <string key="@type">Music</string>
                    </xsl:when>
                    <xsl:when test="mods:typeOfResource = 'sound recording'">
                        <string key="@type">Audio</string>
                    </xsl:when>
                    <xsl:when test="mods:typeOfResource = 'software, multimedia'">
                        <string key="@type">Multimedia</string>
                    </xsl:when>
                    <xsl:when test="mods:typeOfResource = 'notated music'">
                        <string key="@type">NotatedMusic</string>
                    </xsl:when>
                    <xsl:when test="mods:typeOfResource = 'mixed material'">
                        <string key="@type">MixedMaterial</string>
                    </xsl:when>
                    <xsl:when test="mods:typeOfResource = 'cartographic'">
                        <string key="@type">Cartography</string>
                    </xsl:when>
                    <xsl:when test="mods:typeOfResource = 'three dimensional object'">
                        <string key="@type">Object</string>
                    </xsl:when>
                    <xsl:when test="mods:typeOfResource = 'moving image'">
                        <string key="@type">MovingImage</string>
                    </xsl:when>
                    <xsl:otherwise>
                        <string key="@type">Text</string>
                    </xsl:otherwise>
                </xsl:choose>
                <array key="genreForm">
                    <xsl:call-template name="content_type"/>
                    <xsl:call-template name="type"/>
                </array>
                <array key="language">
                    <xsl:for-each select="mods:language/mods:languageTerm[@type = 'code']">
                        <dict>
                            <string key="@type">Language</string>
                            <string key="@id">https://id.kb.se/language/<xsl:value-of select="."/></string>
                            <string key="code"><xsl:value-of select="."/></string>
                            <string key="langCode"><xsl:value-of select="."/></string>
                            <dict key="source">
                                <string key="@type">Source</string>
                                <string key="code"><xsl:value-of select="@authority"/></string>
                            </dict>
                        </dict>
                    </xsl:for-each>
                    <xsl:for-each select="mods:language/mods:languageTerm[not(@type)]">
                        <dict>
                            <string key="@type">Language</string>
                            <string key="@id">https://id.kb.se/language/<xsl:value-of select="text()"/></string>
                            <string key="code"><xsl:value-of select="text()"/></string>
                        </dict>
                    </xsl:for-each>
                </array>
                <array key="hasTitle">
                    <xsl:apply-templates select="mods:titleInfo"/>
                </array>
                <xsl:if test="mods:abstract">
                    <array key="summary">
                        <xsl:for-each select="mods:abstract">
                            <dict>
                                <string key="@type">Summary</string>
                                <string key="label"><xsl:value-of select="text()"/></string>
                                <xsl:if test="@lang">
                                    <dict key="language">
                                        <string key="@type">Language</string>
                                        <string key="@id">https://id.kb.se/language/<xsl:value-of select="@lang"/></string>
                                        <string key="code"><xsl:value-of select="@lang"/></string>
                                    </dict>
                                </xsl:if>
                            </dict>
                        </xsl:for-each>
                    </array>
                </xsl:if>
                <array key="contribution">
                    <xsl:call-template name="names"/>
                </array>
                <array key="subject">
                    <xsl:call-template name="subjects"/>
                    <xsl:call-template name="uka_subjects"/>
                </array>
                <array key="hasNote">
                    <xsl:if test="mods:note[@type = 'creatorCount']">
                        <dict>
                            <string key="@type">CreatorCount</string>
                            <string key="label"><xsl:value-of select="mods:note[@type = 'creatorCount']"/></string>
                        </dict>
                    </xsl:if>
                    <dict>
                        <string key="@type">PublicationStatus</string>
                        <xsl:choose>
                            <xsl:when test="mods:note[@type = 'publicationStatus'] = 'Published'">
                                <string key="@id">https://id.kb.se/term/swepub/Published</string>
                            </xsl:when>
                            <xsl:when test="not(mods:note[@type = 'publicationStatus'])">
                                <string key="@id">https://id.kb.se/term/swepub/Published</string>
                            </xsl:when>
                            <xsl:when test="mods:note[@type = 'publicationStatus'] = 'Preprint'">
                                <string key="@id">https://id.kb.se/term/swepub/Preprint</string>
                            </xsl:when>
                            <xsl:when test="mods:note[@type = 'publicationStatus'] = 'Submitted'">
                                <string key="@id">https://id.kb.se/term/swepub/Submitted</string>
                            </xsl:when>
                            <xsl:when test="mods:note[@type = 'publicationStatus'] = 'Accepted'">
                                <string key="@id">https://id.kb.se/term/swepub/Accepted</string>
                            </xsl:when>
                            <xsl:when test="mods:note[@type = 'publicationStatus'] = 'In press'">
                                <string key="@id">https://id.kb.se/term/swepub/InPress</string>
                            </xsl:when>
                            <xsl:when test="mods:note[@type = 'publicationStatus'] = 'Epub ahead of print/Online first'">
                                <string key="@id">https://id.kb.se/term/swepub/EpubAheadOfPrintOnlineFirst</string>
                            </xsl:when>
                        </xsl:choose>
                    </dict>
                    <xsl:for-each select="mods:note[not(@type)]">
                        <dict>
                            <string key="@type">Note</string>
                            <string key="label"><xsl:value-of select="."/></string>
                        </dict>
                    </xsl:for-each>
                </array>
            </dict>
            <xsl:if test="mods:physicalDescription/mods:extent">
                <dict key="extent">
                    <string key="@type">Extent</string>
                    <string key="label"><xsl:value-of select="mods:physicalDescription/mods:extent"/></string>
                </dict>
            </xsl:if>

            <xsl:call-template name="identifiers"/>

            <xsl:if test="mods:relatedItem[@type = 'host'] and mods:relatedItem[@type = 'series']" >
                <array key="partOf">
                    <xsl:for-each select="mods:relatedItem[@type = 'host']">
                        <dict>
                            <xsl:call-template name="relatedItem">
                                <xsl:with-param name="relatedItem" select="." />
                            </xsl:call-template>
                            <array key="hasSeries">
                                <xsl:for-each select="../mods:relatedItem[@type = 'series']">
                                    <dict>
                                        <xsl:call-template name="relatedItem">
                                            <xsl:with-param name="relatedItem" select="." />
                                        </xsl:call-template>
                                    </dict>
                                </xsl:for-each>
                            </array>
                        </dict>
                    </xsl:for-each>
                </array>
            </xsl:if>
            <xsl:if test="mods:relatedItem[@type = 'host'] and not(mods:relatedItem[@type = 'series'])">
                <array key="partOf">
                    <xsl:for-each select="mods:relatedItem[@type = 'host']">
                        <dict>
                            <xsl:call-template name="relatedItem">
                                <xsl:with-param name="relatedItem" select="." />
                            </xsl:call-template>
                        </dict>
                    </xsl:for-each>
                </array>
            </xsl:if>
            <xsl:if test="mods:relatedItem[@type = 'series'] and not(mods:relatedItem[@type = 'host'])">
                <array key="hasSeries">
                    <xsl:for-each select="mods:relatedItem[@type = 'series']">
                        <dict>
                            <xsl:call-template name="relatedItem">
                                <xsl:with-param name="relatedItem" select="." />
                            </xsl:call-template>
                        </dict>
                    </xsl:for-each>
                </array>
            </xsl:if>
            <xsl:if test="mods:recordInfo">
                <dict key="meta">
                    <string key="@type">AdminMetadata</string>
                    <xsl:if test="mods:recordInfo/mods:recordContentSource">
                        <dict key="assigner">
                            <string key="@type">Agent</string>
                            <string key="label"><xsl:value-of select="mods:recordInfo/mods:recordContentSource"/></string>
                        </dict>
                    </xsl:if>
                    <xsl:if test="mods:recordInfo/mods:recordContentSource/@authority">
                        <dict key="source">
                            <string key ="@type">Source</string>
                            <string key="value"><xsl:value-of select="mods:recordInfo/mods:recordContentSource/@authority"/></string>
                        </dict>
                    </xsl:if>
                    <xsl:if test="mods:recordInfo/mods:recordCreationDate">
                        <string key="creationDate">
                            <xsl:call-template name="date">
                                 <xsl:with-param name="date" select="mods:recordInfo/mods:recordCreationDate" />
                            </xsl:call-template>
                        </string>
                    </xsl:if>
                    <xsl:if test="mods:recordInfo/mods:recordChangeDate">
                        <string key="changeDate">
                            <xsl:call-template name="date">
                                 <xsl:with-param name="date" select="mods:recordInfo/mods:recordChangeDate" />
                            </xsl:call-template>
                        </string>
                    </xsl:if>
                </dict>
            </xsl:if>
            <xsl:if test="mods:physicalDescription/mods:form">
                <dict key="carrierType">
                    <string key="@type">CarrierType</string>
                    <string key="label"><xsl:value-of select="mods:physicalDescription/mods:form"/></string>
                    <xsl:if test="mods:physicalDescription/mods:form[@authority = 'marcform']">
                        <dict key="source">
                            <string key="@type">Source</string>
                            <string key="code"><xsl:value-of select="mods:physicalDescription/mods:form/@authority"/></string>
                        </dict>
                    </xsl:if>
                </dict>
            </xsl:if>
            <xsl:if test="mods:originInfo">
                <xsl:if test="mods:originInfo/mods:publisher or mods:originInfo/mods:place or mods:originInfo/mods:dateIssued">
                    <array key="publication">
                        <dict>
                            <string key="@type">Publication</string>
                            <xsl:if test="mods:originInfo/mods:publisher">
                                <dict key="agent">
                                    <string key="@type">Agent</string>
                                    <string key="label"><xsl:value-of select="mods:originInfo/mods:publisher"/></string>
                                </dict>
                            </xsl:if>
                            <xsl:if test="mods:originInfo/mods:place/mods:placeTerm">
                                <dict key="place">
                                    <string key="@type">Place</string>
                                    <string key="label"><xsl:value-of select="mods:originInfo/mods:place/mods:placeTerm"/></string>
                                </dict>
                            </xsl:if>
                            <xsl:if test="mods:originInfo/mods:dateIssued">
                                <string key="date">
                                    <xsl:call-template name="date">
                                        <xsl:with-param name="date" select="mods:originInfo/mods:dateIssued" />
                                    </xsl:call-template>
                                </string>
                            </xsl:if>
                        </dict>
                    </array>>
                </xsl:if>
                <xsl:if test="mods:originInfo/mods:dateOther">
                    <xsl:for-each select="mods:originInfo/mods:dateOther[@type = 'defence']">
                        <array key="dissertation">
                            <dict>
                                <string key="@type">Dissertation</string>
                                <string key="date">
                                    <xsl:call-template name="date">
                                        <xsl:with-param name="date" select="current()" />
                                    </xsl:call-template>
                                </string>
                            </dict>
                        </array>>
                    </xsl:for-each>
                    <xsl:if test="mods:originInfo/mods:dateOther[@type != 'defence']">
                        <array key="provisionActivity">
                            <xsl:for-each select="mods:originInfo/mods:dateOther[@type != 'defence']">
                                    <dict>
                                        <xsl:choose>
                                            <xsl:when test="@type = 'available'">
                                                <string key="@type">Availability</string>
                                            </xsl:when>
                                            <xsl:when test="@type = 'digitized'">
                                                <string key="@type">Digitization</string>
                                            </xsl:when>
                                            <xsl:when test="@type = 'online'">
                                                <string key="@type">OnlineAvailability</string>
                                            </xsl:when>
                                            <xsl:when test="@type = 'openAccess'">
                                                <string key="@type">OpenAccessAvailability</string>
                                            </xsl:when>
                                        </xsl:choose>
                                        <xsl:choose>
                                            <xsl:when test="current()[@point = 'start']">
                                                <string key="startDate">
                                                    <xsl:call-template name="date">
                                                        <xsl:with-param name="date" select="current()" />
                                                    </xsl:call-template>
                                                </string>
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <string key="date">
                                                    <xsl:call-template name="date">
                                                        <xsl:with-param name="date" select="current()" />
                                                    </xsl:call-template>
                                                </string>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </dict>
                            </xsl:for-each>
                        </array>
                    </xsl:if>
                </xsl:if>
                <xsl:if test="mods:originInfo/mods:edition">
                    <string key="editionStatement">
                        <xsl:value-of select="mods:originInfo/mods:edition"/>
                    </string>
                </xsl:if>
            </xsl:if>
            <xsl:if test="mods:location">
                  <array key="electronicLocator">
                    <xsl:for-each select="mods:location/*">
                      <dict>
                        <string key="@type">Resource</string>
                        <string key="uri"><xsl:value-of select="text()"/></string>
                        <xsl:if test="@displayLabel != ''">
                            <string key="label"><xsl:value-of select="@displayLabel"/></string>
                        </xsl:if>
                        <xsl:if test="@note != '' or @usage = 'primary' or @access != ''">
                            <array key="hasNote">
                              <xsl:for-each select=".">
                                <xsl:if test="@usage = 'primary'">
                                  <dict>
                                    <string key="@type">Note</string>
                                    <string key="noteType">URL usage</string>
                                    <string key="label">primary</string>
                                  </dict>
                                </xsl:if>
                                <xsl:if test="@access != ''">
                                    <dict>
                                        <string key="@type">Note</string>
                                        <xsl:choose>
                                            <xsl:when test="@access = 'preview'">
                                                <string key="label">Preview</string>
                                            </xsl:when>
                                        </xsl:choose>
                                        <xsl:choose>
                                            <xsl:when test="@access = 'raw object'">
                                                <string key="label">Raw object</string>
                                            </xsl:when>
                                        </xsl:choose>
                                        <xsl:choose>
                                            <xsl:when test="@access = 'object in context'">
                                                <string key="label">Object in context</string>
                                            </xsl:when>
                                        </xsl:choose>
                                    </dict>
                                </xsl:if>
                                <xsl:if test="@note != ''">
                                  <dict>
                                    <string key="@type">Note</string>
                                    <string key="label"><xsl:value-of select="@note"/></string>
                                  </dict>
                                </xsl:if>
                              </xsl:for-each>
                            </array>
                        </xsl:if>
                      </dict>
                    </xsl:for-each>
                  </array>
                </xsl:if>
            <xsl:if test="mods:accessCondition">
                <array key="usageAndAccessPolicy">
                    <xsl:for-each select="mods:accessCondition">
                        <dict>
                            <xsl:choose>
                                <xsl:when test="@type = 'use and reproduction' and @xlink:href != ''">
                                     <string key="@id"><xsl:value-of select="@xlink:href"/></string>
                                </xsl:when>
                                <xsl:when test="@type = 'restriction on access' and @displayLabel = 'embargo'">
                                    <string key="@type">Embargo</string>
                                    <xsl:if test="text() != ''">
                                        <string key="endDate"><xsl:value-of select="text()"/></string>
                                    </xsl:if>
                                </xsl:when>
                                <xsl:otherwise>
                                    <string key="@type">AccessPolicy</string>
                                    <string key="label"><xsl:value-of select="text()"/></string>
                                </xsl:otherwise>
                            </xsl:choose>
                        </dict>
                    </xsl:for-each>
                </array>
            </xsl:if>
        </dict>
    </xsl:template>

    <xsl:template name="type">
        <xsl:for-each select="mods:genre[@type = 'outputType' and @authority = 'kb.se']">
            <dict>
                <xsl:choose>
                    <xsl:when test="../mods:genre[@type = 'outputType' and @authority = 'kb.se'] and text() = 'ArtisticPerformance/VisualArtworks'">
                        <string key="@id">https://id.kb.se/term/swepub/ArtisticWork</string>
                    </xsl:when>
                    <xsl:when test="../mods:genre[@type = 'outputType' and @authority = 'kb.se'] and text() = 'artistic-work/curated-exhibition-or-event'">
                        <string key="@id">https://id.kb.se/term/swepub/artistic-work/original-creative-work</string>
                    </xsl:when>
                    <xsl:when test="../mods:genre[@type = 'outputType' and @authority = 'kb.se'] and text() = 'publication/translation'">
                        <string key="@id">https://id.kb.se/term/swepub/publication/critical-edition</string>
                    </xsl:when>
                    <xsl:otherwise>
                        <string key="@id">https://id.kb.se/term/swepub/<xsl:value-of select="."/></string>
                    </xsl:otherwise>
                </xsl:choose>
            </dict>
        </xsl:for-each>
        <xsl:for-each select="mods:genre[@type = 'publicationType' and @authority = 'svep']">
            <xsl:choose>
                <xsl:when test="text() = 'art'">
                    <dict>
                        <string key="@id">https://id.kb.se/term/swepub/JournalArticle</string>
                    </dict>
                    <xsl:if test="not(../mods:genre[@type = 'outputType' and @authority = 'kb.se'])">
                        <xsl:choose>
                                <xsl:when test="../mods:genre[@type = 'contentType' and @authority = 'svep'] = 'ref'">
                                     <dict>
                                        <string key="@id">https://id.kb.se/term/swepub/publication/journal-article</string>
                                    </dict>
                                </xsl:when>
                                <xsl:when test="../mods:genre[@type = 'contentType' and @authority = 'svep'] = 'vet'">
                                     <dict>
                                        <string key="@id">https://id.kb.se/term/swepub/publication/magazine-article</string>
                                    </dict>
                                </xsl:when>
                                <xsl:when test="../mods:genre[@type = 'contentType' and @authority = 'svep'] = 'pop'">
                                     <dict>
                                        <string key="@id">https://id.kb.se/term/swepub/publication/newspaper-article</string>
                                    </dict>
                                </xsl:when>
                        </xsl:choose>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="text() = 'bok'">
                    <dict>
                        <string key="@id">https://id.kb.se/term/swepub/Book</string>
                    </dict>
                    <xsl:if test="not(../mods:genre[@type = 'outputType' and @authority = 'kb.se'])">
                        <dict>
                            <string key="@id">https://id.kb.se/term/swepub/publication/book</string>
                        </dict>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="text() = 'kon'">
                    <dict>
                        <string key="@id">https://id.kb.se/term/swepub/ConferencePaper</string>
                    </dict>
                    <xsl:if test="not(../mods:genre[@type = 'outputType' and @authority = 'kb.se'])">
                        <dict>
                            <string key="@id">https://id.kb.se/term/swepub/conference</string>
                        </dict>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="text() = 'kap'">
                    <dict>
                        <string key="@id">https://id.kb.se/term/swepub/BookChapter</string>
                    </dict>
                    <xsl:if test="not(../mods:genre[@type = 'outputType' and @authority = 'kb.se'])">
                        <dict>
                            <string key="@id">https://id.kb.se/term/swepub/publication/book-chapter</string>
                        </dict>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="text() = 'dok'">
                    <dict>
                        <string key="@id">https://id.kb.se/term/swepub/DoctoralThesis</string>
                    </dict>
                    <xsl:if test="not(../mods:genre[@type = 'outputType' and @authority = 'kb.se'])">
                        <dict>
                            <string key="@id">https://id.kb.se/term/swepub/publication/doctoral-thesis</string>
                        </dict>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="text() = 'rap'">
                    <dict>
                        <string key="@id">https://id.kb.se/term/swepub/Report</string>
                    </dict>
                    <xsl:if test="not(../mods:genre[@type = 'outputType' and @authority = 'kb.se'])">
                        <dict>
                            <string key="@id">https://id.kb.se/term/swepub/publication/report</string>
                        </dict>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="text() = 'rec'">
                    <dict>
                        <string key="@id">https://id.kb.se/term/swepub/Review</string>
                    </dict>
                    <xsl:if test="not(../mods:genre[@type = 'outputType' and @authority = 'kb.se'])">
                        <dict>
                            <string key="@id">https://id.kb.se/term/swepub/publication/book-review</string>
                        </dict>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="text() = 'sam'">
                    <dict>
                        <string key="@id">https://id.kb.se/term/swepub/EditorialCollection</string>
                    </dict>
                    <xsl:if test="not(../mods:genre[@type = 'outputType' and @authority = 'kb.se'])">
                        <dict>
                            <string key="@id">https://id.kb.se/term/swepub/publication/edited-book</string>
                        </dict>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="text() = 'for'">
                    <dict>
                        <string key="@id">https://id.kb.se/term/swepub/ResearchReview</string>
                    </dict>
                    <xsl:if test="not(../mods:genre[@type = 'outputType' and @authority = 'kb.se'])">
                        <dict>
                            <string key="@id">https://id.kb.se/term/swepub/publication/review-article</string>
                        </dict>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="text() = 'kfu'">
                    <dict>
                        <string key="@id">https://id.kb.se/term/swepub/ArtisticWork</string>
                    </dict>
                    <xsl:if test="not(../mods:genre[@type = 'outputType' and @authority = 'kb.se'])">
                        <dict>
                            <string key="@id">https://id.kb.se/term/swepub/artistic-work</string>
                        </dict>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="text() = 'lic'">
                    <dict>
                        <string key="@id">https://id.kb.se/term/swepub/LicentiateThesis</string>
                    </dict>
                    <xsl:if test="not(../mods:genre[@type = 'outputType' and @authority = 'kb.se'])">
                        <dict>
                            <string key="@id">https://id.kb.se/term/swepub/publication/licentiate-thesis</string>
                        </dict>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="text() = 'pat'">
                    <dict>
                        <string key="@id">https://id.kb.se/term/swepub/Patent</string>
                    </dict>
                    <xsl:if test="not(../mods:genre[@type = 'outputType' and @authority = 'kb.se'])">
                        <dict>
                            <string key="@id">https://id.kb.se/term/swepub/intellectual-property/patent</string>
                        </dict>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="text() = 'pro'">
                    <dict>
                        <string key="@id">https://id.kb.se/term/swepub/EditorialProceedings</string>
                    </dict>
                    <xsl:if test="not(../mods:genre[@type = 'outputType' and @authority = 'kb.se'])">
                        <dict>
                            <string key="@id">https://id.kb.se/term/swepub/conference/proceeding</string>
                        </dict>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="text() = 'ovr'">
                    <dict>
                        <string key="@id">https://id.kb.se/term/swepub/OtherPublication</string>
                    </dict>
                    <xsl:if test="not(../mods:genre[@type = 'outputType' and @authority = 'kb.se'])">
                        <dict>
                            <string key="@id">https://id.kb.se/term/swepub/publication</string>
                        </dict>
                    </xsl:if>
                </xsl:when>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>

    <xsl:template name="content_type">
            <xsl:if test="mods:genre[@type = 'contentType' and @authority = 'svep']">
                <dict>
                    <string key="@id">https://id.kb.se/term/swepub/svep/<xsl:value-of select="mods:genre[@type = 'contentType' and @authority = 'svep']"/></string>
                </dict>
            </xsl:if>
    </xsl:template>

    <xsl:template name="date">
        <xsl:param name="date" />
        <string><xsl:value-of select="$date"/></string>
    </xsl:template>

    <xsl:template name="relatedItem">
        <xsl:param name="relatedItem" />
        <xsl:choose>
            <xsl:when test="mods:genre = 'dataset'">
                <string key="@type">Dataset</string>
            </xsl:when>
            <xsl:otherwise>
                <string key="@type">Work</string>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="mods:genre = 'project' or mods:genre = 'programme' or mods:genre = 'grantAgreement' or mods:genre = 'initiative' or mods:genre = 'event'">
            <array key="genreForm">
                <xsl:for-each select="mods:genre">
                    <xsl:choose>
                        <xsl:when test="text() = 'project'">
                            <dict>
                                <string key="@id">https://id.kb.se/term/swepub/project</string>
                            </dict>
                        </xsl:when>
                        <xsl:when test="text() = 'programme'">
                            <dict>
                                <string key="@id">https://id.kb.se/term/swepub/programme</string>
                            </dict>
                        </xsl:when>
                        <xsl:when test="text() = 'grantAgreement'">
                            <dict>
                                <string key="@id">https://id.kb.se/term/swepub/grantAgreement</string>
                            </dict>
                        </xsl:when>
                        <xsl:when test="text() = 'initiative'">
                            <dict>
                                <string key="@id">https://id.kb.se/term/swepub/initiative</string>
                            </dict>
                        </xsl:when>
                        <xsl:when test="text() = 'event'">
                            <dict>
                                <string key="@id">https://id.kb.se/term/swepub/event</string>
                            </dict>
                        </xsl:when>
                    </xsl:choose>
                </xsl:for-each>
            </array>
        </xsl:if>
        <xsl:if test="mods:titleInfo/*">
            <array key="hasTitle">
                <xsl:for-each select="mods:titleInfo">
                    <dict>
                        <xsl:choose>
                            <xsl:when test="@type = 'alternative'"><string key="@type">VariantTitle</string></xsl:when>
                            <xsl:otherwise><string key="@type">Title</string></xsl:otherwise>
                        </xsl:choose>
                        <xsl:if test="../@type = 'series'">
                            <xsl:choose>
                                <xsl:when test="mods:partNumber[. != '']">
                                    <string key="partNumber"><xsl:value-of select="mods:partNumber"/></string>
                                </xsl:when>
                                <xsl:when test="../mods:identifier[@type = 'issue number']">
                                    <string key="partNumber"><xsl:value-of select="../mods:identifier[@type = 'issue number']"/></string>
                                </xsl:when>
                            </xsl:choose>
                        </xsl:if>
                        <xsl:if test="position()=1">
                            <xsl:if test="../mods:part/mods:detail[@type = 'volume'] != ''">
                                <string key="volumeNumber"><xsl:value-of select="../mods:part/mods:detail[@type = 'volume']"/></string>
                            </xsl:if>
                            <xsl:if test="../mods:part/mods:detail[@type = 'issue'] != ''">
                                <string key="issueNumber"><xsl:value-of select="../mods:part/mods:detail[@type = 'issue']"/></string>
                            </xsl:if>
                            <xsl:if test="../mods:part/mods:detail[@type = 'issue number'] != ''">
                                <string key="issueNumber"><xsl:value-of select="../mods:part/mods:detail[@type = 'issue number']"/></string>
                            </xsl:if>
                            <xsl:if test="../mods:part/mods:detail[@type = 'artNo'] != ''">
                                <string key="articleNumber"><xsl:value-of select="../mods:part/mods:detail[@type = 'artNo']"/></string>
                            </xsl:if>
                        </xsl:if>
                        <xsl:for-each select="*">
                            <xsl:choose>
                                <xsl:when test="local-name() = 'title'"><string key="mainTitle"><xsl:value-of select="."/></string></xsl:when>
                                <xsl:when test="local-name() = 'subTitle'"><string key="subtitle"><xsl:value-of select="."/></string></xsl:when>
                                <xsl:when test="local-name() = 'partNumber'"></xsl:when>
                                <xsl:otherwise><string key="{@type}"><xsl:value-of select="."/></string></xsl:otherwise>
                            </xsl:choose>
                        </xsl:for-each>
                    </dict>
                </xsl:for-each>
            </array>
        </xsl:if>
        <xsl:if test="mods:name">
            <array key="contribution">
                <xsl:call-template name="names"/>
            </array>
        </xsl:if>
        <xsl:if test="mods:identifier">
            <xsl:choose>
                <xsl:when test="@type = 'series'">
                    <xsl:call-template name="identifiers">
                        <xsl:with-param name="elements" select="mods:identifier[@type != 'issue number']"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="identifiers"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:if test="mods:part/mods:extent/mods:start != '' or mods:part/mods:extent/mods:end != '' or mods:part/mods:extent/mods:total != ''">
            <dict key="hasInstance">
                <string key="@type">Instance</string>
                <array key="extent">
                    <xsl:for-each select="mods:part/mods:extent">
                        <xsl:if test="mods:start != '' or mods:end != ''">
                            <dict>
                                <string key="@type">Extent</string>
                                <xsl:choose>
                                    <xsl:when test="mods:start and not(mods:end)">
                                        <string key="label"><xsl:value-of select="mods:start" />-</string>
                                    </xsl:when>
                                    <xsl:when test="mods:end and not(mods:start)">
                                        <string key="label">-<xsl:value-of select="mods:end" /></string>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <string key="label"><xsl:value-of select="mods:start" />-<xsl:value-of select="mods:end" /></string>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </dict>
                        </xsl:if>
                        <xsl:if test="mods:total != ''">
                            <dict>
                                <string key="@type">Extent</string>
                                <string key="label"><xsl:value-of select="mods:total" /></string>
                            </dict>
                        </xsl:if>
                    </xsl:for-each>
                </array>
            </dict>
        </xsl:if>
        <xsl:if test="mods:note or mods:part/mods:citation/mods:caption">
            <array key="hasNote">
                <xsl:for-each select="mods:note">
                    <xsl:choose>
                        <xsl:when test="current()[@type = 'sfo']">
                            <dict>
                                <string key="@type">SFO</string>
                                <string key="label"><xsl:value-of select="." /></string>
                            </dict>
                        </xsl:when>
                        <xsl:otherwise>
                            <dict>
                                <string key="@type">Note</string>
                                <string key="label"><xsl:value-of select="." /></string>
                            </dict>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:for-each>
                <xsl:for-each select="mods:part/mods:citation/mods:caption">
                    <dict>
                        <string key="@type">Note</string>
                        <string key="noteType">partText</string>
                        <string key="label"><xsl:value-of select="." /></string>
                    </dict>
                </xsl:for-each>
            </array>
        </xsl:if>
    </xsl:template>

    <xsl:template name="affiliations">
        <xsl:param name="orgs" />
            <xsl:variable name="languages">
                <xsl:for-each select="$orgs/mods:affiliation/@lang">
                    <lang><xsl:value-of select="."/></lang>
                </xsl:for-each>
                <lang></lang>
            </xsl:variable>
            <xsl:for-each select="set:distinct(exsl:node-set($languages)/lang)">
                <xsl:variable name="currentLang" select="."/>
                <xsl:choose>
                    <xsl:when test="$currentLang = ''">
                        <xsl:for-each select="$orgs/mods:affiliation[not(@lang) or @lang = $currentLang]">
                            <xsl:if test="not($orgs/mods:affiliation[@authority = current()/@valueURI])">
                                <xsl:call-template name="affiliation">
                                     <xsl:with-param name="lang" select="$currentLang" />
                                     <xsl:with-param name="orgs" select="$orgs" />
                                     <xsl:with-param name="org" select="." />
                                </xsl:call-template>
                            </xsl:if>
                        </xsl:for-each>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:for-each select="$orgs/mods:affiliation[@lang = $currentLang]">
                            <xsl:if test="not($orgs/mods:affiliation[@authority = current()/@valueURI])">
                                <xsl:call-template name="affiliation">
                                     <xsl:with-param name="lang" select="$currentLang" />
                                     <xsl:with-param name="orgs" select="$orgs" />
                                     <xsl:with-param name="org" select="." />
                                </xsl:call-template>
                            </xsl:if>
                        </xsl:for-each>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:for-each>
    </xsl:template>

    <xsl:template name="affiliation">
        <xsl:param name="orgs" />
        <xsl:param name="org" />
        <xsl:param name="lang" />
        <dict>
            <xsl:choose>
                <xsl:when test="starts-with($org/@valueURI,'https://id.kb.se/country/')">
                    <string key="@id"><xsl:value-of select="$org/@valueURI"/></string>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:choose>
                        <xsl:when test="$org/@type = 'code' or $org/@authority = 'kb.se/collaboration'">
                            <string key="@type">Collaboration</string>
                        </xsl:when>
                        <xsl:otherwise>
                            <string key="@type">Organization</string>
                        </xsl:otherwise>
                    </xsl:choose>
                    <string key="name"><xsl:value-of select="$org"/></string>
                    <xsl:if test="$org/@lang">
                        <dict key="language">
                            <string key="@type">Language</string>
                            <string key="@id">https://id.kb.se/language/<xsl:value-of select="$org/@lang"/></string>
                            <string key="code"><xsl:value-of select="$org/@lang"/></string>
                        </dict>
                    </xsl:if>
                    <xsl:if test="$org/@valueURI and $org/@authority">
                        <array key="identifiedBy">
                            <xsl:choose>
                                <xsl:when test="$org/@authority = 'kb.se'">
                                    <xsl:call-template name="identifier">
                                        <xsl:with-param name="type">uri</xsl:with-param>
                                        <xsl:with-param name="value" select="$org/@valueURI"/>
                                        <xsl:with-param name="sourceCode">kb.se</xsl:with-param>
                                    </xsl:call-template>
                                </xsl:when>
                                <xsl:when test="$org/@authority = 'kb.se/collaboration'">
                                    <xsl:call-template name="identifier">
                                        <xsl:with-param name="type">uri</xsl:with-param>
                                        <xsl:with-param name="value" select="$org/@valueURI"/>
                                    </xsl:call-template>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:call-template name="identifier">
                                        <xsl:with-param name="type" select="$org/@authority"/>
                                        <xsl:with-param name="value" select="$org/@valueURI"/>
                                    </xsl:call-template>
                                </xsl:otherwise>
                            </xsl:choose>
                        </array>
                        <xsl:choose>
                            <xsl:when test="$lang = ''">
                                <xsl:if test="$orgs/mods:affiliation[@valueURI = current()/@authority and (not(@lang) or @lang = $lang)]">
                                    <array key="hasAffiliation">
                                        <xsl:for-each select="$orgs/mods:affiliation[@valueURI = current()/@authority and (not(@lang) or @lang = $lang)]">
                                            <xsl:call-template name="affiliation">
                                                <xsl:with-param name="org" select="." />
                                                <xsl:with-param name="lang" select="$lang" />
                                                <xsl:with-param name="orgs" select="$orgs" />
                                            </xsl:call-template>
                                        </xsl:for-each>
                                    </array>
                                </xsl:if>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:if test="$orgs/mods:affiliation[@valueURI = current()/@authority and @lang = $lang]">
                                    <array key="hasAffiliation">
                                        <xsl:for-each select="$orgs/mods:affiliation[@valueURI = current()/@authority and @lang = $lang]">
                                            <xsl:call-template name="affiliation">
                                                <xsl:with-param name="org" select="." />
                                                <xsl:with-param name="lang" select="$lang" />
                                                <xsl:with-param name="orgs" select="$orgs" />
                                            </xsl:call-template>
                                        </xsl:for-each>
                                    </array>
                                </xsl:if>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
        </dict>
    </xsl:template>

    <xsl:template match="mods:titleInfo">
        <dict>
            <xsl:choose>
                <xsl:when test="@type = 'alternative'"><string key="@type">VariantTitle</string></xsl:when>
                <xsl:otherwise><string key="@type">Title</string></xsl:otherwise>
            </xsl:choose>
            <xsl:for-each select="*">
                <xsl:choose>
                    <xsl:when test="local-name() = 'title'"><string key="mainTitle"><xsl:value-of select="."/></string></xsl:when>
                    <xsl:when test="local-name() = 'subTitle'"><string key="subtitle"><xsl:value-of select="."/></string></xsl:when>
                    <xsl:otherwise><string key="{@type}"><xsl:value-of select="."/></string></xsl:otherwise>
                </xsl:choose>
            </xsl:for-each>
        </dict>
    </xsl:template>

    <xsl:template name="names">
        <xsl:for-each select="mods:name">
            <dict>
                <string key="@type">Contribution</string>
                <dict key="agent">
                    <xsl:if test="@type = 'conference'">
                        <string key="@type">Meeting</string>
                        <xsl:if test="mods:namePart != ''">
                            <xsl:if test="mods:namePart[@lang]">
                                <dict key="nameByLang">
                                    <xsl:for-each select="mods:namePart[@lang]">
                                        <string key="{@lang}"><xsl:value-of select="."/></string>
                                    </xsl:for-each>
                                </dict>
                            </xsl:if>
                            <xsl:if test="mods:namePart[not(@lang)]">
                                <xsl:choose>
                                    <xsl:when test="count(mods:namePart[not(@lang)]) > 1">
                                        <array key="name">
                                            <xsl:for-each select="mods:namePart[not(@lang)]">
                                                <string><xsl:value-of select="."/></string>
                                            </xsl:for-each>
                                        </array>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <string key="name">
                                            <xsl:for-each select="mods:namePart[not(@lang)]">
                                                <xsl:value-of select="."/>
                                                <xsl:if test=". != ../mods:namePart[not(@lang) and last()]">
                                                    <string>, </string>
                                                </xsl:if>
                                            </xsl:for-each>
                                        </string>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:if>
                        </xsl:if>
                    </xsl:if>
                    <xsl:if test="@type = 'corporate'">
                        <string key="@type">Organization</string>
                        <xsl:if test="mods:namePart != ''">
                            <xsl:if test="mods:namePart[@lang]">
                                <dict key="nameByLang">
                                    <xsl:for-each select="mods:namePart[@lang]">
                                        <string key="{@lang}"><xsl:value-of select="."/></string>
                                    </xsl:for-each>
                                </dict>
                            </xsl:if>
                            <xsl:if test="mods:namePart[not(@lang)]">
                                <xsl:choose>
                                    <xsl:when test="count(mods:namePart[not(@lang)]) > 1">
                                        <array key="name">
                                            <xsl:for-each select="mods:namePart[not(@lang)]">
                                                <string><xsl:value-of select="."/></string>
                                            </xsl:for-each>
                                        </array>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <string key="name">
                                            <xsl:for-each select="mods:namePart[not(@lang)]">
                                                <xsl:value-of select="."/>
                                                <xsl:if test=". != ../mods:namePart[not(@lang) and last()]">
                                                    <string>, </string>
                                                </xsl:if>
                                            </xsl:for-each>
                                        </string>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:if>
                        </xsl:if>
                    </xsl:if>
                    <xsl:if test="@type = 'personal'">
                        <string key="@type">Person</string>
                        <xsl:for-each select="mods:namePart">
                            <xsl:choose>
                                <xsl:when test="@type = 'date'"><string key="lifeSpan"><xsl:value-of select="."/></string></xsl:when>
                                <xsl:when test="@type = 'family'"><string key="familyName"><xsl:value-of select="."/></string></xsl:when>
                                <xsl:when test="@type = 'given'"><string key="givenName"><xsl:value-of select="."/></string></xsl:when>
                                <xsl:otherwise><string key="{@type}"><xsl:value-of select="."/></string></xsl:otherwise>
                            </xsl:choose>
                        </xsl:for-each>
                    </xsl:if>
                    <xsl:choose>
                        <xsl:when test="mods:nameIdentifier[not(@invalid) and . != '']">
                            <array key="identifiedBy">
                                <xsl:for-each select="mods:nameIdentifier[not(@invalid) and . != '']">
                                    <xsl:call-template name="identifier">
                                        <xsl:with-param name="type" select="@type"/>
                                        <xsl:with-param name="value" select="."/>
                                    </xsl:call-template>
                                </xsl:for-each>
                            </array>
                        </xsl:when>
                        <xsl:when test="mods:description[@type = 'orcid'] or (@authority != '' and @xlink:href != '')">
                            <array key="identifiedBy">
                                <xsl:if test="mods:description[@type = 'orcid']">
                                    <xsl:call-template name="identifier">
                                        <xsl:with-param name="type">orcid</xsl:with-param>
                                        <xsl:with-param name="value" select="mods:description[@type = 'orcid']"/>
                                    </xsl:call-template>
                                </xsl:if>
                                <xsl:if test="@authority != '' and @xlink:href != ''">
                                    <xsl:call-template name="identifier">
                                        <xsl:with-param name="type" select="@authority"/>
                                        <xsl:with-param name="value" select="@xlink:href"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </array>
                        </xsl:when>
                    </xsl:choose>
                    <xsl:if test="mods:nameIdentifier[@invalid = 'yes' and . != '']">
                        <array key="incorrectlyIdentifiedBy">
                            <xsl:for-each select="mods:nameIdentifier[@invalid = 'yes' and . != '']">
                                <xsl:call-template name="identifier">
                                    <xsl:with-param name="type" select="@type"/>
                                    <xsl:with-param name="value" select="."/>
                                </xsl:call-template>
                            </xsl:for-each>
                        </array>
                    </xsl:if>
                </dict>
                <array key="role">
                    <xsl:for-each select="mods:role/mods:roleTerm">
                        <dict><string key="@id">http://id.loc.gov/vocabulary/relators/<xsl:value-of select="."/></string></dict>
                    </xsl:for-each>
                </array>
                <xsl:if test="./mods:affiliation">
                    <array key="hasAffiliation">
                        <xsl:call-template name="affiliations">
                             <xsl:with-param name="orgs" select="." />
                        </xsl:call-template>
                    </array>
                </xsl:if>
            </dict>
        </xsl:for-each>
    </xsl:template>

     <xsl:template name="uka_subjects">
        <xsl:for-each select="mods:subject[@authority = 'uka.se' and @xlink:href]">
            <dict>
                <string key="@id">https://id.kb.se/term/uka/<xsl:value-of select="@xlink:href"/></string>
                <string key="@type">Topic</string>
                <string key="code"><xsl:value-of select="@xlink:href"/></string>
                <string key="prefLabel"><xsl:value-of select="mods:topic[last()]"/></string>
                <xsl:if test="@lang">
                    <dict key="language">
                        <string key="@type">Language</string>
                        <string key="@id">https://id.kb.se/language/<xsl:value-of select="@lang"/></string>
                        <string key="code"><xsl:value-of select="@lang"/></string>
                    </dict>
                </xsl:if>
                <dict key="inScheme">
                    <string key="@id">https://id.kb.se/term/uka/</string>
                    <string key="@type">ConceptScheme</string>
                    <string key="code"><xsl:value-of select="@authority"/></string>
                </dict>
                <xsl:if test="count(mods:topic) > 1">
                    <dict key="broader">
                        <xsl:call-template name="broader">
                            <xsl:with-param name="topic" select="count(mods:topic) - 1"/>
                        </xsl:call-template>
                    </dict>
                </xsl:if>
            </dict>
        </xsl:for-each>
    </xsl:template>

    <xsl:template name="subjects">
        <xsl:for-each select="mods:subject[(@authority != 'uka.se') or not(@authority)]">
            <dict>
                <string key="@type">Topic</string>
                <xsl:if test="@xlink:href">
                    <string key="code"><xsl:value-of select="@xlink:href"/></string>
                </xsl:if>
                <xsl:if test="@authority">
                    <dict key="inScheme">
                        <string key="@id">
                            <xsl:choose>
                                <xsl:when test="@lang">
                                    <xsl:value-of select="concat(@authority, '/', @lang)"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:value-of select="@authority"/>
                                </xsl:otherwise>
                            </xsl:choose>
                        </string>
                        <string key="@type">ConceptScheme</string>
                        <string key="code"><xsl:value-of select="@authority"/></string>
                    </dict>
                </xsl:if>
                <xsl:if test="@lang">
                    <dict key="language">
                        <string key="@type">Language</string>
                        <string key="@id">https://id.kb.se/language/<xsl:value-of select="@lang"/></string>
                        <string key="code"><xsl:value-of select="@lang"/></string>
                    </dict>
                </xsl:if>
                <string key="prefLabel"><xsl:value-of select="mods:topic[last()]"/></string>
                <xsl:if test="count(mods:topic) > 1">
                    <dict key="broader">
                        <xsl:call-template name="broader">
                            <xsl:with-param name="topic" select="count(mods:topic) - 1"/>
                        </xsl:call-template>
                    </dict>
                </xsl:if>
            </dict>
        </xsl:for-each>
    </xsl:template>

    <xsl:template name="broader">
        <xsl:param name="topic" />
            <string key="prefLabel"><xsl:value-of select="mods:topic[$topic]"/></string>
            <xsl:if test="not($topic = 1)">
                <dict key="broader">
                    <xsl:call-template name="broader">
                        <xsl:with-param name="topic" select="$topic - 1"/>
                    </xsl:call-template>
                </dict>
            </xsl:if>
    </xsl:template>

    <xsl:template name="identifiers">
        <xsl:param name="elements" select="mods:identifier"/>
        <array key="identifiedBy">
            <xsl:for-each select="$elements[not(@invalid) and . != '']">
                <xsl:call-template name="identifier">
                    <xsl:with-param name="type" select="@type"/>
                    <xsl:with-param name="value" select="."/>
                </xsl:call-template>
            </xsl:for-each>
        </array>
        <xsl:if test="$elements[@invalid = 'yes' and . != '']">
            <array key="incorrectlyIdentifiedBy">
                <xsl:for-each select="$elements[@invalid = 'yes' and . != '']">
                    <xsl:call-template name="identifier">
                        <xsl:with-param name="type" select="@type"/>
                        <xsl:with-param name="value" select="."/>
                    </xsl:call-template>
                </xsl:for-each>
            </array>
        </xsl:if>
    </xsl:template>

    <xsl:template name="identifier">
        <xsl:param name="type"/>
        <xsl:param name="value"/>
        <xsl:param name="sourceCode" select="''"/>
        <dict>
            <xsl:variable name="typeXML">
                <xsl:call-template name="identifierType">
                    <xsl:with-param name="type" select="$type"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:copy-of select="$typeXML"/>
            <string key="value"><xsl:value-of select="$value"/></string>
            <xsl:if test="@displayLabel">
                <string key="qualifier"><xsl:value-of select="@displayLabel"/></string>
            </xsl:if>
            <xsl:choose>
                <xsl:when test="$sourceCode">
                    <dict key="source">
                        <xsl:call-template name="identifierType">
                            <xsl:with-param name="type">source</xsl:with-param>
                        </xsl:call-template>
                        <string key="code"><xsl:value-of select="$sourceCode"/></string>
                    </dict>
                </xsl:when>
                <xsl:when test="$typeXML = 'Local'">
                    <dict key="source">
                        <xsl:call-template name="identifierType">
                            <xsl:with-param name="type">source</xsl:with-param>
                        </xsl:call-template>
                        <string key="code"><xsl:value-of select="$type"/></string>
                    </dict>
                </xsl:when>
            </xsl:choose>
        </dict>
    </xsl:template>

    <xsl:template name="identifierType">
        <xsl:param name="type"/>
        <xsl:choose>
            <xsl:when test="$type = 'doi'">
                <string key="@type">DOI</string>
            </xsl:when>
            <xsl:when test="$type = 'hdl'">
                <string key="@type">Hdl</string>
            </xsl:when>
            <xsl:when test="$type = 'isbn'">
                <string key="@type">ISBN</string>
            </xsl:when>
            <xsl:when test="$type = 'ocolc'">
                <string key="@type">WorldCatNumber</string>
            </xsl:when>
            <!-- "worldcat" has been changed to "ocolc"; "worldcat" kept for backwards compatibility" -->
            <xsl:when test="$type = 'worldcat'">
                <string key="@type">WorldCatNumber</string>
            </xsl:when>
            <xsl:when test="$type = 'se-libr'">
                <string key="@type">LibrisNumber</string>
            </xsl:when>
             <!-- "libris" has been changed to "se-libr"; "libris" kept for backwards compatibility" -->
            <xsl:when test="$type = 'libris'">
                <string key="@type">LibrisNumber</string>
            </xsl:when>
            <xsl:when test="$type = 'patent_number'">
                <string key="@type">PatentNumber</string>
            </xsl:when>
            <xsl:when test="$type = 'pmid'">
                <string key="@type">PMID</string>
            </xsl:when>
            <xsl:when test="$type = 'scopus'">
                <string key="@type">ScopusID</string>
            </xsl:when>
            <xsl:when test="$type = 'isi'">
                <string key="@type">ISI</string>
            </xsl:when>
            <xsl:when test="$type = 'issue number'">
                <string key="@type">IssueNumber</string>
            </xsl:when>
            <xsl:when test="$type = 'issn'">
                <string key="@type">ISSN</string>
            </xsl:when>
            <xsl:when test="$type = 'eissn'">
                <string key="@type">ISSN</string>
            </xsl:when>
            <xsl:when test="$type = 'orcid'">
                <string key="@type">ORCID</string>
            </xsl:when>
            <xsl:when test="$type = 'uri'">
                <string key="@type">URI</string>
            </xsl:when>
            <xsl:when test="$type = 'urn' or $type = 'urn:nbn'">
                <string key="@type">URN</string>
            </xsl:when>
            <xsl:when test="$type = 'source'">
                <string key="@type">Source</string>
            </xsl:when>
            <xsl:when test="$type = 'isni'">
                <string key="@type">ISNI</string>
            </xsl:when>
            <xsl:when test="$type = 'swecris'">
                <string key="@type">SweCRIS</string>
            </xsl:when>
            <xsl:when test="$type = 'cordis'">
                <string key="@type">CORDIS</string>
            </xsl:when>
            <xsl:when test="$type = 'fundref'">
                <string key="@type">FundRef</string>
            </xsl:when>
            <xsl:when test="$type = 'ringgold'">
                <string key="@type">Ringgold</string>
            </xsl:when>
            <xsl:when test="$type = 'grid'">
                <string key="@type">GRID</string>
            </xsl:when>
            <xsl:otherwise>
                <string key="@type">Local</string>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>
