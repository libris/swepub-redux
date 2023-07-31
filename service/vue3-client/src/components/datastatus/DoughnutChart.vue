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
        plugins: {
          tooltip: {
            backgroundColor: '#fff',
            titleColor: '#727272',
            titleFont: {
              family: "'Open sans', sans-serif",
              size: 14,
            },
            bodyColor: '#000',
            bodyFont: {
              family: "'Open sans', sans-serif",
              size: 14,
            },
            borderColor: '#949494',
            borderWidth: 1,
            callbacks: {
              title: ((tooltipItem) => this.chartData.labels[tooltipItem[0].dataIndex]),
              label: ((tooltipItem) => {
                const { dataIndex } = tooltipItem;
                const total = this.chartData.total[dataIndex].toLocaleString();
                const suffix = total === 1 ? 'post' : 'poster';
                const percentage = this.chartData.percentage[dataIndex];
                return `${total} ${suffix} (${percentage}%)`;
              }),
            },
          },
        }
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
