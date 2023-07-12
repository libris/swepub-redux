<script>
/*
  Base component for a search-select to be extended for various use cases

  v-model bind selected value in parent like so:
  <select-base v-model="selectedOrg" />

  providedOptions - pass options directly. Will load if no apiEndpoint is defined
  @clear event - select box is cleared
  'multiple' flag will render a multi-picker in vue-select
*/
import vSelect from 'vue-select';
import 'vue-select/dist/vue-select.css';
import FetchMixin from '@/components/mixins/FetchMixin.vue';

export default {
  name: 'select-base',
  mixins: [FetchMixin],
  components: {
    vSelect,
  },
  props: {
    providedOptions: {
      type: [Array, Object],
      required: false,
    },
    modelValue: {
      type: [String, Array], // single, multiple
    },
    value: {
      type: [String, Array], // single, multiple
    },
    incomingError: { // send in provided options error here
      default: null,
    },
    multiple: {
      type: Boolean,
      default: false,
    },
    clearable: {
      type: Boolean,
      default: false,
    },
    useValueProp: {
      required: false,
    },
    useLabelProp: {
      required: false,
    },
  },
  data() {
    return {
      options: [],
      loading: false,
      fetchMsg: '',
      error: this.incomingError,
      label: 'No title provided',
      valueProp: 'value', // what prop to emit as value
      labelProp: 'label', // where v-select should look for label
    };
  },
  computed: {
  },
  methods: {
    getOptions() {
      if (this.apiEndpoint) { // fetch options
        this.fetchData(this.apiEndpoint)
          .then((response) => {
            this.options = this.transformOptions(response);
          })
        // eslint-disable-next-line no-console
          .catch((err) => console.warn(err));
      } else if (this.providedOptions) { // provided options
        this.options = this.transformOptions(this.providedOptions);
      }
    },
    transformOptions(options) {
      return options;
    },
    setSelected(val) {
      if (!val || val.length === 0) {
        this.$emit('clear');
      }
      this.$emit('update:modelValue', val);
    },
  },
  mounted() {
    this.getOptions();

    if (this.useValueProp != null) {
      this.valueProp = this.useValueProp;
    }

    if (this.useLabelProp != null) {
      this.labelProp = this.useLabelProp;
    }
  },
};
</script>

<template>
  <div class="SelectBase" :aria-busy="loading">
    <label :for="`${$options.name}-select`" class="SelectBase-label">
      {{this.label}}
    </label>

    <slot name="helpbubble"></slot>

    <div class="SelectBase-spinnerContainer" v-if="loading" >
      <!-- <vue-simple-spinner size="small" /> -->
      spinner
    </div>

    <v-select v-else
      :options="options"
      :inputId="`${$options.name}-select`"
      :multiple="multiple"
      :label="labelProp"
      :reduce="option => option[this.valueProp]"
      :modelValue="modelValue"
      :clearable="clearable"
      @update:modelValue="setSelected"
    >
      <span slot="no-options">
        <span>{{fetchMsg}}</span>
      </span>
    </v-select>

    <p v-if="error"><span class="error">{{error}}</span></p>
  </div>
</template>

<style lang="scss">
.SelectBase {
  padding: 1rem 0;

  &-spinnerContainer {
    display: flex;
  }
}
</style>
