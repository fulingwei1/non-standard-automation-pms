# Scheduler Config 代码审查检查清单

**审查日期：** _____________
**审查人员：** _____________
**修改范围：** `app/utils/scheduler_config.py`

---

## 📋 审查概述

### 审查目标
1. ✅ 验证 cron 表达式修改的合理性
2. ✅ 验证 owner 字段修改的准确性
3. ✅ 验证新增字段（dependencies_tables、risk_level、sla）的完整性
4. ✅ 评估修改对现有任务的影响
5. ✅ 确保元数据与实现代码的一致性

### 核心原则
- **cron 和 owner 是敏感字段**：修改前必须经过审查
- **依赖表必须准确**：用于评估数据库变更影响
- **风险级别必须合理**：用于运维优先级判断
- **SLA 必须可执行**：用于监控和告警

---

## 🔍 必检项（P0 - 阻塞问题）

### 1. Cron 表达式修改检查

#### 1.1 修改 cron 的审查要点

- [ ] **修改原因说明**
  - [ ] PR 描述中是否说明了修改 cron 的原因？
  - [ ] 是否评估了对其他任务的影响（时间冲突、资源竞争）？
  - [ ] 是否考虑了业务时间窗口（如避免工作时间执行重任务）？

- [ ] **Cron 格式验证**
  ```python
  # 正确的 cron 格式示例
  {"minute": 0}                    # 每小时整点
  {"hour": 9, "minute": 0}        # 每天 9:00
  {"hour": 8, "minute": 30}       # 每天 8:30
  {"minute": 15}                  # 每小时 :15
  ```
  - [ ] 格式是否符合 APScheduler 要求？
  - [ ] 时间值是否在有效范围内（hour: 0-23, minute: 0-59）？

- [ ] **时间冲突检查**
  - [ ] 是否与其他高频任务冲突（如多个任务都在 `{"minute": 0}`）？
  - [ ] 是否会导致数据库连接池耗尽？
  - [ ] 是否会导致系统负载峰值？

**审查示例：**
```python
# ❌ 错误：修改了关键任务的执行时间，未说明原因
"cron": {"hour": 9, "minute": 0},  # 原来是 {"hour": 7, "minute": 0}

# ✅ 正确：修改有明确原因，且评估了影响
# 原因：7:00 与缺料预警冲突，改为 9:00 避免数据库压力
"cron": {"hour": 9, "minute": 0},
```

---

### 2. Owner 字段修改检查

#### 2.1 修改 owner 的审查要点

- [ ] **Owner 变更原因**
  - [ ] PR 描述中是否说明了 owner 变更的原因？
  - [ ] 是否通知了原 owner 和新 owner？
  - [ ] 是否更新了相关文档？

- [ ] **Owner 格式验证**
  - [ ] Owner 是否为有效的团队/角色名称？
  - [ ] 是否与现有 owner 命名规范一致（如 "Backend Platform", "PMO", "Supply Chain"）？

- [ ] **责任转移验证**
  - [ ] 新 owner 是否有权限访问相关资源？
  - [ ] 新 owner 是否了解任务的功能和依赖？

**审查示例：**
```python
# ❌ 错误：随意修改 owner，未说明原因
"owner": "New Team",  # 原来是 "Backend Platform"

# ✅ 正确：owner 变更有明确原因
# 原因：任务功能从后端平台迁移到 PMO 团队管理
"owner": "PMO",  # 原 "Backend Platform"
```

---

### 3. 新增字段完整性检查

#### 3.1 dependencies_tables 字段

- [ ] **字段存在性**
  - [ ] 每个任务是否都有 `dependencies_tables` 字段？
  - [ ] 字段是否为列表类型？

- [ ] **表名准确性**
  - [ ] 表名是否与数据库实际表名一致？
  - [ ] 是否包含了所有依赖的表（包括间接依赖）？
  - [ ] 表名是否使用下划线命名（如 `project_milestones` 而非 `projectMilestones`）？

