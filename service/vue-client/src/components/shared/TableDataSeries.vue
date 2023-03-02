<script>
export default {
  name: 'table-data-series',
  props: {
    tdKey: {
      type: String,
      required: true,
    },
    tdValue: {
      type: [Array, Object],
      required: true,
    },
    targetKeys: {
      type: [Array],
      required: false,
    },
    renderFn: {
      type: Function,
      required: false,
    },
    renderComponent: {
      type: String,
      required: false,
    },
    showEmptyValues: {
      type: Boolean,
      default: false,
    },
  },
};
</script>

<template>
  <div>
    <table v-for="(value, index) in tdValue" :key="index">
      <tbody>
        <tr v-for="key in Object.keys(value)" :key="key">
          <td><strong>{{key}}</strong></td>
          <td>{{value[key]}}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style lang="scss" scoped>
table {
  background: white;
}
</style>
