import { shallowMount } from '@vue/test-utils';
import MainHeader from '@/components/shared/MainHeader.vue';

let wrapper = null;

const $store = {
  getters: {
    settings: {
      language: 'swe',
    },
  },
};

beforeEach(() => {
  wrapper = shallowMount(MainHeader, {
    propsData: {
    },
    mocks: {
      $store,
    },
    stubs: ['font-awesome-icon', 'router-link'],
  });
});

afterEach(() => {
  wrapper.destroy();
});

describe('MainHeader', () => {
  it('renders a header element', () => {
    expect(wrapper.findAll('header').length).toBe(1);
  });

  it('contains the skip link', () => {
    expect(wrapper.findAll('#skip-link').length).toBe(1);
  });

  it('collapses on click', async () => {
    expect(wrapper.vm.navCollapsed).toBe(false);
    wrapper.find('.MainHeader-toggle').trigger('click');
    expect(wrapper.vm.navCollapsed).toBe(true);
  });
});
