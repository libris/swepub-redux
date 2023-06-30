<script>
// provides a basic fetch data method that accepts a url adress and
// resolves with a data object on success, or rejects with error (get err.message).
// includes settings.apiPath, spinner component - no need to include these
// data, loading & error vars - make sure to shadow these

import { mapState } from 'pinia';
import VueSimpleSpinner from 'vue-simple-spinner';
import * as Network from '@/utils/Network';
import { useSettingsStore } from '@/stores/settings';

export default {
  name: 'fetch-mixin',
  components: {
    VueSimpleSpinner,
  },
  props: {
  },
  data() {
    return {
      data: null,
      loading: false,
      error: null,
      errorBase: 'Ett fel har inträffat: ',
    };
  },
  computed: {
    ...mapState(useSettingsStore, ['apiPath'])
  },
  methods: {
    fetchData(q) {
      this.data = null;
      this.loading = true;
      this.error = null;
      return new Promise((resolve, reject) => {
        Network.get(`${this.apiPath}${q}`)
          .then((response) => {
            this.loading = false;
            if (response.statusCode === 200) {
              this.data = response;
              resolve(response);
            } else {
              response.json()
                .then((json) => {
                  const reason = json.errors.join(', ');
                  const msg = this.errorBase + reason;
                  this.error = msg;
                  reject(new Error(msg));
                })
                .catch(() => {
                  const msg = `${this.errorBase}: ${response.status} ${response.statusText}`;
                  this.error = msg;
                  reject(new Error(msg));
                });
            }
          }).catch((err) => {
            this.loading = false;
            const msg = this.errorBase + err;
            this.error = msg;
            reject(new Error(msg));
          });
      });
    },
  },
  mounted() {
  },
  watch: {
  },
};
</script>
