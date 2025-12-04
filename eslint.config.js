import { defineConfig } from 'eslint-define-config';
import typescriptEslintPlugin from '@typescript-eslint/eslint-plugin';
import parser from '@typescript-eslint/parser';
import eslintPluginReactHooks from 'eslint-plugin-react-hooks';

export default defineConfig([
  {
    ignores: [
      'node_modules',
      'ui-tests/playwright-report',
      'lib',
      'dist',
      'coverage',
      '**/*.d.ts'
    ],
    plugins: {
      '@typescript-eslint': typescriptEslintPlugin,
      'react-hooks': eslintPluginReactHooks
    },
    languageOptions: {
      parser: parser,
      parserOptions: {
        project: './tsconfig.json',
        sourceType: 'module'
      }
    },
    rules: {
      '@typescript-eslint/naming-convention': [
        'error',
        {
          selector: 'interface',
          format: ['PascalCase'],
          custom: {
            regex: '^I[A-Z]',
            match: true
          }
        }
      ],
      '@typescript-eslint/no-unused-vars': [
        'warn',
        {
          args: 'none',
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^_'
        }
      ],
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-namespace': 'off',
      '@typescript-eslint/no-use-before-define': 'off',
      curly: ['error', 'all'],
      eqeqeq: 'error',
      'prefer-arrow-callback': 'error',
      'react-hooks/exhaustive-deps': 'error',
      quotes: [
        'error',
        'single',
        {
          avoidEscape: true,
          allowTemplateLiterals: false
        }
      ]
    }
  },
  {
    files: ['*.ts', '*.tsx'],
    extends: [
      'plugin:@typescript-eslint/eslint-recommended',
      'plugin:@typescript-eslint/recommended'
    ]
  },
  {
    files: ['*.jsx', '*.js'],
    extends: ['eslint:recommended']
  },
  {
    files: ['*.tsx', '*.jsx'],
    extends: ['plugin:react-hooks/recommended']
  },
  {
    files: ['*'],
    extends: ['plugin:prettier/recommended']
  }
]);
