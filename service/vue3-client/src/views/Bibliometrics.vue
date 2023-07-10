<script>
import { defineAsyncComponent } from 'vue';
import TabMenu from '@/components/shared/TabMenu.vue';

import { KeepAlive } from 'vue';
const BibliometricsSearch = defineAsyncComponent(() => import('@/components/bibliometrics/Search.vue'));
const DataDump = defineAsyncComponent(() => import('@/components/bibliometrics/DataDump.vue'));

export default {
  // eslint-disable-next-line
  name: 'bibliometrics',
  components: {
    TabMenu,
    BibliometricsSearch,
    DataDump,
    KeepAlive
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
    <TabMenu class="horizontal-wrapper" @go="switchTab" :tabs="tabs" :active="activeTab" />

    <BibliometricsSearch v-show="activeTab === 'search'" :query="query" />

    <DataDump v-show="activeTab === 'datadump'" />
  </div>
</template>
