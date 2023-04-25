<script>
import Helptexts from '@/assets/json/helptexts.json';
import { mapGetters } from 'vuex';
import ExportMixin from '@/components/mixins/ExportMixin';
import * as Network from '@/utils/Network';
import VueSimpleSpinner from 'vue-simple-spinner';
import SelectSource from '@/components/shared/SelectSource';
import SelectBase from '@/components/shared/SelectBase';

const ExportButtons = () => import('@/components/shared/ExportButtons');

const TableDataLink = () => import('@/components/shared/TableDataLink');
const TableDataList = () => import('@/components/shared/TableDataList');
const TableDataBoolean = () => import('@/components/shared/TableDataBoolean');
const TableDataMultiLine = () => import('@/components/shared/TableDataMultiLine');
const TableDataId = () => import('@/components/shared/TableDataId');
const TableDataSeries = () => import('@/components/shared/TableDataSeries');

export default {
  name: 'export-data',
  mixins: [ExportMixin],
  components: {
    VueSimpleSpinner,
    ExportButtons,
    SelectSource,
    SelectBase,

    TableDataLink,
    TableDataList,
    TableDataBoolean,
    TableDataMultiLine,
    TableDataId,
    TableDataSeries,
  },
  props: {
    query: {
      type: Object,
    },
  },
  data() {
    return {
      previewOrg: null,
      previewHit: null,
      sources: [],
      filteredSources: [],
      fields: [
        {
          key: 'recordId',
          component: 'TableDataId', // component to render
          props: { // props to be passed
            deduped(data) {
              return data.publicationCount > 1;
            },
          },
          label: 'ID',
          selected: true,
          group: 'post',
        },
        {
          key: 'duplicateIds',
          component: 'TableDataList',
          label: 'Sammanslagna ID',
          selected: true,
          group: 'post',
        },
        {
          key: 'publicationCount',
          label: 'Antal poster',
          selected: false,
          group: 'post',
        },
        {
          key: 'source',
          label: 'Organisation',
          component: 'TableDataList',
          selected: true,
          group: 'org',
        },
        {
          key: 'creatorCount',
          label: 'Upphovsantal',
          selected: false,
          group: 'org',
        },
        {
          key: 'creators',
          label: 'Upphovsperson',
          component: 'TableDataList',
          props: {
            targetKeys: ['familyName', 'givenName'], // nested key to be rendered & selected for export
          },
          selected: false,
          group: 'org',
        },
        {
          key: 'creators',
          label: 'Lokalt personID',
          component: 'TableDataList',
          props: {
            targetKeys: ['localId'],
          },
          selected: false,
          group: 'org',
        },
        {
          key: 'creators',
          label: 'ORCID',
          component: 'TableDataList',
          props: {
            targetKeys: ['ORCID'],
            renderComponent: 'TableDataLink',
            unshift: 'https://orcid.org/',
          },
          selected: false,
          group: 'org',
        },
        {
          key: 'creators',
          label: 'Affiliering auktoriserad',
          component: 'TableDataList',
          props: {
            targetKeys: ['affiliation'],
          },
          selected: false,
          group: 'org',
        },
        {
          key: 'creators',
          label: 'Affiliering fritext',
          component: 'TableDataList',
          props: {
            renderFn: this.joinFreetextAffils,
            targetKeys: ['freetext_affiliations'],
          },
          selected: false,
          group: 'org',
        },
        {
          key: 'title',
          label: 'Titel',
          selected: false,
          group: 'publication',
        },
        {
          key: 'outputTypes',
          label: 'Outputtyp',
          component: 'TableDataList',
          props: {
            renderComponent: 'TableDataLink',
            unshift: 'https://id.kb.se/term/swepub/',
          },
          selected: true,
          group: 'publication',
        },
        {
          key: 'publicationType',
          label: 'Publikationstyp',
          component: 'TableDataLink',
          props: {
            unshift: 'https://id.kb.se/term/swepub/',
          },
          selected: false,
          group: 'publication',
        },
        {
          key: 'contentMarking',
          label: 'Innehållsmärkning',
          selected: true,
          group: 'publication',
        },
        {
          key: 'publicationYear',
          label: 'Utgivningsår',
          selected: true,
          group: 'publication',
        },
        {
          key: 'publicationStatus',
          label: 'Publiceringsstatus',
          component: 'TableDataLink',
          props: {
            unshift: 'https://id.kb.se/term/swepub/',
          },
          selected: true,
          group: 'publication',
        },
        {
          key: 'languages',
          label: 'Språk',
          component: 'TableDataList',
          selected: false,
          group: 'publication',
        },
        {
          key: 'keywords',
          label: 'Nyckelord',
          component: 'TableDataList',
          selected: false,
          group: 'publication',
        },
        {
          key: 'summary',
          label: 'Sammanfattning',
          component: 'TableDataMultiLine',
          props: {
            trimAt: 1500,
            lines: 5,
          },
          selected: false,
          group: 'publication',
        },
        {
          key: 'archiveURI',
          label: 'Länk till arkiv',
          selected: false,
          component: 'TableDataLink',
          group: 'publication',
        },
        {
          key: 'DOI',
          component: 'TableDataList',
          props: {
            renderComponent: 'TableDataLink',
          },
          label: 'DOI',
          selected: true,
          group: 'publication_id',
        },
        {
          key: 'ISBN',
          label: 'ISBN',
          component: 'TableDataList',
          selected: false,
          group: 'publication_id',
        },
        {
          key: 'ISI',
          label: 'ISI ID',
          selected: false,
          group: 'publication_id',
        },
        {
          key: 'scopusId',
          label: 'Scopus ID',
          selected: false,
          group: 'publication_id',
        },
        {
          key: 'PMID',
          label: 'PubMed ID',
          selected: false,
          group: 'publication_id',
        },
        {
          key: 'electronicLocator',
          label: 'Fulltextlänk',
          component: 'TableDataLink',
          selected: false,
          group: 'open_access',
        },
        {
          key: 'openAccess',
          label: 'Öppen tillgång',
          selected: false,
          component: 'TableDataBoolean',
          group: 'open_access',
        },
        {
          key: 'publicationChannel',
          label: 'Publiceringskanal',
          selected: true,
          group: 'channel',
        },
        {
          key: 'publisher',
          label: 'Utgivare',
          selected: false,
          group: 'channel',
        },
        {
          key: 'ISSN',
          label: 'ISSN',
          component: 'TableDataList',
          selected: false,
          group: 'channel',
        },
        {
          key: 'swedishList',
          label: 'Svenska listan',
          component: 'TableDataLink',
          props: {
            unshift: 'https://id.kb.se/term/swepub/swedishlist/',
          },
          selected: false,
          group: 'channel',
        },
        {
          key: 'subjects',
          label: 'SSIF 1-siffrig',
          component: 'TableDataList',
          props: {
            targetKeys: ['oneDigitTopics'],
            renderFn: this.extractSubject,
          },
          selected: false,
          group: 'subject',
        },
        {
          key: 'subjects',
          label: 'SSIF 3-siffrig',
          component: 'TableDataList',
          props: {
            targetKeys: ['threeDigitTopics'],
            renderFn: this.extractSubject,
          },
          selected: true,
          group: 'subject',
        },
        {
          key: 'subjects',
          label: 'SSIF 5-siffrig',
          component: 'TableDataList',
          props: {
            targetKeys: ['fiveDigitTopics'],
            renderFn: this.extractSubject,
          },
          selected: false,
          group: 'subject',
        },
        {
          key: 'autoclassified',
          label: 'Autoklassning',
          selected: false,
          group: 'subject',
          component: 'TableDataBoolean',
        },
        {
          key: 'DOAJ',
          label: 'DOAJ',
          selected: false,
          component: 'TableDataBoolean',
          group: 'open_access',
        },
        {
          key: 'openAccessVersion',
          label: 'Version',
          component: 'TableDataLink',
          group: 'open_access',
          selected: false,
        },
        {
          key: 'series',
          label: 'Serie',
          selected: false,
          component: 'TableDataSeries',
          group: 'channel',
        },
      ],
      fieldGroups: [
        {
          id: 'post',
          label: 'Post',
          selected: false,
          indeterminate: false,
        },
        {
          id: 'org',
          label: 'Organisation/upphov',
          selected: false,
          indeterminate: false,
        },
        {
          id: 'publication',
          label: 'Publikation',
          selected: false,
          indeterminate: false,
        },
        {
          id: 'publication_id',
          label: 'Publikations-ID',
          selected: false,
          indeterminate: false,
        },
        {
          id: 'channel',
          label: 'Publiceringskanal',
          selected: false,
          indeterminate: false,
        },
        {
          id: 'subject',
          label: 'Forskningsämne',
          selected: false,
          indeterminate: false,
        },
        {
          id: 'open_access',
          label: 'Öppen tillgång',
          selected: false,
          indeterminate: false,
        },
      ],
    };
  },
  computed: {
    ...mapGetters([
      'settings',
    ]),
    apiEndpoint() {
      return `${this.settings.apiPath}/bibliometrics`;
    },
    exportDescr() {
      return Helptexts.bibliometrics.export_descr;
    },
    allIsChecked() {
      return this.selectedFields.length === this.fields.length;
    },
    selectedFields() {
      return this.fields.filter((field) => field.selected);
    },
    previewInfo() {
      return `${this.hitCount} ${this.hitCount === 1 ? 'post' : 'poster'}`;
    },
  },
  methods: {
    updateGroups() {
      this.fieldGroups = this.fieldGroups.map((group) => {
        const fields = this.fields.filter((field) => {
          if (field.hasOwnProperty('group')) {
            return field.group === group.id;
            // eslint-disable-next-line
          } console.warn(`${field.label} has no group!`);
          return false;
        });
        const selectedFields = fields.filter((field) => field.selected);

        return {
          ...group,
          fields,
          selected: selectedFields.length === fields.length,
          indeterminate: selectedFields.length > 0 && selectedFields.length < fields.length,
        };
      });
    },
    fetchData(type, success, fail, acceptHeader) {
      const queryCopy = { ...this.query };
      if (type === 'preview') {
        if (this.previewOrg != null) {
          queryCopy.org = [this.previewOrg];
        } else {
          delete queryCopy.org;
        }

        queryCopy.limit = this.previewLimit;
      }

      if (type === 'export') {
        // specify fields for export here
        const fields = this.selectKeysForExport();
        queryCopy.fields = fields;
      }

      if (type === 'hitCount') {
        queryCopy.limit = 1;
      }

      const jsonBody = JSON.stringify(queryCopy);
      Network.post(this.apiEndpoint, jsonBody, acceptHeader)
        .then((response) => {
          if (response.statusCode === 200) {
            success(response);
          } else {
            response.json().then((json) => {
              fail(json.errors.join(', '));
            })
              .catch(() => { // no json error
                fail(response.statusText);
              });
          }
        }).catch((err) => fail(err));
    },
    toggleAll() {
      if (this.allIsChecked) {
        // eslint-disable-next-line no-return-assign
        this.fields.map((field) => field.selected = false);
      } else {
        // eslint-disable-next-line no-return-assign
        this.fields.map((field) => field.selected = true);
      }
    },
    getFileName(fileType) {
      return `Swepub_bibliometrics_export.${fileType}`;
    },
    selectKeysForExport() {
      const selectedKeys = [];
      this.selectedFields.forEach((field) => {
        if (field.hasOwnProperty('props') && field.props.hasOwnProperty('targetKeys')) {
          selectedKeys.push(...field.props.targetKeys);
        } else selectedKeys.push(field.key);
      });
      return selectedKeys;
    },
    extractSubject(props) {
      let arr = [];
      Object.keys(props.tdValue).forEach((el) => {
        props.targetKeys.forEach((key) => {
          if (el === key) {
            arr = props.tdValue[el];
          }
        });
      });
      return arr;
    },
    joinFreetextAffils(props) {
      const mapped = props.tdValue.map((el) => {
        if (el.hasOwnProperty('freetext_affiliations') && el.freetext_affiliations) {
          return el.freetext_affiliations.map((e) => e.join(', ')).join(' | ');
        }
        return null;
      });
      return mapped;
    },
    onGroupChange(group) {
      const selectedFields = group.fields.filter((field) => field.selected);

      group.fields.forEach((groupField) => {
        this.fields = this.fields.map((f) => {
          if (f.key === groupField.key) {
            f.selected = selectedFields.length !== group.fields.length;
          }
          return f;
        });
      });

      this.updateGroups();
    },
    getFieldPreview(field) {
      if (this.previewHit != null) {
        return this.previewHit[field.key];
      }

      return '';
    },
    fetchSources() {
      Network.get('/api/v1/info/sources')
        .then(({ sources }) => {
          if (sources != null && sources.length > 0) {
            this.sources = sources;
            this.filterSources();
          }
        });
    },
    filterSources() {
      if (this.sources != null) {
        if (this.query.org.length > 0) {
          /* eslint-disable */
          this.filteredSources = [...this.sources].filter((source) =>
            this.query.org.indexOf(source.code) > -1
          );
          /* eslint-enable */
        } else {
          this.filteredSources = [...this.sources];
        }

        if (this.filteredSources.length > 0) {
          this.previewOrg = this.filteredSources[0].code;
        } else {
          this.previewOrg = null;
        }
      }
    },
    onGoNextPreviewHit() {
      if (this.previewData == null) {
        return false;
      }

      /* eslint-disable */
      const orgHits = [...this.previewData.hits].filter((_hit) =>
        _hit.source.indexOf(this.previewOrg) > -1
      );
      /* eslint-enable */

      if (orgHits.length > 0) {
        if (this.previewHit != null) {
          /* eslint-disable */
          const currentIndex = orgHits.findIndex((_hit) =>
            _hit.recordId === this.previewHit.recordId
          );
          /* eslint-enable */

          if (currentIndex + 1 < orgHits.length) {
            this.previewHit = orgHits[currentIndex + 1];
            return true;
          }
        }

        // eslint-disable-next-line
        this.previewHit = orgHits[0];
      }

      return true;
    },
    onGoPrevPreviewHit() {
      if (this.previewData == null) {
        return false;
      }

      /* eslint-disable */
      const orgHits = [...this.previewData.hits].filter((_hit) =>
        _hit.source.indexOf(this.previewOrg) > -1
      );
      /* eslint-enable */

      if (orgHits.length > 0) {
        if (this.previewHit != null) {
          /* eslint-disable */
          const currentIndex = orgHits.findIndex((_hit) =>
            _hit.recordId === this.previewHit.recordId
          );
          /* eslint-enable */

          if (currentIndex - 1 >= 0) {
            this.previewHit = orgHits[currentIndex - 1];
            return true;
          }
        }

        // eslint-disable-next-line
        this.previewHit = orgHits[orgHits.length - 1];
      }

      return true;
    },
  },
  mounted() {
    this.updateGroups();
    this.fetchSources();
  },
  watch: {
    previewData() {
      this.onGoNextPreviewHit();
    },
    previewOrg() {
      this.previewHit = null;
      this.getPreview();
      this.onGoNextPreviewHit();
    },
    query() {
      this.filterSources();
    },
  },
};
</script>

