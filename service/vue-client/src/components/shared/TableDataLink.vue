<script>
/**
 * Dumb component renders a table cell
 *
 * tdValue - rendered as link href & link text
 * shift - add this string to beginning of tdValue for link text & url
 * unshift - remove this value from beginning of link text
 * newTab - opens in new browser tab, adds indicator icon
 */
export default {
  name: 'table-data-link',
  components: {
  },
  props: {
    tdKey: {
      type: String,
    },
    tdValue: {
      type: String,
      required: true,
    },
    unshift: {
      type: String,
      required: false,
    },
    shift: {
      type: String,
      required: false,
    },
    newTab: {
      type: Boolean,
      default: true,
    },

  },
  data() {
    return {};
  },
  computed: {
    linkUrl() {
      if (this.tdValue) {
        if (this.shift) {
          return this.shift + this.tdValue;
        }
        return this.tdValue;
      } return '';
    },
    linkText() {
      if (this.tdValue && typeof this.tdValue === 'string') {
        let text = this.tdValue;
        if (this.unshift) {
          if (text.startsWith(this.unshift)) {
            text = text.replace(this.unshift, '');
          }
        }
        if (this.shift) {
          text = this.shift + text;
        }
        return text;
      } return null;
    },
    target() {
      if (this.newTab) {
        return {
          target: '_blank',
          rel: 'noopener noreferrer',
        };
      } return '';
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
  <span class="TableDataLink">
    <font-awesome-icon v-if="newTab"
      class="TableDataLink-icon"
      title="Öppnar i ny flik"
      :icon="['fa', 'external-link-alt']"/>
    <a :href="linkUrl" v-bind="target" :title="this.linkUrl">{{linkText}}</a>
  </span>
</template>

<style lang="scss">
.TableDataLink {
  &-icon {
    color: $greyDarker;
    margin-right: 5px;
  }
}
</style>
