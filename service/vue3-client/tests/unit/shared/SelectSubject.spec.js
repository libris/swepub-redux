import { shallowMount } from '@vue/test-utils';
import SelectSubject from '@/components/shared/SelectSubject.vue';

import { enableFetchMocks } from 'jest-fetch-mock';

enableFetchMocks();

const apiReponse = {
  1: {
    eng: 'Natural Sciences',
    swe: 'Naturvetenskap',
    subcategories: {
      101: {
        eng: 'Mathematics',
        swe: 'Matematik',
        subcategories: {
          10101: {
            eng: 'Mathematical Analysis',
            swe: 'Matematisk analys',
          },
          10102: {
            eng: 'Geometry',
            swe: 'Geometri',
          },
          10103: {
            eng: 'Algebra and Logic',
            swe: 'Algebra och logik',
          },
          10104: {
            eng: 'Discrete Mathematics',
            swe: 'Diskret matematik',
          },
          10105: {
            eng: 'Computational Mathematics',
            swe: 'Beräkningsmatematik',
          },
          10106: {
            eng: 'Probability Theory and Statistics',
            swe: 'Sannolikhetsteori och statistik',
          },
          10199: {
            eng: 'Other Mathematics',
            swe: 'Annan matematik',
          },
        },
      },
    },
  },
  2: {
    eng: 'Engineering and Technology',
    swe: 'Teknik',
    subcategories: {
      201: {
        eng: 'Civil Engineering',
        swe: 'Samhällsbyggnadsteknik',
        subcategories: {
          20101: {
            eng: 'Architectural Engineering',
            swe: 'Arkitekturteknik',
          },
          20102: {
            eng: 'Construction Management',
            swe: 'Byggproduktion',
          },
        },
      },
    },
  },
};

const transformed = [
  { label: '1 - Naturvetenskap', id: '1' },
  { label: '101 - Matematik', id: '101' },
  { label: '10101 - Matematisk analys', id: '10101' },
  { label: '10102 - Geometri', id: '10102' },
  { label: '10103 - Algebra och logik', id: '10103' },
  { label: '10104 - Diskret matematik', id: '10104' },
  { label: '10105 - Beräkningsmatematik', id: '10105' },
  { label: '10106 - Sannolikhetsteori och statistik', id: '10106' },
  { label: '10199 - Annan matematik', id: '10199' },
  { label: '2 - Teknik', id: '2' },
  { label: '201 - Samhällsbyggnadsteknik', id: '201' },
  { label: '20101 - Arkitekturteknik', id: '20101' },
  { label: '20102 - Byggproduktion', id: '20102' }];

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
  wrapper = shallowMount(SelectSubject, {
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

describe('SelectSubject', () => {
  it('transforms the options correctly', async () => {
    await wrapper.vm.$nextTick();
    expect(JSON.stringify(transformed))
      .toEqual(JSON.stringify(wrapper.vm.options));
  });
});