<template>
  <section
    class="ExportData"
    id="preview-section"
    aria-labelledby="preview-heading"
    ref="previewSection"
    :aria-busy="previewLoading"
    aria-live="polite"
  >
    <!-- loading -->
    <vue-simple-spinner
      v-if="previewLoading"
      class="ExportData-previewLoading"
    />

    <!-- error -->
    <div v-else-if="previewError">
      <p class="error" role="alert" aria-atomic="true">{{ previewError }}</p>
    </div>

    <!-- has preview data -->
    <template v-else>
      <hr class="horizontal-wrapper divided-section">

      <h2 id="preview-heading" class="horizontal-wrapper heading heading-md">
        Val av parametrar
      </h2>

      <!-- no hits -->
      <p v-if="previewData.total === 0" class="horizontal-wrapper">
        Inga träffar
      </p>

      <!-- export limit exceeded -->
      <div v-else-if="exportLimitExceededWarning" class="horizontal-wrapper">
        <span class="error" role="alert" aria-atomic="true">{{ exportLimitExceededWarning }}</span>
      </div>

      <!-- export possible -->
      <div v-else>
        <div class="horizontal-wrapper">
          <p class="ExportData-descr" v-html="exportDescr" id="export-data-descr" />

          <div class="ExportData-tools">
            <div></div>

            <div class="buttons-wrapper">
              <!-- hits info -->
              <p class="bold" role="status">
                <span class="phone">
                  Exportera
                </span>
                {{ ' ' + previewInfo }}
              </p>

              <!-- export btns -->
              <export-buttons
                :exportLoading="exportLoading"
                :exportAllowed="exportAllowed"
                :exportError="exportError"
                @export-json="exportJson"
                @export-csv="exportCsv"
                @export-tsv="exportTsv"
              />
            </div>
          </div>
        </div>

        <!-- field toggle -->
        <section
          class="ExportData-pickerContainer horizontal-wrapper"
          aria-labelledby="export-data-descr"
          aria-controls="preview-section"
        >
          <table class="ExportData-table">
            <thead>
              <tr>
                <th class="desktop-checkAll">
                  <input
                    type="checkbox"
                    id="export_checkAll"
                    :checked="allIsChecked"
                    @change="toggleAll"
                  />
                </th>

                <th class="desktop-cell">
                  Parametrar ({{ selectedFields.length }}/{{ fields.length }})
                </th>

                <th>
                  <div class="ExportData-previewSelector">
                    <div class="select-container">
                      Förhandsgranska
                      <select-base
                        v-model="previewOrg"
                        :providedOptions="filteredSources"
                        :value="previewOrg"
                        :multiple="false"
                        useValueProp="code"
                        useLabelProp="name"
                      />
                    </div>

                    <div class="next-source-button tablet" @click="onGoPrevPreviewHit">
                      <span
                        class="icon"
                        :style="{ transform: 'rotate(180deg)', marginLeft: 0, marginRight: '1rem' }"
                      >
                        <font-awesome-icon
                          :icon="['fa', 'chevron-right']"
                          role="presentation"
                        />
                      </span>

                      <span class="desktop">
                        Föregående
                      </span>
                    </div>

                    <div class="next-source-button tablet" @click="onGoNextPreviewHit">
                      <span class="desktop">
                        Nästa
                      </span>

                      <span class="icon">
                        <font-awesome-icon
                          :icon="['fa', 'chevron-right']"
                          role="presentation"
                        />
                      </span>
                    </div>
                  </div>
                </th>
              </tr>
            </thead>

            <tbody>
              <tr class="narrow-row">
                <td>
                  <input
                    type="checkbox"
                    id="export_checkAll"
                    :checked="allIsChecked"
                    @change="toggleAll"
                  />
                </td>

                <td>
                  Parametrar ({{ selectedFields.length }}/{{ fields.length }})
                </td>
              </tr>
            </tbody>

            <tbody
              class="ExportData-tableGroup"
              :aria-labelledby="`group-${group.id}`"
              v-for="group in fieldGroups"
              :key="group.id"
            >
              <!-- GROUP ROW-->
              <tr class="ExportData-tableGroupRow tablet-row">
                <td class="ExportData-tableCellAction">
                  <input
                    type="checkbox"
                    :id="`${group.id}`"
                    :indeterminate.prop="group.indeterminate"
                    v-model="group.selected"
                    @change="onGroupChange(group)"
                  />
                </td>

                <td class="ExportData-tableCellLabel">
                  {{ group.label }}
                </td>

                <td class="ExportData-tableCellPreview desktop-cell">
                </td>
              </tr>

              <!-- GROUP FIELDS-->
              <tr
                class="ExportData-tableFieldRow"
                v-for="(field, index) in group.fields"
                :key="`${group.id}-${field.key}-${index}`"
                :class="field.selected ? 'selected' : ''"
              >
                <td class="ExportData-tableCellAction">
                  <input
                    type="checkbox"
                    :id="`${group.id}-${field.key}-${index}`"
                    v-model="field.selected"
                    @change="updateGroups"
                  />
                </td>

                <td class="ExportData-tableCellLabel">
                  <span class="ExportData-tableCellLabelContent">
                    {{ field.label }}
                  </span>

                  <div class="no-desktop">
                    <component
                      v-if="(field.component &&
                      (getFieldPreview(field)) || field.component === 'TableDataBoolean')"
                      :is="field.component"
                      :tdKey="field.key"
                      :tdValue="getFieldPreview(field)"
                      :trData="field"
                      v-bind="field.props"
                    />

                    <span v-else-if="field.key" :title="field.key">
                      {{ getFieldPreview(field) }}
                    </span>
                  </div>
                </td>

                <td class="ExportData-tableCellPreview desktop-cell">
                  <!-- Renders the component and passes props
                  specified in tableCols component prop -->
                  <!-- must force-render a falsey boolean value -->
                  <component
                    v-if="(field.component &&
                    (getFieldPreview(field)) || field.component === 'TableDataBoolean')"
                    :is="field.component"
                    :tdKey="field.key"
                    :tdValue="getFieldPreview(field)"
                    :trData="field"
                    v-bind="field.props"
                  />

                  <span v-else-if="field.key" :title="field.key">
                    {{ getFieldPreview(field) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>
    </template>
  </section>
</template>

<style lang="scss">
.ExportData {
  margin-bottom: 3em;

  table {
    border-spacing: 0;
  }

  &-table {
    width: 100%;
    max-width: 100%;

    @media (max-width: 850px) {
      overflow-x: auto;
      table-layout: auto;
    }

    th, td {
      border-top: 1px solid $greyLight;
      border-right: 1px solid $greyLight;
      padding: 1rem;
    }

    th {
      position: sticky;
      top: 0;
      box-shadow: 0px 1px 0px $greyLight;
      font-weight: 600;
      text-align: left;
      background-color: white;
      white-space: nowrap;
      text-overflow: ellipsis;
    }

    th.desktop-checkAll {
      width: 0px;
      padding: 0px;

      input {
        display: none;
      }

      @media (min-width: $screen-md) {
        width: auto;
        padding: 1rem;

        input {
          display: block;
        }
      }
    }

    tr.ExportData-tableGroupRow {
      td {
        font-weight: bold;
        background-color: $greyLighter;
      }
    }

    tr.ExportData-tableFieldRow {
      td {
        color: $greyLight;
        font-style: italic;
      }

      &.selected {
        td {
          color: inherit;
          font-style: normal;
        }
      }
    }

    td {
      vertical-align: middle;
      box-sizing: border-box;

      // Nested table cells
      td {
        padding: 0;
        white-space: normal;
      }

      @media (min-width: $screen-md) {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }

    tbody {
      tr {
        td {
          &:first-of-type {
            border-left: 1px solid $greyLight;
          }
        }
      }

      &:last-of-type {
        tr:last-of-type {
          td {
            border-bottom: 1px solid $greyLight;
          }
        }
      }
    }

    thead {
      th:first-of-type {
        border-left: 1px solid $greyLight;
      }
    }

    td.ExportData-tableCellAction {
      width: auto;
    }

    td.ExportData-tableCellPreview {
      width: 100%;
      white-space: normal;
    }

    .ExportData-tableCellLabelContent {
      font-weight: bold;
    }

    input[type="checkbox"] {
      margin-bottom: 0;
    }
  }

  &-previewLoading {
    margin-top: 2em;
  }

  &-descr {
    max-width: $screen-md;
  }

  &-pickerContainer {
    width: 100%;
    margin-bottom: .75rem;
    margin-top: .75rem;
  }

  .PreviewTable {
    max-height: 70vh;
  }

  .ExportData-previewSelector {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .select-container {
      display: flex;
      flex: 1;
      flex-direction: column;

      @media (min-width: $screen-md) {
        flex-direction: row;
        align-items: center;
      }

      .vs__selected-options {
        flex-wrap: nowrap;
      }
    }

    .SelectBase {
      flex: 1;
      padding: 0;

      &-label {
        display: none;
      }

      @media (min-width: $screen-md) {
        margin-left: .75rem;
      }
    }

    .next-source-button {
      display: flex;
      align-items: center;
      font-weight: normal;
      cursor: pointer;
      margin-left: 2rem;

      .icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #E1E3E6;
        border-radius: 100%;
        height: 3rem;
        width: 3rem;
        margin-left: 1rem;
      }
    }
  }

  .ExportData-tools {
    display: flex;
    justify-content: space-between;
    flex-direction: column;

    .buttons-wrapper {
      display: flex;
      flex-direction: column;
    }

    @media (min-width: $screen-md) {
      flex-direction: row;

      .buttons-wrapper {
        flex-direction: row;
      }

      .ExportButtons {
        margin-left: 1.25rem;
      }
    }
  }

  .phone {
    display: initial;
  }

  .no-desktop {
    display: inherit;
  }

  .desktop-cell, .tablet-row, .tablet-cell, .tablet, .desktop {
    display: none !important;
  }

  .phone-row, .narrow-row {
    display: table-row !important;
  }

  /* responsive settings for toggle section */
  @media (min-width: $screen-md) {
    .tablet-row {
      display: table-row !important;
    }

    .tablet-cell {
      display: table-cell !important;
    }

    .phone-row, .phone {
      display: none !important;
    }

    .tablet {
      display: inherit !important;
    }
  }

  @media (min-width: $screen-lg) {
    .desktop-cell {
      display: table-cell !important;
    }

    .no-desktop, .narrow-row {
      display: none !important;
    }

    .desktop {
      display: inherit !important;
    }

    .ExportData-tableCellLabelContent {
      font-weight: normal;
    }
  }
}
</style>
