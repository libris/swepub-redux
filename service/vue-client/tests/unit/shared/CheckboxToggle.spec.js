import { shallowMount } from '@vue/test-utils';
import CheckboxToggle from '@/components/shared/CheckboxToggle.vue';

let wrapper = null;
const onInput = jest.fn();
const valueProp = false;

beforeEach(() => {
  wrapper = shallowMount(CheckboxToggle, {
    propsData: {
      value: valueProp,
      id: 'test',
      label: 'test label',
    },
    listeners: {
      input: onInput,
    },
  });
});

afterEach(() => {
  wrapper.destroy();
  jest.clearAllMocks();
});

describe('CheckboxToggle', () => {
  it('renders an element with role checkbox', () => {
    expect(wrapper.attributes('role')).toBe('checkbox');
  });

  it('omits .is-checked and aria-checked when value is false', () => {
    expect(wrapper.classes('is-checked')).toBe(false);
    expect(wrapper.attributes('aria-checked')).toBe('false');
  });

  it('adds .is-checked and aria-checked when value is true', () => {
    wrapper.setProps({ value: !valueProp });
    wrapper.vm.$nextTick(() => {
      expect(wrapper.classes('is-checked')).toBe(true);
      expect(wrapper.attributes('aria-checked')).toBe('true');
    });
  });

  it('renders the label', () => {
    expect(wrapper.find('span').text()).toBe('test label');
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
