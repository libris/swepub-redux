import { shallowMount } from '@vue/test-utils';
import PaginationComponent from '@/components/shared/PaginationComponent.vue';

let wrapper = null;
let buttons = null;
const onGo = jest.fn();

beforeEach(() => {
  wrapper = shallowMount(PaginationComponent, {
    propsData: {
      pagination: {
        prev: {},
        next: {},
      },
    },
    listeners: {
      go: onGo,
    },
  });

  buttons = wrapper.findAll('[role=button]');
});

afterEach(() => {
  wrapper.destroy();
  jest.clearAllMocks();
});

describe('PaginationComponent', () => {
  it('has two buttons', () => {
    expect(buttons.length).toBe(2);
  });

  it('enables buttons if pagination.prev and pagination.next props', () => {
    const activeButtons = buttons.filter((button) => button.attributes('aria-disabled'));
    expect(activeButtons.length).toBe(0);
  });

  it('emits go event on prev click', async () => {
    await buttons.at(0).trigger('click');
    expect(onGo).toHaveBeenCalledWith('prev');
  });

  it('emits go event on next keyup enter', async () => {
    await buttons.at(1).trigger('keyup.enter');
    expect(onGo).toHaveBeenCalledWith('next');
  });

  it('disables buttons if missing pagination.prev and pagination.next', () => {
    wrapper.setProps({ pagination: null });
    wrapper.vm.$nextTick(async () => {
      const activeButtons = buttons.filter((button) => button.attributes('aria-disabled'));
      expect(activeButtons.length).toBe(2);
      await buttons.trigger('click');
      expect(onGo).not.toHaveBeenCalled();
    });
  });

  it('renders the error if error prop', () => {
    expect(wrapper.find('.error').exists()).toBe(false);
    wrapper.setProps({ error: 'test error' });
    wrapper.vm.$nextTick(() => {
      const err = wrapper.find('.error');
      expect(err.exists()).toBe(true);
      expect(err.text()).toBe('test error');
    });
  });
});
