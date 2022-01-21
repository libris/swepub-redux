import { shallowMount } from '@vue/test-utils';
import Process from '@/views/Process.vue';

let wrapper = null;

const $route = {
  name: 'Process',
  params: {
    section: 'test',
  },
};

beforeEach(() => {
  wrapper = shallowMount(Process, {
    propsData: {
    },
    mocks: {
      $route,
    },
    stubs: ['DataQuality', 'HarvestStatus'],
  });
});

afterEach(() => {
  wrapper.destroy();
});

describe('Process', () => {
  it('has quality tab as default on mount', () => {
    expect(wrapper.find('tab-menu-stub').attributes('active')).toBe('quality');
  });
});
