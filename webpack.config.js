const path = require('path');
const webpack = require('webpack');
const VueLoaderPlugin = require('vue-loader/lib/plugin');
const UglifyJsPlugin = require('uglifyjs-webpack-plugin');
const HardSourceWebpackPlugin = require('hard-source-webpack-plugin');

module.exports = {
    mode: 'production',
    entry: path.resolve(__dirname, 'client/src/index.js'),
    output: {
        path: path.resolve(__dirname, 'client/dist'),
        filename: '[name].js',
        publicPath: '/static/',
    },
    module: {
        rules: [
            {
                test: /\.vue$/,
                include: path.resolve(__dirname, 'client/src'),
                loader: 'vue-loader'
            },
            {
                test: /\.js$/,
                include: path.resolve(__dirname, 'client/src'),
                loader: 'babel-loader'
            },
            {
                test: /\.css$/,
                use: [
                    'vue-style-loader',
                    'css-loader'
                ]
            }
        ]
    },
    resolve: {
        alias: {
            vue: 'vue/dist/vue.js',
        },
        modules: [
            path.resolve(__dirname, 'client/src'),
            path.resolve(__dirname, 'node_modules'),
        ],
    },
    plugins: [
        new VueLoaderPlugin(),
        new UglifyJsPlugin(),
        new HardSourceWebpackPlugin(),
        new webpack.optimize.SplitChunksPlugin(),
    ]
}

