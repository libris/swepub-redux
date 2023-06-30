<script>
/*
  v-model-bind this to parent like so:
  <year-picker v-model="years" legend="Utgivningsår"/>

  and years: { from: 1900, to: 1901 },
*/

export default {
  name: 'year-picker',
  components: {
  },
  props: {
    legend: {
      type: String,
      required: false,
    },
    value: {
      type: Object,
      required: true,
      validator(val) {
        return val.hasOwnProperty('from') && val.hasOwnProperty('to');
      },
    },
    error: {
      type: [Boolean, String],
      default: false,
    },
  },
  data() {
    return {
    };
  },
  computed: {
    from() {
      if (this.value.from) {
        return parseInt(this.value.from);
      } return '';
    },
    to() {
      if (this.value.to) {
        return parseInt(this.value.to);
      } return '';
    },
  },
  methods: {
    handleInput() {
      const from = this.$refs.fromValue.value;
      const to = this.$refs.toValue.value;
      this.$emit('input', { from, to });
    },
  },
  mounted() {
  },
  watch: {
  },
};
</script>

<template>
  <fieldset class="YearPicker">
    <legend v-if="legend">{{legend}}</legend>
    <slot name="helpbubble"></slot>
    <div>
      <label class="YearPicker-label">
        Från och med
      <input id="year-from"
        class="YearPicker-dateInput"
        :class="{'has-error' : error}"
        :aria-invalid="!!error"
        type="number"
        ref="fromValue"
        :value="from"
        @input="handleInput"
        min="1000"
        max="2500"
        step="1"/></label>
      <label class="YearPicker-label">
        till och med
      <input id="year-to"
        class="YearPicker-dateInput"
        :class="{'has-error' : error}"
        :aria-invalid="!!error"
        type="number"
        ref="toValue"
        :value="to"
        @input="handleInput"
        min="1000"
        max="2500"
        step="1"/></label>
      <span v-if="error"
        class="error is-inline"
        role="alert"
        aria-atomic="true">{{error}}</span>
    </div>
  </fieldset>
</template>

<style lang="scss">
.YearPicker {

  &-label {
    font-weight: initial;
  }

  &-dateInput {
    margin: 0 10px 0 5px;
    width: 90px;

    &.has-error {
      border-color: $danger;
    }
  }
}
</style>
