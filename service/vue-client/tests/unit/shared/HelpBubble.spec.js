import { shallowMount } from '@vue/test-utils';
import HelpBubble from '@/components/shared/HelpBubble.vue';

let wrapper = null;
const tooltip = jest.fn();

const $route = {
  name: 'test',
};

const $store = {
  getters: {
    settings: {
      language: 'swe',
    },
  },
};

beforeEach(() => {
  wrapper = shallowMount(HelpBubble, {
    propsData: {
      bubbleKey: 'test',
      color: 'red',
      exportError: 'test error',
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

describe('HelpBubble', () => {
  it('renders a question mark icon when tooltipObj is located', () => {
    const fa = wrapper.find('font-awesome-icon-stub');
    expect(fa.exists()).toBe(true);
    expect(fa.attributes('icon')).toBe('fas,question-circle');
  });

  it('sets the tooltip text when tooltipObj is located', () => {
    expect(wrapper.vm.tooltipObj.text).toBe('this is a test text');
  });

  it('does not render an icon when tooltipObj is not located (incorrect bubbleKey prop path)', () => {
    wrapper.setProps({ bubbleKey: 'nonExistantKey' });
    wrapper.vm.$nextTick(() => {
      const fa = wrapper.find('font-awesome-icon-stub');
      expect(fa.exists()).toBe(false);
    });
  });

  it('opens the tooltip on helpbubble click', async () => {
    await wrapper.trigger('click');
    expect(wrapper.vm.isOpen).toEqual(true);
  });

  it('opens the tooltip on keyup enter', async () => {
    await wrapper.trigger('keyup.enter');
    expect(wrapper.vm.isOpen).toEqual(true);
  });

  it('sets the color according to color prop', () => {
    expect(wrapper.attributes('style')).toBe('color: red;');
  });
});
