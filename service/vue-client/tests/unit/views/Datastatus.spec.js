import { shallowMount } from '@vue/test-utils';
import Datastatus from '@/views/Datastatus.vue';

import { enableFetchMocks } from 'jest-fetch-mock';

enableFetchMocks();

let wrapper = null;
let sync = null;
const fetchMsg = 'fetch successful';
const apiReponse = { fetchMsg };

const $route = {
  name: 'Datastatus',
  params: {
    section: 'test',
  },
};

const $store = {
  getters: {
    settings: {
      language: 'swe',
      apiPath: '/api/v1',
    },
  },
};

beforeEach(() => {
  sync = jest.spyOn(Datastatus.methods, 'sync');
  fetch.resetMocks();
  fetch.mockResponse(JSON.stringify(apiReponse));
  wrapper = shallowMount(Datastatus, {
    propsData: {
      params: {},
      query: {},
    },
    mocks: {
      $route,
      $store,
    },
    stubs: ['SelectSource', 'YearPicker', 'ShortStats', 'DatastatusSummary', 'DatastatusValidations', 'DatastatusSubjects', 'router-link'],
  });
});

afterEach(() => {
  wrapper.destroy();
  jest.clearAllMocks();
});

describe('Datastatus', () => {
  it('syncs form state on mount', () => {
    expect(sync).toHaveBeenCalled();
  });

  it('fetches sources on mount', async () => {
    await wrapper.vm.$nextTick();
    expect(wrapper.vm.sources.fetchMsg).toBe(fetchMsg);
  });

  it('fetches summary on mount', async () => {
    await wrapper.vm.$nextTick();
    expect(wrapper.vm.data.fetchMsg).toBe(fetchMsg);
  });

  it('displays a spinner while fetching (on mount)', async () => {
    expect(wrapper.find('vue-simple-spinner-stub').exists()).toBe(true);
    await wrapper.vm.$nextTick();
    expect(wrapper.find('vue-simple-spinner-stub').exists()).toBe(false);
  });

  it('renders stats if it has data', async () => {
    expect(wrapper.find('datastatussummary-stub').exists()).toBe(false);
    await wrapper.vm.$nextTick();
    expect(wrapper.find('datastatussummary-stub').exists()).toBe(true);
  });

  it('sets the yearInputError on erroneous selection', async () => {
    expect(wrapper.vm.yearInputError).toBeFalsy();
    wrapper.setData({ selected: { source: '', years: { to: '1', from: '2' } } });
    await wrapper.vm.$nextTick();
    expect(wrapper.vm.yearInputError).toBeTruthy();
  });

  it('disables the submit button on yearInputError', async () => {
    expect(wrapper.find('.Datastatus-submit .btn').attributes('disabled')).toBe(undefined);
    wrapper.setData({ selected: { source: '', years: { to: '1', from: '2' } } });
    await wrapper.vm.$nextTick();
    expect(wrapper.find('.Datastatus-submit .btn').attributes('disabled')).toBe('disabled');
  });

  it('displays the fetch error', async () => {
    expect(wrapper.find('.error').exists()).toBe(false);
    wrapper.setData({ error: 'test error' });
    await wrapper.vm.$nextTick();
    expect(wrapper.find('.error').exists()).toBe(true);
  });
});
