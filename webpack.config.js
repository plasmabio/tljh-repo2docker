import path from 'path';

const __dirname = new URL('.', import.meta.url).pathname;

const config = {
  mode: process.env.NODE_ENV ?? 'development',
  module: {
    rules: [
      {
        test: /\.tsx?$/,
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

const distRoot = path.resolve(__dirname, 'tljh_repo2docker', 'static', 'js');

const environmentsPageConfig = {
  name: 'environments',
  entry: './src/environments/main.tsx',
  output: {
    path: distRoot,
    filename: 'environments.js'
  },
  ...config
};

const serversPageConfig = {
  name: 'servers',
  entry: './src/servers/main.tsx',
  output: {
    path: distRoot,
    filename: 'servers.js'
  },
  ...config
};

export default [environmentsPageConfig, serversPageConfig];
