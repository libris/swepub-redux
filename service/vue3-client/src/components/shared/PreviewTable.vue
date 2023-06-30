<script>
const TableDataLink = () => import('@/components/shared/TableDataLink.vue');
const TableDataList = () => import('@/components/shared/TableDataList.vue');
const TableDataBoolean = () => import('@/components/shared/TableDataBoolean.vue');
const TableDataMultiLine = () => import('@/components/shared/TableDataMultiLine.vue');
const TableDataId = () => import('@/components/shared/TableDataId.vue');
const TableDataSeries = () => import('@/components/shared/TableDataSeries.vue');

export default {
  name: 'preview-table',
  components: {
    TableDataLink,
    TableDataList,
    TableDataBoolean,
    TableDataMultiLine,
    TableDataId,
    TableDataSeries,
  },
  props: {
    previewData: {
      type: Object,
      default: () => {},
    },
    tableCols: {
      type: Array,
      default: () => [],
    },
    tableLayout: {
      type: String,
      default: 'fixed',
    },
    hitsProp: {
      type: String,
      default: 'hits',
    },
  },
  data() {
    return {};
  },
  computed: {
  },
  methods: {
  },
  mounted() {
  },
};
</script>

<template>
  <div class="PreviewTable" :class="tableLayout">
    <table class="PreviewTable-table">
      <thead>
        <tr>
          <th v-for="(col, index) in tableCols"
            :class="`col-${col.key}`"
            :key="`th-${col.key}-${index}`"
            :title="col.label">{{col.label}}</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="item in previewData[hitsProp]" :key="item.record_id">
          <td
            v-for="(col, index) in tableCols"
            :key="`td-${col.key}-${index}`"
            :class="`col-${col.key}`"
          >
            <!-- Renders the component and passes props
            specified in tableCols component prop -->
            <!-- must force-render a falsey boolean value -->
            <component
              v-if="(col.component &&
              (item[col.key]) || col.component === 'TableDataBoolean')"
              :is="col.component"
              :tdKey="col.key"
              :tdValue="item[col.key]"
              :trData="item"
              v-bind="col.props"
            />

            <span v-else-if="item[col.key]" :title="item[col.key]">
              {{item[col.key]}}
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style lang="scss">
.PreviewTable {
  display: inline-block;
  width: 100%;
  max-width: 100%;
  border: 1px solid $greyLight;

  &.fixed {
    & table {
      table-layout: fixed;
    }

    @media (max-width: 850px) {
      overflow-x: auto;
      & table {
        table-layout: auto;
      }
    }
  }

  &.auto {
    overflow-x: auto;

    & table {
      table-layout: auto;

      & td {
        max-width: 250px;
        max-width: 15vw;

        &:last-of-type {
          width: 100%;
        }
      }
    }
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  th {
    position: sticky;
    top: 0;
    box-shadow: 0px 1px 0px $greyLight;
    font-weight: 600;
    text-transform: uppercase;
    text-align: left;
    padding: 1em;
    background-color: $greyLighter;
    border-bottom: 1px solid $greyLight;
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;

    @media (max-width: 850px) {
      padding: 5px;
    }
  }

  tr {
    &:nth-child(even) {
      background-color: $greyLighter;
    }
  }

  td {
    padding: 1em;
    vertical-align: baseline;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    box-sizing: border-box;

    @media (max-width: 850px) {
      padding: 5px;
    }
  }

  & .col-source,
  .col-publication_year {
    width: 65px;
  }

  & .col-code {
    width: 175px;
  }
}
</style>
