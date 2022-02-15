# vue-client

Developing the frontend locally requires [Node.js](https://nodejs.org) and running the commands below require [Yarn](https://yarnpkg.com/).
## Project setup
Install dependencies
```
yarn
```

### Compiles and hot-reloads for development
```
yarn serve
```

### Compiles and minifies for production
```
yarn build
```

### Run tests

The frontend app includes a number of unit tests of single components, and e2e-tests of the user workflow. These are written in isolation and don't require any other running services. All network requests are mocked.

To run all tests (headless, for CI and build script integration)

```
yarn test:all
```

**Unit tests**

To run them manually: `yarn test:unit`

And add flags:

`--verbose` for detailed results
`--coverage` to get a coverage report
`--watch` watch for changes during test writing

**E2e tests**

To run in Cypress UI/browser: `yarn test:e2e`

`--headless` runs them in the console.

E2e coverage report can be found here: 
`vue-client/tests/e2e/coverage/lcov-report/index.html`

### Lints and fixes files
```
yarn lint
```

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).
