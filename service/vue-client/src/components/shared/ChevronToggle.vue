<script>
// v-model the outer component like so:
// <chevron-toggle v-model="expanded"/>

export default {
  name: 'chevron-toggle',
  components: {
  },
  props: {
    value: {
      type: Boolean,
      required: true,
      default: false,
    },
    ariaControls: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
    };
  },
  computed: {
    toggled() {
      return this.value;
    },
  },
  methods: {
    toggle() {
      this.$emit('input', !this.value);
    },
  },
};
</script>

<template>
  <div class="ChevronToggle icon"
    :class="{'is-toggled' : toggled}"
    role="button"
    tabindex="0"
    @click.stop="toggle"
    @keyup.enter="toggle"
    :aria-controls="ariaControls"
    :aria-expanded="toggled ? 'true' : 'false'"
    :aria-label="toggled ? 'Minimera' : 'Expandera'">
    <font-awesome-icon :icon="['fa', 'chevron-down']"
      role="presentation"
      size="lg"
      fixed-width/>
  </div>
</template>

<style lang="scss">
.ChevronToggle {
  color: $grey;
  display: inline-block;
  height: 20px;
  margin-left: 5px;
  cursor: pointer;
  transition: transform 0.1s ease;

  &.is-toggled {
    transform: rotate(180deg);
  }
}
</style>
