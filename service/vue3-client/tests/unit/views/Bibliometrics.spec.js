import { shallowMount } from '@vue/test-utils';
import Bibliometrics from '@/views/Bibliometrics.vue';

let wrapper = null;

const $route = {
  name: 'Bibliometrics',
  params: {
    section: 'test',
  },
};

beforeEach(() => {
  wrapper = shallowMount(Bibliometrics, {
    propsData: {
    },
    mocks: {
      $route,
    },
    stubs: ['BibliometricsSearch', 'DataDump'],
  });
});

afterEach(() => {
  wrapper.destroy();
});

describe('Bibliometrics', () => {
  it('has search tab as default on mount', () => {
    expect(wrapper.find('tab-menu-stub').attributes('active')).toBe('search');
  });
});
