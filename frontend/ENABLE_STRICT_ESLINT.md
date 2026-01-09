# 启用严格 ESLint 配置指南

## 当前状态

- ✅ 存在严格配置：`eslint.config.strict.js`
- ❌ 当前使用宽松配置：`eslint.config.js`
- ⚠️ 项目规范要求：禁止提交包含 ESLint error 的代码

## 启用步骤

### 1. 备份当前配置
```bash
cd frontend
cp eslint.config.js eslint.config.backup.js
```

### 2. 启用严格配置
```bash
cp eslint.config.strict.js eslint.config.js
```

### 3. 检查问题数量
```bash
npm run lint 2>&1 | tee eslint-errors.log
```

### 4. 自动修复可修复的问题
```bash
npm run lint -- --fix
```

### 5. 手动修复剩余问题

重点关注：
- 未使用的变量和导入
- React Hooks 依赖数组不完整
- 使用 `==` 而非 `===`
- if/else 缺少大括号

## 渐进式启用（推荐）

如果问题太多，可以分阶段启用：

### 阶段1：启用核心规则
在 `eslint.config.js` 中添加：
```javascript
rules: {
  'no-unused-vars': ['error', {
    vars: 'all',
    args: 'after-used',
    varsIgnorePattern: '^_',
    argsIgnorePattern: '^_',
  }],
  'react-hooks/exhaustive-deps': 'error',  // 从 warning 升级
}
```

### 阶段2：启用最佳实践规则
```javascript
'eqeqeq': ['error', 'always'],
'curly': ['error', 'all'],
'no-empty': ['error', { allowEmptyCatch: false }],
```

### 阶段3：启用完整严格配置
使用 `eslint.config.strict.js` 的全部规则

## 预期影响

启用严格配置后，可能会发现：
- 大量未使用的变量和导入
- React Hooks 依赖数组问题
- 代码风格不一致（== vs ===）
- 空代码块

## 修复优先级

1. **高优先级**：未使用的变量/导入（影响性能）
2. **中优先级**：React Hooks 依赖（可能导致 bug）
3. **低优先级**：代码风格（== vs ===，curly braces）

## 注意事项

- 修复前先提交当前工作
- 可以创建新分支进行修复
- 建议分批修复，每次修复一类问题
- 修复后运行测试确保功能正常
