const path = require('path');
process.env.VUE_APP_VERSION = require('./package.json').version;

process.env.VUE_APP_API_PATH = 'api/v1';
// TODO: https://jira.kb.se/browse/SWEPUB2-619
// process.env.VUE_APP_SWEPUB_VERSION = require('./swepub.json').version;

module.exports = {
  publicPath: '/',
  css: {
    loaderOptions: {
      sass: {
        additionalData: `
        @import "@/styles/_variables.scss";
        @import "@/styles/_fonts.scss";
        `,
      },
    },
    // supress cypress code coverage warnings when running yarn test:e2e
    extract: process.env.NODE_ENV === 'production' ? {
      ignoreOrder: true,
    } : false,
  },
  configureWebpack: {
    optimization: {
      splitChunks: {
        cacheGroups: {
          node_vendors: {
            test: /[\\/]node_modules[\\/]/,
            chunks: 'all',
            priority: 1,
          },
        },
      },
    },
    resolve: {
      extensions: ['.js', '.vue', '.json'],
      alias: {
        '~': path.resolve(__dirname, 'src/'),
        '@': path.resolve('src/'),
      },
    },
    externals: {
      moment: 'moment',
    },
  },
  chainWebpack(config) {
    config.plugins.delete('prefetch');
  },
  devServer: {
    proxy: {
      '^/api/v1': {
        target: 'http://127.0.0.1',
        changeOrigin: true,
      },
    },
  },
  transpileDependencies: ['vue-select'],
};
