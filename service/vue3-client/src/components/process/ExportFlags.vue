<script>
import { defineAsyncComponent } from 'vue';
import { mapState } from 'pinia';
import Helptexts from '@/assets/json/helptexts.json';
import * as Network from '@/utils/Network';
import ExportMixin from '@/components/mixins/ExportMixin.vue';
import VueSimpleSpinner from 'vue-simple-spinner';
import { useSettingsStore } from '@/stores/settings';

const ExportButtons = defineAsyncComponent(() => import('@/components/shared/ExportButtons.vue'));
const PaginationComponent = defineAsyncComponent(() => import('@/components/shared/PaginationComponent.vue'));
const PreviewCard = defineAsyncComponent(() => import('@/components/process/PreviewCard.vue'));

export default {
  name: 'export-flags',
  mixins: [ExportMixin],
  components: {
    VueSimpleSpinner,
    ExportButtons,
    PaginationComponent,
    PreviewCard,
  },
  props: {
    query: {
      type: Object,
    },
  },
  data() {
    return {
    };
  },
  computed: {
    ...mapState(useSettingsStore, ['apiPath']),
    apiEndpoint() {
      return `${this.apiPath}${this.$route.fullPath}`;
    },
    exportDescr() {
      return Helptexts.dataQuality.export_descr;
    },
    previewInfo() {
      const totalPosts = parseInt(this.previewData.total);
      const firstPostOnPage = parseInt(this.currentOffset) + 1;
      let lastPostOnPage = parseInt(this.currentOffset) + parseInt(this.previewLimit);
      if (lastPostOnPage > totalPosts) {
        lastPostOnPage = totalPosts;
      }
      const hits = totalPosts === 1 ? 'post' : 'poster';
      return `Visar ${firstPostOnPage}-${lastPostOnPage} av ${totalPosts} ${hits}`;
    },
    exportAllowed() {
      if (this.previewData && (this.exportLoading || this.exportLimitExceededWarning)) {
        return false;
      } return true;
    },
  },
  methods: {
    fetchData(type, success, fail, acceptHeader) {
      let responseHeader = null;
      let url = this.apiEndpoint;
      if (type === 'preview') {
        const limit = `&limit=${this.previewLimit}`;
        url += limit;
        // send back the 'link' header for pagination
        responseHeader = 'link';
      }
      if (type === 'prev' || type === 'next') {
        const pagUrl = this.pagination[type].url;
        if (!pagUrl) {
          return fail('Pagination link not found');
        } url = pagUrl;
        responseHeader = 'link';
      }
      if (type === 'export') {
        // customize parameters for flags export
      }
      return Network.get(url, acceptHeader, responseHeader)
        .then((response) => {
          if (response.statusCode === 200) {
            success(response);
          } else {
            response.json().then((json) => {
              fail(json.errors.join(', '));
            })
              .catch(() => { // no json error
                fail(response.statusText);
              });
          }
        }).catch((err) => fail(err));
    },
    getFileName(fileType) {
      let interval = '';
      if (this.previewData.from && this.previewData.to) {
        interval = `_${this.previewData.from}-${this.previewData.to}`;
      }
      return `${this.previewData.code}${interval}.${fileType}`;
    },
  },
  mounted() {
    this.getPreview();
  },
  watch: {
  },
};
</script>

<template>
<section class="ExportFlags horizontal-wrapper"
  aria-labelledby="preview-heading"
  ref="previewSection"
  :aria-busy="previewLoading"
  aria-live="polite">
  <!-- loading -->
  <!-- <vue-simple-spinner v-if="previewLoading" class="ExportFlags-previewLoading"/> -->
  <div v-if="previewLoading">spinner</div>
  <!-- error -->
  <div v-else-if="previewError">
    <p class="error" role="alert" aria-atomic="true">{{previewError}}</p>
  </div>
  <!-- has preview data -->
  <template v-else>
    <hr class="divided-section">
    <h2 id="preview-heading" class="heading heading-md">
      Förhandsgranskning av export
    </h2>
    <!-- no hits -->
    <p v-if="previewData.total === 0">
      Inga träffar</p>
    <!-- export limit exceeded -->
    <div v-else-if="exportLimitExceededWarning">
      <span class="error" role="alert" aria-atomic="true">{{exportLimitExceededWarning}}</span>
    </div>
    <!-- export possible -->
    <div v-else>
      <p class="ExportFlags-descr" id="export-flags-descr" v-html="exportDescr"></p>
      <!-- export btns -->
      <export-buttons :exportLoading="exportLoading"
        :exportAllowed="exportAllowed"
        :exportError="exportError"
        @export-json="exportJson"
        @export-csv="exportCsv"
        @export-tsv="exportTsv"/>
      <div class="ExportFlags-previewControl" :class="{'is-loading' : paginationLoading}">
        <!-- hits info -->
        <p class="bold" role="status">{{previewInfo}}</p>
        <!-- pagination -->
        <pagination-component v-if="pagination"
          :pagination="pagination"
          :error="paginationError"
          @go="paginate"/>
      </div>
      <!-- pagination loader -->
      <!-- <vue-simple-spinner v-if="previewLoading" class="ExportFlags-previewLoading"/> -->
      <div v-if="previewLoading">spinner</div>
      <!-- preview cards -->
      <ol v-else class="ExportFlags-cardList">
        <preview-card v-for="(item, index) in previewData.hits"
          :key="`item-${index}`"
          :cardData="item"
          aria-label="resultatlista"/>
      </ol>
      <!-- pagination -->
      <div class="ExportFlags-previewControl" :class="{'is-loading' : paginationLoading}">
        <p class="bold" role="status"></p>
        <pagination-component v-if="pagination"
          :pagination="pagination"
          @go="paginate"
          ariaLabel="sidfot"/>
      </div>
    </div>
  </template>
</section>
</template>

<style lang="scss">
.ExportFlags {
  margin-bottom: 3em;

  &-previewLoading {
    margin-top: 2em;
  }

  &-descr {
    max-width: $screen-md;
  }

  &-previewControl {
    display: flex;
    justify-content: space-between;
    align-items: baseline;

    &.is-loading {
      visibility: hidden;
    }
  }

  &-cardList {
    list-style-type: none;
    padding: 0;
    margin: 0;
  }
}
</style>
