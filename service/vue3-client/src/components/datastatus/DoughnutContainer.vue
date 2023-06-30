<script>
// handles communication between chart and legend components
const DoughnutChart = () => import('@/components/datastatus/DoughnutChart.vue');
const ChartLegend = () => import('@/components/datastatus/ChartLegend.vue');
const SrChartTable = () => import('@/components/datastatus/SrChartTable.vue');

export default {
  name: 'doughnut-container',
  components: {
    DoughnutChart,
    ChartLegend,
    SrChartTable,
  },
  props: {
    chartData: {
      type: Object,
      required: true,
    },
    chartStyles: {
      type: Object,
    },
    chartId: {
      type: String,
      default: 'doughnut-chart',
    },
    describedbyId: {
      type: String,
      default: '',
    },
    linked: {
      type: Boolean,
      default: true,
    },
  },
  data() {
    return {
      openTooltip: null,
    };
  },
  computed: {
  },
  methods: {
    handleLegendHover(e) {
      this.openTooltip = e;
    },
    handleLegendLeave() {
      this.openTooltip = null;
    },
  },
  mounted() {
  },
  watch: {
  },
};
</script>

<template>
  <div class="DoughnutContainer">
    <doughnut-chart :chartData="chartData"
      :chartId="chartId"
      :openTooltip="openTooltip"
      :styles="chartStyles"
      aria-hidden="true"/>
    <chart-legend :data="chartData"
      @mouseover="handleLegendHover"
      @mouseleave="handleLegendLeave"
      :linked="linked"
      :describedbyId="describedbyId"/>
    <sr-chart-table :chartData="chartData" :describedbyId="describedbyId"/>
  </div>
</template>

<style lang="scss">
.DoughnutContainer {
  display: flex;
  flex: 1;
  flex-wrap: nowrap;
  max-width: 100%;

  @media (max-width: 600px) {
    flex-wrap: wrap;
  }
}

</style>
