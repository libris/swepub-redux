import { shallowMount } from '@vue/test-utils';
import TableDataId from '@/components/shared/TableDataId.vue';

let wrapper = null;
const tooltip = jest.fn();
const id = 'oai:DiVA.org:hb-23274';
const $route = {
  name: 'Bibliometrics',
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
  wrapper = shallowMount(TableDataId, {
    propsData: {
      tdKey: 'recordId',
      tdValue: id,
      deduped: () => false,
    },
    directives: {
      tooltip,
    },
    mocks: {
      $route,
      $store,
    },
    stubs: ['font-awesome-icon'],
  });
});

afterEach(() => {
  wrapper.destroy();
  jest.clearAllMocks();
});

describe('TableDataId', () => {
  it('displays an icon if record is deduplicated', async () => {
    expect(wrapper.find('font-awesome-icon-stub[icon="fas,copy"]').exists()).toBe(false);
    wrapper.setProps({ deduped: () => true });
    await wrapper.vm.$nextTick();
    expect(wrapper.find('font-awesome-icon-stub[icon="fas,copy"]').exists()).toBe(true);
  });

  it('renders a link if url can be resolved', async () => {
    wrapper.vm.$route.name = 'test';
    await wrapper.vm.$nextTick();
    expect(wrapper.find('a').exists()).toBe(false);

    wrapper.vm.$route.name = 'Bibliometrics';
    await wrapper.vm.$nextTick();
    const link = wrapper.find('a');
    expect(link.exists()).toBe(true);
    expect(link.attributes('href').startsWith('/api')).toBe(true);
  });

  it('opens link in new tab and display an icon to indicate this', () => {
    expect(wrapper.find('font-awesome-icon-stub[icon="fa,external-link-alt"]').exists()).toBe(true);
    expect(wrapper.find('a').attributes('target')).toBe('_blank');
  });

  it('prints the id as text if linkUrl cannot be determined', async () => {
    wrapper.vm.$route.name = 'test';
    await wrapper.vm.$nextTick();
    expect(wrapper.find('a').exists()).toBe(false);
    expect(wrapper.find('.TableDataId > span').text()).toBe(id);
  });
});
