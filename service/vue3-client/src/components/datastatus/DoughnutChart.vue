<template>
  <Doughnut
    :options="chartOptions"
    :data="chartData"
    :style="chartStyles"
  />
</template>

<script>
/* eslint-disable no-underscore-dangle */
import { Doughnut } from 'vue-chartjs';
import { Chart, CategoryScale, LinearScale, Tooltip, DoughnutController, ArcElement } from 'chart.js';
import ChartDeffered from 'chartjs-plugin-deferred';

Chart.register(ChartDeffered, CategoryScale, LinearScale, Tooltip, DoughnutController, ArcElement);

export default {
  name: 'doughnut-chart',
  components: {
    Doughnut,
  },
  props: {
    chartData: {
      type: Object,
    },
    height: {
      default: null,
    },
    width: {
      default: null,
    },
    openTooltip: {
      type: Number,
      default: null,
    },
  },
  data() {
    return {
      // shared settings for all doughnuts
      chartOptions: {
        cutoutPercentage: 70,
        aspectRatio: 1,
        legend: {
          display: false,
        },
        tooltips: {
          backgroundColor: '#fff',
          titleFontColor: '#727272',
          titleFontFamily: "'Open sans', sans-serif",
          titleFontSize: 14,
          bodyFontColor: '#000',
          bodyFontFamily: "'Open sans', sans-serif",
          bodyFontSize: 14,
          borderColor: '#949494',
          borderWidth: 1,
          // callbacks: {
          //   title: ((tooltipItem) => this.chartData.labels[tooltipItem[0].index]),
          //   label: ((tooltipItem) => {
          //     const { index } = tooltipItem;
          //     const total = this.chartData.total[index].toLocaleString();
          //     const suffix = total === 1 ? 'post' : 'poster';
          //     const percentage = this.chartData.percentage[index];
          //     return `${total} ${suffix} (${percentage}%)`;
          //   }),
          // },
        },
      },
    };
  },
  computed: {
    chartStyles() {
      return {
        height: (this.height ?? '400') + 'px',
        width: (this.width ?? '400') + 'px',
      }
    }
  }
};
</script>
