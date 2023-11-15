import { shallowMount } from '@vue/test-utils';
import MainFooter from '@/components/shared/MainFooter.vue';

let wrapper = null;

const $store = {
  getters: {
    settings: {
      language: 'swe',
    },
  },
};

beforeEach(() => {
  wrapper = shallowMount(MainFooter, {
    propsData: {
    },
    mocks: {
      $store,
    },
    stubs: ['font-awesome-icon'],
  });
});

afterEach(() => {
  wrapper.destroy();
});

describe('MainFooter', () => {
  it('renders a footer element', () => {
    expect(wrapper.findAll('footer').length).toBe(1);
  });
});
