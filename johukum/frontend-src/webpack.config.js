let path = require('path')
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;


let common = {
    resolve: {
        alias: {
            'react': 'preact-compat',
            'react-dom': 'preact-compat',
            // Not necessary unless you consume a module using `createClass`
            'create-react-class': 'preact-compat/lib/create-react-class',
            // Not necessary unless you consume a module requiring `react-dom-factories`
            'react-dom-factories': 'preact-compat/lib/react-dom-factories'
        }
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader'
                }
            },
            {
                test: /react-select\/dist\/react-select.esm.js/,
                exclude: [],
                loader: path.resolve('dev-tools/webpack/loaders/react-select-loader.js') //  your custom loader
            },
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader']
            }
        ]
    },

}

const businessDataList = {
    entry: path.join(__dirname, 'src/apps/businessDataList/index.js'),
    output: {
        path: path.join(__dirname, '../static/js_apps/'),
        library: 'BusinessDataList',
        libraryTarget: 'umd',
        libraryExport: 'default',
        filename: 'businessDataList.js'
    },
    ...common,
    // plugins: [
    //     new BundleAnalyzerPlugin()
    // ]
}

const mobileDataList = {
    entry: path.join(__dirname, 'src/apps/mobileDataList/index.js'),
    output: {
        path: path.join(__dirname, '../static/js_apps/'),
        library: 'MobileDataList',
        libraryTarget: 'umd',
        libraryExport: 'default',
        filename: 'mobileDataList.js'
    },
    ...common
}

const businessDataAdd = {
    entry: path.join(__dirname, 'src/apps/businessDataAdd/index.js'),
    output: {
        path: path.join(__dirname, '../static/js_apps/'),
        library: 'BusinessDataAdd',
        libraryTarget: 'umd',
        libraryExport: 'default',
        filename: 'businessDataAdd.js'
    },
    ...common
}

const businessDataFileUpload = {
    entry: path.join(__dirname, 'src/apps/businessDataFileUpload/index.js'),
    output: {
        path: path.join(__dirname, '../static/js_apps/'),
        library: 'BusinessDataFileUpload',
        libraryTarget: 'umd',
        libraryExport: 'default',
        filename: 'businessDataFileUpload.js'
    },
    ...common
}

const businessDataEdit = {
    entry: path.join(__dirname, 'src/apps/businessDataEdit/index.js'),
    output: {
        path: path.join(__dirname, '../static/js_apps/'),
        library: 'BusinessDataEdit',
        libraryTarget: 'umd',
        libraryExport: 'default',
        filename: 'businessDataEdit.js'
    },
    ...common
}

module.exports = [businessDataList, businessDataAdd, businessDataFileUpload, businessDataEdit, mobileDataList]