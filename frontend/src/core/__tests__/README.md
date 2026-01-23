# 前端核心基础设施测试

## 测试文件结构

```
frontend/src/core/
├── hooks/
│   ├── __tests__/
│   │   ├── useDataLoader.test.ts      # 数据加载Hook测试
│   │   ├── usePaginatedData.test.ts   # 分页数据Hook测试
│   │   ├── useForm.test.ts            # 表单Hook测试
│   │   └── useTable.test.ts           # 表格Hook测试
│   ├── useDataLoader.ts
│   ├── usePaginatedData.ts
│   ├── useForm.ts
│   └── useTable.ts
└── components/
    ├── DataTable/
    │   ├── __tests__/
    │   │   └── DataTable.test.tsx     # 数据表格组件测试
    │   └── DataTable.tsx
    └── FilterPanel/
        ├── __tests__/
        │   └── FilterPanel.test.tsx   # 筛选面板组件测试
        └── FilterPanel.tsx
```

## 运行测试

### 运行所有核心测试

```bash
cd frontend
pnpm test src/core
```

### 运行特定测试

```bash
# 运行Hook测试
pnpm test src/core/hooks

# 运行组件测试
pnpm test src/core/components

# 运行单个测试文件
pnpm test src/core/hooks/__tests__/useDataLoader.test.ts
```

### 生成覆盖率报告

```bash
pnpm test:run --coverage src/core
```

## 测试覆盖

### Hooks 测试

#### useDataLoader
- ✅ 数据加载成功
- ✅ 加载状态处理
- ✅ 错误状态处理
- ✅ enabled 选项
- ✅ 手动刷新
- ✅ 自动重试（useDataLoaderWithRetry）

#### usePaginatedData
- ✅ 初始化默认值
- ✅ 分页数据加载
- ✅ 页码变更
- ✅ 筛选变更
- ✅ 关键词变更
- ✅ 排序变更
- ✅ 重置筛选
- ✅ enabled 选项

#### useForm
- ✅ 初始化默认值
- ✅ 字段变更
- ✅ 错误清除
- ✅ 表单验证
- ✅ 表单提交（成功/失败）
- ✅ 表单重置
- ✅ resetOnSuccess 选项
- ✅ 字段值设置
- ✅ 字段触摸状态
- ✅ 字段错误获取

#### useTable
- ✅ 初始化默认值
- ✅ 默认选中项
- ✅ 行key获取（字符串/函数）
- ✅ 选择/取消选择
- ✅ 全选/取消全选
- ✅ 清除选择
- ✅ Ant Design rowSelection 配置
- ✅ 数据变更时更新选中行

### 组件测试

#### DataTable
- ✅ 数据渲染
- ✅ 加载状态
- ✅ 分页处理
- ✅ 关键词搜索
- ✅ 筛选变更
- ✅ 刷新功能
- ✅ 初始筛选条件
- ✅ 初始关键词

#### FilterPanel
- ✅ Select 筛选器渲染
- ✅ Input 筛选器渲染
- ✅ Date 筛选器渲染
- ✅ DateRange 筛选器渲染
- ✅ Number 筛选器渲染
- ✅ 筛选值变更
- ✅ 清除按钮显示/隐藏
- ✅ 清除功能
- ✅ 当前筛选值显示
- ✅ 垂直布局

## 测试工具

- **Vitest** - 测试框架
- **@testing-library/react** - React 组件测试
- **@testing-library/user-event** - 用户交互模拟
- **@tanstack/react-query** - 数据获取测试

## 注意事项

1. **React Query Provider**: 所有使用 React Query 的测试都需要 `QueryClientProvider` 包装
2. **异步测试**: 使用 `waitFor` 等待异步操作完成
3. **用户交互**: 使用 `fireEvent` 或 `userEvent` 模拟用户操作
4. **Mock**: 使用 `vi.fn()` 和 `vi.mock()` 模拟外部依赖

## 最佳实践

1. **测试隔离**: 每个测试用例应该独立，不依赖其他测试
2. **清理**: 使用 `beforeEach` 清理 mock 和状态
3. **断言**: 使用明确的断言，验证期望的行为
4. **覆盖率**: 目标覆盖率 > 80%
5. **可读性**: 测试代码应该清晰易懂，描述测试场景

## 下一步

- [ ] 添加 CommonForm 组件测试
- [ ] 添加 Dashboard 组件测试
- [ ] 添加集成测试
- [ ] 添加 E2E 测试
- [ ] 提升测试覆盖率到 90%+
