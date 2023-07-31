<script>
import { Transition, defineAsyncComponent } from 'vue';
import FetchMixin from '@/components/mixins/FetchMixin.vue';
import YearPicker from '@/components/shared/YearPicker.vue';
import Helptexts from '@/assets/json/helptexts.json';
import * as StringUtil from '@/utils/String';
import SelectSource from '@/components/shared/SelectSource.vue';
import ValidationMixin from '@/components/mixins/ValidationMixin.vue';
import Spinner from '../shared/Spinner.vue';

const HelpBubble = defineAsyncComponent(() => import('@/components/shared/HelpBubble.vue'));
const FlagPicker = defineAsyncComponent(() => import('@/components/process/FlagPicker.vue'));
const ExportFlags = defineAsyncComponent(() => import('@/components/process/ExportFlags.vue'));

export default {
  name: 'data-quality',
  mixins: [ValidationMixin, FetchMixin],
  components: {
    SelectSource,
    YearPicker,
    FlagPicker,
    ExportFlags,
    HelpBubble,
    Transition,
    Spinner,
  },
  props: {
    query: { // passed from vue router
      type: Object,
      default: null,
    },
    params: { // passed from vue router
      type: Object,
      default: null,
    },
  },
  data() {
    return {
      flagSpec: {
        validations: {
          type: 'validation_flags',
          target: 'invalid',
          title: 'Ofullständiga data',
        },
        audits: {
          type: 'audit_flags',
          target: 'invalid',
          title: 'Motstridiga data',
        },
        enrichments: {
          type: 'enrichment_flags',
          target: 'enriched',
          title: 'Berikade data',
        },
      },
      selected: {},
      loading: false,
      data: null,
      error: '',
    };
  },
  computed: {
    syncedQuery() {
      // Syncs ui state with url query/params or default values.
      return {
        source: this.params.source,
        service: this.params.service,
        years: {
          // empty value ok only if there is a source
          from: this.query.from || (this.params.source ? '' : StringUtil.getYear()),
          to: this.query.to || (this.params.source ? '' : StringUtil.getYear()),
        },
        flags: {
          enrichment_flags: this.query.enrichment_flags || null,
          validation_flags: this.query.validation_flags || null,
          audit_flags: this.query.audit_flags || null,
        },
      };
    },
    serviceDescr() {
      return Helptexts.dataQuality.service_descr;
    },
    flagDescr() {
      return Helptexts.dataQuality.flag_descr;
    },
    selectedAsRouteObj() {
      // resolves current selection into a routable object if required selections have been made
      if (!this.selected.source || this.yearInputError) {
        return null;
      }
      const selectedCopy = { ...this.selected };
      // remove 'empty' flag keys
      Object.keys(
        selectedCopy.flags,
      ).forEach((key) => !selectedCopy.flags[key] && delete selectedCopy.flags[key]);

      return {
        params: { source: selectedCopy.source, service: selectedCopy.service },
        query: { ...selectedCopy.years, ...selectedCopy.flags },
      };
    },
    selectedSourceUrl() {
      // resolves selected source & years as url
      if (this.selectedAsRouteObj) {
        const routeCopy = { ...this.selectedAsRouteObj };
        return this.$router.resolve({
          params: { service: null, source: routeCopy.params.source },
          query: { from: routeCopy.query.from, to: routeCopy.query.to },
        }).href;
      } return null;
    },
    selectedExportUrl() {
      // resolves selected as export url
      if (this.selectedAsRouteObj) {
        const flagList = Object.keys(this.flagSpec).map((flag) => this.flagSpec[flag].type);
        // ...if any flag is selected
        if (flagList.some((flag) => this.selectedAsRouteObj.query.hasOwnProperty(flag))) {
          const routeCopy = { ...this.selectedAsRouteObj };
          routeCopy.params.service = 'export';
          return this.$router.resolve(routeCopy).href;
        } return null;
      } return null;
    },
    hasExportInUrl() {
      return !!this.params.source && this.params.service === 'export';
    },
    selectionUnchanged() {
      // current selection != loaded selection
      const selectedQueryKeys = Object.keys(this.selectedAsRouteObj.query);
      const queryKeys = Object.keys(this.query);
      const selectedParamKeys = Object.keys(this.selectedAsRouteObj.params);

      if (selectedQueryKeys.length !== queryKeys.length) {
        return false;
      }
      const queryUnchanged = selectedQueryKeys
        .every((key) => this.selectedAsRouteObj.query[key] === this.query[key]);
      const paramUnchanged = selectedParamKeys
        .every((key) => this.selectedAsRouteObj.params[key] === this.params[key]);

      if (queryUnchanged && paramUnchanged) {
        return true;
      } return false;
    },
  },
  methods: {
    push(url) {
      this.$router.push(url)
        .catch((err) => {
          // identical route, fetch data again anyway
          this.fetchFlagSummary();
          // eslint-disable-next-line no-console
          console.warn(err.message);
        });
    },
    handleFlagPickerChange(type, value) {
      this.selected.flags = { ...this.selected.flags, [type]: value };
    },
    fetchFlagSummary() {
      if (this.selectedSourceUrl) {
        this.fetchData(this.selectedSourceUrl)
          .then((res) => {
            if (!res.hasOwnProperty('hits') && !res.hasOwnProperty('total')) {
              // remove when api delivers proper no hits reply
              this.data.total = 0;
            }
            this.$nextTick(() => {
              // don't scroll to flag section if export section is present
              if (!this.hasExportInUrl) {
                this.$refs.flagSection.scrollIntoView({ behavior: 'smooth' });
              }
            });
          })
          // eslint-disable-next-line no-console
          .catch((err) => console.warn(err));
      } else this.clearResults();
    },
    clearSearch() {
      this.selected = {
        source: null,
        years: { from: StringUtil.getYear(), to: StringUtil.getYear() },
      };
      this.$router.push('/process')
      // eslint-disable-next-line no-console
        .catch((err) => console.warn(err.message));
    },
    clearResults() {
      this.error = '';
      this.data = null;
    },
  },
  created() {
    this.selected = { ...this.syncedQuery }; // apply default values before mount
  },
  mounted() {
    this.fetchFlagSummary();
  },
  watch: {
    query() {
      this.selected = { ...this.syncedQuery };
      // dont't fetch summary if export
      if (!this.hasExportInUrl) {
        this.fetchFlagSummary();
      }
    },
  },
  filters: {
    toLowerCase(val) {
      if (val) {
        return val.toLowerCase();
      } return val;
    },
  },
};
</script>