- [ ] **完整性验证**
  ```python
  # 示例：检查任务实现代码，确认依赖表
  # 如果任务查询了 projects 表，dependencies_tables 必须包含 "projects"
  "dependencies_tables": ["projects", "project_milestones", "alert_records"]
  ```
  - [ ] 是否通过代码审查确认了依赖表的准确性？
  - [ ] 是否遗漏了关联表（如通过外键关联的表）？

**审查示例：**
```python
# ❌ 错误：遗漏了依赖表
"dependencies_tables": ["projects"],  # 实际还依赖 project_milestones

# ✅ 正确：包含所有依赖表
"dependencies_tables": ["projects", "project_milestones", "alert_records"]
```

#### 3.2 risk_level 字段

- [ ] **字段存在性**
  - [ ] 每个任务是否都有 `risk_level` 字段？
  - [ ] 字段值是否为有效枚举（LOW/MEDIUM/HIGH/CRITICAL）？

- [ ] **风险级别合理性**
  - [ ] 风险级别是否与任务重要性匹配？
  - [ ] 是否考虑了任务失败对业务的影响？

**风险级别定义：**
- **CRITICAL**: 任务失败会导致业务严重中断（如缺料预警）
- **HIGH**: 任务失败会影响关键业务流程（如项目健康度计算）
- **MEDIUM**: 任务失败会影响非关键功能（如统计快照）
- **LOW**: 任务失败影响较小（如提醒类任务）

**审查示例：**
```python
# ❌ 错误：风险级别设置不合理
"risk_level": "LOW",  # 缺料预警应该是 CRITICAL

# ✅ 正确：风险级别与任务重要性匹配
"risk_level": "CRITICAL",  # 缺料预警失败会导致生产中断
```

#### 3.3 sla 字段

- [ ] **字段存在性**
  - [ ] 每个任务是否都有 `sla` 字段？
  - [ ] 字段是否为字典类型？

- [ ] **SLA 字段完整性**
  ```python
  "sla": {
      "max_execution_time_seconds": 300,  # 最大执行时间（秒）
      "retry_on_failure": True,            # 失败是否重试
  }
  ```
  - [ ] 是否包含 `max_execution_time_seconds`？
  - [ ] 是否包含 `retry_on_failure`？
  - [ ] 时间值是否合理（不应过短或过长）？

- [ ] **SLA 合理性验证**
  - [ ] `max_execution_time_seconds` 是否基于实际执行时间设置？
  - [ ] `retry_on_failure` 是否考虑了任务特性（如幂等性）？

**审查示例：**
```python
# ❌ 错误：SLA 设置不合理
"sla": {
    "max_execution_time_seconds": 10,  # 10秒对于批量计算任务太短
    "retry_on_failure": True,
}

# ✅ 正确：SLA 设置合理
"sla": {
    "max_execution_time_seconds": 1200,  # 20分钟，适合批量计算
    "retry_on_failure": True,
}
```

---

## 🔄 一致性检查（P1 - 重要问题）

### 4. 元数据与实现代码一致性

- [ ] **模块和函数验证**
  ```python
  # 检查模块和函数是否可导入
  from app.utils.scheduled_tasks import calculate_project_health
  ```
  - [ ] `module` 字段是否指向正确的模块路径？
  - [ ] `callable` 字段是否指向模块中存在的函数？
  - [ ] 函数签名是否与调用方式匹配？

- [ ] **依赖表与代码一致性**
  - [ ] 代码中查询的表是否都在 `dependencies_tables` 中？
  - [ ] `dependencies_tables` 中的表是否都在代码中被使用？

- [ ] **描述与功能一致性**
  - [ ] `description` 是否准确描述了任务功能？
  - [ ] `category` 是否与任务功能匹配？

---

## 📊 影响评估（P1 - 重要问题）

### 5. 修改影响评估

