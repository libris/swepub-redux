<script setup>
/*
Renders a FA question icon with a v-tooltip on click

PROPS:
bubbleKey - where to look for copy in helpbubbles.json, mapped by [route.name][bubbleKey]
color: color for the icon itself
*/
import Helpbubbles from '@/assets/json/helpbubbles.json';
import { Dropdown } from 'floating-vue';
import Tooltip from './Tooltip.vue';
import { useSettingsStore } from '@/stores/settings';
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const $route = useRoute();
const language = useSettingsStore().language;

const labelByLang = {
  swe: 'Hjälp',
  en: 'Help',
};

const props = defineProps({
  bubbleKey: {
    type: String,
    required: true,
  },
  color: {
    type: String,
    required: false,
  },
});

const tooltipObj = computed(() => {
  if (Helpbubbles.hasOwnProperty($route.name)
  && Helpbubbles[$route.name].hasOwnProperty(props.bubbleKey)) {
    return Helpbubbles[$route.name][props.bubbleKey];
  }
  if (Helpbubbles['*'].hasOwnProperty(props.bubbleKey)) {
    // shared bubbles
    return Helpbubbles['*'][props.bubbleKey];
  }
  // eslint-disable-next-line
  console.warn(`Found no help bubble for ${$route.name}.${props.bubbleKey}`);
  return null;
});

const tooltipHTML = computed(() => {
  if (tooltipObj.value == null) {
    return null;
  }

  const tHead = tooltipObj.value.hasOwnProperty('title') ? `<div class="t-header heading heading-xs">${tooltipObj.value.title}</div>` : '';
  const tBody = `<div class="t-body">${tooltipObj.value.text}</div>`;
  return `<div class="t-wrapper">${tHead}${tBody}</div>`;
});

const label = computed(() => {
  let tooltipTitle = '';
  if (tooltipObj.hasOwnProperty('title')) {
    tooltipTitle = tooltipObj.title;
  }

  return `${tooltipTitle} ${labelByLang[language]}`;
});
</script>

<template>
  <Tooltip :label="label">
      <Dropdown>
        <div
          class="HelpBubble"
          role="button"
          v-if="tooltipObj && tooltipObj.text"
          :style="color ? {color: color} : ''"
          tabindex="0"
        >
          <font-awesome-icon
            :icon="['fas', 'question-circle']"
            fixed-width
          />
        </div>

        <template #popper>
          <div class="HelpBubble-inner" v-html="tooltipHTML" />
        </template>
      </Dropdown>
  </Tooltip>
</template>

<style lang="scss">
.HelpBubble {
  display: inline-block;
  color: $brandPrimary;
  cursor: pointer;
  font-size: $font-base;

  &-inner {
    .t-wrapper {
      display: flex;
      flex-direction: column;
      max-width: 400px;
      overflow-wrap: break-word;
      word-wrap: break-word;
      hyphens: auto;

      .t-header {
        background-color: $blue;
        color: $white;
        padding: 5px 10px;
      }

      .t-body {
        padding: 5px 10px
      }
    }
  }
}

.v-popper--theme-dropdown {
  .v-popper__arrow-inner {
    border-color: $blue;
  }
}
</style>
