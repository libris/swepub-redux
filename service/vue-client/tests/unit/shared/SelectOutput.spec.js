import { shallowMount } from '@vue/test-utils';
import SelectOutput from '@/components/shared/SelectOutput.vue';

import { enableFetchMocks } from 'jest-fetch-mock';

enableFetchMocks();

const apiReponse = {
  'intellectual-property': {
    swe: 'Immaterialrättslig output',
    subcategories: {
      patent: {
        swe: 'Patent',
      },
      other: {
        swe: 'Övrig immaterialrättslig output',
      },
    },
  },
  conference: {
    swe: 'Konferensoutput',
    subcategories: {
      paper: {
        swe: 'Paper i proceeding',
      },
      poster: {
        swe: 'Poster',
      },
      proceeding: {
        swe: 'Proceeding (redaktörskap)',
      },
      other: {
        swe: 'Övriga konferensbidrag',
      },
    },
  },
  'artistic-work': {
    swe: 'Konstnärlig output',
    subcategories: {
      'artistic-thesis': {
        swe: 'Dokumenterat konstnärligt forskningsprojekt (doktorsavhandling)',
      },
      'original-creative-work': {
        swe: 'Konstnärligt arbete',
      },
    },
  },
  publication: {
    swe: 'Publikation',
    subcategories: {
      'newspaper-article': {
        swe: 'Artikel i dags-/nyhetstidning',
      },
      'journal-article': {
        swe: 'Artikel i vetenskaplig tidskrift',
      },
      'magazine-article': {
        swe: 'Artikel i övriga tidskrifter',
      },
      'encyclopedia-entry': {
        swe: 'Bidrag till encyklopedi',
      },
      book: {
        swe: 'Bok',
      },
      'doctoral-thesis': {
        swe: 'Doktorsavhandling',
      },
      'review-article': {
        swe: 'Forskningsöversiktsartikel',
      },
      'foreword-afterword': {
        swe: 'För-/Efterord',
      },
      'editorial-letter': {
        swe: 'Inledande text i tidskrift / proceeding (letters, editorials, comments, notes)',
      },
      'report-chapter': {
        swe: 'Kapitel i rapport',
      },
      'book-chapter': {
        swe: 'Kapitel i samlingsverk',
      },
      'licentiate-thesis': {
        swe: 'Licentiatavhandling',
      },
      preprint: {
        swe: 'Preprint',
      },
      report: {
        swe: 'Rapport',
      },
      'book-review': {
        swe: 'Recension',
      },
      'edited-book': {
        swe: 'Samlingsverk (redaktörsskap)',
      },
      'journal-issue': {
        swe: 'Special-/temanummer av tidskrift (redaktörskap)',
      },
      'critical-edition': {
        swe: 'Textkritisk utgåva',
      },
      'working-paper': {
        swe: 'Working paper',
      },
      other: {
        swe: 'Övrig publikation',
      },
    },
  },
  other: {
    swe: 'Övrig output',
    subcategories: {
      'data-set': {
        swe: 'Dataset',
      },
      software: {
        swe: 'Programvara',
      },
    },
  },
};

const transformed = [{ label: 'IMMATERIALRÄTTSLIG OUTPUT - ALLA', value: '*intellectual-property' }, { label: 'Immaterialrättslig output', value: 'intellectual-property' }, { label: 'Patent', value: 'intellectual-property.patent' }, { label: 'Övrig immaterialrättslig output', value: 'intellectual-property.other' }, { label: 'KONFERENSOUTPUT - ALLA', value: '*conference' }, { label: 'Konferensoutput', value: 'conference' }, { label: 'Paper i proceeding', value: 'conference.paper' }, { label: 'Poster', value: 'conference.poster' }, { label: 'Proceeding (redaktörskap)', value: 'conference.proceeding' }, { label: 'Övriga konferensbidrag', value: 'conference.other' }, { label: 'KONSTNÄRLIG OUTPUT - ALLA', value: '*artistic-work' }, { label: 'Konstnärlig output', value: 'artistic-work' }, { label: 'Dokumenterat konstnärligt forskningsprojekt (doktorsavhandling)', value: 'artistic-work.artistic-thesis' }, { label: 'Konstnärligt arbete', value: 'artistic-work.original-creative-work' }, { label: 'PUBLIKATION - ALLA', value: '*publication' }, { label: 'Publikation', value: 'publication' }, { label: 'Artikel i dags-/nyhetstidning', value: 'publication.newspaper-article' }, { label: 'Artikel i vetenskaplig tidskrift', value: 'publication.journal-article' }, { label: 'Artikel i övriga tidskrifter', value: 'publication.magazine-article' }, { label: 'Bidrag till encyklopedi', value: 'publication.encyclopedia-entry' }, { label: 'Bok', value: 'publication.book' }, { label: 'Doktorsavhandling', value: 'publication.doctoral-thesis' }, { label: 'Forskningsöversiktsartikel', value: 'publication.review-article' }, { label: 'För-/Efterord', value: 'publication.foreword-afterword' }, { label: 'Inledande text i tidskrift / proceeding (letters, editorials, comments, notes)', value: 'publication.editorial-letter' }, { label: 'Kapitel i rapport', value: 'publication.report-chapter' }, { label: 'Kapitel i samlingsverk', value: 'publication.book-chapter' }, { label: 'Licentiatavhandling', value: 'publication.licentiate-thesis' }, { label: 'Preprint', value: 'publication.preprint' }, { label: 'Rapport', value: 'publication.report' }, { label: 'Recension', value: 'publication.book-review' }, { label: 'Samlingsverk (redaktörsskap)', value: 'publication.edited-book' }, { label: 'Special-/temanummer av tidskrift (redaktörskap)', value: 'publication.journal-issue' }, { label: 'Textkritisk utgåva', value: 'publication.critical-edition' }, { label: 'Working paper', value: 'publication.working-paper' }, { label: 'Övrig publikation', value: 'publication.other' }, { label: 'ÖVRIG OUTPUT - ALLA', value: '*other' }, { label: 'Övrig output', value: 'other' }, { label: 'Dataset', value: 'other.data-set' }, { label: 'Programvara', value: 'other.software' }];

let wrapper = null;
const $store = {
  getters: {
    settings: {
      language: 'swe',
    },
  },
};

beforeEach(() => {
  fetch.resetMocks();
  fetch.mockResponse(JSON.stringify(apiReponse));
  wrapper = shallowMount(SelectOutput, {
    propsData: {
      apiEndpoint: null,
    },
    mocks: {
      $store,
    },
  });
});

afterEach(() => {
  wrapper.destroy();
  jest.clearAllMocks();
});

describe('SelectOutput', () => {
  it('transforms the options correctly', async () => {
    await wrapper.vm.$nextTick();
    expect(JSON.stringify(transformed))
      .toEqual(JSON.stringify(wrapper.vm.options));
  });
});
