import { defineStore } from 'pinia'

// process.env.VITE_VUE_APP_VERSION = require('./package.json').version;
// process.env.VITE_VUE_APP_API_PATH = '/api/v1';


export const useSettingsStore = defineStore('settings', {
  state: () => ({
    serviceName: 'Swepub',
    version: `0.0`,
    apiPath: `/api/v1`,
    matomoId: 'MATOMO_ID',
    language: 'swe',
    navigation: [
      {
        id: 'bibliometrics',
        label: 'Bibliometri',
        path: '/bibliometrics',
      },
      {
        id: 'process',
        label: 'Databearbetning',
        path: '/process',
      },
      {
        id: 'classify',
        label: 'Ämnesklassificering',
        path: '/classify',
      },
      {
        id: 'datastatus',
        label: 'Datastatus',
        path: '/datastatus',
      },
    ],
  }),
});