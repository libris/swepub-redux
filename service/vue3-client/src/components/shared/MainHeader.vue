<script>
import { mapState } from 'pinia';
import { useSettingsStore } from '@/stores/settings';
import blackLogo from '@/assets/img/kb_logo_black.svg';
import MainNav from '@/components/shared/MainNav.vue';

export default {
  name: 'main-header',
  data() {
    return {
      logo: {
        src: blackLogo,
        alt: 'Kungliga bibliotekets logotyp',
      },
      navCollapsed: false,
    };
  },
  computed: {
    ...mapState(useSettingsStore, ['serviceName', 'version']),
  },
  components: {
    'main-nav': MainNav,
  },
  mounted() {
  },
  watch: {
    // eslint-disable-next-line
    '$route.fullPath': function () {
      this.navCollapsed = true;
    },
  },
};
</script>

<template>
  <header class="MainHeader" aria-label="sidhuvud" id="main-header">
    <a id="skip-link" href="#main"><span>Till innehållet</span></a>
    <div class="MainHeader-container">
      <div class="MainHeader-brand" role="banner">
        <div class="MainHeader-logoWrap">
          <router-link to="/">
            <img class="MainHeader-logo" :src="logo.src" :alt="logo.alt"/>
          </router-link>
        </div>
        <div class="MainHeader-serviceWrap">
          <h1 class="MainHeader-serviceName">
            <router-link to="/" class="MainHeader-serviceLink">{{ serviceName }}
              <sup class="MainHeader-version"> {{ version }}</sup>
            </router-link>
          </h1>
        </div>
      </div>
      <span class="MainHeader-toggle"
          role="button"
          tabindex="0"
          @click="navCollapsed = !navCollapsed"
          @keyup.enter="navCollapsed = !navCollapsed"
          aria-controls="navlinks"
          :aria-expanded="!navCollapsed ? 'true' : 'false'"
          :aria-label="!navCollapsed ? 'Minimera meny' : 'Expandera meny'">
          <font-awesome-icon :icon="['fas', navCollapsed ? 'bars' : 'times']"
            role="presentation"
            fixed-width/>
        </span>
      <main-nav :collapsed="navCollapsed"/>
    </div>
  </header>
</template>

<style scoped lang="scss">
.MainHeader {
  width: 100%;
  background-color: $light;
  color: $black;
  border-top: 5px solid $brandPrimary;
  font-weight: 300;

  &-container {
    max-width: $screen-lg;
    width: 95%;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
  }

  #skip-link {
    padding: 5px;
    font-weight: 500;
    position: absolute;
    top: 5px;
    left: -100%;

    &:active, &:focus {
      left: 2px;
    }
  }

  &-brand {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 5px;
  }

  &-logoWrap {
    margin: 0 1em 0rem 0;
    padding: 8px 0;
  }

  &-logo {
    width: 50px;
    height: 50px;
    vertical-align: middle;
  }

  &-serviceName {
    font-weight: 300;
    font-size: 2.4rem;
    line-height: 1.2;
    white-space: nowrap;
  }

  &-serviceLink {
    text-decoration: none;
    border: 0;
    color: $black;

    &:hover {
      color: inherit;
    }
  }

  &-version {
    font-size: 50%;
    color: $greyDarker;
    font-weight: 600;
  }

  &-toggle {
    display: block;
    font-size: 2.3rem;
    cursor: pointer;
    color: $greyDarker;
    height: 30px;
    margin: 0.7em 0;
  }

  @media (min-width: $screen-md) {
    .MainHeader-toggle {
      display: none;
    }
  }
}
</style>
