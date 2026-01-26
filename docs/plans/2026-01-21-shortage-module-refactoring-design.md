# 缺料管理模块重构设计文档

> 日期：2026-01-21
> 状态：已通过评审
> 目标：消除功能重复，按业务流程重新划分模块边界

---

## 1. 问题背景

### 1.1 当前问题

- **服务层重复**：`shortage_management_service.py` 与 `shortage_reports_service.py` 功能完全相同
- **API 层重复**：`/shortage/` 和 `/shortage_alerts/` 两个模块 95%+ 代码重复
- **数据模型混乱**：存在 `AlertRecord`、`ShortageReport`、`MaterialShortage` 三套并行模型
- **菜单分散**：4 个菜单项（缺料管理、缺料预警、缺料管理看板、缺料报告）职责不清

### 1.2 重复统计

| 功能模块 | 重复程度 |
|---------|---------|
| 到货跟踪 (Arrivals) | 100% |
| 物料替代 (Substitutions) | 100% |
| 物料调拨 (Transfers) | 95% |
| 缺料上报 (Reports) | 100% |
| 统计分析 (Statistics) | 100% |

---

## 2. 设计方案

### 2.1 整体架构：按业务流程三层划分

```
发现问题 → 解决问题 → 分析问题
   │           │           │
Detection   Handling   Analytics
```

### 2.2 目录结构

```
app/
├── api/v1/endpoints/shortage/        # 统一入口
│   ├── __init__.py                   # 路由聚合
│   ├── detection/                    # 第一层：预警检测
│   │   ├── __init__.py
│   │   ├── alerts.py                 # 预警 CRUD + 确认/解决
│   │   └── monitoring.py             # 齐套检查、库存监控
│   │
│   ├── handling/                     # 第二层：缺料处理
│   │   ├── __init__.py
│   │   ├── reports.py                # 缺料上报
│   │   ├── substitutions.py          # 物料替代
│   │   ├── transfers.py              # 物料调拨
│   │   └── arrivals.py               # 到货跟踪
│   │
│   └── analytics/                    # 第三层：统计报表
│       ├── __init__.py
│       ├── statistics.py             # 统计概览、原因分析
│       └── dashboard.py              # 看板、日报、趋势
│
├── services/shortage/                # 服务层
│   ├── __init__.py
│   ├── alert_service.py              # 预警服务
│   ├── report_service.py             # 上报服务
│   ├── solution_service.py           # 解决方案服务
│   └── analytics_service.py          # 统计服务
│
└── models/shortage/                  # 模型层（保持不变）
    └── ...
```

---

## 3. API 路由设计

### 3.1 Detection 层（预警检测）

```
GET    /shortage/detection/alerts                    # 预警列表
GET    /shortage/detection/alerts/{id}               # 预警详情
PUT    /shortage/detection/alerts/{id}/acknowledge   # 确认预警
PUT    /shortage/detection/alerts/{id}/resolve       # 解决预警
POST   /shortage/detection/alerts/{id}/follow-ups    # 添加跟进
GET    /shortage/detection/alerts/{id}/follow-ups    # 跟进列表
GET    /shortage/detection/kit-checks                # 齐套检查列表
POST   /shortage/detection/kit-checks/run            # 执行齐套检查
GET    /shortage/detection/inventory-warnings        # 库存预警
```

### 3.2 Handling 层（缺料处理）

```
# 缺料上报
GET    /shortage/handling/reports                    # 上报列表
POST   /shortage/handling/reports                    # 创建上报
GET    /shortage/handling/reports/{id}               # 上报详情
PUT    /shortage/handling/reports/{id}/confirm       # 确认
PUT    /shortage/handling/reports/{id}/handle        # 处理中
PUT    /shortage/handling/reports/{id}/resolve       # 解决

# 物料替代
GET    /shortage/handling/substitutions              # 替代列表
POST   /shortage/handling/substitutions              # 创建替代申请
GET    /shortage/handling/substitutions/{id}         # 替代详情
PUT    /shortage/handling/substitutions/{id}/tech-approve   # 技术审批
PUT    /shortage/handling/substitutions/{id}/prod-approve   # 生产审批
PUT    /shortage/handling/substitutions/{id}/execute        # 执行替代

# 物料调拨
GET    /shortage/handling/transfers                  # 调拨列表
POST   /shortage/handling/transfers                  # 创建调拨
GET    /shortage/handling/transfers/{id}             # 调拨详情
PUT    /shortage/handling/transfers/{id}/approve     # 审批
PUT    /shortage/handling/transfers/{id}/execute     # 执行

# 到货跟踪
GET    /shortage/handling/arrivals                   # 到货列表
POST   /shortage/handling/arrivals                   # 创建到货记录
GET    /shortage/handling/arrivals/{id}              # 到货详情
PUT    /shortage/handling/arrivals/{id}/status       # 更新状态
POST   /shortage/handling/arrivals/{id}/follow-up    # 创建跟催
POST   /shortage/handling/arrivals/{id}/receive      # 确认收货
```

