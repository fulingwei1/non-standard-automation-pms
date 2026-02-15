# 🚀 项目成本列表功能 - 快速开始指南

**5分钟部署，立即使用！**

---

## ⚡ 快速开始（3步）

### 步骤1: 安装依赖

```bash
cd frontend
pnpm add xlsx
```

或者使用 npm:

```bash
npm install xlsx
```

### 步骤2: 更新路由

编辑 `frontend/src/routes/modules/projectRoutes.jsx`

**添加导入**:

```jsx
import ProjectListWithCost from "../../pages/ProjectListWithCost";
```

**添加路由**（选择一种方式）:

**方式A - 新增路由**（保留原项目列表）:
```jsx
<Route path="/projects-cost" element={<ProjectListWithCost />} />
```

**方式B - 替换路由**（推荐）:
```jsx
<Route path="/projects" element={<ProjectListWithCost />} />
```

### 步骤3: 启动服务器

```bash
pnpm dev
```

访问: `http://localhost:5173/projects-cost` （方式A）或 `http://localhost:5173/projects` （方式B）

---

## 🎯 功能预览

### 1. 成本摘要显示

每个项目卡片显示：
- 💰 总成本（万元）
- 📊 预算（万元）
- 📈 预算使用率（带进度条）
- ⚠️ 超支状态

### 2. 智能筛选

- ✅ 一键开启/关闭成本显示
- ✅ 仅显示超支项目
- ✅ 4种排序方式（时间/成本/使用率）
- ✅ 搜索项目名称/编号/客户

### 3. 成本明细弹窗

点击"查看成本明细"查看：
- 📊 成本概览（总成本/预算/差异）
- 📈 预算使用率进度条
- 🥧 成本结构饼图
- 📋 成本明细表（人工/材料/设备/差旅/其他）
- ⚠️ 超支/预警提示

### 4. 导出Excel

一键导出含完整成本数据的Excel报表

---

## 🎨 视觉特性

### 颜色编码

- 🟢 **绿色** (< 80%): 成本安全
- 🟠 **琥珀色** (80-90%): 注意
- 🟡 **黄色** (90-100%): 预警
- 🔴 **红色** (> 100%): 超支

### 超支项目高亮

- 🔴 红色顶部边框
- 🔴 红色环形边框
- 🔴 "超支" 徽章
- 🔴 红色成本使用率

---

## 📖 使用示例

### 示例1: 查看所有项目成本

1. 访问项目列表页面
2. 确保"显示成本"开关开启
3. 查看每个项目的成本摘要

### 示例2: 找出超支项目

1. 开启"仅超支项目"开关
2. 查看筛选结果（红色高亮）
3. 点击"导出Excel"生成报表

### 示例3: 找出预算告急的项目

1. 选择排序方式：预算使用率（高→低）
2. 查看顶部项目（黄色预警）
3. 及时采取成本控制措施

---

## 🧪 快速测试

访问页面后，检查：

- [ ] 页面正常加载
- [ ] 项目卡片显示成本信息
- [ ] 超支项目红色高亮
- [ ] "仅超支项目"筛选工作正常
- [ ] 排序功能正常
- [ ] 点击"查看成本明细"打开弹窗
- [ ] 导出Excel生成文件

---

## 📂 新增文件清单

```
frontend/src/
├── lib/utils/
│   └── cost.js                          ← 成本工具函数
├── components/project/
│   ├── ProjectCostFilter.jsx            ← 成本筛选器
│   └── ProjectCostDetailDialog.jsx      ← 成本明细弹窗
└── pages/
    └── ProjectListWithCost.jsx          ← 成本增强项目列表
```

---

## 🐛 常见问题

### Q: xlsx 安装失败？

```bash
# 清除缓存后重试
rm -rf node_modules package-lock.json
npm install
npm install xlsx
```

### Q: 页面显示空白？

检查：
1. 路由配置是否正确
2. 浏览器控制台是否有错误
3. 后端服务器是否启动

### Q: 成本数据不显示？

检查：
1. "显示成本"开关是否开启
2. 后端API是否支持 `include_cost` 参数
3. 项目是否有成本数据

### Q: 导出Excel失败？

检查：
1. xlsx 依赖是否安装
2. 浏览器控制台是否有错误
3. 是否有可导出的数据

---

## 📚 完整文档

| 文档 | 说明 |
|-----|------|
| `PROJECT_COST_FRONTEND_IMPLEMENTATION.md` | 完整实施报告 |
| `frontend/ROUTE_UPDATE_EXAMPLE.md` | 路由配置详细示例 |
| `frontend/COST_FEATURE_TEST_CHECKLIST.md` | 完整测试清单 |
| `TASK_COMPLETION_PROJECT_COST_FRONTEND.md` | 任务完成报告 |

---

## 🎉 开始使用！

```bash
# 1. 安装依赖
cd frontend && pnpm add xlsx

# 2. 更新路由（手动编辑）
# 编辑 src/routes/modules/projectRoutes.jsx

# 3. 启动服务器
pnpm dev

# 4. 访问页面
# http://localhost:5173/projects-cost
```

---

**享受强大的成本管理功能！** 🚀💰📊
