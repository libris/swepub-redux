<script>
import TabMenu from '@/components/shared/TabMenu';

const BibliometricsSearch = () => import('@/components/bibliometrics/Search');
const DataDump = () => import('@/components/bibliometrics/DataDump');

export default {
  // eslint-disable-next-line
  name: 'bibliometrics',
  components: {
    TabMenu,
    BibliometricsSearch,
    DataDump,
  },
  props: {
    query: { // passed from vue router
      type: Object,
      default: null,
    },
  },
  data() {
    return {
      tabs: [
        { id: 'search', text: 'Uttag' },
        { id: 'datadump', text: 'Datadump' },
      ],
    };
  },
  computed: {
    activeTab() {
      if (this.$route.params.section === 'datadump') {
        return this.$route.params.section;
      } return 'search';
    },
  },
  methods: {
    switchTab(id) {
      if (id === 'datadump') {
        this.$router.push({ path: `/bibliometrics/${id}` })
        // eslint-disable-next-line
          .catch(err => console.warn(err.message));
      } else {
        this.$router.push({ path: '/bibliometrics' })
        // eslint-disable-next-line
          .catch(err => console.warn(err.message));
      }
    },
  },
};
</script>

<template>
  <div class="Bibliometrics vertical-wrapper">
    <tab-menu class="horizontal-wrapper" @go="switchTab" :tabs="tabs" :active="activeTab" />
    <keep-alive>
      <bibliometrics-search v-show="activeTab === 'search'" :query="query" />
    </keep-alive>
    <keep-alive>
      <data-dump v-show="activeTab === 'datadump'" />
    </keep-alive>
  </div>
</template>

<style lang="scss">
:root {
}
</style>
