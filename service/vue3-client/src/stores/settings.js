import { defineStore } from 'pinia'

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    serviceName: 'Swepub',
    version: `${import.meta.env.VITE_VUE_APP_VERSION}`,
    apiPath: `${import.meta.env.VITE_VUE_APP_API_PATH}`,
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