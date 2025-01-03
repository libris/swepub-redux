const path = require('path');
process.env.VUE_APP_VERSION = require('./package.json').version;

process.env.VUE_APP_API_PATH = '/api/v2';
// TODO: https://jira.kb.se/browse/SWEPUB2-619
// process.env.VUE_APP_SWEPUB_VERSION = require('./swepub.json').version;


// TODO: Remove this ugly workaround, introduced to make e2e tests not fail
// due to publicPath nedding to be /app/ for Flask/nginx...
publicPath = '/app/';
if (['test', 'e2e'].includes(process.env.NODE_ENV)) {
  publicPath = '/';
}

module.exports = {
  publicPath: publicPath,
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
      '^/api/v2': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
  transpileDependencies: ['vue-select'],
};
