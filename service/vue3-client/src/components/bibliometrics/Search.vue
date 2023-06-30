<script>
import * as StringUtil from '@/utils/String';
import Helptexts from '@/assets/json/helptexts.json';
import YearPicker from '@/components/shared/YearPicker.vue';
import SelectSource from '@/components/shared/SelectSource.vue';
import SelectSubject from '@/components/shared/SelectSubject.vue';
import SelectOutput from '@/components/shared/SelectOutput.vue';
import ValidationMixin from '@/components/mixins/ValidationMixin.vue';

const HelpBubble = () => import('@/components/shared/HelpBubble.vue');
const ExportData = () => import('@/components/bibliometrics/ExportData.vue');

export default {
  name: 'bibliometrics-search',
  mixins: [ValidationMixin],
  components: {
    SelectSource,
    SelectSubject,
    SelectOutput,
    YearPicker,
    HelpBubble,
    ExportData,
  },
  props: {
    query: { // passed from vue router
      type: Object,
      default: null,
    },
  },
  data() {
    return {
      selected: {},
      publicationStatuses: [
        { value: 'published', label: 'Publicerat' },
        { value: 'epub', label: 'Epub ahead of print/Online first' },
        { value: 'submitted', label: 'Submitted, Accepted, In print' },
      ],
      contentMarkings: [
        { value: 'ref', label: 'Sakkunniggranskat (ref)' },
        { value: 'vet', label: 'Övrigt vetenskapligt (vet)' },
        { value: 'pop', label: 'Övrigt (populärvetenskap, debatt) (pop)' },
      ],
      search: null,
    };
  },
  computed: {
    serviceDescr() {
      return Helptexts.bibliometrics.service_descr;
    },
    canGoToExport() {
      return !this.yearInputError;
    },
    hasQueryInUrl() {
      return Object.keys(this.query).length > 0
      && this.query.constructor === Object;
    },
    syncedForm() {
      // syncs form state with this.query, falls back to default values
      // (initial state for clean page load & clear)
      return {
        org: this.asArr(this.query.org) || [],
        years: {
          from: this.getYearValue('from'),
          to: this.getYearValue('to'),
        },
        subject: this.asArr(this.query.subject) || [],
        genreForm: this.joinGenreForm(),
        keywords: this.query.keywords || '',
        publicationStatus: this.asArr(this.query.publicationStatus) || [],
        contentMarking: this.asArr(this.query.contentMarking) || [],
        swedishList: this.query.swedishList === 'true' || null,
        openAccess: this.query.openAccess === 'true' || null,
      };
    },
    selectedAsFullPath() {
      // maps current state of form as url params
      const selectedObj = this.splitGenreForm({ ...this.selected });
      selectedObj.from = selectedObj.years.from;
      selectedObj.to = selectedObj.years.to;
      delete selectedObj.years;
      // remove unused params
      Object.keys(selectedObj).forEach((el) => {
        if (Array.isArray(selectedObj[el]) && selectedObj[el].length === 0) {
          delete selectedObj[el];
        } else if (!selectedObj[el] || selectedObj[el] === 'false') {
          delete selectedObj[el];
        }
      });
      // resolve into a querystring to avoid handling types, i.e true vs "true"
      return this.$router.resolve({ query: selectedObj }).href;
    },
    selectedAsReqObj() {
      // maps current state of form as request body for api
      return this.splitGenreForm({ ...this.selected });
    },
  },
  methods: {
    pushQuery() {
      let pathToPush = '';
      if (this.selectedAsFullPath === '/bibliometrics') {
        pathToPush = '/bibliometrics?from=&to=';
      } else {
        pathToPush = this.selectedAsFullPath;
      }
      this.$router.push(pathToPush)
      // eslint-disable-next-line
        .catch(err => console.warn(err.message));
    },
    doSearch() {
      this.search = this.selectedAsReqObj;
    },
    splitGenreForm(obj) {
      // splits shared genreForm into 'genreForm' and 'match-genreForm' params
      const broad = [];
      const narrow = [];
      if (obj.genreForm) {
        obj.genreForm.forEach((el) => {
          if (el.startsWith('*')) {
            broad.push(el.substr(1));
          } else narrow.push(el);
        });
        obj.genreForm = narrow;
        obj['match-genreForm'] = broad;
      }
      return obj;
    },
    joinGenreForm() {
      // joins 'genreForm' and 'match-genreForm' params into shared genreForm obj
      let broad = this.asArr(this.query['match-genreForm']) || [];
      const narrow = this.asArr(this.query.genreForm) || [];
      broad = broad.map((genre) => `*${genre}`);
      return [...broad, ...narrow];
    },
    clearSelected() {
      this.search = null;
      this.$router.push({ query: {} })
      // eslint-disable-next-line
        .catch(err => console.warn(err.message));
    },
    asArr(query) {
      // single values are stored as strings in $route.query
      // need them as arrs to make v-model with multiple checkboxes work
      if (typeof query === 'string') {
        return [query];
      } return query;
    },
    getYearValue(param) {
      if (this.hasQueryInUrl) {
        // if years are explicitly left out, we don't want to overwrite with current year
        return this.query[param] ? this.query[param] : '';
      }
      // ...only when view is loaded in a 'clean' state
      return StringUtil.getYear();
    },
  },
  created() {
    this.selected = { ...this.syncedForm }; // apply form values before mount
  },
  mounted() {
    this.$nextTick(() => {
      if (this.hasQueryInUrl) {
        this.doSearch();
      }
    });
  },
  watch: {
    query() {
      this.selected = { ...this.syncedForm }; // sync form state with query
      if (this.hasQueryInUrl) {
        this.doSearch();
      } else this.clearSelected();
    },
  },
};
</script>

