<script>
/**
 * Renders a string as a multiline block of text.
 *
 * props:
 * lines - number of lines to allow in table. CSS line-clamp support only.
 * trimAt - cut the rendered text at this char. Fallback for no line-clamp support/limit alt-text.
 *
 */

export default {
  name: 'table-data-multi-line',
  components: {
  },
  props: {
    tdKey: {
      type: String,
      required: true,
    },
    tdValue: {
      type: String,
      required: true,
    },
    trimAt: {
      type: Number,
      default: 1500,
    },
    lines: {
      type: Number,
      default: 2,
    },
  },
  data() {
    return {};
  },
  computed: {
    trimmed() {
      if (this.trimAt > this.tdValue.length) {
        return this.tdValue;
      } return this.tdValue.substring(0, this.trimAt).concat('...');
    },
    lineClampObj() {
      return {
        '-webkit-line-clamp': this.lines,
      };
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
  <span class="TableDataMultiLine"
    :title="trimmed"
    :style="lineClampObj">{{trimmed}}</span>
</template>

<style scoped lang="scss">

.TableDataMultiLine {
  white-space: initial;
  word-wrap: break-word;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

</style>
