<script>
import Helptexts from '@/assets/json/helptexts.json';

export default {
  name: 'data-dump',
  data() {
    return {};
  },
  computed: {
    content() {
      return Helptexts.bibliometrics.datadump;
    },
  },
};
</script>

<template>
  <section class="Datadump horizontal-wrapper"
    id="datadump-section"
    role="tabpanel"
    aria-labelledby="datadump-tab">
    <div class="DataDump-content" v-html="content"></div>
  </section>
</template>

<style lang="scss">
.DataDump {
  &-content {
    max-width: $screen-md;
  }
}
</style>
