<script>
import { mapGetters } from 'vuex';
import logoWhite from '@/assets/img/logotyp_vit.svg';

export default {
  name: 'main-footer',
  data() {
    return {
      logo: {
        src: logoWhite,
        alt: 'Kungliga bibliotekets logotyp',
      },
    };
  },
  computed: {
    ...mapGetters([
      'settings',
    ]),
  },
};
</script>

<template>
  <footer class="MainFooter">
    <div class="MainFooter-container">
      <div class="MainFooter-logoWrapper">
        <img class="MainFooter-logo" :src="logo.src" :alt="logo.alt"/>
      </div>
      <nav class="MainFooter-nav" aria-label="Meny sidfot">
        <div class="MainFooter-group">
          <div class="MainFooter-headerWrap">
            <h2 class="MainFooter-header heading heading-md">Information</h2>
          </div>
          <div class="MainFooter-linksWrap">
            <ul class="MainFooter-links">
              <li><a href="https://www.kb.se/swepub">Om Swepub</a></li>
              <li><a href="https://www.kb.se/samverkan-och-utveckling/libris/librissamarbetet/sandlistor.html">Sändlistor</a></li>
              <li><a href="https://www.kb.se/swepub-versionsinformation">Versionsinformation</a></li>
              <li><a :href="`${settings.apiPath}/apidocs/`">API-dokumentation</a></li>
            </ul>
            <ul class="MainFooter-links">
              <li><a href="https://www.kb.se/swepub-ordlista">Swepub ordlista</a></li>
              <li><a href="https://www.kb.se/om-oss/hantering-av-personuppgifter.html#Librisswepub">Om dataskydd (GDPR)</a></li>
              <li><a href="https://www.kb.se/digital-tillganglighet">Tillgänglighetsredogörelse</a></li>
            </ul>
          </div>
        </div>
        <div class="MainFooter-group">
          <div class="MainFooter-headerWrap">
            <h2 class="MainFooter-header heading heading-md">Kontakt</h2>
          </div>
          <div class="MainFooter-linksWrap">
            <ul class="MainFooter-links">
              <li><a href="mailto:libris@kb.se">libris@kb.se</a></li>
              <li>
                <font-awesome-icon aria-label="Twitter icon"
                class="MainFooter-icon" :icon="['fab', 'twitter']"/>
                <a href="https://twitter.com/swepub">Swepub på Twitter</a></li>
            </ul>
          </div>
        </div>
      </nav>
    </div>
  </footer>
</template>

<style scoped lang="scss">
.MainFooter {
  background-color: $dark;
  padding: 20px 0;
  color: $white;
  width: 100%;

  &-container {
    width: 95%;
    max-width: $screen-lg;
    margin: auto;
    display: flex;
  }

  &-logoWrapper {
    flex-basis: 20%;
  }

  &-logo {
    width: 120px;
    height: auto;
  }

  &-nav {
    display: flex;
    flex-wrap: wrap;
  }

  &-group {
    margin: 0 3em;
  }

  &-header {
    font-weight: initial;
    padding: 0 1em 1rem 0;
    border-bottom: 1px solid $white;
    display: inline-block;
  }

  &-linksWrap {
    display: flex;
    flex-wrap: wrap;
  }

  &-links {
    list-style-type: none;
    font-weight: 300;
    padding: 0;
    margin: 0 3em 0 0;
    line-height: 2em;

    &:last-of-type {
      margin-right: 0;
    }

    & li a {
      color: $white;
      word-break: break-word;
      hyphens: auto;
    }
  }

  &-links:last-of-type {
    margin-right: 0;
  }

  &-icon {
    margin-right: 5px;
  }

  @media (max-width: $screen-md) {
    padding-bottom: 30px;

    &-logo {
      width: 100px;
      margin-left: -10px;
    }

    &-group {
      margin: 0 1em;
    }
  }
}
</style>
