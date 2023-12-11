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
        swe: 'Vetenskaplig eller kommenterad utgåva',
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

const transformed = [{"label":"IMMATERIALRÄTTSLIG OUTPUT - ALLA","value":"*intellectual-property","sortKey":"IMMATERIALRÄTTSLIG OUTPUT - ALLA"},{"label":"Immaterialrättslig output","value":"intellectual-property","sortKey":"IMMATERIALRÄTTSLIG OUTPUT - ALLA"},{"label":"-- Patent","value":"intellectual-property.patent","sortKey":"IMMATERIALRÄTTSLIG OUTPUT - ALLA - Patent"},{"label":"-- Övrig immaterialrättslig output","value":"intellectual-property.other","sortKey":"IMMATERIALRÄTTSLIG OUTPUT - ALLA - Övrig immaterialrättslig output"},{"label":"KONFERENSOUTPUT - ALLA","value":"*conference","sortKey":"KONFERENSOUTPUT - ALLA"},{"label":"Konferensoutput","value":"conference","sortKey":"KONFERENSOUTPUT - ALLA"},{"label":"-- Paper i proceeding","value":"conference.paper","sortKey":"KONFERENSOUTPUT - ALLA - Paper i proceeding"},{"label":"-- Poster","value":"conference.poster","sortKey":"KONFERENSOUTPUT - ALLA - Poster"},{"label":"-- Proceeding (redaktörskap)","value":"conference.proceeding","sortKey":"KONFERENSOUTPUT - ALLA - Proceeding (redaktörskap)"},{"label":"-- Övriga konferensbidrag","value":"conference.other","sortKey":"KONFERENSOUTPUT - ALLA - Övriga konferensbidrag"},{"label":"KONSTNÄRLIG OUTPUT - ALLA","value":"*artistic-work","sortKey":"KONSTNÄRLIG OUTPUT - ALLA"},{"label":"Konstnärlig output","value":"artistic-work","sortKey":"KONSTNÄRLIG OUTPUT - ALLA"},{"label":"-- Dokumenterat konstnärligt forskningsprojekt (doktorsavhandling)","value":"artistic-work.artistic-thesis","sortKey":"KONSTNÄRLIG OUTPUT - ALLA - Dokumenterat konstnärligt forskningsprojekt (doktorsavhandling)"},{"label":"-- Konstnärligt arbete","value":"artistic-work.original-creative-work","sortKey":"KONSTNÄRLIG OUTPUT - ALLA - Konstnärligt arbete"},{"label":"PUBLIKATION - ALLA","value":"*publication","sortKey":"PUBLIKATION - ALLA"},{"label":"Publikation","value":"publication","sortKey":"PUBLIKATION - ALLA"},{"label":"-- Artikel i dags-/nyhetstidning","value":"publication.newspaper-article","sortKey":"PUBLIKATION - ALLA - Artikel i dags-/nyhetstidning"},{"label":"-- Artikel i vetenskaplig tidskrift","value":"publication.journal-article","sortKey":"PUBLIKATION - ALLA - Artikel i vetenskaplig tidskrift"},{"label":"-- Artikel i övriga tidskrifter","value":"publication.magazine-article","sortKey":"PUBLIKATION - ALLA - Artikel i övriga tidskrifter"},{"label":"-- Bidrag till encyklopedi","value":"publication.encyclopedia-entry","sortKey":"PUBLIKATION - ALLA - Bidrag till encyklopedi"},{"label":"-- Bok","value":"publication.book","sortKey":"PUBLIKATION - ALLA - Bok"},{"label":"-- Doktorsavhandling","value":"publication.doctoral-thesis","sortKey":"PUBLIKATION - ALLA - Doktorsavhandling"},{"label":"-- Forskningsöversiktsartikel","value":"publication.review-article","sortKey":"PUBLIKATION - ALLA - Forskningsöversiktsartikel"},{"label":"-- För-/Efterord","value":"publication.foreword-afterword","sortKey":"PUBLIKATION - ALLA - För-/Efterord"},{"label":"-- Inledande text i tidskrift / proceeding (letters, editorials, comments, notes)","value":"publication.editorial-letter","sortKey":"PUBLIKATION - ALLA - Inledande text i tidskrift / proceeding (letters, editorials, comments, notes)"},{"label":"-- Kapitel i rapport","value":"publication.report-chapter","sortKey":"PUBLIKATION - ALLA - Kapitel i rapport"},{"label":"-- Kapitel i samlingsverk","value":"publication.book-chapter","sortKey":"PUBLIKATION - ALLA - Kapitel i samlingsverk"},{"label":"-- Licentiatavhandling","value":"publication.licentiate-thesis","sortKey":"PUBLIKATION - ALLA - Licentiatavhandling"},{"label":"-- Preprint","value":"publication.preprint","sortKey":"PUBLIKATION - ALLA - Preprint"},{"label":"-- Rapport","value":"publication.report","sortKey":"PUBLIKATION - ALLA - Rapport"},{"label":"-- Recension","value":"publication.book-review","sortKey":"PUBLIKATION - ALLA - Recension"},{"label":"-- Samlingsverk (redaktörsskap)","value":"publication.edited-book","sortKey":"PUBLIKATION - ALLA - Samlingsverk (redaktörsskap)"},{"label":"-- Special-/temanummer av tidskrift (redaktörskap)","value":"publication.journal-issue","sortKey":"PUBLIKATION - ALLA - Special-/temanummer av tidskrift (redaktörskap)"},{"label":"-- Vetenskaplig eller kommenterad utgåva","value":"publication.critical-edition","sortKey":"PUBLIKATION - ALLA - Vetenskaplig eller kommenterad utgåva"},{"label":"-- Working paper","value":"publication.working-paper","sortKey":"PUBLIKATION - ALLA - Working paper"},{"label":"-- Övrig publikation","value":"publication.other","sortKey":"PUBLIKATION - ALLA - Övrig publikation"},{"label":"ÖVRIG OUTPUT - ALLA","value":"*other","sortKey":"ÖVRIG OUTPUT - ALLA"},{"label":"Övrig output","value":"other","sortKey":"ÖVRIG OUTPUT - ALLA"},{"label":"-- Dataset","value":"other.data-set","sortKey":"ÖVRIG OUTPUT - ALLA - Dataset"},{"label":"-- Programvara","value":"other.software","sortKey":"ÖVRIG OUTPUT - ALLA - Programvara"}];

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
