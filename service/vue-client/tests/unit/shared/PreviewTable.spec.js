import { shallowMount } from '@vue/test-utils';
import PreviewTable from '@/components/shared/PreviewTable.vue';

let wrapper = null;

beforeEach(() => {
  wrapper = shallowMount(PreviewTable, {
    propsData: {
      tableCols: [{}, {}], // 2
      previewData: {
        from: 2020,
        hits: [{}, {}, {}], // 3
        query: {},
        to: 2020,
        total: 201,
      },
      tableLayout: 'test',
    },
  });
});

afterEach(() => {
  wrapper.destroy();
});

describe('PreviewTable', () => {
  it('renders the same number of table headers as length of prop tableCols', () => {
    expect(wrapper.findAll('th').length).toBe(2);
  });

  it('renders the same number of table rows as length of previewData[hitsProp]', () => {
    expect(wrapper.findAll('tr').length).toBe(3 + 1); // +1 row for thead
  });

  it('applies the tableLayout class', () => {
    expect(wrapper.classes('test')).toBe(true);
  });
});
