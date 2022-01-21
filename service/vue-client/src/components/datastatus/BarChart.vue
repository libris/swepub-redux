<script>
import { Bar, mixins } from 'vue-chartjs';
import 'chartjs-plugin-deferred';

const { reactiveProp } = mixins;

export default {
  name: 'bar-chart',
  extends: Bar,
  mixins: [reactiveProp],
  components: {
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
        tooltips: {
          mode: 'index',
          intersect: false,
          backgroundColor: '#fff',
          titleFontColor: '#727272',
          titleFontFamily: "'Open sans', sans-serif",
          titleFontSize: 14,
          bodyFontColor: '#000',
          bodyFontFamily: "'Open sans', sans-serif",
          bodyFontSize: 14,
          borderColor: '#949494',
          borderWidth: 1,
          callbacks: {
            title: ((tooltipItem) => this.chartData.labels[tooltipItem[0].index]),
            label: ((tooltipItem) => {
              const { datasetIndex, index } = tooltipItem;
              const number = this.chartData.datasets[datasetIndex].data[index];
              const suffix = number === 1 ? 'post' : 'poster';
              const percentage = this.chartData.percentage[index];
              return `${number} ${suffix} (${percentage}%)`;
            }),
          },
        },
        hover: {
          mode: 'index',
          intersect: false,
        },
        scales: {
          yAxes: [{
            ticks: {
              beginAtZero: true,
              precision: 0,
              fontFamily: "'Open sans', sans-serif",
              fontSize: 14,
              fontColor: '#000',
            },
          }],
          xAxes: [{
            ticks: {
              fontFamily: "'Open sans', sans-serif",
              fontSize: 14,
              fontColor: '#000',
            },
          }],
        },
      },
    };
  },
  computed: {
  },
  methods: {
  },
  mounted() {
    this.addPlugin({ id: 'chartjs-plugin-deferred' });
    this.renderChart(this.chartData, this.chartOptions);
  },
  watch: {
  },
};
</script>
