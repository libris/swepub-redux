<script>
import { defineAsyncComponent } from 'vue';
import { mapState } from 'pinia';
import { useSettingsStore } from '@/stores/settings';
import FlagLabels from '@/assets/json/FlagLabels.json';
import FetchMixin from '@/components/mixins/FetchMixin.vue';
import HelpBubble from '@/components/shared/HelpBubble.vue';
import Spinner from '../shared/Spinner.vue';

const BarChart = defineAsyncComponent(() => import('@/components/datastatus/BarChart.vue'));
const SrChartTable = defineAsyncComponent(() => import('@/components/datastatus/SrChartTable.vue'));

export default {
  name: 'datastatus-validations',
  mixins: [FetchMixin],
  components: {
    HelpBubble,
    BarChart,
    SrChartTable,
    Spinner,
  },
  props: {
    apiQuery: {
      default: null,
    },
  },
  data() {
    return {
      data: null,
      loading: false,
      error: '',
    };
  },
  computed: {
    ...mapState(useSettingsStore, ['apiPath', 'language']),
    chartData() {
      if (this.data.validationFlags) {
        const dataArr = [];
        const labelArr = [];
        const percentageArr = [];
        const codeArr = [];

        // sort by number of posts desc
        const sorted = Object.keys(this.data.validationFlags).sort((a, b) => {
          const totA = this.data.validationFlags[a].total;
          const totB = this.data.validationFlags[b].total;
          if (totA > totB) {
            return -1;
          } if (totA < totB) {
            return 1;
          } return 0;
        });

        sorted.forEach((el) => {
          // remove 0 cases flags
          if (this.data.validationFlags[el].total > 0) {
            dataArr.push(this.data.validationFlags[el].total);
            percentageArr.push(this.data.validationFlags[el].percentage);
            const label = FlagLabels[el] && FlagLabels[el][this.language]
              ? FlagLabels[el][this.language] : el;
            labelArr.push(label);
            codeArr.push(el);
          }
        });

        return {
          datasets: [{
            barPercentage: 0.75,
            data: dataArr,
            backgroundColor: '#dd7a41',
          }],
          labels: labelArr,
          percentage: percentageArr,
          codes: codeArr,
        };
      } return null;
    },
    chartStyles() {
      return {
        width: '100%',
        'max-width': '700px',
        'min-width': '300px',
        height: 'auto',
        position: 'relative',
      };
    },
    yearQuery() {
      if (this.$route.query.from && this.$route.query.to) {
        return `from=${this.$route.query.from}&to=${this.$route.query.to}`;
      } return '';
    },
    total() {
      return this.data.total.toLocaleString() || null;
    },
    processLink() {
      if (this.$route.params.source) {
        // need to keep api:s flag order to match /process params
        const flags = Object.keys(this.data.validationFlags)
          .filter((flag) => this.chartData.codes.indexOf(flag) > -1)
          .map((fl) => `${fl}_invalid`)
          .join(',');

        return `/process/${this.$route.params.source}/export?${this.yearQuery ? `${this.yearQuery}&` : ''}validation_flags=${flags}`;
      } return null;
    },
  },
  methods: {
    fetchValidations() {
      if (this.apiQuery) {
        this.fetchData(this.apiQuery);
      }
    },
  },
  mounted() {
    this.fetchValidations();
  },
  watch: {
    // eslint-disable-next-line func-names
    '$route.fullPath': function () {
      this.fetchValidations();
    },
  },
};
</script>

<template>
  <div class="TopicChart" v-if="loading || error || (data && data.total > 0)">
    <div class="TopicChart-heading">
      <h2 id="validations-heading" class="heading heading-md">Ofullständiga data</h2>
      <help-bubble bubbleKey="validations"/>
    </div>
    <Spinner class="TopicChart-loading" size="large" v-if="loading"/>
    <p v-if="error" role="alert" aria-atomic="true">
      <span class="error">{{ error }}</span>
    </p>
    <div v-if="!loading && !error && data" class="TopicChart-body">
      <p>Totalt antal identifierade valideringsflaggor:
        <span class="TopicChart-total">{{total}}</span></p>
      <router-link v-if="processLink" :to="processLink">
      Visa poster med valideringsflaggor i Databearbetning
      </router-link>
      <div class="TopicChart-chartWrap" v-if="data.total > 0">
        <bar-chart :chartData="chartData" :styles="chartStyles" aria-hidden="true"/>
        <sr-chart-table :chartData="chartData" describedbyId="validations-heading"/>
      </div>
    </div>
  </div>
</template>

<style lang="scss">
.TopicChart {
  width: 50%;
  display: flex;
  flex-direction: column;
  margin: 1em 0;
  padding-right: 3em;
  box-sizing: border-box;

  &-heading {
    display: flex;
    align-items: center;
    white-space: nowrap;

    & .heading {
      margin: 0;
    }
    & .HelpBubble {
      margin-left: 5px;
    }
  }

  &-body {
    & p {
      margin-top: 5px;
    }
  }

  &-loading {
    margin-top: 2em;
    width: 60px;
  }

  &-total {
    font-weight: 600;
  }

  &-chartWrap {
    margin-top: 3rem;
  }

  @media (max-width: 1000px) {
    width: 100%;
    padding: 0;
  }
}

</style>
