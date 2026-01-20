# TODO/FIXME 标记处理总结

> **更新日期**: 2026-01-20
> **处理进度**: **95%** (仅剩 8 处待处理)

---

## 一、处理概览

经过代码库全面核查，原先记录的大量 TODO 已在模块化重构过程中被实现或清理。

| 统计项 | 原记录 | 当前实际 |
|--------|:------:|:--------:|
| 总 TODO/FIXME 数量 | ~145 个 | **8 个** |
| 已处理 | 4 个 | **137+ 个** |
| 待处理 | ~141 个 | **8 个** |
| 处理进度 | 3% | **95%** |

---

## 二、已处理的 TODO/FIXME ✅

### 1. 通知功能实现 ✅

**文件**: `app/api/v1/endpoints/task_center.py`

- ✅ **任务转办通知** - 转办任务时发送通知给目标用户
- ✅ **转办拒绝通知** - 拒绝转办时通知原转办人
- ✅ **评论@用户通知** - 评论中@用户时发送通知

### 2. IP 地址获取 ✅

**文件**: `app/api/v1/endpoints/acceptance/`

- ✅ **验收签字 IP 地址** - 从 Request 对象获取客户端 IP 地址

### 3. 报表中心功能 ✅ (原高优先级，已全部实现)

**文件**: `app/api/v1/endpoints/report_center/` (已模块化拆分)

- ✅ 权限矩阵读取
- ✅ 报表数据生成
- ✅ 文件导出功能
- ✅ 各角色视角数据对比
- ✅ 模板配置生成

### 4. 缺料管理功能 ✅ (原高优先级，已全部实现)

**文件**: `app/api/v1/endpoints/shortage/` 或 `assembly_kit/shortage_alerts.py`

- ✅ BOM 更新逻辑
- ✅ 项目库存调拨

### 5. 中优先级功能 ✅ (原记录已全部处理)

| 原记录模块 | 原描述 | 状态 |
|------------|--------|:----:|
| 任务分配 | 根据角色查找用户并分配 | ✅ 已实现 |
| 售前管理 | 解析 cost_template JSON | ✅ 已实现 |
| 工作量管理 | 从 WorkerSkill 表获取技能 | ✅ 模块重构 |
| PMO 阶段推进 | 推进到下一阶段的逻辑 | ✅ 已实现 (`pmo/phases.py:322-347`) |
| PMO 负荷复用 | 调用 workload 模块 API | ✅ 已实现 |
| 销售权限 | 实现更严格的权限检查 | ✅ 已实现 |

---

## 三、待处理的 TODO/FIXME (8 处)

### 高优先级 (P1) - 4 处

#### 1. 审批权限验证

**文件**: `app/api/v1/endpoints/projects/approvals.py:200`

```python
# TODO: 验证当前用户是否有权限审批（角色或指定审批人）
# 简化处理：任何活跃用户都可以审批
```

**建议**: 集成 `approval_engine` 的权限检查逻辑

#### 2. 审批通知服务 (3 处)

**文件**: `app/services/approval_engine/notify.py:373-375`

```python
# TODO: 根据用户配置和通知类型选择渠道
# TODO: 异步发送通知
# TODO: 通知去重和聚合
```

**建议**:
- 集成企业微信/钉钉 SDK
- 使用 Celery 或 APScheduler 实现异步
- 添加 Redis 缓存实现去重

#### 3. 审批代理通知

**文件**: `app/services/approval_engine/delegate.py:350`

```python
# TODO: 发送通知
```

**建议**: 复用 `notify.py` 的通知服务

### 中优先级 (P2) - 3 处

#### 4. ERP 集成

**文件**: `app/api/v1/endpoints/projects/sync_utils.py:73`

```python
# 实际ERP集成逻辑（待实现）
```

**建议**: 根据客户实际 ERP 系统对接需求实现

#### 5. 齐套率历史快照 (2 处)

**文件**: `app/api/v1/endpoints/kit_rate/dashboard.py:108, 207`

```
历史快照功能待实现（需要创建 KitRateSnapshot 模型）
```

**建议**:
- 创建 `KitRateSnapshot` 模型
- 添加定时任务每日生成快照

### 低优先级 (P3) - 1 处

#### 6. 团队表模型

**文件**: `app/models/sales/workflow.py:132`

```python
team_id = Column(Integer, comment="团队ID（团队目标，暂未实现团队表）")
```

**建议**: 当需要团队目标管理功能时实现

---

## 四、前端 TODO 情况

前端 TODO 主要是 API 集成相关，不在本文档统计范围。

详见: `docs/progress/FRONTEND_API_INTEGRATION_STATUS_SUMMARY.md`

---

## 五、注意事项

1. **状态值 "TODO"**:
   - `app/models/progress.py` 中的 `"TODO"` 是任务状态枚举值，不是待办事项

2. **模块化重构说明**:
   - 原单文件 `presale.py`, `pmo.py`, `sales.py` 等已拆分为多个子目录
   - 原行号已失效，请按模块目录查找

3. **向后兼容**:
   - 所有修改保持向后兼容，不影响现有功能

---

## 六、下一步建议

### 短期 (1-2 周)

1. **完善审批系统** (P1)
   - 实现审批权限验证
   - 集成通知渠道（企微/邮件）
   - 实现异步通知和去重

### 中期 (1 个月)

2. **齐套率增强** (P2)
   - 创建 KitRateSnapshot 模型
   - 实现历史趋势分析

### 长期 (按需)

3. **外部系统集成** (P2/P3)
   - ERP 集成（根据客户需求）
   - 团队管理模块（按需开发）

---

**最后更新**: 2026-01-20
