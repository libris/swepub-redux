<script>
/*

  HOW TO USE:
  This component can show a tablist and emit an event on tab click.

  Props:
    * Tabs    - Expects an array of tab-objects
    * Active  - Expects a string matched against the id on the tab-object and put as active.
    * Link    - If true, component expects tab-objects to have a link prop.
                It will then render a <router-link> instead of emitting an event.

  Tab-Objects:
    A tab object needs two things.
      * id   -  identifier, used when emitting the go-event and to match against the "active" prop.
      * text -  A fancy text for your tab, which should be in english. The component will
        automatically try to translate this text to the users language, based on the i18n file.
      * html -  (Optional) Raw html for the item, will replace 'text'

    Example tab-object:
      {'id': 'MyTab1', 'text': 'My tab text' }
      {'id': 'MyTab1', 'html': 'My <strong>tab</strong> text' }

  The go-event:
    If a tab is clicked, it will emit an event with the id on the tab.
    It's up to you to add a handler to this. See example below.

  Example use:
      <tab-menu @go="myHandler" :tabs="[
        {'id': 'MyTab1', 'text': 'My tab text' },
        {'id': 'MyOtherTab', 'text': 'My other text' }
      ]" :active="myActivePageVariable"></tab-menu>

*/

export default {
  name: 'tab-menu',
  props: {
    tabs: {
      default: () => [],
      type: Array,
    },
    active: {
      type: String,
      default: '',
    },
    link: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
    };
  },
  methods: {
    go(name) {
      this.$emit('go', name);
    },
  },
  computed: {
  },
  components: {
  },
};
</script>

<template>
  <div class="TabMenu">
    <div v-if="!link" class="TabMenu-tabList" role="tablist" ref="tablist">
      <span class="TabMenu-tab"
        v-for="item in tabs"
        tabindex="0"
        :key="item.id"
        @click="go(item.id)"
        @keyup.enter="go(item.id)"
        :class="{'is-active': active === item.id }"
        role="tab"
        :aria-selected="active === item.id ? 'true' : 'false'">
          <span v-if="item.html"
            :id="`${item.id}-tab`"
            v-html="item.html"
            class="TabMenu-tabText"></span>
          <span v-else
            :id="`${item.id}-tab`"
            class="TabMenu-tabText">{{item.text}}</span>
      </span>
    </div>
    <ul v-else class="TabMenu-tabList" role="tablist" ref="tablist">
      <li v-for="item in tabs"
        class="TabMenu-linkContainer"
        :key="item.id"
        role="tab"
        :aria-selected="active === item.id ? 'true' : 'false'">
        <router-link class="TabMenu-tab"
          :class="{'is-active': active === item.id }"
          :to="item.link">
          <span :id="item.id" v-if="item.html" v-html="item.html" class="TabMenu-tabText"></span>
          <span :id="item.id" v-else class="TabMenu-tabText">{{item.text}}</span>
        </router-link>
      </li>
    </ul>
  </div>
</template>

<style lang="scss">

.TabMenu {
  display: block;
  opacity: 1;
  transition: opacity 0.25s ease;
  position: relative;

  &-tabList {
    margin: 0 0 10px -10px;
    padding: 0;
    white-space: nowrap;
    overflow: hidden;
  }
  &-underline {
    display: inline-block;
    transition: all 0.25s ease .025s;
    position: relative;
    height: 3px;
    top: 0.5em;
    margin: 0px;
    min-width: 5px;
    border: none;
    background-color: $brandPrimary;
  }

  &-linkContainer {
    display: inline-block;
  }

  &-tab {
    cursor: pointer;
    text-decoration: none;
    position: relative;
    display: inline-block;
    padding: 5px 10px;
    color: $greyDarker;
    font-weight: 600;
    font-size: 16px;
    font-size: 1.6rem;
    margin: 0 0 5px 0;
    text-transform: uppercase;
    transition: color 0.2s ease;
    border: dashed transparent;
    border-width: 1px 0px 1px 0px;
    white-space: nowrap;

    @media (min-width: $screen-md) {
      font-size: 18px;
      font-size: 1.8rem;
    }

    @media (max-width: 500px) {
      font-size: inherit;
    }

    &:hover,
    &:focus {
      color: $brandPrimary;
      text-decoration: none;
    }
    &.is-active {
      color: $black;
      text-decoration: none;

      & .TabMenu-tabText {
        border-bottom: 2px solid $brandPrimary;

        @media (min-width: $screen-md) {
          border-bottom-width: 3px;
        }
      }
    }
  }
}
</style>
