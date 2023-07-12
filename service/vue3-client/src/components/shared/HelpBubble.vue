<script setup>
/*
Renders a FA question icon with a v-tooltip on click

PROPS:
bubbleKey - where to look for copy in helpbubbles.json, mapped by [route.name][bubbleKey]
color: color for the icon itself

*/
// import { mixin as clickaway } from 'vue-clickaway';
// import { VTooltip } from 'v-tooltip';
import Helpbubbles from '@/assets/json/helpbubbles.json';
import { useSettingsStore } from '@/stores/settings';
import { useFloating, autoPlacement } from '@floating-ui/vue';
import { computed, ref } from 'vue';
import { useRoute } from 'vue-router';

const $route = useRoute();
let trigger = ref(null);
let floating = ref(null);
const floatingStyles = useFloating(trigger, floating, {
  middleware: [autoPlacement()]
});

const language = useSettingsStore().language;
let isOpen = ref(false);

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
  const tHead = tooltipObj.hasOwnProperty('title') ? `<div class="t-header heading heading-xs">${tooltipObj.title}</div>` : '';
  const tBody = `<div class="t-body">${tooltipObj.text}</div>`;
  return `<div class="t-wrapper">${tHead}${tBody}</div>`;
});

const label = computed(() => {
  let tooltipTitle = '';
  if (tooltipObj.hasOwnProperty('title')) {
    tooltipTitle = tooltipObj.title;
  }

  return `${tooltipTitle} ${labelByLang[language]}`;
})

const toggleTooltip = () => {
  isOpen = !isOpen;
};

const closeTooltip = () => {
  isOpen = false;
};
</script>

    <!-- CONTAINER: @click.stop.prevent="toggleTooltip"
    @keyup.enter.stop.prevent="toggleTooltip"
    v-on-clickaway="closeTooltip" -->


    <!-- ICON: v-tooltip.right-start="{
    content: tooltipHTML,
    trigger: 'manual',
    show: isOpen,
    html: true }" -->

<template>
  <div
    ref="trigger"
    class="HelpBubble"
    role="button"
    :aria-label="label"
    v-if="tooltipObj && tooltipObj.text"
    :style="color ? {color: color} : ''"
    tabindex="0"
  >
    <font-awesome-icon
      :icon="['fas', 'question-circle']"
      :aria-label="label"
      fixed-width
    />
  </div>

  <div ref="floating" :style="{ top: floatingStyles.y.value + 'px', left: floatingStyles.x.value + 'px' }" class="tooltip">
    {{ label }}
  </div>
</template>

<style lang="scss">
.HelpBubble {
  display: inline-block;
  color: $brandPrimary;
  cursor: pointer;
  font-size: $font-base;
}

.tooltip {
  display: block !important;
  z-index: 10000;
  position: absolute;
  top: 0;
  left: 0;

  .tooltip-inner {
    background: $white;
    border: 1px solid $brandPrimary;
    border-radius: 0.25em;
  }

  .tooltip-arrow {
    width: 0;
    height: 0;
    border-style: solid;
    position: absolute;
    margin: 5px;
    border: 1px solid $brandPrimary;
    z-index: 1;
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

  &[x-placement^="bottom"] {
    margin-top: 10px;

    .tooltip-arrow {
      border-width: 0 5px 5px 5px;
      border-left-color: transparent !important;
      border-right-color: transparent !important;
      border-top-color: transparent !important;
      top: -5px;
      left: calc(50% - 5px);
      margin-top: 0;
      margin-bottom: 0;
    }
  }

  &[x-placement^="right"] {
    margin-left: 20px;

    .tooltip-arrow {
      border-width: 5px 5px 5px 0;
      border-left-color: transparent !important;
      border-top-color: transparent !important;
      border-bottom-color: transparent !important;
      left: -5px;
      top: calc(100% - 5px);
      margin-left: 0;
      margin-right: 0;
    }
  }

  &[x-placement^="left"] {
    margin-right: 5px;

    .tooltip-arrow {
      border-width: 5px 0 5px 5px;
      border-top-color: transparent !important;
      border-right-color: transparent !important;
      border-bottom-color: transparent !important;
      right: -5px;
      top: calc(50% - 5px);
      margin-left: 0;
      margin-right: 0;
    }
  }

  &[aria-hidden='true'] {
    visibility: hidden;
    opacity: 0;
    transition: opacity .15s, visibility .15s;
  }

  &[aria-hidden='false'] {
    visibility: visible;
    opacity: 1;
    transition: opacity .15s;
  }

  & .t-wrapper {
    display: flex;
    flex-direction: column;
    max-width: 400px;
    overflow-wrap: break-word;
    word-wrap: break-word;
    hyphens: auto;

    & .t-header {
      background-color: $blue;
      color: $white;
      padding: 5px 10px;
    }

    & .t-body {
      padding: 5px 10px

    }
  }
}
</style>
