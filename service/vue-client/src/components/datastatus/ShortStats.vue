<script>
import ShortStat from '@/components/datastatus/ShortStat';

export default {
  name: 'short-stats',
  components: {
    ShortStat,
  },
  props: {
    data: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
    };
  },
  computed: {
    stats() {
      return [
        {
          id: 'ssif',
          title: 'Ämnesklassificering (SSIF)',
          text: 'poster klassificerade enligt SSIF',
          ...this.data.ssif,
        },
        {
          id: 'open_access',
          title: 'Öppen tillgång',
          text: 'poster öppet tillgängliga',
          ...this.data.openAccess,
        },
        {
          id: 'swedish_list',
          title: 'Svenska listan',
          text: 'poster publicerade enligt Svenska listan',
          ...this.data.swedishList,
        },
      ];
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
  <section class="ShortStats">
    <div class="ShortStats-container horizontal-wrapper">
      <short-stat v-for="stat in stats" :key="stat.id" :stat="stat"></short-stat>
    </div>
  </section>
</template>

<style lang="scss">
.ShortStats {
  background-color: $greyLighter;
  width: 100vw;
  position: relative;
  left: 50%;
  right: 50%;
  margin-left: -50vw;
  margin-right: -50vw;
  padding: 0 2em;
  box-sizing: border-box;

  &-container {
    display: flex;
    flex-wrap: wrap;
  }
}
</style>
