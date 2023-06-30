<script>
/* eslint-disable no-underscore-dangle */
import { Doughnut, mixins } from 'vue-chartjs';
import 'chartjs-plugin-deferred';

const { reactiveProp } = mixins;

export default {
  name: 'doughnut-chart',
  extends: Doughnut,
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
          callbacks: {
            title: ((tooltipItem) => this.chartData.labels[tooltipItem[0].index]),
            label: ((tooltipItem) => {
              const { index } = tooltipItem;
              const total = this.chartData.total[index].toLocaleString();
              const suffix = total === 1 ? 'post' : 'poster';
              const percentage = this.chartData.percentage[index];
              return `${total} ${suffix} (${percentage}%)`;
            }),
          },
        },
      },
    };
  },
  computed: {
  },
  methods: {
    showTooltip(index) {
      const chart = this.$data._chart;
      const segment = chart.getDatasetMeta(0).data[index];

      if (typeof (Event) === 'function') {
        // supports customEvents
        // dispatch mouseevent for pie hover effect
        const rect = chart.canvas.getBoundingClientRect();
        const point = segment.getCenterPoint();
        const event = new MouseEvent('mousemove', {
          clientX: rect.left + point.x,
          clientY: rect.top + point.y,
        });
        const node = chart.canvas;
        node.dispatchEvent(event);
      } else {
        // fallback (IE11)
        // set tooltip to active
        chart.tooltip._active = [segment];
        chart.tooltip.update();
        chart.draw();
      }
    },
    hideTooltips() {
      const chart = this.$data._chart;

      if (typeof (Event) === 'function') {
        // supports customEvents
        // dispatch mouseevent
        const evt = new MouseEvent('mousemove', {
          clientX: 0,
          clientY: 0,
        });
        const node = chart.canvas;
        node.dispatchEvent(evt);
      } else {
        // fallback (IE11)
        // set tooltip to inactive
        chart.tooltip._active = [];
        chart.tooltip.update();
        chart.draw();
      }
    },
  },
  mounted() {
    this.addPlugin({ id: 'chartjs-plugin-deferred' });
    this.renderChart(this.chartData, this.chartOptions);
  },
  watch: {
    openTooltip(val) {
      if (val !== null) {
        this.showTooltip(val);
      } else this.hideTooltips();
    },
  },
};
</script>
