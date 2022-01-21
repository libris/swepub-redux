<script>
import { mapGetters } from 'vuex';
import FlagLabels from '@/assets/json/FlagLabels.json';

const HelpBubble = () => import('@/components/shared/HelpBubble');

export default {
  name: 'FlagCard',
  components: {
    HelpBubble,
  },
  props: {
    data: {
      type: Object,
      default: null,
    },
    selectable: {
      type: Boolean,
      default: true,
    },
    flagType: {
      type: String,
      required: true,
    },
  },
  data() {
    return {};
  },
  computed: {
    ...mapGetters([
      'settings',
    ]),
    isPicked() {
      return this.data.checked;
    },
    cardTitle() {
      if (FlagLabels.hasOwnProperty(this.data.name)) {
        return FlagLabels[this.data.name][this.settings.language];
      }
      return this.data.name;
    },
  },
  methods: {
    toggle() {
      if (this.selectable) {
        this.$emit('toggle');
      }
    },
  },
  mounted() {
  },
  watch: {
  },
};
</script>

<template>
<div class="FlagCard"
  :class="{'is-selectable' : selectable}"
  @click="toggle">
  <div class="FlagCard-header">
    <h4 class="FlagCard-title heading heading-xs"
    :id="`flagcard-title-${flagType}-${data.name}`">{{ cardTitle }}</h4>
    <help-bubble :bubbleKey="`${flagType}_${data.name}`" color="rgba(255, 255, 255, 0.70)"/>
  </div>
  <div class="FlagCard-body">
    <p class="FlagCard-count" :id="`count-${flagType}-${data.name}`">
      {{ `${data.count} ${data.count === 1 ? 'post' : 'poster'}` }}
    </p>
    <font-awesome-layers class="FlagCard-checkbox fa-lg"
      v-if="selectable"
      tabindex="0"
      @keyup.enter="toggle"
      role="checkbox"
      :aria-checked="data.checked ? 'true' : 'false'"
      :aria-labelledby="`flagcard-title-${flagType}-${data.name} count-${flagType}-${data.name}`">
      <font-awesome-icon aria-label="checkbox"
        :icon="['fas', 'square']"
        class="fa-w-16"
        :style="{ color: 'white' }" />
      <font-awesome-icon aria-label="checkbox"
        :icon="['far', 'square']"
        class="fa-w-16"/>
      <font-awesome-icon aria-label="checkbox"
        v-show="isPicked"
        :icon="['fa', 'check']"
        transform="shrink-7"/>
    </font-awesome-layers>
  </div>
</div>

</template>

<style lang="scss">
.FlagCard {
  display: flex;
  flex-direction: column;

  &.is-selectable {
    cursor: pointer;
    pointer-events: initial;
  }

  /* flexbox fallback */
  width: 200px;
  margin: 0 2em 1em 0;

  @supports (display: grid) {
    width: auto;
    margin: 0;
  }

  &-header {
    background-color: #ddd;
    padding: 0.5rem 1rem;
    color: $white;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .enrichments & {
      background-color: $enrichment;
    }

    .validations & {
      background-color: $validation;
    }

    .audits & {
      background-color: $audit;
    }
  }

  &-title {
    margin: 0;
  }

  &-checkbox {
  }

  &-body {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background-color: $shadow;
    border-bottom: 1px solid $shadow;
  }

  &-count {
    font-weight: 600;
    margin: 0;
  }

  &-bodyDivider {
    height: 1px;
  }
}
</style>
