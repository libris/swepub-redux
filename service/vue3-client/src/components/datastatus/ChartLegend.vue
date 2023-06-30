<script>
export default {
  name: 'chart-legend',
  components: {
  },
  props: {
    data: {
      type: Object,
      required: true,
    },
    linked: {
      type: Boolean, // text is router-link to /datastatus/code
    },
    describedbyId: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
    };
  },
  computed: {
    legendData() {
      return this.data.datasets[0].data.map((el, index) => ({
        value: el,
        label: this.data.labels[index],
        code: this.data.code[index],
        color: this.data.datasets[0].backgroundColor[index],
      }));
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
  <ul class="ChartLegend" :aria-labelledby="describedbyId">
    <li v-for="(item, index) in legendData"
      :key="item.code"
      class="ChartLegend-item"
      @mouseover="$emit('mouseover', index)"
      @mouseleave="$emit('mouseleave', index)">
      <span class="ChartLegend-dot" :style="{ backgroundColor: item.color }"></span>
      <router-link v-if="linked"
        @focus.native="$emit('mouseover', index)"
        @blur.native="$emit('mouseleave', index)"
        class="ChartLegend-text link"
        :to="`/datastatus/${item.code}`">{{item.label}}</router-link>
      <span v-else
        class="ChartLegend-text"
        @focus="$emit('mouseover', index)"
        @blur="$emit('mouseleave', index)"
        tabindex="0">{{item.label}}</span>
    </li>
  </ul>
</template>

<style lang="scss">
.ChartLegend {
  max-height: 350px;
  overflow-y: auto;
  list-style-type: none;
  margin: 0;
  padding: 1rem;
  margin-left: 2em;

  &-item {
    margin: 3px 0;

    &:hover {
      & .ChartLegend-dot {
        transform: scale(1.2);
      }
    }
  }

  &-dot {
    display: inline-block;
    margin-right: 7px;
    vertical-align: middle;
    width: 15px;
    height: 15px;
    border-radius: 50%;
    transition: transform 0.1s ease;
    background-color: $grey;
  }

  &-text {
    color: $black;
    text-decoration: none;
    cursor: pointer;

    &:visited {
      color: $black;
    }
    &.link:hover {
      text-decoration: underline;
    }
  }

  @media (max-width: 600px) {
    margin-left: 0;
  }
}
</style>