<template>
  <section class="DataQuality"
    id="dataQuality-section"
    role="tabpanel"
    aria-labelledby="quality-tab">
    <section class="Process-search horizontal-wrapper"
      :aria-busy="loading"
      aria-labelledby="dataQuality-service-descr">
      <p id="dataQuality-service-descr" class="Process-descr" v-html="serviceDescr"></p>
      <div aria-describedby="dataQuality-service-descr" role="form">
        <select-source v-model="selected.source" @clear="clearResults">
          <template v-slot:helpbubble>
            <help-bubble bubbleKey="organization"/>
          </template>
        </select-source>
        <year-picker v-model="selected.years"
          legend="Utgivningsår"
          :error="yearInputError">
          <template v-slot:helpbubble>
            <help-bubble bubbleKey="publication_year"/>
          </template>
        </year-picker>
        <div class="Process-submit">
          <button id="submit-btn"
            class="btn"
            :class="{'disabled' : (!selectedSourceUrl || selectionUnchanged) && !error}"
            @click.prevent="push(selectedSourceUrl)"
            :disabled="(!selectedSourceUrl || selectionUnchanged) && !error">Visa</button>
          <button id="clear-btn"
            class="btn btn--warning"
            :class="{'disabled' : !selected.source}"
            @click.prevent="clearSearch"
            :disabled="!selected.source">Rensa</button>
          <Spinner v-if="loading"/>
          <div v-if="error">
            <span class="error" role="alert" aria-atomic="true">{{ error }}</span>
          </div>
        </div>
      </div>
    </section>
    <Transition name="fade">
      <section class="horizontal-wrapper"
        v-if="data"
        ref="flagSection"
        aria-labelledby="flagdata-heading">
        <hr class="divided-section">
        <h2 id="flagdata-heading" class="heading heading-lg">{{data.source}}
          <span v-if="data.from">{{data.from}}</span>
          <span v-if="data.to">-{{data.to}}</span>
        </h2>
        <p v-if="!this.data.total || this.data.total < 1">Inga träffar</p>
        <div v-else>
          <p class="Process-descr" v-html="flagDescr"></p>
          <flag-picker v-for="(flag, key) in flagSpec"
            v-show="data && data[key]"
            :key="key"
            :class="key"
            @change="handleFlagPickerChange"
            :result-data="data[key]"
            :flagType="flag.type"
            :target="flag.target"
            :expandable="flag.expandable"
            :selectable="flag.selectable"
            :query="query">
            <template v-slot:title>
              {{flag.title}}
            </template>
            <template v-slot:noflags>
              Det finns inga poster med {{ flag.title | toLowerCase }}
            </template>
          </flag-picker>
          <button class="btn DataQuality-proceed"
            :class="{'disabled' : !selectedExportUrl || selectionUnchanged}"
            :disabled="!selectedExportUrl || selectionUnchanged"
            @click="push(selectedExportUrl)">Förhandsgranska export</button>
        </div>
      </section>
    </Transition>

    <Transition name="fade">
      <!-- selectionUnchanged check match url query with valid select state,
      prevents showing weird results if user tampers with params -->
      <export-flags v-if="hasExportInUrl &&
        selectedExportUrl &&
        selectionUnchanged &&
        data &&
        data.total > 0"
        :query="query"/>
    </Transition>
  </section>
</template>

<style scoped lang="scss">
.DataQuality {

  &-proceed {
    margin-top: 2em;
  }
}
</style>
