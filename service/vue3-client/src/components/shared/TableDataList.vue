<script>
/**
 * Renders a list in a table cell
 *
 * targetKeys - (array) keys to render in an object or array of objects.
 *
 * renderFn - (function) custom render function has to return a plain (filtered) array
 *
 * renderComponent - (string) optionallty pass a component name to be rendered as the list item.
 * Don't forget to register it here...
 *
 * showEmptyValues - (bool) true will print blank lines for null/empty values
 * = good for data that needs to correlate across tr:s, default false
 */

const TableDataLink = () => import('@/components/shared/TableDataLink.vue');

export default {
  name: 'table-data-list',
  components: {
    TableDataLink,
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
  data() {
    return {
      limit: 5,
    };
  },
  computed: {
    mappedList() {
      let mappedList = [];
      if (this.renderFn) {
        // custom render function
        mappedList = this.renderFn(this.$props);
      }
      if (!this.renderFn && this.isArray) {
        // default rendering of array
        this.tdValue.forEach((el) => {
          if (this.targetKeys) {
            const localList = [];
            this.targetKeys.forEach((key) => { // add multiple targetkeys ex firstname lastname
              if (el.hasOwnProperty(key)) {
                localList.push(el[key]);
              }
            });
            mappedList.push(localList.join(' '));
          } else {
            mappedList.push(el);
          }
        });
      }
      return mappedList;
    },
    filteredList() { // only if showEmptyValues option is set to false
      if (!this.showEmptyValues) {
        return this.mappedList.filter((el) => el !== '' && el !== null);
      } return this.mappedList;
    },
    limitedList() { // slice by this.limit
      if (this.exceedsLimit) {
        const sliced = this.filteredList.slice(0, this.limit);
        return sliced;
      } return this.filteredList;
    },
    exceedsLimit() {
      return this.limit && this.filteredList.length > this.limit;
    },
    isArray() {
      return this.tdValue && Array.isArray(this.tdValue);
    },
  },
  methods: {
  },
  mounted() {
  },
  watch: {
  },
};
</script>

<template>
  <ul class="TableDataList" v-if="limitedList.length > 0">
    <li v-for="(item, index) in limitedList"
      :key="`${tdKey}-${index}`"
      :title="item">
      <component v-if="renderComponent"
        :is="renderComponent"
        v-bind="{...$attrs, ... {tdValue: item}}"></component>
      <span v-else-if="!item" class="empty">-</span>
      <template v-else>{{item}}</template>
    </li>
    <li v-if="exceedsLimit">...</li>
  </ul>
</template>

<style lang="scss">
.TableDataList {
  list-style-type: none;
  margin: 0;
  padding: 0;

  & li {
    text-overflow: ellipsis;
    overflow: hidden;

    & .empty {
      visibility: hidden;
    }
  }
}
</style>
