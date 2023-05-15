<script>
import { mapGetters } from 'vuex';
import * as Network from '@/utils/Network';
import ExportMixin from '@/components/mixins/ExportMixin';
import VueSimpleSpinner from 'vue-simple-spinner';

const PaginationComponent = () => import('@/components/shared/PaginationComponent');
const PreviewTable = () => import('@/components/shared/PreviewTable');

export default {
  name: 'harvest-rejected',
  mixins: [ExportMixin],
  components: {
    VueSimpleSpinner,
    PaginationComponent,
    PreviewTable,
  },
  props: {
    harvestId: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      fields: [
        {
          key: 'record_id',
          label: 'Record ID',
          component: 'TableDataMultiLine',
          props: {
            trimAt: 1500,
            lines: 5,
          },
        },
        {
          key: 'errors',
          label: 'Feltyp',
          component: 'TableDataList',
          props: {
            targetKeys: ['error_code'],
          },
        },
        {
          key: 'errors',
          label: 'beskrivning',
          component: 'TableDataList',
          props: {
            targetKeys: ['labelByLang'],
            renderFn: this.errorByLang,
          },
        },
      ],
      exportLimit: 1000000, // no export = should never reach limit
      shouldScroll: false,
    };
  },
  computed: {
    ...mapGetters([
      'settings',
    ]),
    apiPath() {
      return `${this.settings.apiPath}/process/${this.harvestId}/rejected?limit=${this.previewLimit}`;
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
  },
  methods: {
    fetchData(type, success, fail, acceptHeader) {
      let url = this.apiPath;
      if (type === 'prev' || type === 'next') {
        const pagUrl = this.pagination[type].url;
        if (!pagUrl) {
          return fail('Pagination link not found');
        } url = pagUrl;
      }
      return Network.get(url, acceptHeader, 'link')
        .then((response) => {
          if (response.statusCode === 200) {
            success(response);
          } else {
            response.json().then((json) => {
              fail(json.errors.join(', '));
            })
              .catch(() => { // json parse error
                fail(response.statusText);
              });
          }
        }).catch((err) => fail(err));
    },
    errorByLang(props) {
      const lang = this.settings.language;
      let arr = [];
      if (props.hasOwnProperty('tdValue') && Array.isArray(props.tdValue)) {
        arr = props.tdValue.map((el) => {
          if (el.hasOwnProperty('labelByLang') && el.labelByLang.hasOwnProperty(lang)) {
            return el.labelByLang[lang];
          } return '';
        });
      }
      return arr;
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
  <div class="HarvestRejected" :aria-busy="previewLoading" aria-live="polite">
    <!-- loading -->
    <vue-simple-spinner v-if="previewLoading" class="HarvestRejected-previewLoading"/>
    <!-- error -->
    <div v-else-if="previewError">
      <p role="alert" aria-atomic="true"><span class="error">{{previewError}}</span></p>
    </div>
    <!-- if preview data -->
    <template v-else>
      <!-- no hits -->
      <p v-if="previewData.total === 0" class="horizontal-wrapper">Inga träffar</p>
      <!-- preview -->
      <template v-else>
        <div class="HarvestRejected-previewControl" :class="{'is-loading' : paginationLoading}">
          <!-- hits info -->
          <p class="bold" role="status">{{previewInfo}}</p>
          <!-- pagination -->
          <pagination-component v-if="pagination"
            :pagination="pagination"
            :error="paginationError"
            @go="paginate"/>
        </div>
        <!-- pagination loader -->
        <vue-simple-spinner class="HarvestRejected-previewLoading" v-if="paginationLoading" />
        <!-- preview table -->
        <preview-table v-else
          :previewData="previewData"
          :tableCols="selectedFields"
          hitsProp='rejected_publications'
          tableLayout='fixed'/>
        <!-- pagination -->
        <div class="HarvestRejected-previewControl"
          :class="{'is-loading' : paginationLoading}"
          v-if="pagination">
          <p class="bold" role="status"></p>
          <pagination-component :pagination="pagination" @go="paginate" ariaLabel="sidfot"/>
        </div>
      </template>
    </template>
  </div>
</template>

<style lang="scss">
.HarvestRejected {

  &-previewControl {
    display: flex;
    justify-content: space-between;
    align-items: baseline;

    &.is-loading {
      visibility: hidden;
    }
  }

  &-previewLoading {
    margin: 2em;
  }
}
</style>
