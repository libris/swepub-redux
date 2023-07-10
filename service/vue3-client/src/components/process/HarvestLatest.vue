<script>
import { defineAsyncComponent } from 'vue';
import FetchMixin from '@/components/mixins/FetchMixin.vue';

const HelpBubble = defineAsyncComponent(() => import('@/components/shared/HelpBubble.vue'));
const HarvestSummary = defineAsyncComponent(() => import('@/components/process/HarvestSummary.vue'));
const HarvestRejected = defineAsyncComponent(() => import('@/components/process/HarvestRejected.vue'));

export default {
  name: 'harvest-latest',
  mixins: [FetchMixin],
  components: {
    HelpBubble,
    HarvestSummary,
    HarvestRejected,
  },
  props: {
  },
  data() {
    return {
      data: null,
      loading: false,
      error: '',
    };
  },
  computed: {
    apiEndpoint() {
      return `/process/${this.$route.params.source}/status`;
    },
  },
  methods: {
    fetchHarvestLatest() {
      this.fetchData(this.apiEndpoint)
      // eslint-disable-next-line no-console
        .catch((err) => console.warn(err));
    },
  },
  mounted() {
    this.fetchHarvestLatest();
  },
  watch: {
    // eslint-disable-next-line func-names
    '$route.params.source': function () {
      this.fetchHarvestLatest();
    },
  },
};
</script>

<template>
  <section
    class="HarvestLatest"
    :aria-busy="loading"
    aria-labelledby="status-tab harvest-latest-heading"
  >
    <!-- <vue-simple-spinner v-if="loading"/> -->
    <p v-if="error">
      <span class="error" role="alert" aria-atomic="true">{{ error }}</span>
    </p>
    <div v-if="!loading && !error && data">
      <h2 id="harvest-latest-heading" class="heading heading-lg">
        {{ data.source_name }}</h2>
      <div class="HarvestStatus-headerWrapper">
        <h3 class="HarvestStatus-header heading heading-md">Översikt</h3>
        <help-bubble bubbleKey="harvest_overview"/>
      </div>
      <harvest-summary :harvestData="data"/>
      <section class="HarvestLatest-subsection"
        v-if="data.rejected && data.rejected > 0 && data.harvest_id"
        aria-labelledby="preview-heading">
        <div class="HarvestStatus-headerWrapper">
          <h3 id="preview-heading" class="HarvestStatus-header heading heading-md">
            Avvisade poster</h3>
          <help-bubble bubbleKey="harvest_rejected"/>
        </div>
        <harvest-rejected :harvestId="data.harvest_id"/>
      </section>
    </div>
  </section>
</template>

<style scoped lang="scss">
.HarvestLatest {
  &-subsection {
    margin-top: 2em;
  }
}
</style>
