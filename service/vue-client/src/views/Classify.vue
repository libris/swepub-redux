<script>
import TabMenu from '@/components/shared/TabMenu';

const ClassifyForm = () => import('@/components/classify/ClassifyForm');
const ClassifyDocumentation = () => import('@/components/classify/Documentation');

export default {
  // eslint-disable-next-line
  name: 'classify',
  components: {
    ClassifyForm,
    ClassifyDocumentation,
    TabMenu,
  },
  data() {
    return {
      tabs: [
        { id: 'classify', text: 'Ämnesklassificering' },
        { id: 'about', text: 'Om tjänsten' },
      ],
    };
  },
  computed: {
    activeTab() {
      if (this.$route.params.section === 'about') {
        return this.$route.params.section;
      } return 'classify';
    },
  },
  methods: {
    switchTab(id) {
      if (id === 'about') {
        this.$router.push({ path: `/classify/${id}` })
        // eslint-disable-next-line
          .catch(err => console.warn(err.message));
      } else {
        this.$router.push({ path: '/classify' })
        // eslint-disable-next-line
          .catch(err => console.warn(err.message));
      }
    },
  },
};
</script>

<template>
  <div class="vertical-wrapper horizontal-wrapper">
    <tab-menu @go="switchTab" :tabs="tabs" :active="activeTab" />
    <keep-alive>
      <classifyForm v-show="activeTab === 'classify'"/>
    </keep-alive>
    <keep-alive>
      <classify-documentation v-show="activeTab === 'about'"/>
    </keep-alive>
  </div>
</template>

<style lang="scss">

:root {
}
</style>