<template>
  <section class="Search" id="search-section" role="tabpanel" aria-labelledby="search-tab">
    <div class="Search-wrapper horizontal-wrapper">
      <p id="service-descr" class="Search-descr" v-html="serviceDescr"></p>

      <div aria-describedby="service-descr" role="form">
        <div class="Search-SelectContainer">
          <select-source v-model="selected.org" multiple>
            <template v-slot:helpbubble>
              <help-bubble bubbleKey="organization"/>
            </template>
          </select-source>

          <select-subject v-model="selected.subject" multiple>
            <template v-slot:helpbubble>
              <help-bubble bubbleKey="subject"/>
            </template>
          </select-subject>
        </div>

        <div class="Search-SelectContainer">
          <select-output v-model="selected.genreForm" multiple>
            <template v-slot:helpbubble>
              <help-bubble bubbleKey="output"/>
            </template>
          </select-output>

          <div class="Search-fieldset">
            <label for="keywords_input">Nyckelord</label>
            <help-bubble bubbleKey="keywords"/>

            <input class="Search-input"
              type="text"
              id="keywords_input"
              v-model="selected.keywords"
            />
          </div>
        </div>

        <year-picker v-model="selected.years" legend="Utgivningsår" :error="yearInputError">
          <template v-slot:helpbubble>
            <help-bubble bubbleKey="publication_year"/>
          </template>
        </year-picker>

        <div class="Search-toggleGroups">
          <fieldset class="Search-checkboxGroup Search-fieldset">
            <legend id="publication-status">
              Publiceringsstatus
            </legend>

            <help-bubble bubbleKey="publication_status"/>

            <div class="Search-checkboxGroupItems" id="publication-statuses">
              <div
                v-for="status in publicationStatuses"
                :key="status.value"
                class="Search-inputContainer"
              >
                <input
                  :id="status.value"
                  type="checkbox"
                  :value="status.value"
                  v-model="selected.publicationStatus"
                />

                <label :for="status.value" class="Search-sublabel is-inline">
                  {{status.label}}
                </label>
              </div>
            </div>
          </fieldset>

          <fieldset class="Search-checkboxGroup Search-fieldset">
            <legend id="content-marking">
              Innehållsmärkning
            </legend>

            <help-bubble bubbleKey="content_marking"/>

            <div class="Search-checkboxGroupItems" id="content-markings">
              <div v-for="mark in contentMarkings" :key="mark.value" class="Search-inputContainer">
                <input
                  :id="mark.value"
                  type="checkbox"
                  :value="mark.value"
                  v-model="selected.contentMarking"
                />
                <label :for="mark.value" class="Search-sublabel is-inline">{{mark.label}}</label>
              </div>
            </div>
          </fieldset>

          <fieldset class="Search-fieldset">
            <legend>Svenska listan</legend>
            <help-bubble bubbleKey="swedish_list"/>

            <div class="Search-inputContainer">
              <input id="swedish-list" type="checkbox" v-model="selected.swedishList" />
              <label for="swedish-list" class="Search-sublabel is-inline">
                Endast output ingående i sakkunniggranskade publiceringskanaler enligt Svenska
                listan
              </label>
            </div>
          </fieldset>

          <fieldset class="Search-fieldset">
            <legend>Öppen tillgång</legend>
            <help-bubble bubbleKey="open_access"/>

            <div class="Search-inputContainer">
              <input id="open-access" type="checkbox" v-model="selected.openAccess" />
              <label for="open-access" class="Search-sublabel is-inline">
                Endast öppet tillgänglig output
              </label>
            </div>
          </fieldset>
        </div>

        <button
          id="submit-btn"
          class="btn"
          @click.prevent="pushQuery"
          :class="{'disabled' : !canGoToExport}"
          :disabled="!canGoToExport"
        >
          Visa
        </button>

        <button id="clear-btn" class="btn btn--warning" @click.prevent="clearSelected">
          Rensa
        </button>
      </div>
    </div>

    <transition name="fade">
      <export-data v-if="search" :query="search"/>
    </transition>
  </section>
