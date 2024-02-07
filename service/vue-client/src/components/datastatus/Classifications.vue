<script>
import FetchMixin from '@/components/mixins/FetchMixin';
import HelpBubble from '@/components/shared/HelpBubble';
import palettes from '@/assets/json/chartPalettes.json';

const DoughnutContainer = () => import('@/components/datastatus/DoughnutContainer');

export default {
  name: 'datastatus-classifications',
  components: {
    HelpBubble,
    DoughnutContainer,
  },
  mixins: [FetchMixin],
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
    chartData() {
      if (this.data && this.data.hasOwnProperty('ssif')) {
        const classifications = this.data.ssif;
        const totalArr = [];
        const labelArr = [];
        const codeArr = [];
        const colorArr = [];
        const percentageArr = [];

        // sort by number of posts desc
        const sorted = Object.keys(classifications)
          .sort((a, b) => {
            const totA = classifications[a].total;
            const totB = classifications[b].total;
            if (totA > totB) {
              return -1;
            } if (totA < totB) {
              return 1;
            } return 0;
          });

        sorted.forEach((el, index) => {
          if (classifications[el].total > 0) {
            // remove 0 cases flags
            totalArr.push(classifications[el].total);
            percentageArr.push(classifications[el].percentage);
            labelArr.push(el);
            codeArr.push(el);
            colorArr.push(palettes.classifications.oneDigit[index]);
          }
        });

        return {
          datasets: [{
            data: totalArr,
            backgroundColor: colorArr,
          }],
          labels: labelArr,
          code: codeArr,
          percentage: percentageArr,
          total: totalArr,
        };
      } return null;
    },
    chartStyles() {
      return {
        width: '75%',
        'max-width': '450px',
        'min-width': '200px',
        height: 'auto',
        position: 'relative',
      };
    },
    yearQuery() {
      if (this.$route.query.from && this.$route.query.to) {
        return `from=${this.$route.query.from}&to=${this.$route.query.to}`;
      } return '';
    },
    processLink() {
      if (this.$route.params.source) {
        return `/process/${this.$route.params.source}/export?${this.yearQuery
          ? `${this.yearQuery}&` : ''}enrichment_flags=auto_classify_enriched`;
      } return null;
    },
  },
  methods: {
    fetchClassifications() {
      if (this.apiQuery) {
        this.fetchData(this.apiQuery);
      }
    },
  },
  mounted() {
    this.fetchClassifications();
  },
  watch: {
    // eslint-disable-next-line func-names
    '$route.fullPath': function () {
      this.fetchClassifications();
    },
  },
};
</script>

<template>
  <div class="TopicChart" v-if="loading || error || (data && data.total > 0)">
    <div class="TopicChart-heading">
      <h2 id="classifications-heading" class="heading heading-md">Forskningsämne (SSIF)</h2>
      <help-bubble bubbleKey="classifications"/>
    </div>
    <vue-simple-spinner class="TopicChart-loading" size="large" v-if="loading"/>
    <p v-if="error" role="alert" aria-atomic="true">
      <span class="error">{{ error }}</span>
    </p>
    <div v-if="!loading && !error && data" class="TopicChart-body">
      <p>Fördelning av forskningsämne på 1-siffernivå</p>
      <router-link v-if="processLink" :to="processLink">
      Visa av Swepub autoklassificerade poster i Databearbetning
      </router-link>
      <div class="TopicChart-chartWrap">
        <doughnut-container :chartData="chartData"
          :chartStyles="chartStyles"
          chartId="classifications-doughnut"
          :linked="false"
          describedbyId="classifications-heading"/>
      </div>
    </div>
  </div>
</template>

<style lang="scss">
/* shares styles with Validations */
</style>
