<script>
import VueSimpleSpinner from 'vue-simple-spinner';

export default {
  name: 'export-buttons',
  components: {
    VueSimpleSpinner,
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
    <vue-simple-spinner v-if="exportLoading" />
    <div v-if="exportError">
      <span class="error" role="alert" aria-atomic="true">{{exportError}}</span>
    </div>
  </div>
</template>

<style lang="scss">
  .ExportButtons {
    display: flex;
    align-items: center;
    margin-top: 2em;
    flex-wrap: wrap;

    & .btn {
      margin-top: 0;
      margin-bottom: 5px;
    }
  }
</style>
