<script>
export default {
  name: 'not-found',
  components: {
  },
  props: {
  },
  data() {
    return {};
  },
  computed: {
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
  <div class="NotFound vertical-wrapper horizontal-wrapper">
    <h1>404</h1>
    <p role="alert">Sidan <span class="NotFound-path">{{$route.path}}</span> kunde inte hittas</p>
    <div>
      <a href="/">Tillbaka till Swepubs startsida</a>
    </div>
  </div>
</template>

<style lang="scss">
:root {
.NotFound {
  &-path {
    padding: 2px 4px;
    border-radius: 4px;
    background-color: $dangerBg;
  }
}
}
</style>
