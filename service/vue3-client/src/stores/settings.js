import { defineStore } from 'pinia'

export const useCounterStore = defineStore('counter', {
  state: () => ({
    serviceName: 'Swepub',
    version: `${process.env.VUE_APP_VERSION}`,
    apiPath: `${process.env.VUE_APP_API_PATH}`,
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