</template>

<style lang="scss">
.Search {
  &-wrapper {
    margin-bottom: 1em;
  }

  &-descr {
    max-width: $screen-md;
  }

  &-sublabel {
    flex: 1;
    font-weight: inherit;
  }

  &-inputContainer {
    display: flex;
    align-items: flex-start;
    border-bottom: 1px solid transparent;
    margin-bottom: .5rem;
    padding-bottom: .5rem;

    input {
      margin-bottom: 0;
      position: relative;
      top: 3px;
    }

    label {
      margin-bottom: 0;
    }

    &:last-of-type {
      border-bottom: 0;
      margin-bottom: 0;
      padding-bottom: 0;
    }
  }

  &-fieldset {
    padding: 1rem 0;
  }

  &-checkboxGroup {
    & legend {
      cursor: pointer;
      & span {
        margin-right: 10px;
      }
    }

    &.is-hidden {
      padding-bottom: 0;

      & > .Search-checkboxGroupItems {
        display: none;
      }
    }
  }

  &-input {
    width: 100%;
    margin-bottom: 0;
  }

  &-toggleGroups {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
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

  &-SelectContainer {
    display: flex;

    > div {
      flex: 1;
      flex-direction: row;

      &:first-of-type {
        margin-right: 1.5rem;
      }

      &:last-of-type {
        margin-left: 1.5rem;
      }

      .vs__dropdown-toggle {
        min-height: 36px;
      }
    }
  }

  /* responsive settings for toggle section */
  @media (max-width: $screen-md) {
    &-SelectContainer {
      flex-direction: column;

      > div {
        margin: 0 !important;
      }
    }
  }

  @media (max-width: $screen-lg) {
    &-toggleGroups {
      grid-template-columns: repeat(1, 1fr);
    }

    &-inputContainer {
      margin-bottom: 1rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid $greyLight;
    }
  }

}
</style>
