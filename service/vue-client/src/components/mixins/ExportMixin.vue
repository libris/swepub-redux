<script>
/*
* Shared methods & variables for components that needs preview/export logic
* Data settings can be customized/overwritten locally.
* Components that use this mixin must supply their own...
* - fetchData method, incl success and fail callbacks
* - previewSection ref if scrollIntoView is used
*/

import * as StringUtil from '@/utils/String';
import * as parseLink from 'parse-link-header';

export default {
  name: 'export-mixin',
  components: {
  },
  props: {
  },
  data() {
    return {
      previewData: {},
      previewLoading: false,
      previewError: '',
      exportLoading: false,
      exportError: '',
      paginationLoading: false,
      paginationError: '',
      hitCount: 0,
      // setttings
      previewLimit: 20,
      exportLimit: 9999999,
      shouldScroll: true,
      currentOffset: 0,
    };
  },
  computed: {
    selectedFields() {
      // overwrite locally to support field selection by user
      if (this.fields) {
        return this.fields;
      }
      return [];
    },
    exportLimitExceededWarning() {
      if (this.previewData && (this.hitCount > this.exportLimit)) {
        return `Antalet träffar (${this.hitCount}) överskrider exportgränsen på ${this.exportLimit} poster. Avgränsa sökningen och försök igen.`;
      }
      return false;
    },
    exportAllowed() {
      if (this.previewData && (this.selectedFields.length === 0
      || this.exportLoading || this.exportLimitExceededWarning)) {
        return false;
      } return true;
    },
    pagination() {
      if (this.previewData && this.previewData.hasOwnProperty('link')) {
        return parseLink(this.previewData.link);
      }
      return null;
    },
  },
  methods: {
    getPreview() {
      this.previewLoading = true;
      this.previewData = null;
      this.previewError = '';
      this.exportError = '';

      this.fetchData('preview',
        (response) => { // success
          this.previewLoading = false;
          this.previewData = response;
          this.$nextTick(() => {
            if (this.shouldScroll && this.$refs.previewSection) {
              this.$refs.previewSection.scrollIntoView({ behavior: 'smooth' });
            }
          });
        },
        (err) => { // fail
          this.previewLoading = false;
          this.previewError = `Ett fel inträffade vid förhandsgranskning: ${err}`;
        });
    },
    getHitCount() {
      this.hitCount = 0;

      this.fetchData('hitCount', (response) => { // success
        if (response != null) {
          this.hitCount = response.total;
        }
      });
    },
    paginate(direction) {
      this.paginationLoading = true;
      this.paginationError = '';
      const futureOffset = this.pagination[direction].offset;
      this.fetchData(direction,
        (response) => { // success
          this.paginationLoading = false;
          this.currentOffset = futureOffset;
          this.previewData = response;
        },
        (err) => { // fail
          this.paginationLoading = false;
          this.paginationError = `Kunde inte hämta poster: ${err}`;
        });
    },
    exportJson() {
      this.doExport();
    },
    exportCsv() {
      this.doExport('text/csv');
    },
    exportTsv() {
      this.doExport('text/tab-separated-values');
    },
    doExport(acceptHeader = null) {
      this.exportLoading = true;
      this.exportError = '';

      this.fetchData('export',
        (response) => { // success
          // remove statusCode in export
          if (response.statusCode) {
            delete response.statusCode;
          }
          this.exportLoading = false;
          if (acceptHeader && acceptHeader.startsWith('text')) { // tsv/csv export
            const { text } = response;
            let fileName = '';
            if (acceptHeader === 'text/tab-separated-values') {
              fileName = this.getFileName('tsv');
            } else if (acceptHeader === 'text/csv') {
              fileName = this.getFileName('csv');
            }
            StringUtil.download(text, fileName, `${acceptHeader};charset=utf-8`);
          } else {
            // json export
            const jsonCopy = JSON.stringify(response);
            const fileName = this.getFileName('json');
            StringUtil.download(jsonCopy, fileName, 'application/json');
          }
        },
        (err) => { // fail
          this.exportLoading = false;
          this.exportError = `Ett fel inträffade vid export: ${err}`;
        }, acceptHeader);
    },
  },
  watch: {
    query(newVal) {
      this.getPreview(newVal);
      this.getHitCount();
    },
  },
  mounted() {
    this.getHitCount();
  },
};
</script>
