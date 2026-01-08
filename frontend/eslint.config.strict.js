/**
 * 严格版 ESLint 配置
 *
 * 使用方法：
 * 1. 重命名此文件为 eslint.config.js（备份原文件）
 * 2. 运行 npm run lint 查看所有问题
 * 3. 运行 npm run lint -- --fix 自动修复部分问题
 *
 * 建议：先修复现有问题后再启用此配置
 */

import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import react from 'eslint-plugin-react'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist', 'node_modules', 'build']),
  {
    files: ['**/*.{js,jsx}'],
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
      // ============================================
      // 1. 未使用变量 - 严格模式
      // ============================================
      'no-unused-vars': [
        'error',
        {
          vars: 'all',                    // 检查所有变量
          args: 'after-used',             // 检查未使用的参数（在使用的参数之后）
          ignoreRestSiblings: true,       // 忽略解构中的 rest 兄弟
          argsIgnorePattern: '^_',        // 忽略以 _ 开头的参数
          varsIgnorePattern: '^_',        // 忽略以 _ 开头的变量
          caughtErrors: 'all',            // 检查 catch 中的错误变量
          caughtErrorsIgnorePattern: '^_', // 忽略以 _ 开头的错误变量
        },
      ],

      // ============================================
      // 2. React Hooks 规则 - 严格模式
      // ============================================
      'react-hooks/rules-of-hooks': 'error',        // Hook 调用规则
      'react-hooks/exhaustive-deps': 'error',       // 升级为 error（原为 warn）

      // ============================================
      // 3. 变量定义规则
      // ============================================
      'no-undef': 'error',                          // 禁止使用未定义的变量
      'no-use-before-define': ['error', {           // 禁止在定义前使用
        functions: false,                           // 允许函数提升
        classes: true,
        variables: true,
      }],

      // ============================================
      // 4. 最佳实践
      // ============================================
      'no-case-declarations': 'error',              // switch case 中必须用 {} 包裹声明
      'no-empty': ['error', { allowEmptyCatch: false }],  // 禁止空代码块
      'no-console': ['warn', {                      // 警告 console（生产环境应移除）
        allow: ['warn', 'error'],
      }],
      'eqeqeq': ['error', 'always'],               // 必须使用 === 和 !==
      'curly': ['error', 'all'],                   // if/else/for/while 必须使用 {}

      // ============================================
      // 5. React 规则
      // ============================================
      'react/jsx-key': 'error',                    // 列表渲染必须有 key
      'react/jsx-no-duplicate-props': 'error',    // 禁止重复的 props
      'react/jsx-no-undef': 'error',              // 禁止使用未定义的组件
      'react/no-unescaped-entities': ['error', {
        forbid: ['>', '}'],
      }],
      'react/jsx-closing-tag-location': 'warn',
      'react/self-closing-comp': ['error', {       // 无子元素必须自闭合
        component: true,
        html: true,
      }],
      'react/jsx-boolean-value': ['error', 'never'], // 布尔 prop 省略 ={true}
      'react/jsx-curly-brace-presence': ['error', { // 不必要的 {}
        props: 'never',
        children: 'never',
      }],

      // ============================================
      // 6. 导入规则（需要安装 eslint-plugin-import）
      // ============================================
      // 'import/no-unused-modules': 'error',      // 需要额外插件
      // 'import/no-duplicates': 'error',          // 需要额外插件

      // ============================================
      // 7. 关闭的规则（格式类交给 Prettier）
      // ============================================
      'react/jsx-closing-bracket-location': 'off',
      'react/jsx-indent': 'off',
      'react/jsx-indent-props': 'off',
      'react/jsx-wrap-multilines': 'off',
    },
  },
])
