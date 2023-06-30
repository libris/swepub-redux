<script>

export default {
  name: 'pagination-component',
  components: {
  },
  props: {
    pagination: {
      type: Object,
      default: null,
    },
    error: {
      type: String,
      default: '',
    },
    ariaLabel: {
      // option to distinguish landmarks for a11y
      type: String,
      default: '',
    },
  },
  data() {
    return {};
  },
  computed: {
    hasPrev() {
      return this.pagination && this.pagination.hasOwnProperty('prev');
    },
    hasNext() {
      return this.pagination && this.pagination.hasOwnProperty('next');
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
  <nav class="PaginationComponent" :aria-label="`Paginering ${ariaLabel}`">
    <span v-if="error" class="error" role="alert" aria-atomic="true">{{error}}</span>
    <span class="PaginationComponent-link"
      role="button"
      :aria-disabled="!hasPrev"
      :tabindex="hasPrev ? 0 : -1"
      @click="hasPrev && $emit('go', 'prev')"
      @keyup.enter="hasPrev && $emit('go', 'prev')">&lt; Föregående</span>
    <span class="PaginationComponent-link"
      role="button"
      :aria-disabled="!hasNext"
      :tabindex="hasNext ? 0 : -1"
      @click="hasNext && $emit('go', 'next')"
      @keyup.enter="hasNext && $emit('go', 'next')">Nästa &gt;</span>
  </nav>
</template>

<style lang="scss">
.PaginationComponent {
  white-space: nowrap;

  &-link {
    cursor: pointer;
    font-weight: 600;
    margin-left: 1rem;
    &:hover {
      text-decoration: underline;
    }

    &[aria-disabled=true] {
      color: $inactive;
      pointer-events: none;
    }
  }

}
</style>
