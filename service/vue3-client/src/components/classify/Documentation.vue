<script>
import Helptexts from '@/assets/json/helptexts.json';

export default {
  name: 'classify-documentation',
  data() {
    return {
    };
  },
  computed: {
    classify_doc() {
      return Helptexts.classify.documentation;
    },
  },
};
</script>

<template>
  <section class="Documentation"
    id="about-section"
    role="tabpanel"
    aria-labelledby="about-tab"
    v-html="classify_doc">
  </section>
</template>

<style lang="scss">

.Documentation {
  max-width: $screen-md;

  & strong {
    font-weight: 700;
    margin-bottom: 0;

    & + p {
      margin-top: 0;
    }
  }
}
</style>
