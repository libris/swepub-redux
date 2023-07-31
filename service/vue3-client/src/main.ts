import 'whatwg-fetch';
import { createApp } from 'vue'
import { createPinia } from 'pinia'

import { FontAwesomeIcon, FontAwesomeLayers } from '@fortawesome/vue-fontawesome';

import VueMatomo from 'vue-matomo';
import FloatingVue from 'floating-vue';
import App from './App.vue'
import router from './router'
import * as LayoutUtil from '@/utils/Layout'
import { useSettingsStore } from '@/stores/settings';
import '@/utils/Icons';
import 'floating-vue/dist/style.css'

const app = createApp(App)

app.use(createPinia());
app.use(router);
app.use(FloatingVue);

// only use Matomo if id is present, i.e in production mode
// TODO: Figure out how we initialize something using values from store
// if (store.getters.settings.matomoId) {
// 	app.use(VueMatomo, {
// 		host: 'https://analytics.kb.se',
// 		siteId: store.getters.settings.matomoId,
// 		trackerFileName: 'matomo',
// 		disableCookies: true,
// 		router,
// 		enableLinkTracking: true,
// 	});
// }

router.afterEach((route) => {
	const { serviceName } = useSettingsStore();
	const routeTitle = route.meta.title ? `${route.meta.title} | ` : '';
	const documentTitle = routeTitle + serviceName;
	document.title = documentTitle;
});

app.component('font-awesome-icon', FontAwesomeIcon);
app.component('font-awesome-layers', FontAwesomeLayers);

app.mount('#app')
