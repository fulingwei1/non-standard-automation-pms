# Agent Team - 项目成本列表前端开发

**启动时间**: 2026-02-14 23:32  
**任务发起**: 符哥  
**协调人**: Claude AI Agent  
**会话ID**: `agent:main:subagent:f4848b19-1879-434d-8711-1ce475429be3`  
**运行ID**: `616bea2e-e517-4ca8-aaf1-18eae6c8899f`

---

## 🎯 任务目标

**开发项目列表前端页面，集成成本显示功能**

**完成后效果**:
```
┌─────────────────────────────────────────────────────────────┐
│ 项目列表 - 成本管理视图                    [仅超支] [导出]  │
├─────────────────────────────────────────────────────────────┤
│ 项目编号 ↕ │ 项目名称 ↕ │ 进度 │ 成本↕ │ 预算 │ 使用率↕ │  │
├─────────────────────────────────────────────────────────────┤
│ P2026001   │ XX测试设备  │ 60%  │ 75万  │ 90万 │ █████ 83% ✅│
│ P2026002   │ YY自动化线  │ 85%  │ 120万 │100万 │ ██████ 120%⚠️│ ← 红色高亮
│ P2026003   │ ZZ检测设备  │ 40%  │ 30万  │ 50万 │ ███ 60% ✅  │
└─────────────────────────────────────────────────────────────┘

功能:
✅ 成本列显示（总成本、预算、使用率进度条）
✅ 超支项目红色高亮
✅ 按成本/使用率排序
✅ 仅显示超支项目开关
✅ 成本明细展开/弹窗（人工、材料、设备、差旅、其他）
✅ 导出Excel（含成本数据）
✅ 响应式设计
```

---

## 📋 任务内容

### 1. **项目列表页面** 
- [ ] 创建/修改项目列表页面组件
- [ ] 集成成本API：`GET /api/v1/projects/?include_cost=true`
- [ ] 显示成本列：总成本、预算、使用率
- [ ] 超支项目红色高亮（整行/边框）
- [ ] 成本使用率进度条（绿/黄/红）

### 2. **排序功能**
- [ ] 按成本升序/降序
- [ ] 按预算使用率排序
- [ ] 保留原有排序（项目编号、名称、进度等）

### 3. **筛选功能**
- [ ] "仅显示超支项目"开关按钮
- [ ] 结合其他筛选条件（阶段、状态）

### 4. **成本明细**
- [ ] 点击"查看明细"按钮
- [ ] 弹窗/展开显示成本明细
- [ ] 饼图可视化（可选）

### 5. **导出功能**
- [ ] 导出Excel（含成本数据）
- [ ] 导出PDF报表（可选）

### 6. **UI/UX优化**
- [ ] 成本格式化（千分位、万元）
- [ ] 百分比显示（83.33%）
- [ ] 响应式设计
- [ ] 加载状态
- [ ] 错误处理

### 7. **性能优化**
- [ ] 分页加载
- [ ] 虚拟滚动（可选）
- [ ] 缓存数据

---

## 📊 技术方案

### 后端API（已完成）
```bash
GET /api/v1/projects/?include_cost=true&sort=cost_desc&overrun_only=false
```

### 前端技术栈（待确认）
- React / Vue.js（根据项目现有技术栈）
- TypeScript
- UI组件库：Ant Design / Element UI / Material-UI
- 图表库：ECharts / Chart.js
- Excel导出：xlsx / ExcelJS

### UI设计要点
```typescript
// 成本使用率进度条颜色
const getProgressColor = (usedPct: number) => {
  if (usedPct < 80) return 'green';    // 安全
  if (usedPct <= 100) return 'orange'; // 预警
  return 'red';                        // 超支
};

// 超支项目高亮
const getRowClassName = (record: Project) => {
  return record.cost_summary?.overrun ? 'overrun-row' : '';
};
```

---

## 📈 进度追踪

