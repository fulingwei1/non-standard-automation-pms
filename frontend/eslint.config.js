import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import react from 'eslint-plugin-react'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist', 'node_modules']),
  {
    files: ['src/**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    plugins: {
      react,
    },
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: 'latest',
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
    rules: {
      'no-unused-vars': [
        'error',
        {
          varsIgnorePattern: '^(?:[A-Z_].*|motion|AnimatePresence|LazyMotion|MotionConfig)$',
          argsIgnorePattern: '^(?:[A-Z_].*|motion|AnimatePresence|LazyMotion|MotionConfig)$',
          caughtErrorsIgnorePattern: '^_',
        },
      ],
      // React Compiler 相关规则过于严格，先关闭以便渐进式收敛
      'react-hooks/preserve-manual-memoization': 'off',
      'react-hooks/static-components': 'off',
      'react-hooks/immutability': 'off',
      'react-hooks/set-state-in-effect': 'off',
      'react-hooks/set-state-in-render': 'off',
      'react-hooks/exhaustive-deps': 'off',
      'react-refresh/only-export-components': 'off',
      // React JSX 规则 - 检测未转义的字符和标签问题
      'react/no-unescaped-entities': [
        'error',
        {
          forbid: ['>', '}'],
        },
      ],
      'react/jsx-closing-tag-location': 'off',
      // 关闭过于严格的格式规则，只保留关键的错误检测
      'react/jsx-closing-bracket-location': 'off',
      'react/jsx-indent': 'off',
      'react/jsx-indent-props': 'off',
      'react/jsx-wrap-multilines': 'off',
    },
  },
  {
    files: [
      'vite.config.js',
      'vitest.config.js',
      'postcss.config.js',
      'tailwind.config.js',
      'scripts/**/*.{js,jsx}',
    ],
    extends: [js.configs.recommended],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.node,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
    },
    rules: {
      'no-unused-vars': [
        'error',
        {
          varsIgnorePattern: '^(?:[A-Z_].*|motion|AnimatePresence|LazyMotion|MotionConfig)$',
          argsIgnorePattern: '^(?:[A-Z_].*|motion|AnimatePresence|LazyMotion|MotionConfig)$',
          caughtErrorsIgnorePattern: '^_',
        },
      ],
      'react-refresh/only-export-components': 'off',
    },
  },
  {
    files: ['src/**/*.{test,spec}.{js,jsx}', 'src/test/**/*.{js,jsx}'],
    extends: [js.configs.recommended],
    languageOptions: {
      ecmaVersion: 2020,
      globals: {
        ...globals.browser,
        ...globals.node,
        vi: 'readonly',
        describe: 'readonly',
        it: 'readonly',
        test: 'readonly',
        expect: 'readonly',
        beforeEach: 'readonly',
        afterEach: 'readonly',
        beforeAll: 'readonly',
        afterAll: 'readonly',
        global: 'readonly',
        process: 'readonly',
        require: 'readonly',
        MockAdapter: 'readonly',
      },
      parserOptions: {
        ecmaVersion: 'latest',
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    rules: {
      'no-unused-vars': [
        'error',
        {
          varsIgnorePattern: '^(?:[A-Z_].*|motion|AnimatePresence|LazyMotion|MotionConfig)$',
          argsIgnorePattern: '^(?:[A-Z_].*|motion|AnimatePresence|LazyMotion|MotionConfig|_).*',
          caughtErrorsIgnorePattern: '^_',
        },
      ],
      'react-hooks/globals': 'off',
    },
  },
])
