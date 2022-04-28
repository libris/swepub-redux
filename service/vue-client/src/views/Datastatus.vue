<script>
import * as Network from '@/utils/Network';
import SelectSource from '@/components/shared/SelectSource';
import YearPicker from '@/components/shared/YearPicker';
import ValidationMixin from '@/components/mixins/ValidationMixin';
import FetchMixin from '@/components/mixins/FetchMixin';
import ShortStats from '@/components/datastatus/ShortStats';

const HelpBubble = () => import('@/components/shared/HelpBubble');
const DatastatusSummary = () => import('@/components/datastatus/Summary');
const DatastatusValidations = () => import('@/components/datastatus/Validations');
const DatastatusSubjects = () => import('@/components/datastatus/Subjects');

export default {
  // eslint-disable-next-line
  name: 'datastatus',
  mixins: [ValidationMixin, FetchMixin],
  components: {
    SelectSource,
    YearPicker,
    HelpBubble,
    DatastatusSummary,
    ShortStats,
    DatastatusValidations,
    DatastatusSubjects,
  },
  props: {
    params: {
      type: Object, // passed from vue-router
    },
    query: {
      type: Object, // passed from vue-router
    },
  },
  data() {
    return {
      data: null,
      sources: null,
      selected: {},
      loading: false,
      error: '',
      sourceError: '',
    };
  },
  computed: {
    syncedSelection() {
      return {
        source: this.params.source ? this.params.source : '',
        years: {
          from: this.query.from ? this.query.from : '',
          to: this.query.to ? this.query.to : '',
        },
      };
    },
    apiQuery() {
      // resolves into a api url/query if form filled out correctly
      if (this.yearInputError) {
        return false;
      }
      const selectedSource = this.selected.source ? this.selected.source : '';
      const paramSource = this.params.source ? this.params.source : '';

      let selectedYears = '';
      if (this.selected.years.from) {
        selectedYears = `?from=${this.selected.years.from}&to=${this.selected.years.to}`;
      }

      let queryYears = '';
      if (this.query.from) {
        queryYears = `?from=${this.query.from}&to=${this.query.to}`;
      }
      // summary query needs to be based on current selection (is pushed),
      // validation & subject on present url params/query
      return {
        summary: `/datastatus${selectedSource || selectedYears ? '/' : ''}${selectedSource}${selectedYears}`,
        validations: `/datastatus/validations${paramSource ? '/' : ''}${paramSource}${queryYears}`,
        subjects: `/datastatus/ssif${paramSource ? '/' : ''}${paramSource}${queryYears}`,
      };
    },
    selectedChanged() {
      if (this.apiQuery && this.apiQuery.summary === this.$route.fullPath) {
        if (!this.data) {
          return true;
        }
        return false;
      } return true;
    },
  },
  methods: {
    sync() {
      this.selected = { ...this.syncedSelection };
    },
    fetchSummary() {
      if (this.apiQuery.summary) {
        this.fetchData(this.apiQuery.summary);
      }
    },
    fetchSources() {
      // source names needed by multiple components
      // fetched here & passed to select-source
      Network.get(`${this.settings.apiPath}/info/sources`)
        .then((response) => {
          if (response.statusCode === 200) {
            this.sources = response;
          } else {
            this.sourceError = `Ett fel har inträffat: ${response.statusText}`;
          }
        }, ((err) => {
          this.sourceError = `Ett fel har inträffat: ${err}`;
        }));
    },
    pushQuery() {
      this.$router.push(this.apiQuery.summary)
        .catch((err) => {
          // fetch anyway on duplicate route error
          this.fetchSummary();
          // eslint-disable-next-line no-console
          console.warn(err.message);
        });
    },
    clearSearch() {
      this.selected = { source: '', years: { from: '', to: '' } };
      this.$router.push('/datastatus')
      // eslint-disable-next-line no-console
        .catch((err) => console.warn(err.message));
    },
  },
  created() {
    this.sync();
  },
  mounted() {
    this.fetchSummary();
    this.fetchSources();
  },
  watch: {
    // eslint-disable-next-line func-names
    '$route.fullPath': function () {
      this.sync();
      this.fetchSummary();
    },
  },
};
</script>

<template>
  <div class="Datastatus vertical-wrapper">
    <section class="Datastatus-search horizontal-wrapper"
      :aria-busy="loading"
      role="form">
      <select-source
        v-model="selected.source"
        @clear="selected.source = ''"
        :incomingError="sourceError"
        :providedOptions="sources">
        <template v-slot:helpbubble>
          <help-bubble bubbleKey="organization"/>
        </template>
      </select-source>
      <div class="Datastatus-formGroup">
        <year-picker v-model="selected.years"
          legend="Utgivningsår"
          :error="yearInputError">
          <template v-slot:helpbubble>
            <help-bubble bubbleKey="publication_year"/>
          </template>
        </year-picker>
        <div class="Datastatus-submit">
          <button id="submit-btn"
            class="btn"
            :class="{'disabled' : !apiQuery || !selectedChanged}"
            @click.prevent="pushQuery"
            :disabled="!apiQuery || !selectedChanged">Visa</button>
          <button id="clear-btn"
            class="btn btn--warning"
            :class="{'disabled' : !selected}"
            @click.prevent="clearSearch"
            :disabled="!selected">Rensa</button>
        </div>
      </div>
    </section>
    <div class="Datastatus-chartContainer horizontal-wrapper" v-if="loading || error || data">
      <hr class="divided-section">
      <vue-simple-spinner v-if="loading" size="large"/>
      <p v-if="error" role="alert" aria-atomic="true">
        <span class="error">{{ error }}</span>
      </p>
      <transition name="fade">
      <datastatus-summary v-if="!loading && data"
        :data="data"
        :sources="sources" />
      </transition>
    </div>
    <transition name="fade">
      <short-stats v-if="data && data.total > 0" :data="{
        openAccess: data.openAccess,
        swedishList: data.swedishList,
        ssif: data.ssif }"/>
    </transition>
    <transition name="fade">
      <section class="Datastatus-chartContainer horizontal-wrapper flex">
        <datastatus-subjects :apiQuery="apiQuery.subjects"/>
        <datastatus-validations :apiQuery="apiQuery.validations"/>
      </section>
    </transition>
    <p v-if="data" class="Datastatus-note">Underliggande data kan hämtas i
      <router-link to="/bibliometrics">Bibliometri</router-link>,
      <router-link to="/bibliometrics/datadump">Datadump</router-link> eller
      <router-link to="/process">Databearbetning</router-link></p>
  </div>
</template>

<style lang="scss">
.Datastatus {
  &-formGroup {
    display: flex;
    flex-direction: column;
  }

  &-submit {
    display: flex;
    align-items: center;
  }

  &-chartContainer {
    margin-top: 2em;
    margin-bottom: 3em;
    &.flex {
      display: flex;
      flex-wrap: wrap;
    }
  }
}
</style>
