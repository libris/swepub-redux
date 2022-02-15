<script>
/**
 * Component to render recordId in table (link + tooltip + dedup indicator)
 * Props:
 * deduped - (function) pass a function what check if item is deduped
 */
import { mapGetters } from 'vuex';
import { VTooltip } from 'v-tooltip';

export default {
  name: 'table-data-id',
  components: {
  },
  directives: {
    tooltip: VTooltip,
  },
  props: {
    tdKey: {
      type: String,
      required: true,
    },
    tdValue: {
      type: String,
      required: true,
    },
    trData: {
      type: Object,
      default: null,
    },
    deduped: {
      type: Function,
      default: null,
    },
  },
  data() {
    return {
      dedupTooltipText: 'Sammanslagen post. Bidragande poster och organisationer syns under Sammanslagna ID och Organisation.',
      linkTooltipText: 'Visa JSON',
      target: {
        target: '_blank',
        rel: 'noopener noreferrer',
      },
    };
  },
  computed: {
    ...mapGetters([
      'settings',
    ]),
    linkUrl() {
      if (this.service) {
        return `${this.settings.apiPath}/${this.service}/publications/${this.tdValue}`;
      }
      return null;
    },
    service() {
      if (this.$route.name === 'Bibliometrics' || this.$route.name === 'Process') {
        return this.$route.name.toLowerCase();
      } return null;
    },
    isBibliometrics() {
      return this.service === 'bibliometrics';
    },
    isDeduped() {
      return this.deduped && this.deduped(this.trData);
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
  <span class="TableDataId">
    <span class="TableDataId-iconWrapper" v-if="isDeduped && isBibliometrics">
      <font-awesome-icon
        :icon="['fas', 'copy']"
        :aria-label="dedupTooltipText"
        v-tooltip.right-start="{
          content: dedupTooltipText,
          classes: 'TableDataId-tooltip',
        }"/>
    </span>
    <span v-if="!isDeduped && isBibliometrics" class="TableDataId-iconWrapper">
      <!-- empty placeholder -->
    </span>
    <span v-if="linkUrl">
      <span class="TableDataId-iconWrapper">
        <font-awesome-icon title="Öppnar i ny flik" :icon="['fa', 'external-link-alt']"/>
      </span>
      <a :href="linkUrl"
        v-tooltip.top="{
          content: linkTooltipText,
          classes: 'TableDataId-tooltip',
        }"
        v-bind="target"
        :title="this.linkUrl">{{tdValue}}</a>
    </span>
    <span v-else>{{tdValue}}</span>
  </span>
</template>

<style lang="scss">
.TableDataId {
  &-iconWrapper {
    width: 20px;
    display: inline-block;
    color: $greyDarker;
  }

  &-tooltip {
    max-width: 300px;

    &[x-placement^="right"] {
      margin-left: 10px;
    }

    & .tooltip-inner {
      color: $white;
      background: $greyDarker;
      border: none;
      padding: 5px 10px;
    }

    & .tooltip-arrow {
      border: 1px solid $greyDarker;
    }

    &[x-placement^="top"] {
      margin-bottom: 10px;

      .tooltip-arrow {
        border-width: 5px 5px 0 5px;
        border-left-color: transparent !important;
        border-right-color: transparent !important;
        border-bottom-color: transparent !important;
        bottom: -5px;
        left: calc(50% - 5px);
        margin-top: 0;
        margin-bottom: 0;
      }
    }
  }
}
</style>
