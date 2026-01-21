# 预警系统合并设计方案

> 日期: 2026-01-21
> 状态: Phase 1 已完成

## 背景

当前系统存在预警系统重复实现问题：

| 表名 | 行数 | 用途 | 状态 |
|------|------|------|------|
| `alert_records` | 27 | 统一预警记录（多态关联） | ✅ 保留 |
| `shortage_alerts` | 0 | 缺料预警（重复） | ❌ 删除 |
| `mat_shortage_alert` | 0 | MES缺料预警（重复） | ❌ 删除 |
| `alert_rules` | 10 | 统一规则配置 | ✅ 保留 |
| `mes_shortage_alert_rule` | 4 | MES缺料规则（重复） | ⚠️ 迁移后删除 |

## 决策

1. **保留**: `alert_records` 作为唯一预警记录表（通过 `target_type` 多态关联）
2. **删除**: 3 个空的重复表
3. **迁移**: `mes_shortage_alert_rule` 的 4 条规则到 `alert_rules`

## 统一数据模型

### 现有架构（保留）

```
┌─────────────────────────────────────────────────────────────┐
│  alert_rules (预警规则)                                      │
│  - target_type 区分业务类型: PROJECT/MATERIAL/SHORTAGE/...  │
├─────────────────────────────────────────────────────────────┤
│  alert_records (预警记录)                                    │
│  - target_type + target_id 关联任意业务对象                  │
│  - alert_data JSON ��储业务特定字段                          │
├─────────────────────────────────────────────────────────────┤
│  alert_notifications (通知记录)                              │
│  - 关联 alert_records                                        │
└──────────���──────────────────────────────────────────────────┘
```

### target_type 枚举值

- `PROJECT` - 项目预警
- `MATERIAL` - 物料预警
- `SHORTAGE` - 缺料预警（替代 shortage_alerts 和 mat_shortage_alert）
- `SCHEDULE` - 进度预警
- `COST` - 成本预警
- `QUALITY` - 质量预警

## 要删除的表

### 1. shortage_alerts（空表）

```sql
DROP TABLE IF EXISTS shortage_alerts;
```

### 2. mat_shortage_alert（空表）

```sql
DROP TABLE IF EXISTS mat_shortage_alert;
```

### 3. mes_shortage_detail（空表）

```sql
DROP TABLE IF EXISTS mes_shortage_detail;
```

### 4. mes_shortage_alert_rule（迁移后删除）

迁移 4 条规则到 `alert_rules` 后删除：

```sql
-- 先迁移规则（如有需要保留的规则）
INSERT INTO alert_rules (rule_code, rule_name, rule_type, target_type, ...)
SELECT
    'MES_' || rule_code,
    rule_name,
    'SHORTAGE',
    'SHORTAGE',
    ...
FROM mes_shortage_alert_rule;

-- 然后删除
DROP TABLE IF EXISTS mes_shortage_alert_rule;
```

## 要保留的表

| 表名 | 说明 |
|------|------|
| `alert_records` | 统一预警记录 |
| `alert_notifications` | 预警通知 |
| `alert_rules` | 预警规则 |
| `alert_rule_templates` | 规则模板 |
| `alert_statistics` | 预警统计 |
| `alert_subscriptions` | 订阅配置 |
| `mat_alert_log` | 处理日志（缺料专用，暂保留） |
| `mat_shortage_daily_report` | 缺料日报（聚合报表，保留） |
| `shortage_reports` | 缺料报告 |
| `material_shortages` | 物料缺料记录 |

## 服务层分析

### 当前服务分布

```
app/services/
├── alert_rule_engine/          # 规则引擎（通用）- 保留
├── shortage/                   # 缺料服务
│   └── shortage_alerts_service.py  # 使用 shortage_alerts 表 - 需要迁移
├── wechat_alert_service.py     # 微信通知 - 保留
├── shortage_report_service.py  # 缺料报告 - 保留
└── ...
```

### 需要修改的服务

1. `shortage_alerts_service.py` - 改用 `alert_records` 表，`target_type='SHORTAGE'`

## 迁移计划

### Phase 1: 验证空表（无破坏性）

1.1 确认 `shortage_alerts`, `mat_shortage_alert`, `mes_shortage_detail` 为空
1.2 检查是否有服务依赖这些表

### Phase 2: 迁移规则

2.1 迁移 `mes_shortage_alert_rule` 的 4 条规则到 `alert_rules`
2.2 验证规则可用

### Phase 3: 更新服务

3.1 修改 `shortage_alerts_service.py` 使用 `AlertRecord` 模型
3.2 更新相关 API 端点

### Phase 4: 清理

4.1 删除空表
4.2 删除旧 Model 类
4.3 运行测试验证

## 实施步骤

由于所有重复表都是空的，实施风险很低：

```sql
-- 1. 删除空的重复表
DROP TABLE IF EXISTS shortage_alerts;
DROP TABLE IF EXISTS mat_shortage_alert;
DROP TABLE IF EXISTS mes_shortage_detail;

-- 2. 迁移 MES 规则（如需保留）
-- [见上面的迁移 SQL]

-- 3. 删除 MES 规则表
DROP TABLE IF EXISTS mes_shortage_alert_rule;
```

## 风险控制

- **风险**: 极低（所有重复表都是空的）
- **回滚**: 可以通过迁移脚本重建表结构
- **测试覆盖**: 运行 alert 相关测试确保功能正常

## 预计工作量

| 阶段 | 文件数 | 复杂度 |
|------|--------|--------|
| Phase 1 | 0 | 低 |
| Phase 2 | 1 | 低 |
| Phase 3 | 2-3 | 中 |
| Phase 4 | 4 | 低 |

---

## 执行记录

### Phase 1 完成 (2026-01-21)

**已删除的孤儿表：**
- `shortage_alerts` - 无对应 Model，0 行数据
- `mes_shortage_detail` - 0 行数据

**暂未删除（有服务依赖）：**
- `mat_shortage_alert` (0 行) - 被以下服务引用：
  - `shortage_report_service.py`
  - `progress_integration_service.py`
  - `urgent_purchase_from_shortage_service.py`
- `mes_shortage_alert_rule` (4 行) - 被 `wechat_alert_service.py` 引用

**Phase 2 待办：**
1. 迁移 `ShortageAlert` 模型的服务到使用 `AlertRecord`
2. 迁移 `mes_shortage_alert_rule` 数据到 `alert_rules`
3. 删除 `mat_shortage_alert` 和 `mes_shortage_alert_rule` 表
4. 删除 `ShortageAlert` 模型类
