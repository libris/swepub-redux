<script>
import palettes from '@/assets/json/chartPalettes.json';

const DoughnutContainer = () => import('@/components/datastatus/DoughnutContainer');

export default {
  name: 'datastatus-summary',
  components: {
    DoughnutContainer,
  },
  props: {
    data: {
      type: Object,
      default: null,
    },
    sources: {
      type: Object,
      default: null,
    },
  },
  data() {
    return {
    };
  },
  computed: {
    source() {
      return this.data.source || false;
    },
    // maps the sources array into key/value pairs for easy lookup
    sourcesAsObj() {
      if (this.sources && this.sources.hasOwnProperty('sources')) {
        return this.sources.sources.reduce((obj, item) => {
          obj[item.code] = item;
          return obj;
        }, {});
      } return null;
    },
    chartData() {
      if (this.data.sources) {
        const labelArr = [];
        const codeArr = [];
        const colorArr = [];
        const totalArr = [];
        const percentageArr = [];
        const threshPercentageArr = [];

        // sort by number of posts desc
        const sorted = Object.keys(this.data.sources).sort((a, b) => {
          const totA = this.data.sources[a].total;
          const totB = this.data.sources[b].total;
          if (totA > totB) {
            return -1;
          } if (totA < totB) {
            return 1;
          } return 0;
        });

        sorted.forEach((el, index) => {
          totalArr.push(this.data.sources[el].total);
          percentageArr.push(this.data.sources[el].percentage);
          // To make sure every slice is visible on-screen (required to trigger tooltip)
          // we must skew proportions a bit (create a min threshold value).
          // Only for visualization, never display these tampered numbers to users!
          // Also, look for 'min-with' option for arcs in future chart.js releases
          threshPercentageArr.push(
            this.data.sources[el].percentage < 0.5 ? 0.5
              : this.data.sources[el].percentage,
          );
          labelArr.push(this.codeAsName(el));
          codeArr.push(el);
          colorArr.push(palettes.sources[index]);
        });

        return {
          datasets: [{
            data: threshPercentageArr,
            backgroundColor: colorArr,
          }],
          labels: labelArr,
          percentage: percentageArr,
          code: codeArr,
          total: totalArr,
        };
      } return null;
    },
    chartStyles() {
      return {
        width: '100%',
        'max-width': '400px',
        'min-width': '300px',
        height: 'auto',
        position: 'relative',
      };
    },
    total() {
      return this.data.total.toLocaleString();
    },
    title() {
      const interval = this.data.from && this.data.to ? `${this.data.from} - ${this.data.to}` : '';
      const name = this.source ? this.codeAsName(this.source) : 'Samtliga poster';
      return `${name} ${interval}`;
    },
  },
  methods: {
    codeAsName(code) {
      if (code && this.sourcesAsObj
      && this.sourcesAsObj.hasOwnProperty(code)
      && this.sourcesAsObj[code].hasOwnProperty('name')) {
        return this.sourcesAsObj[code].name;
      } return code;
    },
  },
  mounted() {
  },
  watch: {
  },
};
</script>

<template>
  <section class="Summary" ref="summarySection">
    <div class="Summary-headingWrap">
      <div>
        <h2 class="heading heading-lg">{{title}}</h2>
        <h3 class="heading-lg" v-if="source">{{total}} poster i Swepub</h3>
        <p v-else id="summary-descr">
          Fördelning antal poster för organisationer som levererar data till Swepub</p>
      </div>
      <div v-if="source">
      <router-link :to="`/process/${source}/status`">
        Visa senaste leverans i Leveransstatus</router-link>
      </div>
    </div>
    <div v-if="!source">
      <div class="Summary-totalContainer">
        <div class="Summary-totalNumberContainer">
          <h2 id="totalNumber">{{total}}</h2>
          <h3 class="heading-lg">poster i Swepub</h3>
        </div>
        <doughnut-container :chartData="chartData"
          chartId="summary-doughnut"
          :chartStyles="chartStyles"
          describedbyId="summary-descr"/>
      </div>
    </div>
  </section>
</template>

<style lang="scss" scoped>
.Summary {

  &-headingWrap {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    flex-wrap: wrap;

    & h2,
    & h3 {
      margin-bottom: 0;
    }
  }

  &-totalContainer {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    margin-top: 2em;
  }

  &-totalNumberContainer {
    margin: 0 8em 2em 2em;

    & > * {
      margin: 0;
    }
  }

  & #totalNumber {
    font-size: 4em;
  }
}
</style>
