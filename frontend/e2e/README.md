# E2E 测试文档

## 概述

本项目使用 Playwright 编写端到端测试，覆盖5个关键业务流程：

1. **用户认证流程** (`auth.spec.js`)
2. **项目管理流程** (`project-management.spec.js`)
3. **销售流程** (`sales-flow.spec.js`)
4. **采购流程** (`procurement-flow.spec.js`)
5. **审批流程** (`approval-flow.spec.js`)

## 测试场景统计

- **总测试文件**: 5个
- **总测试场景**: 25个
- **覆盖模块**: 认证、项目、销售、采购、审批

## 前置条件

1. Node.js 环境（已安装）
2. 安装依赖：
   ```bash
   npm install
   # 或
   pnpm install
   ```

3. 安装 Playwright 浏览器：
   ```bash
   npx playwright install
   ```

## 运行测试

### 运行所有测试
```bash
npx playwright test
```

### 运行特定测试文件
```bash
# 认证测试
npx playwright test auth.spec.js

# 项目管理测试
npx playwright test project-management.spec.js

# 销售流程测试
npx playwright test sales-flow.spec.js

# 采购流程测试
npx playwright test procurement-flow.spec.js

# 审批流程测试
npx playwright test approval-flow.spec.js
```

### UI 模式运行（推荐用于调试）
```bash
npx playwright test --ui
```

### 调试模式
```bash
npx playwright test --debug
```

### 生成HTML报告
```bash
npx playwright show-report
```

## 测试配置

配置文件：`playwright.config.js`

主要配置：
- **超时时间**: 60秒
- **失败重试**: CI环境2次，本地1次
- **截图**: 失败时自动截图
- **视频录制**: 失败时保留视频
- **浏览器**: Chromium (可扩展 Firefox, Safari)

## 测试数据

所有测试使用唯一的时间戳命名，避免数据冲突：
- 项目名称: `E2E测试项目_<timestamp>`
- 线索名称: `E2E测试线索_<timestamp>`
- 订单名称: `E2E采购订单_<timestamp>`

测试后会自动清理创建的数据。

## 测试输出

### 截图
- 位置: `test-results/screenshots/`
- 命名规则: `<场景名称>.png`
- 失败时自动截图

### 视频
- 位置: `test-results/`
- 仅失败时保留

### HTML报告
- 位置: `test-results/html/`
- 运行 `npx playwright show-report` 查看

## 辅助函数

位置：`e2e/helpers/test-helpers.js`

主要函数：
- `login(page, username, password)` - 登录
- `logout(page)` - 登出
- `waitForPageLoad(page)` - 等待页面加载
- `fillFormField(page, label, value)` - 填写表单
- `waitForSuccess(page, message)` - 等待成功提示
- `cleanupItem(page, itemName)` - 清理测试数据
- `generateTestName(prefix)` - 生成唯一名称

## 测试覆盖详情

### 1. 用户认证流程 (6个测试)
- ✅ 显示登录页面元素
- ✅ 成功登录管理员账户
- ✅ 拒绝错误的登录凭证
- ✅ 验证必填字段
- ✅ 成功退出登录
- ✅ 未登录时重定向到登录页

### 2. 项目管理流程 (5个测试)
- ✅ 显示项目列表页面
- ✅ 成功创建新项目
- ✅ 成功编辑项目信息
- ✅ 在项目看板中拖拽任务
- ✅ 成功删除项目

### 3. 销售流程 (5个测试)
- ✅ 成功创建销售线索
- ✅ 成功将线索转为商机
- ✅ 成功将商机转为合同
- ✅ 显示合同审批页面
- ✅ 成功提交合同审批

### 4. 采购流程 (5个测试)
- ✅ 成功创建采购申请
- ✅ 显示供应商列表
- ✅ 成功选择供应商
- ✅ 成功生成采购订单
- ✅ 成功提交订单审批

### 5. 审批流程 (4个测试)
- ✅ 显示审批中心页面
- ✅ 显示待我审批的列表
- ✅ 成功提交审批申请
- ✅ 成功通过审批
- ✅ 成功驳回审批
- ✅ 显示审批通知
- ✅ 显示审批历史

## 最佳实践

1. **测试隔离**: 每个测试独立运行，不依赖其他测试
2. **数据清理**: 使用 `afterEach` 钩子清理测试数据
3. **唯一命名**: 使用时间戳确保测试数据唯一性
4. **错误处理**: 使用 try-catch 处理可选元素
5. **截图记录**: 关键步骤截图便于调试

## 故障排查

### 测试失败
1. 查看 `test-results/screenshots/` 中的失败截图
2. 查看失败时的视频录制
3. 使用 `--debug` 模式逐步调试

### 元素找不到
1. 检查选择器是否正确
2. 增加等待时间
3. 使用 `--ui` 模式查看页面状态

### 服务器未启动
确保后端服务运行：
```bash
# 在后端目录
npm run dev
```

## CI/CD 集成

GitHub Actions 配置示例：

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npx playwright test
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: test-results/
```

## 维护说明

- 新增功能时，添加对应的E2E测试
- 定期更新选择器以适应UI变更
- 保持测试数据清理逻辑正确
- 更新文档说明新增的测试场景

## 联系方式

如有问题，请提交 Issue 或联系开发团队。
