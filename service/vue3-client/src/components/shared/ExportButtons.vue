<script>
import Spinner from './Spinner.vue';

export default {
  name: 'export-buttons',
  components: {
    Spinner,
  },
  props: {
    exportLoading: {
      type: Boolean,
      default: false,
    },
    exportAllowed: {
      type: Boolean,
      default: false,
    },
    exportError: {
      type: String,
      default: '',
    },
  },
};
</script>

<template>
  <div class="ExportButtons" :aria-busy="exportLoading">
    <button class="btn"
      id="export-json"
      :class="{'disabled' : !exportAllowed}"
      :disabled="!exportAllowed"
      @click="$emit('export-json')">Exportera JSON</button>
    <button class="btn"
      id="export-csv"
      :class="{'disabled' : !exportAllowed}"
      :disabled="!exportAllowed"
      @click="$emit('export-csv')">Exportera CSV</button>
    <button class="btn"
      id="export-tsv"
      :class="{'disabled' : !exportAllowed}"
      :disabled="!exportAllowed"
      @click="$emit('export-tsv')">Exportera TSV</button>
      <Spinner v-if="exportLoading" />
    <div v-if="exportError">
      <span class="error" role="alert" aria-atomic="true">{{exportError}}</span>
    </div>
  </div>
</template>

<style lang="scss">
  .ExportButtons {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    flex-direction: column;

    & .btn {
      width: 100%;
      margin: 4px 0;
    }

    @media (min-width: $screen-md) {
      flex-direction: row;

      & .btn {
        border-radius: 0;
        width: auto;
        margin: 0;
        margin-right: 1px;

        &:first-of-type {
          border-top-left-radius: 4px;
          border-bottom-left-radius: 4px;
        }

        &:last-of-type {
          border-top-right-radius: 4px;
          border-bottom-right-radius: 4px;
          margin-right: 0;
        }
      }
    }
  }
</style>
