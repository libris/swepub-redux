<script>
/* eslint-disable max-len */
import { useSettingsStore } from '@/stores/settings';
import { mapState } from 'pinia';

export default {
  name: 'preview-card',
  components: {
  },
  props: {
    cardData: {
      type: Object,
      default: () => {},
    },
  },
  data() {
    return {
    };
  },
  computed: {
    ...mapState(useSettingsStore, ['apiPath']),
    jsonLink() {
      if (this.cardData.record_id) {
        return `${this.apiPath}/process/publications/${this.cardData.record_id}`;
      } return null;
    },
  },
  methods: {
  },
  filters: {
    joined(val) {
      if (val && Array.isArray(val)) {
        return val.join(', ');
      } return val;
    },
  },
};
</script>

<template>
  <li class="PreviewCard">
    <!-- meta information about the record -->
    <div class="PreviewCard-meta">
      <p class="recordId heading-sm">{{ cardData.record_id }}</p>
      <p class="year">{{ cardData.publication_year }}</p>
      <div class="links">
        <a v-if="cardData.repository_url"
          class="capital"
          :href="cardData.repository_url"
          target="_blank"
          rel="noopener noreferrer"
          :aria-label="`${cardData.record_id} Orginalpost i arkiv`">
          <font-awesome-icon :icon="['fa', 'external-link-alt']"
            role="presentation"
            aria-hidden="true"/>
          Orginalpost i arkiv
          </a>
        <a v-if="cardData.mods_url"
          class="capital"
          :href="cardData.mods_url"
          target="_blank"
          rel="noopener noreferrer"
          :aria-label="`${cardData.record_id} MODS-post i Swepub`">
          <font-awesome-icon :icon="['fa', 'external-link-alt']"
            role="presentation"
            aria-hidden="true"/>
          MODS-post i Swepub
        </a>
        <a v-if="jsonLink"
          class="capital"
          :href="jsonLink"
          target="_blank"
          rel="noopener noreferrer"
          :aria-label="`${cardData.record_id} Post i JSON`">
          <font-awesome-icon :icon="['fa', 'external-link-alt']"
            role="presentation"
            aria-hidden="true"/>
          Post i JSON
        </a>
      </div>
    </div>
    <!-- flag information -->
    <div class="PreviewCard-flags">
      <div v-for="(flags, flagCat) in cardData.flags"
        :key="`flagtype-${flagCat}`"
        class="PreviewCard-flagCat">
        <!-- construct 'flag type' -->
        <template v-for="(flagList, flagType) in flags">
          <div v-for="(flag, index) in flagList"
            :key="`li-${flagType}-${index}`"
            class="PreviewCard-flag">
            <div class="PreviewCard-flagValue" :class="{'audit' : flagCat === 'audit'}">
              <p class="heading capital">Flaggtyp</p>
              <p>
                <span class="dot" :class="flagCat" aria-hidden="true"></span>
                  {{flagCat}} {{flagType}}
                <template v-if="flag.code">
                  {{flag.code}}
                </template>
                <template v-else>{{flag}}</template>
              </p>
            </div>
            <div v-if="flagCat === 'validation'" class="PreviewCard-flagValue">
              <p class="heading capital">Ofullständiga data</p>
              <p>{{flag.value}}</p>
            </div>
            <template v-else-if="flagCat === 'enrichment'">
              <div class="PreviewCard-flagValue">
                <p class="heading capital">Ursprungliga data</p>
                <p>{{flag.old_value | joined }}</p>
              </div>
              <div class="PreviewCard-flagValue">
                <p class="heading capital">Berikade data</p>
                <template v-if="flag.code === 'add_oa'">
                  <div v-for="(added_oa, index) in flag.new_value"
                            :key="`ul-add_oa-${index}`"
                            class="links">
                    <template>
                      <span v-for="(value, name) in added_oa" :key="`li-add_oa-${name}`">
                        {{ name }}:
                        <a
                            :href="value"
                            target="_blank"
                            rel="noopener noreferrer"
                            :aria-label="`${value} Länk till fulltext, eller information om öppen tillgång-status`">
                          {{ value }}
                        </a>
                      </span>
                    </template>
                  </div>
                </template>
                <template v-else-if="flag.code === 'add_orcid_from_localid'">
                  <p>
                    <a
                      :href="`https://orcid.org/${flag.new_value}`"
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label="Länk till personens ORCID-sida">
                      {{flag.new_value}}
                    </a>
                  </p>
                </template>
                <template v-else-if="flag.code === 'add_license'">
                  <p>
                    <a
                      :href="`${flag.new_value}`"
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label="Länk till licensen">
                      {{flag.new_value}}
                    </a>
                  </p>
                </template>
                <template v-else>
                  <p>{{flag.new_value | joined }}</p>
                </template>
              </div>
            </template>
          </div>
        </template>
      </div>
    </div>
  </li>
</template>

<style lang="scss">
.PreviewCard {
  padding: 1.5em;
  margin-bottom: 1em;
  border: 1px solid $greyLight;
  border-radius: 5px;
  display: flex;

  &-meta {
    min-width: 200px;
    max-width: 260px;
    padding-right: 1em;
    display: flex;
    flex-direction: column;
    border-right: 1px solid $greyLight;

    & .recordId {
      margin: 0;
      font-weight: 600;
      margin-right: 0.5em;
      overflow-wrap: break-word;
    }

    & .year {
      margin-top: 0;
      margin-right: 1em;
    }

    & .links {
      display: flex;
      flex-direction: column;
      margin-top: 5px;
    }
  }

  &-flags {
    flex: 1;
    padding: 0 0 0 1.5em;
  }

  &-flagCat {
    line-height: 1.7em;
    margin-bottom: 1em;

    & .heading {
      display: none;
    }
  }

  &-flag {
    display: flex;

    &:first-of-type .heading {
      display: block;
    }
  }

  &-flagValue {
    flex-basis: 33%;
    max-width: 275px;
    margin-right: 2em;

    // audits have only one col
    &.audit {
      flex-basis: 100%;
      max-width: 100%;
    }

    & .links {
      display: flex;
      flex-direction: column;
    }
  }

  .dot {
    display: inline-block;
    height: 10px;
    width: 10px;
    margin-right: 2px;
    background-color: $grey;
    border-radius: 50%;

    &.validation {
      background-color: $validation;
    }

    &.enrichment {
      background-color: $enrichment;
    }

    &.audit {
      background-color: $audit;
    }
  }

  & .capital {
    font-weight: 500;
    font-size: 12px;
    text-transform: uppercase;

    &.heading {
      color: $greyDarker;
    }
  }

  & p {
    margin: 0;
  }

  @media (max-width: $screen-md) {
    flex-direction: column;

    &-meta {
      max-width: 100%;
      flex-direction: row;
      align-items: baseline;
      padding: 0 0 1.5em 0;
      border: 0;
      flex-wrap: wrap;

      & .year {
        flex: 1;
      }
    }

    &-flags {
      padding: 0;
    }

    &-flagCat {
      margin-bottom: 1.5em;
    }

    &-flag {
      width: 100%;
      flex-direction: column;
      margin-bottom: 1em;

      & .heading {
        display: block;
      }
    }

    &-flagValue {
      max-width: 100%;
      margin-right: 0;
      margin-bottom: 5px;

      &:not(:first-of-type) {
        margin-left: 1em;
      }
    }
  }

  @media (max-width: $screen-xs) {
    &-meta {
      flex-direction: column;
    }
  }
}
</style>
