import { shallowMount } from '@vue/test-utils';
import TabMenu from '@/components/shared/TabMenu.vue';

let wrapper = null;
const tabs = [{ id: 1, text: 'tab1' }, { id: 2, text: 'tab2' }, { id: 3, text: 'tab3' }];
const onGo = jest.fn();

beforeEach(() => {
  wrapper = shallowMount(TabMenu, {
    propsData: {
      tabs,
    },
    listeners: {
      go: onGo,
    },
    stubs: ['router-link'],
  });
});

afterEach(() => {
  wrapper.destroy();
  jest.clearAllMocks();
});

describe('TabMenu', () => {
  it('renders as many tabs as items in tabs prop', () => {
    expect(wrapper.findAll('.TabMenu-tab').length).toBe(tabs.length);
  });

  it('prints the tabs prop text', () => {
    expect(wrapper.find('.TabMenu-tabText').text()).toBe(tabs[0].text);
  });

  it('renders router-links if link prop is true', async () => {
    wrapper.setProps({ link: true });
    await wrapper.vm.$nextTick();
    expect(wrapper.findAll('router-link-stub').length).toBe(tabs.length);
  });

  it('sets the active tab from active prop', async () => {
    expect(wrapper.findAll('.is-active').length).toBe(0);
    wrapper.setProps({ active: 1 });
    await wrapper.vm.$nextTick();
    expect(wrapper.findAll('.is-active').length).toBe(1);
    expect(wrapper.find('.is-active').attributes('aria-selected')).toBe('true');
  });

  it('emits the go event with tab id on click', () => {
    wrapper.find('.TabMenu-tab').trigger('click');
    expect(onGo).toHaveBeenCalled();
    expect(onGo).toHaveBeenCalledWith(tabs[0].id);
  });

  it('emits the go event with tab id on keyup enter', () => {
    wrapper.find('.TabMenu-tab').trigger('keyup.enter');
    expect(onGo).toHaveBeenCalled();
    expect(onGo).toHaveBeenCalledWith(tabs[0].id);
  });
});
