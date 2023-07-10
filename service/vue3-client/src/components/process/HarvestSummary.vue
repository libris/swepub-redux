<script>
import { defineAsyncComponent } from 'vue';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';

const ChevronToggle = defineAsyncComponent(() => import('@/components/shared/ChevronToggle.vue'));
const HarvestRejected = defineAsyncComponent(() => import('@/components/process/HarvestRejected.vue'));

export default {
  name: 'harvest-summary',
  components: {
    ChevronToggle,
    HarvestRejected,
  },
  props: {
    harvestData: {
      type: Object,
      required: true,
    },
    expandable: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      // if not expandable, expandable content will always show
      expanded: !this.expandable,
      userExpandedOnce: false,
    };
  },
  computed: {
    harvestId() {
      if (this.harvestData.hasOwnProperty('harvest_id')) {
        return this.harvestData.harvest_id;
      } return null;
    },
    start() {
      if (this.harvestData.hasOwnProperty('start_timestamp')) {
        return this.harvestData.start_timestamp;
      } return false;
    },
    successes() {
      if (this.harvestData.hasOwnProperty('successes') && this.harvestData.successes > 0) {
        return this.harvestData.successes;
      } return false;
    },
    rejected() {
      if (this.harvestData.hasOwnProperty('rejected') && this.harvestData.rejected > 0) {
        return this.harvestData.rejected;
      } return false;
    },
    failed() {
      if (this.harvestData.hasOwnProperty('failed_timestamp')) {
        return this.harvestData.failed_timestamp;
      } return false;
    },
    canExpand() {
      // card is allowed to expand AND has additional data to show
      return this.expandable && (this.rejected || this.failed);
    },
  },
  methods: {
    toggleExpanded() {
      if (this.canExpand) {
        this.expanded = !this.expanded;
        this.userExpandedOnce = true;
      }
    },
  },
  filters: {
    formatUTCDate(date) {
      if (date) {
        dayjs.extend(utc);
        return dayjs.utc(date).format();
      } return date();
    },
    toLocale(num) {
      if (num && typeof num === 'number') {
        return num.toLocaleString();
      } return num;
    },
  },
  mounted() {
  },
  watch: {
  },
};
</script>

<template>
  <div class="HarvestSummary">
    <div class="HarvestSummary-card"
      :class="{'is-expandable' : canExpand, 'expanded' : expanded}"
      @click.stop="toggleExpanded">
      <ul class="HarvestSummary-list">
        <li class="HarvestSummary-item">
          <font-awesome-icon
            class="icon"
            :icon="['far', 'clock']"
            role="presentation"
            size="lg"/>
          <span class="label">Hämtning påbörjad:</span>
          <span>{{ start | formatUTCDate }}</span>
        </li>
        <li class="HarvestSummary-item" v-if="successes">
          <font-awesome-icon
            class="icon"
            :icon="['fa', 'long-arrow-alt-right']"
            role="presentation"
            size="lg"/>
          <span class="label">Hämtade poster:</span>
          <span>{{ successes | toLocale }}</span>
        </li>
        <li v-else class="HarvestSummary-item" aria-hidden="true"></li>
        <li class="HarvestSummary-item" v-if="rejected">
          <font-awesome-icon
            class="icon danger"
            :icon="['far', 'times-circle']"
            role="presentation"
            size="lg"/>
          <span class="label">Avvisade poster:</span>
          <span>{{ rejected | toLocale }}</span>
        </li>
        <li v-else class="HarvestSummary-item" aria-hidden="true"></li>
        <li class="HarvestSummary-item" v-if="failed">
          <font-awesome-icon
            class="icon danger"
            :icon="['fa', 'exclamation-circle']"
            role="presentation"
            size="lg"/>
          <span class="label">Avbruten</span>
        </li>
        <li v-else class="HarvestSummary-item" aria-hidden="true"></li>
      </ul>
      <div class="HarvestSummary-toggleContainer" v-if="canExpand">
        <chevron-toggle @input="toggleExpanded"
          :value="expanded"
          :ariaControls="`summary-collapse-${harvestId}`"/>
      </div>
    </div>
    <div class="HarvestSummary-collapsible"
      :class="{'collapsed' : !expanded, 'bordered' : expandable}"
      :id="`summary-collapse-${harvestId}`">
      <p v-if="failed" role="alert" aria-atomic="true">
        <span class="error">
          Hämtningen misslyckades
          {{ failed | formatUTCDate }}{{rejected ? '. Visar poster som bearbetats hittills.' : ''}}
          </span></p>
      <!-- get this data once on-demand, if user toggles card -->
      <harvest-rejected v-if="userExpandedOnce && rejected" :harvestId="harvestId"/>
    </div>
  </div>
</template>

<style lang="scss">
.HarvestSummary {

  &-card {
    padding: 1em;
    border: 1px solid $greyLight;
    display: flex;
    transition: background-color 0.2s ease;

    &.is-expandable {
      cursor: pointer;

      &:hover,
      &.expanded {
        background-color: #f7f7f7;
      }
    }
  }

  &-list {
    list-style-type: none;
    line-height: 2em;
    padding: 0;
    margin: 0;
    display: flex;
    flex-wrap: wrap;
  }

  &-item {
    min-width: 200px;
    margin-right: 1.5em;

    & > * {
      margin-right: 5px;
    }

    & .label {
      font-weight: 600;
    }
  }

  &-toggleContainer {
    display: flex;
    flex: 1;
    justify-content: flex-end;
  }

  & .icon {
    margin-right: 10px;

    &.danger {
      color: $danger;
    }
  }

  &-collapsible {

    &.bordered {
      padding: 1em;
      border-width: 0px 1px 1px 1px;
      border-style: solid;
      border-color: $greyLight;
    }

    &.collapsed {
      display: none;
    }
  }

  @media (max-width: $screen-md) {
    &-list {
      flex-direction: column;
    }
  }
}
</style>
