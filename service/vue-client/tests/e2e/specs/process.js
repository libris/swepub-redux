/* eslint-disable no-unused-expressions */
describe('Process - Dataquality', () => {
  beforeEach(() => {
    cy.server();
    cy.route('**/info/sources', 'fixture:sources.json').as('sources');
    cy.route('**/process/**', 'fixture:process.json').as('process');
    cy.route('**/process/**/export?**', 'fixture:process_export.json').as('export');
  });

  it('displays the view when visiting /process', () => {
    cy.visit('/process');
    cy.get('.Process').should('be.visible');
  });

  it('disables submit button by default', () => {
    cy.get('#submit-btn').should('be.disabled');
  });

  it('fetches sources by default', () => {
    cy.visit('/process');
    cy.wait('@sources').then((xhr) => {
      expect(xhr.method).to.eq('GET');
    });
    cy.get('#select-source-select').should('be.visible');
  });

  it('enables search on source selection', () => {
    cy.get('#select-source-select').click().type('{enter}'); // select first available source
    cy.get('#submit-btn').should('not.be.disabled');
  });

  it('sets params in url on search', () => {
    cy.get('#flagdata-heading').should('not.exist');
    cy.location().should((loc) => {
      expect(loc.path).to.be.empty;
    });
    cy.get('#submit-btn').click();
    cy.get('#flagdata-heading').should('exist');
    cy.location().should((loc) => {
      expect(loc.search).to.not.be.empty;
    });
  });

  it('performs search from url params', () => {
    cy.reload();
    cy.wait('@process').then((xhr) => {
      expect(xhr.method).to.eq('GET');
    });
    cy.get('#submit-btn').should('be.disabled');
    cy.get('#flagdata-heading').should('exist');
  });

  it('prints an error on fetch fail - flag cards', () => {
    cy.route({
      method: 'GET',
      url: '**/process/**',
      status: 500,
      response: {
        message: 'test error',
      },
    });
    cy.reload();
    cy.get('.Process-submit .error').should('be.visible');
    cy.get('#flagdata-heading').should('not.exist');
  });

  it('clears the form', () => {
    cy.reload();
    cy.location().should((loc) => {
      expect(loc.search).to.not.be.empty;
    });
    cy.get('#clear-btn').should('not.be.disabled')
      .click();
    cy.location().should((loc) => {
      expect(loc.search).to.be.empty;
    });
    cy.get('#clear-btn').should('be.disabled');
  });

  it('has no flags selected by default', () => {
    cy.visit('/process');
    cy.get('#select-source-select').click().type('{enter}');
    cy.get('#year-from').clear();
    cy.get('#year-to').clear();
    cy.get('#submit-btn').click();
    cy.get('.FlagCard-checkbox').should('have.length.gt', 1);
    cy.get('.FlagCard-checkbox[aria-checked="true"]').should('have.length', 0);
  });

  it('selects flag on flagcard click', () => {
    cy.get('.FlagCard.is-selectable').first().click();
    cy.get('.FlagCard-checkbox[aria-checked="true"]').should('have.length', 1);
  });

  it('enables preview btn on flag selection', () => {
    cy.get('.btn.DataQuality-proceed').should('not.be.disabled');
  });

  it('can select all flags using the toggle', () => {
    cy.get('.FlagPicker-checkAll').click({ multiple: true, force: true });
    const numCheckboxes = Cypress.$('.FlagCard.is-selectable').length;
    cy.get('.FlagCard-checkbox[aria-checked="true"]').should('have.length', numCheckboxes);
  });

  it('can deselect all flags using the toggle', () => {
    cy.get('.FlagPicker-checkAll').click({ multiple: true, force: true });
    cy.get('.FlagCard-checkbox[aria-checked="true"]').should('have.length', 0);
  });

  it('disables preview btn on no flag selection', () => {
    cy.get('.btn.DataQuality-proceed').should('be.disabled');
  });

  it('fetches limited export from api on preview click', () => {
    cy.get('.FlagPicker-checkAll').click({ multiple: true, force: true });
    cy.get('.btn.DataQuality-proceed').click();
    cy.wait('@export').then((xhr) => {
      expect(xhr.status).to.eq(200);
      expect(xhr.url).to.include('limit=');
    });
  });

  it('sets the url export param on preview btn click', () => {
    cy.url().should('include', '/export?');
  });

  it('enables preview btn only if flag selection is changed', () => {
    cy.get('.btn.DataQuality-proceed').should('be.disabled');
    cy.get('.FlagCard.is-selectable').first().click();
    cy.get('.btn.DataQuality-proceed').should('not.be.disabled');
  });

  it('loads result state with back/forward buttons', () => {
    cy.get('.ExportFlags-cardList').should('be.visible');
    cy.go('back');
    cy.get('.ExportFlags-cardList').should('not.be.visible');
    cy.url().should('not.include', '/export?');
    cy.go('forward');
    cy.get('.ExportFlags-cardList').should('be.visible');
  });

  it('prints an error on fetch fail - export preview', () => {
    cy.route({
      method: 'GET',
      url: '**/process/**/export?**',
      status: 500,
      response: {
        message: 'test error',
      },
    });
    cy.reload();
    cy.get('.ExportFlags .error').should('be.visible');
    cy.get('.PreviewCard').should('not.exist');
  });

  it('loads the export section from url', () => {
    cy.reload();
    cy.get('.btn.DataQuality-proceed').should('be.disabled');
    cy.get('.FlagCard').should('exist');
    cy.get('.PreviewCard').should('exist');
    cy.get('.ExportButtons .btn').should('exist')
      .and('not.be.disabled');
  });

  it('omits limit query when clicking export JSON', () => {
    cy.get('#export-json').click();
    cy.wait('@export').then((xhr) => {
      expect(xhr.url).to.not.include('limit=');
    });
  });

  it('asks for CSV file when clicking export CSV', () => {
    cy.get('#export-csv').click();
    cy.wait('@export').then((xhr) => {
      expect(xhr.requestHeaders.accept).to.eq('text/csv');
    });
  });

  it('asks for TSV file when clicking export TSV', () => {
    cy.get('#export-tsv').click();
    cy.wait('@export').then((xhr) => {
      expect(xhr.requestHeaders.accept).to.eq('text/tab-separated-values');
    });
  });

  it('clears the results', () => {
    cy.get('#clear-btn').should('not.be.disabled')
      .click();
    cy.get('.FlagCard').should('not.exist');
    cy.get('.PreviewCard').should('not.exist');
    cy.location().should((loc) => {
      expect(loc.search).to.be.empty;
    });
    cy.get('#clear-btn').should('be.disabled');
  });
});

