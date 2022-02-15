import 'whatwg-fetch';
import Vue from 'vue';

import VueMatomo from 'vue-matomo';
import { FontAwesomeIcon, FontAwesomeLayers } from '@fortawesome/vue-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import {
  faSquare, faCheckSquare, faCheck, faQuestionCircle, faChevronRight, faChevronDown,
  faExternalLinkAlt, faCopy, faLongArrowAltRight, faExclamationCircle, faBars, faTimes,
} from '@fortawesome/free-solid-svg-icons';
import {
  faSquare as farSquare, faCheckSquare as farCheckSquare, faClock, faTimesCircle,
} from '@fortawesome/free-regular-svg-icons';
import { faTwitter } from '@fortawesome/free-brands-svg-icons';
import * as LayoutUtil from '@/utils/Layout';
import store from './store';
import router from './router';
import App from './App.vue';

Vue.component('font-awesome-icon', FontAwesomeIcon);
Vue.component('font-awesome-layers', FontAwesomeLayers);

library.add(
  faCheckSquare,
  farCheckSquare,
  faSquare,
  farSquare,
  faQuestionCircle,
  faCheck,
  faChevronRight,
  faChevronDown,
  faTwitter,
  faExternalLinkAlt,
  faCopy,
  faClock,
  faLongArrowAltRight,
  faTimesCircle,
  faTimes,
  faExclamationCircle,
  faBars,
);

Vue.config.productionTip = false;

// only use Matomo if id is present, i.e in production mode
if (store.getters.settings.matomoId) {
  Vue.use(VueMatomo, {
    host: 'https://analytics.kb.se',
    siteId: store.getters.settings.matomoId,
    trackerFileName: 'matomo',
    disableCookies: true,
    router,
    enableLinkTracking: true,
  });
}

new Vue({
  router,
  store,
  render: (h) => h(App),
  methods: {
    updateTitle() {
      const { serviceName } = store.getters.settings;
      const routeTitle = this.$route.meta.title ? `${this.$route.meta.title} | ` : '';
      const documentTitle = routeTitle + serviceName;
      document.title = documentTitle;
    },
  },
  mounted() {
    window.addEventListener('keydown', LayoutUtil.handleFirstTab);
    this.updateTitle();
  },
  watch: {
    $route() {
      this.updateTitle();
    },
  },
}).$mount('#app');
