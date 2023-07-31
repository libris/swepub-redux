<script>
export default {
  name: 'table-data-series',
  data() {
    return {
      mainTitle: null,
      identifiedBy: null,
    };
  },
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
  mounted() {
    if (this.tdValue.length > 0) {
      this.tdValue.forEach((value) => {
        if (value.hasTitle != null && value.hasTitle.length > 0) {
          this.mainTitle = value.hasTitle[0].mainTitle;
        }

        if (value.identifiedBy != null) {
          this.identifiedBy = value.identifiedBy;
        }
      });
    }
  },
};
</script>

<template>
  <div>
    <div>
      {{mainTitle}}
    </div>

    <ul
      v-if="identifiedBy != null"
    >
      <li
        v-for="(item) in identifiedBy"
        :key="item['@type']"
      >
        {{ item.qualifier }}: {{ item.value }}
      </li>
    </ul>
  </div>
</template>

<style scoped>
ul {
  padding-left: 2.55rem;
  margin-bottom: 0;
}
</style>
