// e2e tests requires api services running and at least one source harvested

describe('Main navigation', () => {
  beforeEach(() => {
    cy.server();
    cy.route('**/info/sources', 'fixture:sources.json').as('sources');
    cy.route('**/info/research-subjects', 'fixture:research-subjects.json').as('researchSubjects');
    cy.route('**/info/output-types', 'fixture:output-types.json').as('outputTypes');
    cy.route('**/datastatus', 'fixture:datastatus.json').as('datastatus');
    cy.route('**/datastatus/ssif', 'fixture:datastatus_ssif.json').as('ssif');
    cy.route('**/datastatus/validations', 'fixture:datastatus_validations.json').as('validations');
  });

  it('can navigate to /process', () => {
    cy.visit('/');
    cy.get('.MainNav a[href="/process"]')
      .click();
  });

  it('displays process view', () => {
    cy.get('.Process')
      .should('be.visible');
  });

  it('has Process in page title', () => {
    cy.title().should((title) => {
      expect(title).to.contain('Databearbetning');
    });
  });

  it('navigates to /classify', () => {
    cy.get('.MainNav a[href="/classify"]')
      .click();
  });

  it('displays Classify view', () => {
    cy.get('.Classify')
      .should('be.visible');
  });

  it('has Classify in page title', () => {
    cy.title().should((title) => {
      expect(title).to.contain('Ämnesklassificering');
    });
  });

  it('navigates to /datastatus', () => {
    cy.get('.MainNav a[href="/datastatus"]')
      .click();
  });

  it('displays Datastatus view', () => {
    cy.get('.Datastatus')
      .should('be.visible');
  });

  it('has Datastatus in page title', () => {
    cy.title().should((title) => {
      expect(title).to.contain('Datastatus');
    });
  });

  it('navigates to /bibliometrics', () => {
    cy.get('.MainNav a[href="/bibliometrics"]')
      .click();
  });

  it('displays Bibliometrics view', () => {
    cy.get('.Bibliometrics')
      .should('be.visible');
  });

  it('has Bibliometrics in page title', () => {
    cy.title().should((title) => {
      expect(title).to.contain('Bibliometri');
    });
  });

  it('navigates back', () => {
    cy.go('back');
    cy.get('.Datastatus')
      .should('be.visible');
  });

  it('navigates forward', () => {
    cy.go('forward');
    cy.get('.Bibliometrics')
      .should('be.visible');
  });

  it('displays the 404 page', () => {
    cy.visit('/test');
    cy.get('.NotFound').should('exist');
  });
});
