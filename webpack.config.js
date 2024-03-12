const path = require('path');

const config = {
  mode: process.env.NODE_ENV ?? 'development',
  watch: process.env.NODE_ENV === 'production' ? false : true,
  module: {
    rules: [
      {
        test: /.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      }
    ]
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js']
  }
};

const distRoot = path.resolve(
  __dirname,
  'tljh_repo2docker',
  'static',
  'js'
);

const environmentsPageConfig = {
  name: 'environments',
  entry: './src/environments/main.tsx',
  output: {
    path: path.resolve(distRoot, 'react'),
    filename: 'environments.js'
  },
  ...config
};
const serversPageConfig = {
  name: 'servers',
  entry: './src/servers/main.tsx',
  output: {
    path: path.resolve(distRoot, 'react'),
    filename: 'servers.js'
  },
  ...config
};
module.exports = [environmentsPageConfig, serversPageConfig];
