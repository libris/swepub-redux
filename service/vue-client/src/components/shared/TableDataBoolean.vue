<script>
/**
 * Dumb component renders a boolean to a (string) word in current language
 *
 */
import { mapGetters } from 'vuex';

export default {
  name: 'table-data-boolean',
  components: {
  },
  props: {
    tdKey: {
      type: String,
      required: true,
    },
    tdValue: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {};
  },
  computed: {
    ...mapGetters([
      'settings',
    ]),
    valueByLang() {
      const lang = this.settings.language;
      let value = '';
      if (typeof this.tdValue === 'boolean') {
        switch (lang) {
          case 'swe':
            value = this.tdValue ? 'Ja' : 'Nej';
            break;
          default:
            value = this.tdValue ? 'Yes' : 'No';
            break;
        }
      }
      return value;
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
  <span :title="valueByLang">{{valueByLang}}</span>
</template>

<style lang="scss">
:root {
}
</style>
