import { shallowMount } from '@vue/test-utils';
import ExportButtons from '@/components/shared/ExportButtons.vue';

let wrapper = null;
const onClick = jest.fn();

beforeEach(() => {
  wrapper = shallowMount(ExportButtons, {
    propsData: {
      exportLoading: true,
      exportAllowed: false,
      exportError: 'test error',
    },
    listeners: {
      'export-json': onClick,
      'export-csv': onClick,
      'export-tsv': onClick,
    },
  });
});

afterEach(() => {
  wrapper.destroy();
  jest.clearAllMocks();
});

describe('ExportButtons', () => {
  it('does not display a spinner when not loading', () => {
    const loader = wrapper.findAll('vue-simple-spinner-stub');
    expect(loader.length).toEqual(1);
  });

  it('displays a spinner when loading', () => {
    wrapper.setProps({ exportLoading: false });
    wrapper.vm.$nextTick(() => {
      const loader = wrapper.findAll('vue-simple-spinner-stub');
      expect(loader.length).toEqual(0);
    });
  });

  it('does not emit events on click when !exportAllowed', () => {
    const buttons = wrapper.findAll('button');
    buttons.trigger('click');
    expect(onClick).not.toHaveBeenCalled();
  });

  it('emits events on click when exportAllowed', () => {
    wrapper.setProps({ exportAllowed: true });
    wrapper.vm.$nextTick(() => {
      const buttons = wrapper.findAll('button');
      buttons.trigger('click');
      expect(onClick).toHaveBeenCalledTimes(buttons.length);
    });
  });

  it('renders the export error', () => {
    const error = wrapper.find('.error');
    expect(error.text()).toEqual('test error');
  });
});
