# TODO/FIXME 标记处理总结

> **更新日期**: 2026-01-20
> **处理进度**: **98%** (仅剩 2 处待处理)

---

## 一、处理概览

经过代码库全面核查，原先记录的大量 TODO 已在模块化重构过程中被实现或清理。

| 统计项 | 原记录 | 当前实际 |
|--------|:------:|:--------:|
| 总 TODO/FIXME 数量 | ~145 个 | **2 个** |
| 已处理 | 4 个 | **143+ 个** |
| 待处理 | ~141 个 | **2 个** |
| 处理进度 | 3% | **98%** |

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
| PMO 负荷复用 | 调用 workload 模块 API | ✅ ���实现 |
| 销售权限 | 实现更严格的权限检查 | ✅ 已实现 |

### 6. 审批系统 ✅ (2026-01-20 实现)

**审批权限验证**
- ✅ `app/api/v1/endpoints/projects/approvals.py` - 实现 `_check_approval_permission()` 函数
- 支持指定审批人检查、角色检查、向后兼容

**审批通知服务**
- ✅ `app/services/approval_engine/notify.py` - 通知去重（30分钟窗口）
- ✅ 用户通知偏好检查（免打扰时段、渠道偏好）
- ✅ 多渠道通知（站内、邮件、企微队列）

**审批代理通知**
- ✅ `app/services/approval_engine/delegate.py` - 代理审批完成后通知原审批人

### 7. 齐套率历史快照 ✅ (2026-01-20 实现)

**文件**: `app/models/assembly_kit.py`, `app/utils/scheduled_tasks/kit_rate_tasks.py`

- ✅ 创建 `KitRateSnapshot` 模型
- ✅ 每日快照定时任务 (`daily_kit_rate_snapshot`)
- ✅ 阶段切换时自动快照 (`create_stage_change_snapshot`)
- ✅ 趋势查询接口 (`/kit-rate/trend`) - 支持按日/月分组
- ✅ 快照查询接口 (`/kit-rate/snapshots`)

---

## 三、待处理的 TODO/FIXME (2 处)

### 中优先级 (P2) - 1 处

#### 1. ERP 集成

**文件**: `app/api/v1/endpoints/projects/sync_utils.py:73`

```python
# 实际ERP集成逻辑（待实现）
```

**建议**: 根据客户实际 ERP 系统对接需求实现

### 低优先级 (P3) - 1 处

#### 2. 团队表模型

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

### 按需实现 (P2/P3)

1. **ERP 集成** - 根据客户实际 ERP 系统对接
2. **团队管理模块** - 当需要团队目标管理功能时开发

---

**最后更新**: 2026-01-20
