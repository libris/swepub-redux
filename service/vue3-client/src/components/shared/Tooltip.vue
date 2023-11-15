<script setup>
import { toRefs } from 'vue';

const props = defineProps({
  label: {
    type: String,
    required: true,
  },
});

const { label } = toRefs(props);
</script>

<template>
  <div class="tooltip" :label="label" v-tooltip="label">
    <slot />
  </div>
</template>

<style lang="scss">
.tooltip {
  display: inline-flex;
}
</style>
