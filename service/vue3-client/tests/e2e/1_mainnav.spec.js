// e2e tests requires api services running and at least one source harvested

describe('Main navigation', () => {
  beforeEach(() => {
    cy.intercept('**/info/sources', { fixture: 'sources.json' }).as('sources');
    cy.intercept('**/info/research-subjects', { fixture: 'research-subjects.json' }).as('researchSubjects');
    cy.intercept('**/info/output-types', { fixture: 'output-types.json' }).as('outputTypes');
    cy.intercept('**/datastatus', { fixture: 'datastatus.json' }).as('datastatus');
    cy.intercept('**/datastatus/ssif', { fixture: 'datastatus_ssif.json' }).as('ssif');
    cy.intercept('**/datastatus/validations', { fixture: 'datastatus_validations.json' }).as('validations');
  }); 

  it('can navigate to /process', () => {
    cy.visit('/');
    cy.get('.MainNav a[href="/process"]')
      .click();
    cy.location('pathname', { timeout: 10000 }).should('eq', '/process')
    cy.get('.Process').should('be.visible');
    cy.title().should('include', 'Databearbetning')
  });

  it('can navigate to /classify', () => {
    cy.visit('/');
    cy.get('.MainNav a[href="/classify"]')
      .click();
    cy.location('pathname', { timeout: 10000 }).should('eq', '/classify')
    cy.get('.Classify').should('be.visible');
    cy.title().should('include', 'Ämnesklassificering')
  });

  it('can navigate to /datastatus', () => {
    cy.visit('/');
    cy.get('.MainNav a[href="/datastatus"]')
      .click();
    cy.location('pathname', { timeout: 10000 }).should('eq', '/datastatus')
    cy.get('.Datastatus').should('be.visible');
    cy.title().should('include', 'Datastatus')
  });
  
  it('can navigate to /bibliometrics', () => {
    cy.visit('/');
    cy.get('.MainNav a[href="/bibliometrics"]')
      .click();
    cy.location('pathname', { timeout: 10000 }).should('eq', '/bibliometrics')
    cy.get('.Bibliometrics').should('be.visible');
    cy.title().should('include', 'Bibliometri')
  });

  it('navigates back', () => {
    cy.visit('/process');
      cy.get('.MainNav a[href="/classify"]')
      .click();
    cy.go('back');
    cy.get('.Process')
      .should('be.visible');
  });

  it('navigates forward', () => {
    cy.visit('/process');
    cy.get('.MainNav a[href="/classify"]')
    .click();
    cy.go('back');
    cy.go('forward');
    cy.get('.Classify')
      .should('be.visible');
  });

  it('displays the 404 page', () => {
    cy.visit('/test');
    cy.get('.NotFound').should('exist');
  });
});
