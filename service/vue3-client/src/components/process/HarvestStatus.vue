<script>
import { defineAsyncComponent } from 'vue';
import Helptexts from '@/assets/json/helptexts.json';
import SelectSource from '@/components/shared/SelectSource.vue';

const TabMenu = defineAsyncComponent(() => import('@/components/shared/TabMenu.vue'));
const HarvestLatest = defineAsyncComponent(() => import('@/components/process/HarvestLatest.vue'));
const HarvestHistory = defineAsyncComponent(() => import('@/components/process/HarvestHistory.vue'));
const HelpBubble = defineAsyncComponent(() => import('@/components/shared/HelpBubble.vue'));

export default {
  name: 'harvest-status',
  components: {
    SelectSource,
    TabMenu,
    HarvestLatest,
    HarvestHistory,
    HelpBubble,
  },
  props: {
  },
  data() {
    return {
      source: '',
      tabs: [
        { id: 'latest', text: 'Senaste leverans' },
        { id: 'history', text: 'Historik' },
      ],
    };
  },
  computed: {
    default() {
      // initial state of form (on pageload or clear)
      return this.$route.params.source || '';
    },
    serviceDescr() {
      return Helptexts.harvestStatus.service_descr;
    },
    canSearch() {
      // don't allow if form is unchanged
      return !!(this.source && this.source !== this.default) || this.error;
    },
    canClear() {
      return !!this.source;
    },
    hasHarvestParams() {
      return !!this.$route.params.source && this.$route.params.service === 'status';
    },
    activeTab() {
      if (this.hasHarvestParams) {
        if (this.$route.params.subservice === 'history') {
          return 'history';
        } return 'latest';
      } return null;
    },
  },
  methods: {
    clearSearch() {
      this.source = '';
      this.$router.push('/process')
      // eslint-disable-next-line
        .catch(err => console.warn(err.message));
    },
    clearResults() {
      this.error = '';
      this.data = null;
    },
    setHarvestParams() {
      this.$router.push({
        params: { source: this.source, service: 'status', subservice: null },
      // eslint-disable-next-line
      }).then(() => this.$nextTick(() => this.$refs.harvestDivider.scrollIntoView({ behavior: 'smooth' })))
        .catch((err) => {
        // eslint-disable-next-line no-console
          console.warn(err.message);
        });
    },
    switchTab(id) {
      if (id !== this.activeTab) {
        this.$router.push({
          params: { ...this.$route.params, ...{ subservice: id === 'history' ? 'history' : null } },
        }).catch((err) => {
          // eslint-disable-next-line
          console.warn(err.message);
        });
      }
    },
  },
  created() {
    this.source = this.default; // apply default values before mount
  },
  mounted() {
    if (this.hasHarvestParams) {
      this.$nextTick(() => this.$refs.harvestDivider.scrollIntoView({ behavior: 'smooth' }));
    }
  },
  watch: {
  },
};
</script>

<template>
  <section class="HarvestStatus horizontal-wrapper"
    id="harvestStatus-section"
    role="tabpanel"
    aria-labelledby="status-tab">
    <div class="Process-search"
      aria-labelledby="harvestStatus-service-descr">
      <p id="harvestStatus-service-descr" class="Process-descr" v-html="serviceDescr"></p>
      <div aria-describedby="harvestStatus-service-descr" role="form">
        <select-source v-model="source" @clear="clearResults">
          <template v-slot:helpbubble>
            <help-bubble bubbleKey="organization"/>
          </template>
        </select-source>
        <div class="Process-submit">
          <button id="submit-btn"
            class="btn"
            :class="{'disabled' : !canSearch}"
            @click.prevent="setHarvestParams"
            :disabled="!canSearch">Visa</button>
          <button id="clear-btn"
            class="btn btn--warning"
            :class="{'disabled' : !canClear}"
            @click.prevent="clearSearch"
            :disabled="!canClear">Rensa</button>
        </div>
      </div>
    </div>
    <div v-if="hasHarvestParams">
      <hr class="divided-section" ref="harvestDivider">
      <tab-menu @go="switchTab"
        :tabs="tabs"
        :active="activeTab"/>
        <keep-alive>
          <harvest-latest v-if="activeTab === 'latest'"/>
          <harvest-history v-if="activeTab === 'history'"/>
        </keep-alive>
    </div>
  </section>
</template>

<style lang="scss">
.HarvestStatus {
  &-headerWrapper {
    margin-bottom: 1em;
    display: flex;
    align-items: center;
  }

  &-header {
    margin: 0 5px 0 0;
  }

}
</style>
