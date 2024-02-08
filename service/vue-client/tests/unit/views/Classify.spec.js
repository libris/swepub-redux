import { shallowMount } from '@vue/test-utils';
import Classify from '@/views/Classify.vue';

let wrapper = null;

const $route = {
  name: 'Classify',
  params: {
    section: 'test',
  },
};

const $store = {
  getters: {
    settings: {
      language: 'swe',
      apiPath: '/api/v2',
    },
  },
};

beforeEach(() => {
  wrapper = shallowMount(Classify, {
    propsData: {
    },
    mocks: {
      $route,
      $store,
    },
    stubs: ['ClassifyForm', 'ClassifyDocumentation'],
  });
});

afterEach(() => {
  wrapper.destroy();
});

describe('Classify', () => {
  it('has classify tab as default on mount', () => {
    expect(wrapper.find('tab-menu-stub').attributes('active')).toBe('classify');
  });
});
