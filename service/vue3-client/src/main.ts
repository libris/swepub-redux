import { createApp } from 'vue'
import { createPinia } from 'pinia'

import { FontAwesomeIcon, FontAwesomeLayers } from '@fortawesome/vue-fontawesome';

import App from './App.vue'
import router from './router'
import * as LayoutUtil from '@/utils/Layout'
import { useSettingsStore } from '@/stores/settings';
import '@/utils/Icons';

const app = createApp(App)

app.use(createPinia())
app.use(router)

router.afterEach((route) => {
	const { serviceName } = useSettingsStore();
	const routeTitle = route.meta.title ? `${route.meta.title} | ` : '';
	const documentTitle = routeTitle + serviceName;
	document.title = documentTitle;
});

app.component('font-awesome-icon', FontAwesomeIcon);
app.component('font-awesome-layers', FontAwesomeLayers);

app.mount('#app')
