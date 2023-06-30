<script>
const HelpBubble = () => import('@/components/shared/HelpBubble.vue');

export default {
  name: 'short-stat',
  components: {
    HelpBubble,
  },
  props: {
    stat: {
      type: Object,
      default: null,
    },
  },
  data() {
    return {};
  },
  computed: {
    title() {
      return this.stat.title || null;
    },
    text() {
      return this.stat.text || null;
    },
    total() {
      if (this.stat.hasOwnProperty('total')) {
        return this.stat.total.toLocaleString() || null;
      } return null;
    },
    percentage() {
      if (this.stat.hasOwnProperty('percentage')) {
        const rounded = Math.round(this.stat.percentage);
        if (typeof rounded === 'number') {
          return `${rounded}%`;
        } return null;
      } return null;
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
  <aside class="ShortStat" :aria-label="title" v-if="total || percentage">
    <div class="ShortStat-heading">
      <h2 class="heading heading-md">{{title}}</h2>
      <help-bubble :bubbleKey="stat.id"/>
    </div>
    <div class="ShortStat-body">
      <div class="ShortStat-percentageWrap" v-if="percentage">
        <h2 class="heading heading-lg">{{percentage}}</h2>
      </div>
      <div class="ShortStat-totalWrap">
        <h2 class="heading heading-lg">{{total}}</h2>
        <p>{{text}}</p>
      </div>
    </div>
  </aside>
</template>

<style lang="scss">
.ShortStat {
  margin: 3rem 3rem 3rem 0;
  flex: 1;

  &-heading {
    display: flex;
    align-items: center;
    white-space: nowrap;

    & .heading {
      margin: 0;
    }

    & .HelpBubble {
      margin-left: 5px;
    }
  }

  &-body {
    margin-top: 1rem;
    display: flex;
    align-items: flex-start;
  }

  &-percentageWrap {
    border-radius: 50%;
    width: 80px;
    min-width: 80px;
    height: 80px;
    display: flex;
    justify-content: center;
    align-items: center;
    border: 1px solid $black;
    margin-right: 2rem;
  }

  &-totalWrap {
    max-width: 300px;
    & > * {
      margin: 0;
    }
  }
}
</style>
