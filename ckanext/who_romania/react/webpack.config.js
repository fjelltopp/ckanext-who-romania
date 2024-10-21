const path = require('path')

const outputPath = path.resolve('../assets/build/');
const components = {
    'FileInputComponent':
        path.resolve(__dirname, 'components', 'FileInputComponent/index.js'),
}

module.exports = {
    mode: 'production',
    target: 'web',
    entry: components,
    output: {
        path: outputPath,
        filename: '[name].js'
    },
    devtool: false,
    module: {
        rules: [
            {
                test: /\.(jsx|js)$/,
                exclude: /node_modules/,
                use: [{
                    loader: 'babel-loader',
                    options: {
                        presets: [
                            [
                                '@babel/preset-env', {
                                    "targets": "defaults"
                                }
                            ],
                            '@babel/preset-react'
                        ]
                    }
                }]
            }
        ]
    }
}