| 任务 | 状态 | 进度 | 预计完成 |
|------|------|------|---------|
| 页面结构 | 🚀 已启动 | 0% | 0.5天 |
| API集成 | 🔜 待开始 | 0% | 0.5天 |
| 排序筛选 | 🔜 待开始 | 0% | 0.5天 |
| 成本明细 | 🔜 待开始 | 0% | 0.5天 |
| 导出功能 | 🔜 待开始 | 0% | 0.5天 |
| UI优化 | 🔜 待开始 | 0% | 0.5天 |

**总体进度**: 0% (已启动开发)  
**预计总耗时**: 1-2天

---

## 🎯 验收标准

### 功能完整性
- [ ] 项目列表显示成本列（总成本、预算、使用率）
- [ ] 超支项目红色高亮
- [ ] 支持3种排序方式（成本升序/降序、使用率）
- [ ] 支持超支项目筛选（开关按钮）
- [ ] 成本使用率进度条（绿/黄/红）
- [ ] 成本明细展开/弹窗
- [ ] 导出Excel功能

### UI/UX质量
- [ ] 成本格式化（千分位、万元、百分比）
- [ ] 响应式设计（桌面+平板）
- [ ] 加载状态和错误处理
- [ ] 良好的用户体验

### 性能指标
- [ ] 分页加载（每页20-50条）
- [ ] 首屏加载 < 2秒
- [ ] 交互响应 < 100ms

---

## 📊 业务价值

### 实施后收益
✅ **直观查看** - 所有项目成本一目了然  
✅ **快速识别** - 超支项目红色高亮，立即发现  
✅ **灵活排序** - 按成本/使用率排序，找出重点项目  
✅ **便捷导出** - Excel报表，支持离线分析  
✅ **提升效率** - 节省90%时间（从逐个点击到一次查看）

---

## 💡 参考资料

### 后端文档
- `docs/guides/project_cost_list_usage.md` - 使用指南（含前端示例）
- `docs/api/project_cost_list_enhancement.md` - API文档

### 前端示例（从文档中）
```typescript
// API调用
const fetchProjects = async (filters) => {
  const params = new URLSearchParams({
    include_cost: 'true',
    sort: filters.sort || 'cost_desc',
    overrun_only: filters.overrunOnly || 'false',
    page: filters.page || '1',
    page_size: filters.pageSize || '20'
  });
  
  const response = await fetch(`/api/v1/projects/?${params}`);
  return response.json();
};

// 成本显示组件
const CostCell = ({ costSummary }) => (
  <div>
    <div>{formatCost(costSummary.total_cost)}</div>
    <Progress 
      percent={costSummary.budget_used_pct} 
      status={getProgressStatus(costSummary)}
    />
  </div>
);
```

---

## 📁 交付清单

### 前端代码
```
frontend/src/
├── pages/
│   └── ProjectCostList.tsx/vue       # 主页面
├── components/
│   ├── CostSummaryCell.tsx/vue       # 成本单元格
│   ├── CostDetailModal.tsx/vue       # 成本明细弹窗
│   └── CostProgressBar.tsx/vue       # 成本进度条
├── services/
│   └── projectCostApi.ts/js          # API调用
└── utils/
    └── costFormatter.ts/js           # 成本格式化
```

### 样式文件
```
styles/
└── project-cost-list.css/scss        # 样式（超支高亮等）
```

### 文档
```
docs/frontend/
└── project_cost_list_frontend.md     # 前端实现文档
```

---

## 🔔 通知策略

### 何时通知符哥
- ✅ 任务完成时
- ⚠️ 遇到技术选型问题时（React vs Vue）
- ⚠️ 遇到阻塞时
- 📊 重要发现或建议时

### 进度检查点
- **6小时**: 检查页面结构和API集成
- **12小时**: 检查排序筛选功能
- **24小时**: 整体验收

---

**任务创建**: 2026-02-14 23:32  
**预计完成**: 2026-02-15 ~ 2026-02-16（1-2天）

**实时状态查询**:
```bash
openclaw sessions list --kinds isolated
```

**Agent Team正在工作中...** 🚀
