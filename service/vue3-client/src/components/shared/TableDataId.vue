<script>
/**
 * Component to render recordId in table (link + tooltip + dedup indicator)
 * Props:
 * deduped - (function) pass a function what check if item is deduped
 */
import { useSettingsStore } from '@/stores/settings';
import { mapState } from 'pinia';
import Tooltip from './Tooltip.vue';

export default {
  name: 'table-data-id',
  components: {
    Tooltip,
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
    ...mapState(useSettingsStore, ['apiPath']),
    linkUrl() {
      if (this.service) {
        return `${this.apiPath}/${this.service}/publications/${this.tdValue}`;
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
};
</script>

<template>
  <span class="TableDataId">
    <span class="TableDataId-iconWrapper" v-if="isDeduped && isBibliometrics">
      <Tooltip :label="dedupTooltipText">
        <font-awesome-icon
          :icon="['fas', 'copy']"
          :aria-label="dedupTooltipText"
        />
      </Tooltip>
    </span>

    <span v-if="!isDeduped && isBibliometrics" class="TableDataId-iconWrapper">
      <!-- empty placeholder -->
    </span>

    <span v-if="linkUrl">
      <span class="TableDataId-iconWrapper">
        <font-awesome-icon title="Öppnar i ny flik" :icon="['fa', 'external-link-alt']"/>
      </span>

      <Tooltip :label="linkTooltipText">
        <a :href="linkUrl" v-bind="target" :title="this.linkUrl">
          {{tdValue}}
        </a>
      </Tooltip>
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
}
</style>
