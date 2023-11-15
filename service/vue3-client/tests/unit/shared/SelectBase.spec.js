import { shallowMount } from '@vue/test-utils';
import SelectBase from '@/components/shared/SelectBase.vue';

let wrapper = null;

afterEach(() => {
  wrapper.destroy();
  jest.clearAllMocks();
});

describe('SelectBase', () => {
  it('gets the options on mount', () => {
    const getOptions = jest.spyOn(SelectBase.methods, 'getOptions');
    wrapper = shallowMount(SelectBase);
    expect(getOptions).toHaveBeenCalled();
  });

  it('shows the spinner on loading', () => {
    wrapper = shallowMount(SelectBase);
    expect(wrapper.find('vue-simple-spinner-stub').exists()).toBe(false);
    wrapper.setData({ loading: true });
    wrapper.vm.$nextTick(() => {
      expect(wrapper.find('vue-simple-spinner-stub').exists()).toBe(true);
    });
  });

  // it('should fetch options if not provided', () => {
  // });

  it('sets the options if provided', () => {
    wrapper = shallowMount(SelectBase, {
      propsData: {
        providedOptions: ['test'],
      },
    });
    expect(wrapper.vm.options[0]).toBe('test');
  });

  // it('should pass on the input event from vue-select', () => {
  // });

  // it('should emit the clear event on null input', () => {
  // });

  it('displays the incoming error', () => {
    wrapper = shallowMount(SelectBase, {
      propsData: {
        incomingError: 'test error',
      },
    });
    expect(wrapper.find('.error').text()).toBe('test error');
  });
});
