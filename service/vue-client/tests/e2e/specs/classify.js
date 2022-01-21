describe('Classify', () => {
  beforeEach(() => {
    cy.server();
    cy.route('POST', '**/classify', 'fixture:classify.json').as('classify');
  });

  it('displays the view when visiting /classify', () => {
    cy.visit('/classify');
    cy.get('.Classify').should('be.visible');
  });

  it('disabled submit button by default', () => {
    cy.get('#submit-btn').should('be.disabled');
  });

  it('enables submit after input', () => {
    cy.get('#title_input').type('test');
    cy.get('#submit-btn').should('not.be.disabled');
  });

  it('posts expected data on submit', () => {
    cy.visit('/classify');
    cy.get('#title_input').type('test');
    cy.get('#abstract_input').type('test');
    cy.get('#keywords_input').type('test');
    cy.get('#level_5').check();
    cy.get('#submit-btn').click();
    cy.wait('@classify').then((xhr) => {
      expect(JSON.stringify(xhr.requestBody)).to.eq((JSON.stringify({
        level: 5, title: 'test', abstract: 'test', keywords: 'test',
      })));
      expect(xhr.method).to.eq('POST');
    });
  });

  it('displays result', () => {
    cy.get('#result').should('be.visible');
  });

  it('can clear the form', () => {
    cy.get('#clear-btn').should('not.be.disabled')
      .click();
    cy.get('#title_input').should('have.value', '');
    cy.get('#abstract_input').should('have.value', '');
    cy.get('#keywords_input').should('have.value', '');
    cy.get('#level_3').should('be.checked');
    cy.get('#submit-btn').should('be.disabled');
    cy.get('#clear-btn').should('be.disabled');
    cy.get('#result').should('not.be.visible');
  });

  it('displays the about section', () => {
    cy.get('.Documentation').should('not.be.visible');
    cy.get('#about-tab').click();
    cy.url().should('include', '/about');
    cy.get('.Documentation').should('be.visible');
  });

  it('loads about section from url', () => {
    cy.visit('/classify/about');
    cy.get('.Documentation').should('be.visible');
  });
});
