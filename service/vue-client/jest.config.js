module.exports = {
  preset: '@vue/cli-plugin-unit-jest',
  moduleNameMapper: {
    '.+\\.(css|styl|less|sass|scss|png|jpg|svg|ttf|woff|woff2)$': 'jest-transform-stub',
  },
  // collectCoverage: true,
  collectCoverageFrom: [
    'src/components/**/*.{js,vue}',
    'src/views/*.{js,vue}',
    'src/utils/*.{js,vue}',
  ],
  coverageDirectory: '<rootDir>/tests/unit/coverage/',
};
