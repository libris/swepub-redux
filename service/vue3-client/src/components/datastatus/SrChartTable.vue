<script>
// component takes in chart data and renders a table for screen reader use only
// (not visible on-screen).

export default {
  name: 'sr-chart-table',
  props: {
    chartData: {
      type: Object,
      default: () => {},
    },
    describedbyId: {
      type: String,
      default: '',
    },
  },
};
</script>

<template>
  <table class="SrChartTable sr-only" :aria-describedby="describedbyId">
    <tr>
      <th v-for="(label, index) in chartData.labels"
        :key="`label-${index}`"
        scope="col">
        {{label}}
      </th>
    </tr>
    <tr>
      <td v-for="(item, index) in chartData.datasets[0].data"
        :key="`posts-${index}`">
        {{item}} poster
      </td>
    </tr>
    <tr>
      <td v-for="(item, index) in chartData.percentage"
        :key="`percentage-${index}`">
        {{item}}%
      </td>
    </tr>
  </table>
</template>

<style lang="scss">
.SrChartTable {
  table-layout: fixed;
}
</style>
