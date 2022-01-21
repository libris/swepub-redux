import { shallowMount } from '@vue/test-utils';
import TableDataList from '@/components/shared/TableDataList.vue';
import TableDataBoolean from '@/components/shared/TableDataBoolean.vue';

let wrapper = null;

beforeEach(() => {
  wrapper = shallowMount(TableDataList, {
    propsData: {
      tdKey: 'test',
      tdValue: [],
    },
  });
});

afterEach(() => {
  wrapper.destroy();
});

describe('TableDataList', () => {
  it('renders an ul (if tdValue prop is provided)', async () => {
    expect(wrapper.find('ul').exists()).toBe(false);
    wrapper.setProps({ tdValue: [1, 2, 3] });
    await wrapper.vm.$nextTick();
    expect(wrapper.find('ul').exists()).toBe(true);
  });

  it('prints the target keys as list items', async () => {
    wrapper.setProps({ tdValue: [{ first: 'foo', last: 'bar' }], targetKeys: ['first', 'last'] });
    await wrapper.vm.$nextTick();
    expect(wrapper.find('li').text()).toBe('foo bar');
  });

  it('uses the renderFn for rendering if provided', async () => {
    const text = 'example text';
    wrapper.setProps({ tdValue: [1], renderFn: () => [text] });
    await wrapper.vm.$nextTick();
    expect(wrapper.find('li').text()).toBe(text);
  });

  it('uses the renderComponent if provided', async () => {
    wrapper.setProps({ tdValue: [true], renderComponent: TableDataBoolean });
    wrapper.vm.$attrs.tdKey = 'test';
    await wrapper.vm.$nextTick();
    expect(wrapper.find('table-data-boolean-stub').exists()).toBe(true);
  });

  it('restricts the number of li:s by limit variable and adds ... indicator', async () => {
    const limit = 1;
    wrapper.setProps({ tdValue: [1, 2, 3, 4, 5] });
    wrapper.setData({ limit });
    await wrapper.vm.$nextTick();
    expect(wrapper.findAll('li').length).toBe(limit + 1);
    expect(wrapper.findAll('li').at(limit).text()).toBe('...');
  });

  it('prints empy lines if showEmptyValues is true', async () => {
    wrapper.setProps({ tdValue: [1, null, 3, '', 5] });
    await wrapper.vm.$nextTick();
    expect(wrapper.findAll('li').length).toBe(3);
    wrapper.setProps({ showEmptyValues: true });
    await wrapper.vm.$nextTick();
    expect(wrapper.findAll('li').length).toBe(5);
  });
});
