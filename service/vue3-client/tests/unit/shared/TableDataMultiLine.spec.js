import { shallowMount } from '@vue/test-utils';
import TableDataMultiLine from '@/components/shared/TableDataMultiLine.vue';

let wrapper = null;
const lorem = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.';

beforeEach(() => {
  wrapper = shallowMount(TableDataMultiLine, {
    propsData: {
      tdKey: 'test',
      tdValue: lorem,
    },
  });
});

afterEach(() => {
  wrapper.destroy();
});

describe('TableDataMultiLine', () => {
  it('renders a span element', () => {
    expect(wrapper.find('span').exists()).toBe(true);
  });

  it('cuts tdValue at trimAt prop', async () => {
    const trimAt = 1;
    const ellipsLength = 3;
    wrapper.setProps({ trimAt: 1 });
    await wrapper.vm.$nextTick();
    expect(wrapper.find('span').text().length).toBe(trimAt + ellipsLength);
  });

  it('ellipses text if trimmed', async () => {
    wrapper.setProps({ trimAt: 1 });
    await wrapper.vm.$nextTick();
    expect(wrapper.find('span').text().includes('...')).toBe(true);
  });
});