### 3.3 Analytics 层（统计报表）

```
GET    /shortage/analytics/overview                  # 统计概览
GET    /shortage/analytics/cause-analysis            # 原因分析
GET    /shortage/analytics/supplier-delivery         # 供应商交期分析
GET    /shortage/analytics/dashboard                 # 看板数据
GET    /shortage/analytics/daily-report              # 日报
GET    /shortage/analytics/trends                    # 趋势分析
```

---

## 4. 数据模型决策

### 4.1 模型处理

| 模型 | 决策 | 说明 |
|------|------|------|
| `AlertRecord` (target_type='SHORTAGE') | **保留** | 作为预警主表 |
| `ShortageReport` | **保留** | 人工上报，与预警是不同概念 |
| `MaterialShortage` | **废弃** | 迁移到 AlertRecord 后删除 |

### 4.2 概念区分

```
预警（Alert）          上报（Report）
   │                      │
   │ 系统自动检测          │ 人工主动上报
   │ 来自 AlertRecord      │ 来自 ShortageReport
   │                      │
   └──────────┬───────────┘
              │
              ▼
        解决方案（Solution）
              │
    ┌─────────┼─────────┐
    │         │         │
 替代      调拨      到货跟踪
```

---

## 5. 文件操作清单

### 5.1 要删除的文件

```bash
# 整个 shortage_alerts 目录
rm -rf app/api/v1/endpoints/shortage_alerts/

# 旧的 shortage 子目录和文件
rm -rf app/api/v1/endpoints/shortage/reports/
rm -rf app/api/v1/endpoints/shortage/transfers/
rm app/api/v1/endpoints/shortage/arrivals.py
rm app/api/v1/endpoints/shortage/arrival_*.py
rm app/api/v1/endpoints/shortage/substitution*.py
rm app/api/v1/endpoints/shortage/statistics*.py

# 重复服务
rm app/services/shortage_report_service.py
rm app/services/shortage/shortage_reports_service.py
```

### 5.2 服务层合并

| 新服务 | 合并来源 |
|--------|----------|
| `alert_service.py` | `shortage_alerts_service.py` |
| `report_service.py` | `shortage_management_service.py` + `shortage_reports_service.py` |
| `solution_service.py` | 新建，提取替代/调拨/到货逻辑 |
| `analytics_service.py` | `shortage_report_service.py` + 分散的统计逻辑 |

### 5.3 保留不动的文件

- `app/services/urgent_purchase_from_shortage_service.py` - 独立功能

---

## 6. 菜单结构

从 4 个菜单项简化为 3 个：

| 新菜单 | 对应模块 | 说明 |
|--------|----------|------|
| **缺料预警** | detection | 预警列表、齐套检查 |
| **缺料处理** | handling | 上报、替代、调拨、到货 |
| **缺料分析** | analytics | 看板、统计、日报 |

---

## 7. 实施阶段

| 阶段 | 内容 | 风险 |
|------|------|------|
| Phase 1 | 创建新目录结构 | 低 |
| Phase 2 | 合并 Handling 层 | 中 |
| Phase 3 | 合并 Analytics 层 | 低 |
| Phase 4 | 创建 Detection 层，迁移 MaterialShortage | 高 |
| Phase 5 | 删除旧文件，更新路由注册 | 中 |
| Phase 6 | 运行测试，修复问题 | 低 |

---

## 8. 测试策略

### 8.1 验收标准

- [ ] 所有旧功能在新路由下可用
- [ ] 数据迁移后 MaterialShortage 数据完整转移
- [ ] 统计数字与重构前一致
- [ ] 无 500 错误

### 8.2 回滚方案

每个 Phase 单独提交，出现问题时：
```bash
git revert HEAD~n
```
