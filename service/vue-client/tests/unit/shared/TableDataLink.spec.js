import { shallowMount } from '@vue/test-utils';
import TableDataLink from '@/components/shared/TableDataLink.vue';

let wrapper = null;
const tdValue = 'test.com';
const shift = 'http://';
const unshift = 'test';

let link = null;

beforeEach(() => {
  wrapper = shallowMount(TableDataLink, {
    propsData: {
      tdValue,
      newTab: false,
    },
    stubs: ['font-awesome-icon'],
  });
  link = wrapper.find('a');
});

afterEach(() => {
  wrapper.destroy();
});

describe('TableDataLink', () => {
  it('renders a link', () => {
    expect(link.exists()).toBe(true);
  });

  it('sets the tdValue as link text', () => {
    expect(link.text()).toBe(tdValue);
  });

  it('sets target attribute and renders icon if newTab prop is true', async () => {
    expect(wrapper.find('font-awesome-icon-stub[icon="fa,external-link-alt"]').exists()).toBe(false);
    expect(link.attributes('target')).toBe(undefined);
    wrapper.setProps({ newTab: true });
    await wrapper.vm.$nextTick();
    expect(wrapper.find('font-awesome-icon-stub[icon="fa,external-link-alt"]').exists()).toBe(true);
    expect(link.attributes('target')).toBe('_blank');
  });

  it('adds the shift prop value to start of link text and url', async () => {
    wrapper.setProps({ shift });
    await wrapper.vm.$nextTick();
    expect(link.text()).toBe(shift + tdValue);
    expect(link.attributes('href')).toBe(shift + tdValue);
  });

  it('removes the unshift prop value from start of link text', async () => {
    wrapper.setProps({ unshift });
    await wrapper.vm.$nextTick();
    expect(link.text()).toBe(tdValue.replace(unshift, ''));
    expect(link.attributes('href')).toBe(tdValue);
  });
});
