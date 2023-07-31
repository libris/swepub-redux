<template>
  <Bar
    :options="chartOptions"
    :data="chartData"
  />
</template>

<script>
import { Bar } from 'vue-chartjs';
import { Chart, CategoryScale, LinearScale, Tooltip, BarElement } from 'chart.js';
import ChartDeffered from 'chartjs-plugin-deferred';

Chart.register(ChartDeffered, CategoryScale, LinearScale, Tooltip, BarElement);

export default {
  name: 'bar-chart',
  components: {
    Bar,
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
  },
  data() {
    return {
      chartOptions: {
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
        },
        hover: {
          mode: 'index',
          intersect: false,
        },
        scales: {
          yAxes: {
            ticks: {
              beginAtZero: true,
              precision: 0,
              fontFamily: "'Open sans', sans-serif",
              fontSize: 14,
              fontColor: '#000',
            },
          },
          xAxes: {
            ticks: {
              fontFamily: "'Open sans', sans-serif",
              fontSize: 14,
              fontColor: '#000',
            },
          },
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
  },
};
</script>
