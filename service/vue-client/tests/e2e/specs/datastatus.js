describe('Datastatus', () => {
  beforeEach(() => {
    cy.server();
    cy.route('**/info/sources', 'fixture:sources.json').as('sources');
    cy.route('**/datastatus', 'fixture:datastatus.json').as('datastatus');
    cy.route('**/datastatus/**', 'fixture:datastatus.json').as('datastatus_single');
    cy.route('**/datastatus/ssif', 'fixture:datastatus_ssif.json').as('ssif');
    cy.route('**/datastatus/ssif/**', 'fixture:datastatus_ssif_single.json').as('ssif_single');
    cy.route('**/datastatus/validations', 'fixture:datastatus_validations.json').as('validations');
    cy.route('**/datastatus/validations/**', 'fixture:datastatus_validations_single').as('validations_single');
  });

  it('displays the view when visiting /datastatus', () => {
    cy.visit('/datastatus');
    cy.get('.Datastatus').should('be.visible');
  });

  it('disables submit button by default', () => {
    cy.get('#submit-btn').should('be.disabled');
  });

  it('loads sources by default', () => {
    cy.visit('/datastatus');
    cy.wait('@sources').then((xhr) => {
      expect(xhr.method).to.eq('GET');
    });
    cy.get('#select-source-select').should('be.visible');
  });

  it('loads the datastatus summary by default', () => {
    cy.visit('/datastatus');
    cy.wait('@datastatus').then((xhr) => {
      expect(xhr.method).to.eq('GET');
    });
    cy.get('.Summary').should('be.visible');
  });

  it('loads the datastatus ssif by default', () => {
    cy.visit('/datastatus');
    cy.wait('@ssif').then((xhr) => {
      expect(xhr.method).to.eq('GET');
    });
    cy.get('#classifications-heading').should('be.visible');
  });

  it('loads the validation stats by default', () => {
    cy.visit('/datastatus');
    cy.wait('@validations').then((xhr) => {
      expect(xhr.method).to.eq('GET');
    });
    cy.get('#validations-heading').should('be.visible');
  });

  it('prints an error on fetch fail', () => {
    cy.route({
      method: 'GET',
      url: '**/datastatus',
      status: 500,
      response: {
        message: 'test error',
      },
    });
    cy.visit('/datastatus');
    cy.get('.Datastatus-chartContainer .error').should('be.visible');
  });

  it('triggers tooltip on helpbubble click', () => {
    cy.get('.tooltip').should('not.exist');
    cy.get('.HelpBubble').first().click();
    cy.get('.tooltip').should('be.visible');
  });

  it('displays the tooltip text', () => {
    cy.get('.t-header')
      .should(($el) => {
        expect($el.text().trim()).not.equal('');
      });
    cy.get('.t-body')
      .should(($el) => {
        expect($el.text().trim()).not.equal('');
      });
  });

  it('hides tooltip on clickaway', () => {
    cy.get('.tooltip').should('exist');
    cy.get('#main').click({ force: true });
    cy.get('.tooltip').should('not.be.visible');
  });

  it('enables search on source selection', () => {
    cy.get('#select-source-select').click().type('{enter}'); // select first available source
    cy.get('#submit-btn').should('not.be.disabled');
  });

  it('sets url params on search', () => {
    cy.url().should('not.include', 'datastatus/');
    cy.get('#year-from').type(2000);
    cy.get('#year-to').type(2020);
    cy.get('#submit-btn').click();
    cy.url().should('include', 'datastatus/')
      .and('include', 'from=2000')
      .and('include', 'to=2020');
  });

  it('navigates back to earlier state', () => {
    cy.go('back');
    cy.url()
      .should('not.include', 'from=2000')
      .and('not.include', 'to=2020');
    cy.go('forward');
  });

  it('can load single org from url params', () => {
    cy.reload();
    cy.wait('@validations_single').then(() => {
      cy.get('#submit-btn').should('be.disabled');
      cy.get('#totalNumber').should('not.exist');
      cy.get('.Summary').should('be.visible');
      cy.get('.ShortStats').should('be.visible');
    });
  });

  it('clears the results', () => {
    cy.get('#clear-btn').click();
    cy.url().should('not.include', 'datastatus/')
      .and('not.include', 'from=')
      .and('not.include', 'to=');
    cy.get('#totalNumber').should('exist');
    cy.get('#year-from').should('have.value', '');
    cy.get('#year-to').should('have.value', '');
  });
});
