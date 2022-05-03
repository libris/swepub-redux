<script>
import Helptexts from '@/assets/json/helptexts.json';
import { mapGetters } from 'vuex';
import ExportMixin from '@/components/mixins/ExportMixin';
import * as Network from '@/utils/Network';
import VueSimpleSpinner from 'vue-simple-spinner';

const PreviewTable = () => import('@/components/shared/PreviewTable');
const CheckboxToggle = () => import('@/components/shared/CheckboxToggle');
const ExportButtons = () => import('@/components/shared/ExportButtons');

export default {
  name: 'export-data',
  mixins: [ExportMixin],
  components: {
    PreviewTable,
    VueSimpleSpinner,
    CheckboxToggle,
    ExportButtons,
  },
  props: {
    query: {
      type: Object,
    },
  },
  data() {
    return {
      fields: [
        {
          key: 'recordId',
          component: 'TableDataId', // component to render
          props: { // props to be passed
            deduped(data) {
              return data.publicationCount > 1;
            },
          },
          label: 'Record ID',
          selected: true,
          group: 'post',
        },
        {
          key: 'duplicateIds',
          component: 'TableDataList',
          label: 'Sammanslagna ID',
          selected: false,
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
          selected: false,
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
          selected: false,
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
          selected: false,
          group: 'publication',
        },
        {
          key: 'publicationYear',
          label: 'Utgivningsår',
          selected: false,
          group: 'publication',
        },
        {
          key: 'publicationStatus',
          label: 'Publiceringsstatus',
          component: 'TableDataLink',
          props: {
            unshift: 'https://id.kb.se/term/swepub/',
          },
          selected: false,
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
          key: 'DOI',
          component: 'TableDataList',
          label: 'DOI',
          selected: false,
          group: 'publication',
        },
        {
          key: 'ISBN',
          label: 'ISBN',
          component: 'TableDataList',
          selected: false,
          group: 'publication',
        },
        {
          key: 'ISI',
          label: 'ISI ID',
          selected: false,
          group: 'publication',
        },
        {
          key: 'scopusId',
          label: 'Scopus ID',
          selected: false,
          group: 'publication',
        },
        {
          key: 'PMID',
          label: 'PubMed ID',
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
          key: 'electronicLocator',
          label: 'Fulltextlänk',
          component: 'TableDataLink',
          selected: false,
          group: 'publication',
        },
        {
          key: 'openAccess',
          label: 'Öppen tillgång',
          selected: false,
          component: 'TableDataBoolean',
          group: 'publication',
        },
        /* TODO: add the parameters below when revamping frontend */
        /* {
          key: 'openAccessVersion',
          label: 'Öppet tillgänglig version',
          selected: false,
          component: 'TableDataLink',
          group: 'publication',
        },
        {
          key: 'DOAJ',
          label: 'DOAJ',
          selected: false,
          component: 'TableDataBoolean',
          group: 'publication',
        },
        {
          key: 'autoclassified',
          label: 'Autoklassificerad',
          selected: false,
          component: 'TableDataBoolean',
          group: 'publication',
        },
        {
          key: 'series',
          label: 'Serie',
          selected: false,
          component: 'TableDataList',
          group: 'publication',
        },
        */
        {
          key: 'publicationChannel',
          label: 'Publiceringskanal',
          selected: false,
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
          selected: false,
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
      return `Visar ${this.previewLimit > this.previewData.total ? this.previewData.total : this.previewLimit}
              av ${this.previewData.total} ${this.previewData.total === 1 ? 'post' : 'poster'}`;
    },
    fieldGroups() {
      const groups = [
        {
          id: 'post',
          label: 'Post',
        },
        {
          id: 'org',
          label: 'Organisation/upphov',
        },
        {
          id: 'publication',
          label: 'Publikation',
        },
        {
          id: 'channel',
          label: 'Publiceringskanal',
        },
        {
          id: 'subject',
          label: 'Forskningsämne',
        },
      ];
      return groups.map((group) => ({
        ...group,
        fields: this.fields.filter((field) => {
          if (field.hasOwnProperty('group')) {
            return field.group === group.id;
            // eslint-disable-next-line
          } console.warn(`${field.label} has no group!`);
          return false;
        }),
      }));
    },
  },
  methods: {
    fetchData(type, success, fail, acceptHeader) {
      const queryCopy = { ...this.query };
      if (type === 'preview') {
        queryCopy.limit = this.previewLimit;
      }
      if (type === 'export') {
        // specify fields for export here
        const fields = this.selectKeysForExport();
        queryCopy.fields = fields;
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
  },
  mounted() {
  },
  watch: {
  },
};
</script>

<template>
<section class="ExportData"
  id="preview-section"
  aria-labelledby="preview-heading"
  ref="previewSection"
  :aria-busy="previewLoading"
  aria-live="polite">
  <!-- loading -->
  <vue-simple-spinner v-if="previewLoading" class="ExportData-previewLoading"/>
  <!-- error -->
  <div v-else-if="previewError">
    <p class="error" role="alert" aria-atomic="true">{{previewError}}</p>
  </div>
  <!-- has preview data -->
  <template v-else>
    <hr class="horizontal-wrapper divided-section">
    <h2 id="preview-heading" class="horizontal-wrapper heading heading-md">
      Förhandsgranskning av export
    </h2>
    <!-- no hits -->
    <p v-if="previewData.total === 0" class="horizontal-wrapper">
      Inga träffar</p>
    <!-- export limit exceeded -->
    <div v-else-if="exportLimitExceededWarning" class="horizontal-wrapper">
      <span class="error" role="alert" aria-atomic="true">{{exportLimitExceededWarning}}</span>
    </div>
    <!-- export possible -->
    <div v-else>
      <div class="horizontal-wrapper">
        <p class="ExportData-descr" v-html="exportDescr" id="export-data-descr">
        </p>
      </div>
      <!-- field toggle -->
      <section class="ExportData-pickerContainer horizontal-wrapper"
        aria-labelledby="export-data-descr"
        aria-controls="preview-section">
        <div class="ExportData-checkAll">
          <input type="checkbox"
            id="export_checkAll"
            :checked="allIsChecked"
            @change="toggleAll">
          <label class="is-inline" for="export_checkAll">Välj samtliga</label>
        </div>
        <div class="ExportData-toggleGroups">
          <div class="ExportData-toggleGroup"
            role="group"
            :aria-labelledby="`group-${group.id}`"
            v-for="group in fieldGroups"
            :key="group.id">
            <h3 class="ExportData-toggleGroupLegend heading heading-xs" :id="`group-${group.id}`">
              {{group.label}}</h3>
            <ul class="ExportData-togglesGroupList" :aria-labelledby="`group-${group.id}`">
              <li class="ExportData-togglesGroupListItem"
                v-for="(field, index) in group.fields"
                :key="`${group.id}-${field.key}-${index}`">
                <checkbox-toggle :id="`${group.id}-${field.key}-${index}`"
                  :label="field.label"
                  v-model="field.selected"/>
              </li>
            </ul>
          </div>
        </div>
      </section>
      <!-- export btns -->
      <export-buttons :exportLoading="exportLoading"
        :exportAllowed="exportAllowed"
        :exportError="exportError"
        @export-json="exportJson"
        @export-csv="exportCsv"
        @export-tsv="exportTsv"/>
      <p class="bold" v-if="selectedFields.length === 0" role="status">
        Inga fält valda</p>
      <template v-else>
        <!-- hits info -->
        <p class="bold" role="status">{{previewInfo}}</p>
        <!-- preview table -->
        <preview-table :previewData="previewData"
          :tableCols="selectedFields"
          hitsProp='hits'
          tableLayout='auto'/>
      </template>
    </div>
  </template>
</section>
</template>

<style lang="scss">
.ExportData {
  margin-bottom: 3em;

  &-previewLoading {
    margin-top: 2em;
  }

  &-descr {
    max-width: $screen-md;
  }

  &-pickerContainer {
    width: 100%;
    margin-bottom: 2em;
    margin-top: 2em;
  }

  &-toggleGroups {
    display: flex;
    width: 100%;
  }

  &-toggleGroup {
    &:first-of-type {
      & .ExportData-togglesGroupList,
      .ExportData-toggleGroupLegend {
        padding-left: 0;
      }
    }

    &:last-of-type {
      & .ExportData-togglesGroupList {
        border-right: none;
      }
    }
  }

  &-toggleGroupLegend {
    margin: 0;
    padding: 0 2rem;
  }

  &-togglesGroupList {
    list-style-type: none;
    padding: 0 2rem;
    border-right: 1px solid $greyLight;
    display: flex;
    flex-wrap: wrap;
    max-width: 250px;
  }

  &-togglesGroupListItem {
    display: flex;
    margin: 5px;
  }

  /* column wrap for grid supported browsers */
  @supports (display: grid) {
    &-togglesGroupList {
      display: grid;
      grid-auto-flow: column;
      grid-template-rows: repeat(7, auto);
      grid-gap: 10px 15px;
      max-width: unset;
    }

    &-togglesGroupListItem {
      margin: 0;
    }
  }

  /* responsive settings for toggle section */
  @media (max-width: $screen-lg) {
    &-toggleGroups {
      flex-direction: column;
    }

    &-toggleGroup {
      flex: auto;
    }

    &-toggleGroupLegend {
      padding: 0;
    }

    &-togglesGroupList {
      padding: 0;
      display: flex;
      max-width: none;
      border: none;
      grid-gap: 0;
    }

    &-togglesGroupListItem {
      margin: 5px 5px 5px 0;
    }
  }

  &-checkAll {
    display: inline-block;
    padding: 10px;
    border: 1px solid #d0d0d0;
    border: 1px solid $greyLight;
    border-radius: 4px;
    cursor: pointer;
    margin-bottom: 10px;

    & * {
      margin-bottom: 0;
    }
  }

  .PreviewTable {
    max-height: 70vh;
  }
}
</style>
