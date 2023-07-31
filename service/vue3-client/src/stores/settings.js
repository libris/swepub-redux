import { defineStore } from 'pinia'

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    serviceName: 'Swepub',
    version: __APP_VERSION__,
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