describe('Process - Harvest status', () => {
  beforeEach(() => {
    cy.server();
    cy.route('**/info/sources', 'fixture:sources.json').as('sources');
    cy.route('**/process/**/status', 'fixture:status.json').as('status');
    cy.route('**/process/**/rejected**', 'fixture:rejected.json').as('rejected');
    cy.route('**/process/**/status/history', 'fixture:history.json').as('history');
  });

  it('displays the view on tab click', () => {
    cy.visit('/process');
    cy.get('#status-tab').click();
    cy.get('.HarvestStatus').should('be.visible');
  });

  it('disables submit button by default', () => {
    cy.get('#submit-btn').should('be.disabled');
  });

  it('loads sources by default', () => {
    cy.visit('/process');
    cy.get('#status-tab').click();
    cy.wait('@sources').then((xhr) => {
      expect(xhr.method).to.eq('GET');
    });
    cy.get('#select-source-select').should('be.visible');
  });

  it('enables search on source selection', () => {
    cy.get('#select-source-select').click().type('{enter}'); // select first available source
    cy.get('#submit-btn').should('not.be.disabled');
  });

  it('sets url params on search', () => {
    cy.get('.HarvestLatest').should('not.exist');
    cy.url().should('not.include', 'status');
    cy.get('#submit-btn').click();
    cy.get('.HarvestLatest').should('exist');
    cy.url().should('include', 'status');
  });

  it('can load latest harvest from url', () => {
    cy.reload();
    cy.wait(['@status', '@rejected']).then((arr) => {
      arr.forEach((xhr) => {
        expect(xhr.method).to.eq('GET');
      });
    });
    cy.get('#submit-btn').should('be.disabled');
    cy.get('.HarvestLatest').should('exist');
    cy.get('.HarvestRejected').should('exist');
  });

  it('prints an error on fetch fail - harvest', () => {
    cy.route({
      method: 'GET',
      url: '**/process/**/status',
      status: 500,
      response: {
        message: 'test error',
      },
    });
    cy.reload();
    cy.get('.HarvestLatest .error').should('be.visible');
  });

  it('can switch to history tab', () => {
    cy.reload();
    cy.get('.HarvestHistory').should('not.exist');
    cy.get('#history-tab').click();
    cy.get('.HarvestHistory').should('exist');
    cy.url().should('include', '/history');
  });

  it('can load history from url', () => {
    cy.reload();
    cy.wait('@history').then((xhr) => {
      expect(xhr.method).to.eq('GET');
    });
    cy.get('#submit-btn').should('be.disabled');
    cy.get('.HarvestHistory').should('exist');
  });

  it('prints an error on fetch fail - history', () => {
    cy.route({
      method: 'GET',
      url: '**/process/**/status/history',
      status: 500,
      response: {
        message: 'test error',
      },
    });
    cy.reload();
    cy.get('.HarvestHistory .error').should('be.visible');
  });

  it('should fetch rejected on harvest card click', () => {
    cy.reload();
    cy.get('.HarvestSummary-card.is-expandable').first()
      .next().should('not.be.visible')
      .prev()
      .click();
    cy.wait('@rejected').then((xhr) => {
      expect(xhr.method).to.eq('GET');
      cy.get('.HarvestSummary-card.is-expandable').first()
        .should('have.class', 'expanded')
        .next()
        .should('be.visible');
    });
  });

  it('can select rejection harvests only', () => {
    const numCards = Cypress.$('.HarvestSummary').length;
    cy.get('#rejected-only-checkbox').check();
    cy.get('.HarvestSummary').should('not.be.gte', numCards);
  });

  it('can switch to latest tab', () => {
    cy.get('.HarvestLatest').should('not.exist');
    cy.get('#latest-tab').click();
    cy.get('.HarvestLatest').should('exist');
    cy.url().should('not.include', '/history');
  });

  it('clears the form', () => {
    cy.url().should('include', 'status');
    cy.get('#clear-btn').should('not.be.disabled')
      .click();
    cy.url().should('not.include', 'status');
    cy.get('#clear-btn').should('be.disabled');
  });
});
