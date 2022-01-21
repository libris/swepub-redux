<script>
import { mapGetters } from 'vuex';

export default {
  name: 'MainNav',
  props: {
    collapsed: {
      type: Boolean,
      default: true,
    },
  },
  data() {
    return {
    };
  },
  methods: {
  },
  computed: {
    ...mapGetters([
      'settings',
    ]),
  },
  mounted() {
  },
};
</script>

<template>
  <nav id="navlinks"
    class="MainNav"
    :class="{'collapse' : collapsed}"
    aria-label="huvudmeny">
    <ul class="MainNav-navList" aria-labelledby="navlinks">
      <li class="MainNav-navItem">
        <a class="MainNav-navLink" href="http://swepub.kb.se/" target="_blank" rel="noopener noreferrer">Sök</a></li>
      <template v-for="item in settings.navigation">
        <router-link class="MainNav-navItem"
          v-if="item.path"
          :to="item.path"
          tag="li"
          :key="item.id">
          <a class="MainNav-navLink">{{ item.label }}</a>
        </router-link>
        <li v-else class="MainNav-navItem" :key="item.id">
          <span class="MainNav-navLink is-disabled">{{ item.label }}</span>
        </li>
      </template>
    </ul>
  </nav>
</template>

<style lang="scss">
.MainNav {
  flex-basis: 100%;
  margin-bottom: 1rem;

  &-navList {
    list-style-type: none;
    height: 100%;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    flex-wrap: wrap;
    font-size: 1.6rem;
  }

  &-navItem {
    display: flex;
    align-items: center;
    min-height: 40px;

    &.router-link-active {
      & a {
        border-bottom: 2px solid $black;
      }

      @media (min-width: $screen-md) {
        background-color: $brandPrimary;

        & a {
          color: $white;
          border-color: $white;
        }
      }
    }
  }

  &-navLink {
    display: block;
    text-decoration: none;
    cursor: pointer;
    margin: 0 1rem;
    color: $black;
    box-sizing: border-box;
    border-bottom: 2px solid transparent;

    &.is-disabled {
      cursor: initial;

      &:hover {
        border-bottom-color: transparent;
      }
    }

    &:hover {
      border-bottom-color: $black;
    }

    &:visited {
      color: $black;
    }
  }

  &.collapse {
    display: none;
  }

  @media (min-width: $screen-md) {
    flex-basis: auto;
    margin-bottom: 0;

    &.collapse {
      display: block;
    }

    &-navList {
      flex-direction: row;
    }
  }
}
</style>
