import { shallowMount } from '@vue/test-utils';
import YearPicker from '@/components/shared/YearPicker.vue';

let wrapper = null;
const years = { from: '2019', to: '2020' };
const onInput = jest.fn();

beforeEach(() => {
  wrapper = shallowMount(YearPicker, {
    propsData: {
      value: years,
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

describe('TabMenu', () => {
  it('renders two number inputs with labels', () => {
    expect(wrapper.findAll('input[type="number"]').length).toBe(2);
    expect(wrapper.findAll('label').length).toBe(2);
  });

  it('set the value prop as values for inputs', () => {
    expect(wrapper.find('#year-from').element.value).toBe(years.from);
    expect(wrapper.find('#year-to').element.value).toBe(years.to);
  });

  it('renders a legend with text if passed a legend prop', async () => {
    const legendText = 'test legend';
    expect(wrapper.find('legend').exists()).toBe(false);
    wrapper.setProps({ legend: legendText });
    await wrapper.vm.$nextTick();
    expect(wrapper.find('legend').exists()).toBe(true);
    expect(wrapper.find('legend').text()).toBe(legendText);
  });

  it('emits input values on user change', () => {
    wrapper.find('.YearPicker-dateInput').trigger('input');
    expect(onInput).toHaveBeenCalledWith(years);
  });

  it('displays the error', async () => {
    const error = 'test error';
    expect(wrapper.find('.error').exists()).toBe(false);
    wrapper.setProps({ error });
    await wrapper.vm.$nextTick();
    expect(wrapper.find('.error').exists()).toBe(true);
    expect(wrapper.find('.error').text()).toBe(error);
  });
});
