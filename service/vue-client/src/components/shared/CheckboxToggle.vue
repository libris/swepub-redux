<script>
// v-bind to parent like so: v-model="field.selected"
export default {
  name: 'checkbox-toggle',
  components: {
  },
  props: {
    value: {
      type: Boolean,
      required: true,
    },
    id: {
      type: String,
      required: true,
    },
    label: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
    };
  },
  computed: {
    isChecked() {
      return this.value;
    },
  },
  methods: {
    toggle() {
      this.$emit('input', !this.value);
    },
  },
  mounted() {
  },
  watch: {
  },
};
</script>

<template>
  <div class="CheckboxToggle"
    :class="{'is-checked' : isChecked}"
    role="checkbox"
    tabindex="0"
    @click="toggle"
    @keyup.enter="toggle"
    :aria-checked="isChecked ? 'true' : 'false'"
    :aria-labelledby="id">
    <span :id="id">{{label}}</span>
  </div>
</template>

<style scoped lang="scss">

.CheckboxToggle {
  border: 1px solid $purple;
  color: $purple;
  border-radius: 6px;
  font-size: 1.2rem;
  font-weight: 600;
  padding: 3px 6px;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.1s ease;

  &.is-checked {
    background-color: $purple;
    color: $white;
  }

  &:hover:not(.is-checked),
  &:focus:not(.is-checked) {
    background-color: $purpleLight;
  }
}
</style>
