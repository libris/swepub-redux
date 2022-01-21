import { mount } from '@vue/test-utils';
import ChevronToggle from '@/components/shared/ChevronToggle.vue';

let wrapper = null;
const onInput = jest.fn();
const valueProp = false;

beforeEach(() => {
  wrapper = mount(ChevronToggle, {
    propsData: {
      value: valueProp,
      ariaControls: 'test-aria',
    },
    listeners: {
      input: onInput,
    },
    stubs: ['font-awesome-icon'],
  });
});

afterEach(() => {
  wrapper.destroy();
  jest.clearAllMocks();
});

describe('ChevronToggle', () => {
  it('renders a chevron icon', () => {
    const fa = wrapper.find('font-awesome-icon-stub');
    expect(fa.attributes('icon')).toBe('fa,chevron-down');
  });

  it('omits .is-toggled and aria-expanded when value is false', () => {
    expect(wrapper.classes('is-toggled')).toBe(false);
    expect(wrapper.attributes('aria-expanded')).toBe('false');
  });

  it('adds .is-toggled and aria-expanded when value is true', () => {
    // set new props
    wrapper.setProps({ value: !valueProp });
    wrapper.vm.$nextTick(() => {
      expect(wrapper.classes('is-toggled')).toBe(true);
      expect(wrapper.attributes('aria-expanded')).toBe('true');
    });
  });

  it('sets prop aria-controls on element', () => {
    expect(wrapper.attributes('aria-controls')).toBe('test-aria');
  });

  it('emits input event with inverse of "value" prop, on click', () => {
    wrapper.trigger('click');
    expect(onInput).toHaveBeenCalled();
    expect(onInput).toHaveBeenCalledWith(!valueProp);
  });

  it('emits input event with inverse of "value" prop, on keyup enter', () => {
    wrapper.trigger('keyup.enter');
    expect(onInput).toHaveBeenCalled();
    expect(onInput).toHaveBeenCalledWith(!valueProp);
  });
});
