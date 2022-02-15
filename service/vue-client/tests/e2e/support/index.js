// ***********************************************************
// This example support/index.js is processed and
// loaded automatically before your test files.
//
// This is a great place to put global configuration and
// behavior that modifies Cypress.
//
// You can change the location of this file or turn off
// automatically serving support files with the
// 'supportFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

// Import commands.js using ES2015 syntax:
import './commands';

import '@cypress/code-coverage/support';

// Alternatively you can use CommonJS syntax:
// require('./commands')

// Force use of xmlhttprequest, fetch not supported by Cypress
Cypress.on('window:before:load', (win) => {
  delete win.fetch;
});

// workaround to fix smooth-scroll issue, see
// https://github.com/cypress-io/cypress/issues/3200
Cypress.on('window:before:load', (win) => {
  const htmlNode = win.document.querySelector('html');
  htmlNode.classList.add('cypress-tests');
});
