<script>
const FlagCard = () => import('@/components/process/FlagCard.vue');
const HelpBubble = () => import('@/components/shared/HelpBubble.vue');

export default {
  name: 'FlagPicker',
  components: {
    FlagCard,
    HelpBubble,
  },
  props: {
    flagType: { // i.e: validation_flags, enrichment_flags, normalization_flags
      type: String,
      default: '',
    },
    target: { // what prop in resultData to display. Ie invalid, normalized, enriched
      type: String,
      default: '',
    },
    resultData: {
      type: Object,
      default: () => {},
    },
    expandable: {
      type: Boolean,
      default: false,
    },
    selectable: {
      type: Boolean,
      default: true,
    },
    query: {
      type: Object,
    },
  },
  data() {
    return {
      flagList: [],
      isExpanded: false,
    };
  },
  computed: {
    itHasFlags() {
      return this.flagList.length > 0;
    },
    chosenFlags() {
      return this.flagList.filter((item) => item.checked === true);
    },
    allIsPicked() {
      return this.chosenFlags.length === this.flagList.length;
    },
  },
  methods: {
    mapFlags(flagObj) {
      if (flagObj && typeof flagObj === 'object') {
        return Object.keys(flagObj)
          .filter((key) => this.resultData[key].hasOwnProperty(this.target))
          .map((key) => ({
            count: this.resultData[key][this.target],
            name: key,
            // check box on page load based on this.query (passed on from router)
            checked: !!(this.query.hasOwnProperty(this.flagType)
            && this.query[this.flagType].indexOf(`${key}_${this.target}`) > -1),
          }));
      } return [];
    },
    flagToggled(index) {
      this.flagList[index].checked = !this.flagList[index].checked;
    },
    toggleAll() {
      let checkStatus;
      if (this.allIsPicked) {
        checkStatus = false;
      } else checkStatus = true;

      Object.keys(this.flagList).forEach((flag) => {
        this.flagList[flag].checked = checkStatus;
      });
    },
  },
  mounted() {
    this.flagList = this.mapFlags(this.resultData);
  },
  watch: {
    resultData: {
      immediate: true,
      handler(val) {
        this.flagList = this.mapFlags(val);
      },
    },
    chosenFlags(value) {
      const mappedValue = value.map((flag) => `${flag.name}_${this.target}`);
      const joined = mappedValue.join(',');
      this.$emit('change', this.flagType, joined);
    },
  },
};
</script>

<template>
<fieldset class="FlagPicker" :aria-labelledby="`header-${flagType}`">
  <div class="FlagPicker-heading">
    <h3 class="FlagPicker-header heading heading-sm"
      :id="`header-${flagType}`"
      :class="{'is-expandable' : expandable}"
      @click="isExpanded = !isExpanded">
      <slot name="title">
        Title not provided
      </slot>
    </h3>
    <span class="FlagPicker-expand"
      v-if="expandable && itHasFlags"
      :class="{'is-expanded' : isExpanded}"
      @keyup.enter="isExpanded = !isExpanded"
      role="button"
      aria-label="expandera">
      <font-awesome-icon :icon="['fa', 'chevron-right']"/>
    </span>
    <help-bubble :bubbleKey="flagType"/>
  </div>
  <div v-if="!itHasFlags" class="FlagPicker-body">
    <span role="status" aria-live="polite">
      <slot name="noflags"></slot>
    </span>
  </div>
  <div v-else class="FlagPicker-body" v-show="!expandable || isExpanded">
    <div class="FlagPicker-descr">
      <div class="FlagPicker-checkAll"
        v-if="selectable"
        @click="toggleAll">
        <font-awesome-layers role="checkbox"
          tabindex="0"
          @keyup.enter="toggleAll"
          :aria-checked="allIsPicked ? 'true' : 'false'"
          :aria-labelledby="`check-all-${flagType} header-${flagType}`">
          <font-awesome-icon aria-label="checkbox"
          v-if="!allIsPicked" :icon="['far', 'square']" size="lg"/>
          <font-awesome-icon aria-label="checkbox"
          v-else :icon="['far', 'check-square']" size="lg"/>
        </font-awesome-layers>
        <label class="FlagPicker-label is-inline"
          :id="`check-all-${flagType}`">Välj samtliga</label>
      </div>
    </div>
    <div class="FlagPicker-list">
      <FlagCard
        v-for="(flag, index) in flagList"
        :key="index"
        :data="flag"
        :flagType="flagType"
        :selectable="selectable"
        @toggle="flagToggled(index)"/>
    </div>
  </div>
</fieldset>

</template>

<style lang="scss">
.FlagPicker {
  margin-top: 2em;
  padding: 0;
  background-color: $light;
  border-bottom: 1px solid $shadow;

  &-descr {
    margin-bottom: 1.5em;
  }

  &-heading {
    display: flex;
    align-items: center;
    padding: 1em;

    &.is-expandable {
      cursor: pointer;
    }
  }

  &-header {
    margin: 0 5px 0 0;
  }

  &-expand {
    display: inline-block;
    margin: 0 0.5em;
    transition: transform 0.1s ease;

    &.is-expanded {
      transform: rotate(90deg);
    }
  }

  &-body {
    padding: 0 1em 1em;
  }

  &-checkAll {
    display: inline-block;
    padding: 10px;
    border: 1px solid $greyLight;
    border-radius: 4px;
    cursor: pointer;
  }

  &-label {
    margin: 0;
  }

  &-list {
    @supports (display: grid) {
      display: grid;
      grid-column-gap: 2em;
      grid-row-gap: 2em;
      grid-template-columns: repeat(auto-fill, minmax(200px, auto));
    }
    /* flexbox fallback */
    display: flex;
    flex-wrap: wrap;
  }
}
</style>
