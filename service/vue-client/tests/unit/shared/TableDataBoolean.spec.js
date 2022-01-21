import { shallowMount } from '@vue/test-utils';
import TableDataBoolean from '@/components/shared/TableDataBoolean.vue';

let wrapper = null;

const $store = {
  getters: {
    settings: {
      language: 'swe',
    },
  },
};

beforeEach(() => {
  wrapper = shallowMount(TableDataBoolean, {
    propsData: {
      tdValue: true,
      tdKey: 'test',
    },
    mocks: {
      $store,
    },
  });
});

afterEach(() => {
  wrapper.destroy();
});

describe('TableDataBoolean', () => {
  it('renders a word from a boolean value according to language settings', async () => {
    const span = wrapper.find('span');
    expect(span.text()).toBe('Ja');
    expect(span.attributes('title')).toBe('Ja');
    wrapper.setProps({ tdValue: false });
    await wrapper.vm.$nextTick();
    expect(span.text()).toBe('Nej');
  });
});