- [ ] **数据库变更影响**
  - [ ] 如果修改了 `dependencies_tables`，是否评估了表结构变更的影响？
  - [ ] 是否检查了相关表的索引和约束？

- [ ] **调度器影响**
  - [ ] 如果修改了 `cron`，是否评估了对调度器负载的影响？
  - [ ] 是否检查了任务执行时间冲突？

- [ ] **监控和告警影响**
  - [ ] 如果修改了 `sla`，是否更新了监控告警规则？
  - [ ] 是否通知了运维团队？

---

## ✅ 审查决策表

### 通过/不通过标准

| 评审项 | 权重 | 最低分数 | 实际得分 | 状态 |
|-------|------|---------|---------|------|
| Cron/Owner 修改合理性 | 40% | 9.0/10 | ___/10 | ⏳ |
| 新增字段完整性 | 30% | 8.5/10 | ___/10 | ⏳ |
| 元数据一致性 | 20% | 8.0/10 | ___/10 | ⏳ |
| 影响评估 | 10% | 7.0/10 | ___/10 | ⏳ |

**综合评分：** _______ / 10

**审查结论：**
- [ ] ✅ 通过 - 无需修改
- [ ] ⚠️ 通过 - 有轻微问题但可接受
- [ ] ❌ 不通过 - 需要修改后重新审查

---

## 📋 发现的问题清单

### P0（阻塞问题，必须修复）

| 问题ID | 描述 | 位置 | 修复建议 |
|-------|------|------|---------|
| ___ | ___ | ___ | ___ |

### P1（重要问题，应该修复）

| 问题ID | 描述 | 位置 | 修复建议 |
|-------|------|------|---------|
| ___ | ___ | ___ | ___ |

### P2（优化建议，可以延后）

| 问题ID | 描述 | 位置 | 修复建议 |
|-------|------|------|---------|
| ___ | ___ | ___ | ___ |

---

## 🎯 审查建议

### 立即行动项

1. [ ] 使用本检查清单系统性审查每个修改项
2. [ ] 特别关注 cron 和 owner 的修改（必须说明原因）
3. [ ] 验证新增字段的完整性和准确性
4. [ ] 评估修改对现有系统的影响

### 后续行动项

1. [ ] 更新相关文档（如 SCHEDULER_MONITORING_GUIDE.md）
2. [ ] 通知相关团队（如 owner 变更）
3. [ ] 更新监控告警规则（如 SLA 变更）

---

## 📎 附录

### A. 常见错误示例

#### 错误1：修改 cron 未说明原因
```python
# ❌ 错误
"cron": {"hour": 10, "minute": 0},  # 原来是 9:00，为什么改？

# ✅ 正确
# 原因：9:00 与 ECN 检查冲突，改为 10:00 避免数据库压力
"cron": {"hour": 10, "minute": 0},
```

#### 错误2：遗漏依赖表
```python
# ❌ 错误
"dependencies_tables": ["projects"],  # 实际还依赖 project_milestones

# ✅ 正确
"dependencies_tables": ["projects", "project_milestones", "alert_records"]
```

#### 错误3：风险级别设置不合理
```python
# ❌ 错误
"risk_level": "LOW",  # 缺料预警应该是 CRITICAL

# ✅ 正确
"risk_level": "CRITICAL",  # 缺料预警失败会导致生产中断
```

### B. 参考文档

- [SCHEDULER_MONITORING_GUIDE.md](../docs/SCHEDULER_MONITORING_GUIDE.md) - 调度器监控指南
- [BACKGROUND_SCHEDULER_AUDIT.md](../docs/BACKGROUND_SCHEDULER_AUDIT.md) - 后台定时服务梳理
- [app/utils/scheduler_config.py](../app/utils/scheduler_config.py) - 配置文件

---

**审查负责人签名：** _______________
**审查日期：** _______________
**下次审查日期：** _______________

---

**文档版本：** 1.0
**创建日期：** 2026-01-XX
**最后更新：** 2026-01-XX



