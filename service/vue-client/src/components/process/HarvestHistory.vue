<script>
import FetchMixin from '@/components/mixins/FetchMixin';

const HelpBubble = () => import('@/components/shared/HelpBubble');
const HarvestSummary = () => import('@/components/process/HarvestSummary');

export default {
  name: 'harvest-history',
  mixins: [FetchMixin],
  components: {
    HelpBubble,
    HarvestSummary,
  },
  props: {
  },
  data() {
    return {
      data: null,
      loading: false,
      error: '',
      showRejectedOnly: false,
    };
  },
  computed: {
    apiEndpoint() {
      return `/process/${this.$route.params.source}/status/history`;
    },
    filteredHarvests() {
      if (this.data && this.data.harvest_history) {
        if (this.showRejectedOnly) {
          return this.data.harvest_history.filter((item) => item.rejected > 0);
        }
        return this.data.harvest_history;
      } return null;
    },
  },
  methods: {
    fetchHarvestHistory() {
      this.fetchData(this.apiEndpoint)
        // eslint-disable-next-line no-console
        .catch((err) => console.warn(err));
    },
  },
  mounted() {
    this.fetchHarvestHistory();
  },
  watch: {
    // eslint-disable-next-line func-names
    '$route.params.source': function () {
      this.fetchHarvestHistory();
    },
  },
};
</script>

<template>
  <section class="HarvestHistory"
    :aria-busy="loading"
    aria-labelledby="status-tab harvest-history-heading">
    <vue-simple-spinner v-if="loading"/>
    <p v-if="error">
      <span class="error" role="alert" aria-atomic="true">{{ error }}</span>
    </p>
    <div v-if="!loading && !error && data">
    <h2 id="harvest-history-heading" class="heading heading-lg">
        {{ data.source_name }}</h2>
    <div class="HarvestStatus-headerWrapper">
      <h3 class="HarvestStatus-header heading heading-md">Historiska leveranser</h3>
      <help-bubble bubbleKey="harvest_history"/>
    </div>
      <div class="HarvestHistory-checkboxWrap">
        <input id="rejected-only-checkbox" type="checkbox" v-model="showRejectedOnly"/>
        <label for="rejected-only-checkbox" class="is-inline">
          Endast leveranser med avvisade poster</label>
      </div>
      <ol class="HarvestHistory-list">
        <li v-for="(item, index) in filteredHarvests" :key="`harvest-summary-${index}`">
          <harvest-summary :harvestData="item" :expandable="true"/>
        </li>
      </ol>
      <p v-if="filteredHarvests && filteredHarvests.length === 0">Hittade inga leveranser</p>
    </div>
  </section>
</template>

<style scoped lang="scss">
.HarvestHistory {

  &-checkboxWrap {
    & label {
      font-weight: inherit;
    }
  }

  &-list {
    padding: 0;
    list-style-type: none;

    & > li {
      margin: 5px 0;
    }
  }
}
</style>
