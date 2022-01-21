<script>
import TabMenu from '@/components/shared/TabMenu';

const DataQuality = () => import('@/components/process/DataQuality');
const HarvestStatus = () => import('@/components/process/HarvestStatus');

export default {
  name: 'process',
  components: {
    DataQuality,
    HarvestStatus,
    TabMenu,
  },
  props: {
    query: { // passed from vue router
      type: Object,
      default: null,
    },
    params: { // passed from vue router
      type: Object,
      default: null,
    },
  },
  data() {
    return {
      tabs: [
        { id: 'quality', text: 'Datakvalitet' },
        { id: 'status', text: 'Leveransstatus' },
      ],
      activeTab: 'quality',
    };
  },
  computed: {
  },
  methods: {
    switchTab(id) {
      if (id !== this.activeTab) {
        this.activeTab = id;
        if (this.$route.fullPath !== '/process') {
          // clear the search if switching tab
          this.$router.push('/process')
          // eslint-disable-next-line
        .catch(err => console.warn(err.message));
        }
      }
    },
  },
  mounted() {
    if (this.$route.params.service === 'status') {
      this.activeTab = 'status';
    }
  },
  watch: {
  },
};
</script>

<template>
  <div class="Process vertical-wrapper">
    <tab-menu class="horizontal-wrapper" @go="switchTab" :tabs="tabs" :active="activeTab" />
        <data-quality v-if="activeTab === 'quality'" :query="query" :params="params"/>
        <harvest-status v-if="activeTab === 'status'"/>
  </div>
</template>

<style lang="scss">
.Process {
  &-descr {
    max-width: $screen-md;
  }

  &-search {
    margin-bottom: 1em;
  }

  &-submit {
    display: flex;
    align-items: center;

    & * {
      margin-right: 1em;
    }
  }
}
</style>
