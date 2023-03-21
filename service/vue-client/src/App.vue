<template>
  <div id="app" class="App">
    <main-header></main-header>
    <main class="MainContent" id="main">
      <router-view/>
    </main>
    <main-footer/>
  </div>
</template>

<script>
import MainHeader from '@/components/shared/MainHeader';
import MainFooter from '@/components/shared/MainFooter';
import 'normalize.css';

export default {
  name: 'App',
  components: {
    'main-header': MainHeader,
    'main-footer': MainFooter,
  },
};
</script>

<style lang="scss">

/*---------------------------*
* Base
*----------------------------*/

html {
  scroll-behavior: smooth;
  font-size: 62.5%;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: auto;
  -moz-osx-font-smoothing: auto;
}

body {
  font-family: $sans-serif;
  line-height: 1.6;
  font-weight: 400;
  font-size: $font-base;
  background: $white;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/*---------------------------*
* Global classes
*----------------------------*/

.MainContent {
  height: calc(100% - 50px);
  margin: 0 auto;
  width: 95%;
  flex: 1 0 auto;
  transition: margin-left .5s;
}

.vertical-wrapper {
  margin-top: 40px;
  margin-bottom: 50px;

  @media (max-width: 500px) {
    margin-top: 20px;
  }
}

.horizontal-wrapper {
  width: 100%;
  max-width: $screen-lg;
  margin-left: auto;
  margin-right: auto;
}

.divided-section {
  margin-top: 1.5em;
  margin-bottom: 1.5em;
  border: 0;
  border-top: 2px solid $greyLight;
}

.heading {
  text-transform: uppercase;
  font-weight: 600;

  &-lg {
    font-size: 2.2rem;
  }

  &-md {
    font-size: 1.8rem;
  }
  &-sm {
    font-size: 1.6rem;
  }

  &-xs {
    font-size: 1.4rem;
  }
}

.bold {
  font-weight: 700;
}

*:focus {
  outline: 2px solid transparent;
}
.user-is-tabbing *:focus {
  outline: 2px solid #003784;
  outline: auto rgba(19, 73, 150, 0.5)
}

/*---------------------------*
* Elements
*----------------------------*/

h1, h2, h3, h4, h5 {
  font-weight: 400;
}

a {
  color: $linkColor;

  &:visited {
    color: $linkVisited;
  }
}

label,
legend {
  font-weight: 600;
  margin: 0 5px 10px 0;
  display: inline-block;
  cursor: inherit;

  &.is-inline,
  & .is-inline {
    margin-left: 10px;
  }
}

legend {
    float: left;

   & ~ * {
        clear: both;
    }
}

input,
textarea {
  box-sizing: border-box;
  border: 1px solid $greyLight;
  padding: 7px;
  background: $white;
  margin-bottom: 10px;
  border-radius: 4px;

  &:focus {
    border-color: $brandPrimary;
  }
}

fieldset {
  border: none;
  padding: 1rem 0;
  margin: 0;
}

/*---------------------------*
* Buttons
*----------------------------*/

.btn {
  margin: 10px 10px 10px 0;
  border: 0;
  border-radius: 4px;
  background: $brandPrimary;
  color: $white;
  padding: 10px 15px;
  -webkit-appearance: none;
  cursor: pointer;
  font-weight: 600;
  text-transform: uppercase;
  transition: background-color 0.2s ease, opacity .2s ease;;
  opacity: 1;

  &:hover,
  &:focus {
    background-color: $darkBlue;
  }

  &--warning {
    background-color: $danger;

    &:hover,
    &:focus {
      background-color: $dangerAlt;
    }
  }

  &.disabled {
    opacity: 0.5;
    pointer-events: none;
  }
}

/*---------------------------*
* Misc
*----------------------------*/

.vue-simple-spinner {
  border-color: $brandPrimary $mark $mark !important;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity .3s ease;
}

.fade-enter,
.fade-leave-to {
  opacity: 0;
}

.error {
  color: $dangerAlt;
  background-color: $dangerBg;
  padding: 5px;
  border-radius: 4px;

  &.is-inline {
    margin-left: 1rem;
  }
}

.flex {
  display: flex;
}

// disable smooth scroll to make e2e test work properly
.cypress-tests {
  scroll-behavior: inherit;
}

</style>
