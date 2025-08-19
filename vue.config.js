// vue.config.js
const { defineConfig } = require('@vue/cli-service')
const AutoImport = require('unplugin-auto-import/webpack')
const Components = require('unplugin-vue-components/webpack')
const { ElementPlusResolver } = require('unplugin-vue-components/resolvers')
const NodePolyfillPlugin = require('node-polyfill-webpack-plugin')

module.exports = defineConfig({
  publicPath: process.env.NODE_ENV === 'production' ? './' : '/',
  outputDir: 'dist',
  indexPath: 'templates/index.html',
  assetsDir: 'static',
  productionSourceMap: false,
  devServer: {
    client: {
      webSocketURL: {
        hostname: 'localhost',
        pathname: '/ws-dev',
        port: 8080,
        protocol: 'ws'
      }
    },
    proxy: {
      '/api': {
        target: 'http://localhost:10086',
        changeOrigin: true,
        ws: false
      },
      '/ide-ws': {
        target: 'ws://localhost:10086',
        changeOrigin: true,
        ws: true,
        pathRewrite: {
          '^/ide-ws': '/ws'
        }
      }
    }
  },
  chainWebpack: config => {
    config
      .plugin('html')
      .tap(args => {
        args[0].title = 'Python Web IDE'  // Change this to your desired title
        return args
      })
  },
  css: {
    extract: true,
    sourceMap: false
  },
  transpileDependencies: ['pdfjs-dist'],
  configureWebpack: {
    plugins: [
      AutoImport({
        resolvers: [ElementPlusResolver({importStyle: false})],
      }),
      Components({
        resolvers: [ElementPlusResolver({importStyle: false})],
      }),
      new NodePolyfillPlugin(),
    ],
  },
})
