# Agent Team - 项目成本列表增强

**启动时间**: 2026-02-14 20:13  
**任务发起**: 符哥  
**协调人**: Claude AI Agent  
**会话ID**: `agent:main:subagent:22812f3d-1bde-4949-951b-8d12153e9c67`  
**运行ID**: `9a4bd1e3-d29d-409f-9608-18932cc95a94`

---

## 🎯 任务目标

**在项目列表中显示成本信息，方便一次查看所有项目的成本状态**

**完成后效果**:
```
项目列表页面显示：
┌─────────────────────────────────────────────────┐
│ 项目编号 │ 项目名称 │ 进度 │ 成本 │ 预算 │ 使用率 │
├─────────────────────────────────────────────────┤
│ P2026001 │ XX测试设备 │ 60% │ 75万 │ 90万 │ 83% ✅ │
│ P2026002 │ YY自动化线 │ 85% │ 120万│ 100万│ 120% ⚠️│
│ P2026003 │ ZZ检测设备 │ 40% │ 30万 │ 50万 │ 60% ✅ │
└─────────────────────────────────────────────────┘

支持:
- ✅ 一次查看所有项目成本
- ✅ 按成本排序
- ✅ 超支项目高亮显示（红色）
- ✅ 导出全量数据
```

---

## 📋 任务内容

### 1. **后端API增强**
- [ ] 修改 `GET /api/v1/projects` 接口
- [ ] 增加 `include_cost=true` 参数
- [ ] 返回成本摘要数据（总成本、预算、使用率、是否超支）
- [ ] 支持排序：`cost_desc` / `cost_asc` / `budget_used_pct`
- [ ] 支持过滤：`overrun_only=true`（仅超支项目）
- [ ] 批量查询优化（避免N+1）

### 2. **前端增强**（如果有）
- [ ] 项目列表新增列：成本、预算、使用率
- [ ] 超支项目高亮（红色/警告）
- [ ] 排序功能
- [ ] 成本使用率进度条
- [ ] 导出功能

### 3. **性能优化**
- [ ] 批量查询成本数据
- [ ] 数据库索引优化
- [ ] 查询性能测试（100项目 < 1秒）

### 4. **单元测试**
- [ ] 成本数据准确性测试
- [ ] 排序功能测试
- [ ] 过滤功能测试
- [ ] 性能测试
- [ ] 10+个测试用例

### 5. **文档**
- [ ] API文档更新
- [ ] 使用说明

---

## 📊 技术方案

### API接口设计
```python
GET /api/v1/projects?include_cost=true&sort=cost_desc&overrun_only=false

Response:
{
  "items": [
    {
      "project_id": 123,
      "project_name": "XX测试设备",
      "project_code": "P2026001",
      "progress": 60,
      "status": "IN_PROGRESS",
      "cost_summary": {
        "total_cost": 750000,
        "budget": 900000,
        "budget_used_pct": 83.33,
        "overrun": false,
        "remaining_budget": 150000,
        "cost_breakdown": {
          "labor": 400000,
          "material": 250000,
          "equipment": 100000
        }
      }
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

### 排序选项
- `cost_desc`: 按总成本降序
- `cost_asc`: 按总成本升序
- `budget_used_pct`: 按预算使用率降序
- `overrun_first`: 超支项目优先

### 性能优化策略
```python
# 批量查询成本数据
project_ids = [p.id for p in projects]
cost_data = db.query(ProjectCost).filter(
    ProjectCost.project_id.in_(project_ids)
).all()

# 构建成本字典
cost_map = {c.project_id: c for c in cost_data}

# 组装返回数据
for project in projects:
    cost = cost_map.get(project.id)
    project.cost_summary = build_cost_summary(cost)
```

---

## 📈 进度追踪

| 任务 | 状态 | 进度 | 预计完成 |
|------|------|------|---------|
| 后端API增强 | 🚀 已启动 | 0% | 1天 |
| 前端增强 | 🔜 待开始 | 0% | 0.5天 |
| 性能优化 | 🔜 待开始 | 0% | 0.5天 |
| 单元测试 | 🔜 待开始 | 0% | 0.5天 |
| 文档 | 🔜 待开始 | 0% | 0.5天 |

**总体进度**: 0% (已启动开发)  
**预计总耗时**: 1-2天

---

## 🎯 验收标准

### 功能完整性
- [ ] 项目列表API支持 `include_cost=true`
- [ ] 返回完整成本摘要（总成本、预算、使用率、超支标识）
- [ ] 支持3种排序方式
- [ ] 支持超支项目过滤
- [ ] 前端显示成本列（如果有前端）
- [ ] 超支项目高亮显示

### 性能指标
- [ ] 100个项目查询时间 < 1秒
- [ ] 使用批量查询（无N+1问题）
- [ ] 适当的数据库索引

### 质量指标
- [ ] 10+个单元测试
- [ ] 测试覆盖率 > 85%
- [ ] API文档完整

---

## 📊 业务价值

### 当前痛点
❌ 项目列表不显示成本  
❌ 不能按成本排序  
❌ 只能看TOP 10，看不到全部  
❌ 需要逐个点击查看成本，效率低

### 实施后收益
✅ 一次查看所有项目成本  
✅ 快速识别超支项目（红色高亮）  
✅ 按成本排序，找出高成本项目  
✅ 导出全量成本数据  
✅ 提升项目管理效率 50%

---

## 💡 复用现有模块

**已有成本功能**（100%完成，可直接复用）:
- ✅ 成本Dashboard (`/dashboard/cost/overview`)
- ✅ TOP项目成本 (`/dashboard/cost/top-projects`)
- ✅ 单项目成本仪表盘 (`/dashboard/cost/{project_id}`)
- ✅ 成本预警 (`/dashboard/cost/alerts`)
- ✅ EVM挣值管理
- ✅ 成本预测模块
- ✅ 标准成本库

**复用策略**:
- 使用已有的成本计算服务
- 在项目列表API中聚合成本数据
- 前端复用成本显示组件

---

## 📁 交付清单

### 代码文件
```
app/api/v1/endpoints/projects/
  - list.py (修改：增加成本聚合逻辑)

app/services/
  - project_cost_aggregator.py (新增：成本聚合服务)

tests/
  - test_project_list_with_cost.py (新增：10+测试用例)
```

### 文档文件
```
docs/
  - project_list_cost_api.md (新增：API文档)
  - project_list_cost_guide.md (新增：使用指南)
```

---

## 🔔 通知策略

### 何时通知符哥
- ✅ 任务完成时
- ⚠️ 遇到阻塞时
- 📊 重要发现或建议时

### 进度检查点
- **6小时**: 检查后端API开发进度
- **12小时**: 检查前端实现和测试
- **24小时**: 整体验收

---

**任务创建**: 2026-02-14 20:13  
**预计完成**: 2026-02-15 ~ 2026-02-16（1-2天）

**实时状态查询**:
```bash
openclaw sessions list --kinds isolated
```

**Agent Team正在工作中...** 🚀
