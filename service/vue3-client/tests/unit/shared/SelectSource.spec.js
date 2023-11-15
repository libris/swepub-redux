import { shallowMount } from '@vue/test-utils';
import SelectSource from '@/components/shared/SelectSource.vue';

import { enableFetchMocks } from 'jest-fetch-mock';

enableFetchMocks();

const apiReponse = {
  sources: [
    {
      name: 'Högskolan i Borås',
      code: 'hb',
    },
    {
      name: 'Högskolan i Halmstad',
      code: 'hh',
    },
    {
      name: 'Statens väg- och transportforskningsinstitut',
      code: 'vti',
    },
    {
      name: 'Högskolan i Skövde',
      code: 'his',
    },
    {
      name: 'Ersta Sköndal Bräcke högskola',
      code: 'esh',
    },
    {
      name: 'Röda Korsets Högskola',
      code: 'rkh',
    },
    {
      name: 'Konstfack',
      code: 'konstfack',
    },
    {
      name: 'Enskilda Högskolan Stockholm',
      code: 'ths',
    },
    {
      name: 'Nationalmuseum',
      code: 'nationalmuseum',
    },
    {
      name: 'Kungl. Musikhögskolan',
      code: 'kmh',
    },
    {
      name: 'Stockholms konstnärliga högskola',
      code: 'uniarts',
    },
    {
      name: 'Kungl. Konsthögskolan',
      code: 'kkh',
    },
  ],
};

const transformed = [{ name: 'Enskilda Högskolan Stockholm', code: 'ths' }, { name: 'Ersta Sköndal Bräcke högskola', code: 'esh' }, { name: 'Högskolan i Borås', code: 'hb' }, { name: 'Högskolan i Halmstad', code: 'hh' }, { name: 'Högskolan i Skövde', code: 'his' }, { name: 'Konstfack', code: 'konstfack' }, { name: 'Kungl. Konsthögskolan', code: 'kkh' }, { name: 'Kungl. Musikhögskolan', code: 'kmh' }, { name: 'Nationalmuseum', code: 'nationalmuseum' }, { name: 'Röda Korsets Högskola', code: 'rkh' }, { name: 'Statens väg- och transportforskningsinstitut', code: 'vti' }, { name: 'Stockholms konstnärliga högskola', code: 'uniarts' }];

let wrapper = null;
const $store = {
  getters: {
    settings: {
      language: 'swe',
    },
  },
};

beforeEach(() => {
  fetch.resetMocks();
  fetch.mockResponse(JSON.stringify(apiReponse));
  wrapper = shallowMount(SelectSource, {
    propsData: {
      apiEndpoint: null,
    },
    mocks: {
      $store,
    },
  });
});

afterEach(() => {
  wrapper.destroy();
  jest.clearAllMocks();
});

describe('SelectSource', () => {
  it('transforms the options correctly', async () => {
    await wrapper.vm.$nextTick();
    expect(JSON.stringify(transformed))
      .toEqual(JSON.stringify(wrapper.vm.options));
  });
});
