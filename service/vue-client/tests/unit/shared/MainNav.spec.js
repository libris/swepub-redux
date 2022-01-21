import { shallowMount } from '@vue/test-utils';
import MainNav from '@/components/shared/MainNav.vue';

let wrapper = null;

const $store = {
  getters: {
    settings: {
      language: 'swe',
    },
  },
};

beforeEach(() => {
  wrapper = shallowMount(MainNav, {
    propsData: {
      collapsed: false,
    },
    mocks: {
      $store,
    },
    stubs: ['router-link'],
  });
});

afterEach(() => {
  wrapper.destroy();
});

describe('MainHeader', () => {
  it('renders a nav element', () => {
    expect(wrapper.findAll('nav').length).toBe(1);
  });

  it('adds collapse class when passed collapsed prop', async () => {
    expect(wrapper.findAll('.collapse').length).toBe(0);
    wrapper.setProps({ collapsed: true });
    await wrapper.vm.$nextTick();
    expect(wrapper.findAll('.collapse').length).toBe(1);
  });
});
