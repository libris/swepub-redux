/* eslint-disable no-unused-expressions */
describe('Bibliometrics', () => {
  beforeEach(() => {
    cy.server();
    cy.route('**/info/sources', 'fixture:sources.json').as('sources');
    cy.route('**/info/research-subjects', 'fixture:research-subjects.json').as('researchSubjects');
    cy.route('**/info/output-types', 'fixture:output-types.json').as('outputTypes');
    cy.route('POST', '**/bibliometrics', 'fixture:bibliometrics.json').as('bibliometrics');
  });

  it('displays the view when visiting app root', () => {
    cy.visit('/');
    cy.get('.Bibliometrics').should('be.visible');
  });

  it('displays the view when visiting /bibliometrics', () => {
    cy.visit('/bibliometrics');
    cy.get('.Bibliometrics').should('be.visible');
  });

  it('enables submit button by default', () => {
    cy.get('#submit-btn').should('not.be.disabled');
  });

  it('fetches sources by default', () => {
    cy.visit('/bibliometrics');
    cy.wait('@sources').then((xhr) => {
      expect(xhr.method).to.eq('GET');
    });
    cy.get('#select-source-select').should('be.visible');
  });

  it('fetches research-subjects by default', () => {
    cy.visit('/bibliometrics');
    cy.wait('@researchSubjects').then((xhr) => {
      expect(xhr.method).to.eq('GET');
    });
    cy.get('#select-classification-select').should('be.visible');
  });

  it('fetches output-types by default', () => {
    cy.visit('/bibliometrics');
    cy.wait('@outputTypes').then((xhr) => {
      expect(xhr.method).to.eq('GET');
    });
    cy.get('#select-output-select').should('be.visible');
  });

  it('makes limited post request to bibliometrics api on search', () => {
    cy.visit('/bibliometrics');
    cy.get('#submit-btn').click();
    cy.wait('@bibliometrics').then((xhr) => {
      expect(xhr.method).to.eq('POST');
      expect(xhr.requestBody.limit).to.eq(20);
    });
  });

  it('displays error and disables submit button on invalid year input', () => {
    cy.visit('/bibliometrics');
    cy.get('#year-from')
      .clear()
      .type('0')
      .should('have.attr', 'aria-invalid', 'true');
    cy.get('.YearPicker .error').should('be.visible');
    cy.get('#submit-btn').should('be.disabled');
    cy.get('#year-from')
      .clear()
      .type('2020');
    cy.get('#year-to')
      .clear()
      .type('2019')
      .should('have.attr', 'aria-invalid', 'true');
    cy.get('.YearPicker .error').should('be.visible');
    cy.get('#submit-btn').should('be.disabled');
  });

  it('clears the year input error and enables submit button', () => {
    cy.get('.YearPicker .error').should('be.visible');
    cy.get('#year-from')
      .clear()
      .type('2020');
    cy.get('#year-to')
      .clear()
      .type('2020');
    cy.get('.YearPicker .error').should('not.be.visible');
    cy.get('#submit-btn').should('not.be.disabled');
  });

  it('sets year url query on search', () => {
    cy.visit('/bibliometrics');
    cy.get('#year-from')
      .clear()
      .type('1900');
    cy.get('#year-to')
      .clear()
      .type('1900');
    cy.get('#submit-btn').click();
    cy.url()
      .should('include', 'from=1900')
      .and('include', 'to=1900');
    cy.get('#preview-section').should('be.visible');
  });

  it('navigates back to earlier state', () => {
    cy.go('back');
    cy.url()
      .should('not.include', 'from=1900')
      .and('not.include', 'to=1900');
    cy.get('#preview-section').should('not.be.visible');
  });

  it('inputs years from url query', () => {
    cy.visit('/bibliometrics?from=1800&to=1800');
    cy.get('#year-from').should('have.value', '1800');
    cy.get('#year-to').should('have.value', '1800');
    cy.get('#preview-section').should('be.visible');
  });

  it('displays error if invalid years query in url', () => {
    cy.visit('/bibliometrics?from=1800&to=1700');
    cy.get('.YearPicker .error').should('be.visible');
  });

  it('sets the classification url query on search', () => {
    cy.visit('/bibliometrics');
    cy.get('#select-classification-select').click().type('{enter}'); // select first available classification
    cy.get('#submit-btn').click();
    cy.url().should('include', 'classification');
    cy.get('#preview-section').should('be.visible');
  });

  it('sets the output-type url query on search', () => {
    cy.visit('/bibliometrics');
    cy.get('#select-output-select').click().type('{enter}'); // select first available output type
    cy.get('#submit-btn').click();
    cy.url().should('include', 'genreForm');
    cy.get('#preview-section').should('be.visible');
  });

  it('sets keyword url query on search', () => {
    cy.visit('/bibliometrics');
    cy.get('#keywords_input').type('test_keyword');
    cy.get('#submit-btn').click();
    cy.url().should('include', 'keywords=test');
    cy.get('#preview-section').should('be.visible');
  });

  it('inputs keyword from url query', () => {
    cy.visit('/bibliometrics?keywords=test_keyword');
    cy.get('#keywords_input').should('have.value', 'test_keyword');
    cy.get('#preview-section').should('be.visible');
  });

  it('sets publication status url query on search', () => {
    cy.visit('/bibliometrics');
    cy.get('#publication-status').click();
    cy.get('#published').check();
    cy.get('#epub').check();
    cy.get('#submitted').check();
    cy.get('#submit-btn').click();
    cy.url().should('include', 'publicationStatus=published&publicationStatus=epub&publicationStatus=submitted');
    cy.get('#preview-section').should('be.visible');
  });

  it('checks publication status from url query', () => {
    cy.visit('/bibliometrics?publicationStatus=published&publicationStatus=epub&publicationStatus=submitted');
    cy.get('#published').should('be.checked');
    cy.get('#epub').should('be.checked');
    cy.get('#submitted').should('be.checked');
    cy.get('#preview-section').should('be.visible');
  });

  it('sets content marking url query on search', () => {
    cy.visit('/bibliometrics');
    cy.get('#content-marking').click();
    cy.get('#ref').check();
    cy.get('#vet').check();
    cy.get('#pop').check();
    cy.get('#submit-btn').click();
    cy.url()
      .should('include', 'contentMarking=ref&contentMarking=vet&contentMarking=pop');
    cy.get('#preview-section').should('be.visible');
  });

  it('checks content markings from url query', () => {
    cy.visit('/bibliometrics?contentMarking=ref&contentMarking=vet&contentMarking=pop');
    cy.get('#ref').should('be.checked');
    cy.get('#vet').should('be.checked');
    cy.get('#pop').should('be.checked');
    cy.get('#preview-section').should('be.visible');
  });

  it('sets swedish list url query on search', () => {
    cy.visit('/bibliometrics');
    cy.get('#swedish-list').check();
    cy.get('#submit-btn').click();
    cy.url().should('include', 'swedishList=true');
    cy.get('#preview-section').should('be.visible');
  });

  it('checks swedish list from url query', () => {
    cy.visit('/bibliometrics?swedishList=true');
    cy.get('#swedish-list').should('be.checked');
    cy.get('#preview-section').should('be.visible');
  });

  it('clears the form', () => {
    cy.visit('/bibliometrics?classification=1&keywords=test&publicationStatus=published&publicationStatus=epub&publicationStatus=submitted&contentMarking=ref&contentMarking=vet&contentMarking=pop&swedishList=true&match-genreForm=intellectual-property&from=1900&to=1900');
    cy.location().should((loc) => {
      expect(loc.search).to.not.be.empty;
    });
    cy.get('#pop').should('be.checked');
    cy.get('#published').should('be.checked');
    cy.get('#preview-section')
      .should('be.visible');
    cy.get('#clear-btn').click();
    cy.location().should((loc) => {
      expect(loc.search).to.be.empty;
    });
    cy.get('#pop').should('not.be.checked');
    cy.get('#published').should('not.be.checked');
    cy.get('#preview-section').should('not.exist');
  });

  it('sets source url query on search', () => {
    cy.visit('/bibliometrics');
    cy.get('#select-source-select').click().type('{enter}'); // select first available source
    cy.get('#year-from').clear();
    cy.get('#year-to').clear();
    cy.get('#submit-btn').click();
    cy.url().should('include', 'org=');
    cy.get('#preview-section').should('be.visible');
  });

  it('prints an error on fetch fail', () => {
    cy.route({
      method: 'POST',
      url: '**/bibliometrics',
      status: 500,
      response: {
        message: 'test error',
      },
    });
    cy.reload();
    cy.get('#preview-section .error').should('be.visible');
  });

  it('pre-selects record id as export field', () => {
    cy.reload();
    cy.get('.ExportData-toggleGroups .CheckboxToggle.is-checked').should('have.length', 1)
      .and('have.text', 'Record ID');
    cy.get('.PreviewTable-table th').should('have.length', 1)
      .and('have.text', 'Record ID');
  });

  it('can select all fields using the toggle', () => {
    cy.get('#export_checkAll').click();
    cy.get('.ExportData-toggleGroups .CheckboxToggle.is-checked').should('have.length.gt', 1);
    cy.get('.PreviewTable-table th').should('have.length.gt', 1);
  });

  it('can deselect all fields using the toggle', () => {
    cy.get('#export_checkAll').click();
    cy.get('.ExportData-toggleGroups .CheckboxToggle.is-checked').should('have.length', 0);
    cy.get('.PreviewTable').should('not.exist');
  });

  it('disables export btns when no export fields selected', () => {
    cy.get('.ExportButtons .btn').should('be.disabled');
  });

  it('can select fields manually', () => {
    cy.get('.CheckboxToggle').first().click();
    cy.get('.CheckboxToggle').eq(1).click();
    cy.get('.CheckboxToggle').eq(2).click();
    cy.get('.ExportData-toggleGroups .CheckboxToggle.is-checked').should('have.length', 3);
    cy.get('.PreviewTable-table th').should('have.length', 3);
  });

  it('enables export btns when export fields are selected', () => {
    cy.get('.ExportButtons .btn').should('not.be.disabled');
  });

  it('omits limit param and includes fields from UI when clicking export JSON', () => {
    cy.get('#export-json').click();
    cy.wait('@bibliometrics').then((xhr) => {
      expect(JSON.stringify(xhr.requestBody.fields)).to.eq((JSON.stringify(
        ['recordId', 'duplicateIds', 'publicationCount'],
      )));
      expect(xhr.requestBody).to.not.have.ownProperty('limit');
      expect(xhr.method).to.eq('POST');
    });
  });

  it('asks for CSV file when clicking export CSV', () => {
    cy.get('#export-csv').click();
    cy.wait('@bibliometrics').then((xhr) => {
      expect(xhr.requestHeaders.accept).to.eq('text/csv');
    });
  });

  it('asks for TSV file when clicking export TSV', () => {
    cy.get('#export-tsv').click();
    cy.wait('@bibliometrics').then((xhr) => {
      expect(xhr.requestHeaders.accept).to.eq('text/tab-separated-values');
    });
  });

  it('clears the results', () => {
    cy.get('#clear-btn').click();
    cy.get('.ExportData-pickerContainer').should('not.exist');
    cy.get('.PreviewTable').should('not.exist');
  });

  it('displays the datadump section on tab click', () => {
    cy.get('.Datadump').should('not.be.visible');
    cy.get('#datadump-tab').click();
    cy.url().should('include', '/datadump');
    cy.get('.Datadump').should('be.visible');
  });

  it('displays datadump section on url load', () => {
    cy.visit('/bibliometrics/datadump');
    cy.get('.Datadump').should('be.visible');
  });
});
