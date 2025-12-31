// vue.config.js
const { defineConfig } = require('@vue/cli-service')
const AutoImport = require('unplugin-auto-import/webpack')
const Components = require('unplugin-vue-components/webpack')
const { ElementPlusResolver } = require('unplugin-vue-components/resolvers')
const NodePolyfillPlugin = require('node-polyfill-webpack-plugin')

// Determine which app to build based on environment variable
const buildTarget = process.env.BUILD_TARGET || 'ide'

// Multi-page configuration for admin panel
const pagesConfig = buildTarget === 'admin' ? {
  // Admin Panel Build
  admin: {
    entry: 'src/admin/main.js',
    template: 'public/admin.html',
    filename: 'templates/index.html',
    title: 'Admin Panel - Python IDE',
    chunks: ['chunk-vendors', 'chunk-common', 'admin']
  }
} : {
  // Main IDE Build (default)
  index: {
    entry: 'src/main.js',
    template: 'public/index.html',
    filename: 'templates/index.html',
    title: 'Python Web IDE',
    chunks: ['chunk-vendors', 'chunk-common', 'index']
  }
}

module.exports = defineConfig({
  publicPath: process.env.NODE_ENV === 'production' ? './' : '/',
  outputDir: 'dist',
  assetsDir: 'static',
  productionSourceMap: false,
  pages: pagesConfig,
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
