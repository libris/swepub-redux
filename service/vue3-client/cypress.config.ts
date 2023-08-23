import { defineConfig } from 'cypress'

export default defineConfig({
  e2e: {
    specPattern: 'cypress/specs/*.{js,jsx,ts,tsx}',
    baseUrl: 'http://localhost:4173'
  }
})
