# 项目阶段模板化设计方案

> 设计日期: 2026-01-20
> 状态: 已确认

## 一、背景与需求

### 问题
- 当前系统阶段硬编码为 S1-S9，过于粗粒度
- 无法配置大阶段下的小节点
- 不同项目类型（全新/重复/简单）流程不同，无法灵活适配

### 目标
1. 支持「大阶段 + 小节点」的层级结构
2. 阶段和节点完全可配置
3. 支持模板管理，立项时选择并可微调
4. 支持不同项目类型的差异化流程

## 二、设计决策

| 决策项 | 选择 |
|-------|------|
| 配置模式 | 完全可配置（大阶段+小节点都可自定义） |
| 小节点类型 | 任务/审批/交付物 |
| 完成判定 | 按类型：手动/审批流/上传附件/自动 |
| 模板管理权限 | 管理员+项目经理可管理，立项时可微调 |
| 流转规则 | 可配置前置依赖 |
| 技术方案 | 模板驱动（模板层+实例层分离） |

## 三、数据模型

### 3.1 模板层（定义层）

#### StageTemplate (阶段模板表)

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 主键 |
| template_code | String(50) | 模板编码 |
| template_name | String(100) | 模板名称 |
| description | Text | 模板描述 |
| project_type | Enum | 适用项目类型: NEW/REPEAT/SIMPLE/CUSTOM |
| is_default | Boolean | 是否默认模板 |
| is_active | Boolean | 是否启用 |
| created_by | Integer | 创建人ID |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

#### StageDefinition (大阶段定义表)

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 主键 |
| template_id | Integer | 所属模板ID (FK) |
| stage_code | String(20) | 阶段编码 |
| stage_name | String(100) | 阶段名称 |
| sequence | Integer | 排序序号 |
| estimated_days | Integer | 预计工期(天) |
| description | Text | 阶段描述 |
| is_required | Boolean | 是否必需阶段 |

#### NodeDefinition (小节点定义表)

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 主键 |
| stage_definition_id | Integer | 所属阶段ID (FK) |
| node_code | String(20) | 节点编码 |
| node_name | String(100) | 节点名称 |
| node_type | Enum | 节点类型: TASK/APPROVAL/DELIVERABLE |
| sequence | Integer | 排序序号 |
| estimated_days | Integer | 预计工期(天) |
| completion_method | Enum | 完成方式: MANUAL/APPROVAL/UPLOAD/AUTO |
| dependency_node_ids | JSON | 前置依赖节点ID列表 |
| is_required | Boolean | 是否必需节点 |
| required_attachments | Boolean | 是否需上传附件 |
| approval_role_ids | JSON | 审批角色ID列表(审批类节点) |
| auto_condition | JSON | 自动完成条件配置(自动类节点) |

### 3.2 实例层（项目运行时）

#### Project 表新增字段

| 字段 | 类型 | 说明 |
|-----|------|------|
| template_id | Integer | 使用的模板ID (FK) |
| current_stage_id | Integer | 当前所处阶段实例ID |
| current_node_id | Integer | 当前节点实例ID |

#### ProjectStageInstance (项目阶段实例表)

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 主键 |
| project_id | Integer | 所属项目ID (FK) |
| stage_definition_id | Integer | 来源阶段定义ID (FK, nullable) |
| stage_code | String(20) | 阶段编码 |
| stage_name | String(100) | 阶段名称 |
| sequence | Integer | 排序序号 |
| status | Enum | 状态: PENDING/IN_PROGRESS/COMPLETED/SKIPPED |
| planned_start_date | Date | 计划开始日期 |
| planned_end_date | Date | 计划结束日期 |
| actual_start_date | Date | 实际开始日期 |
| actual_end_date | Date | 实际结束日期 |
| is_modified | Boolean | 是否被调整过 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

#### ProjectNodeInstance (项目节点实例表)

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 主键 |
| project_id | Integer | 所属项目ID (FK) |
| stage_instance_id | Integer | 所属阶段实例ID (FK) |
| node_definition_id | Integer | 来源节点定义ID (FK, nullable) |
| node_code | String(20) | 节点编码 |
| node_name | String(100) | 节点名称 |
| node_type | Enum | 节点类型 |
| sequence | Integer | 排序序号 |
| status | Enum | 状态: PENDING/IN_PROGRESS/COMPLETED/SKIPPED |
| completion_method | Enum | 完成方式 |
| dependency_node_instance_ids | JSON | 前置依赖节点实例ID列表 |
| planned_date | Date | 计划完成日期 |
| actual_date | Date | 实际完成日期 |
| completed_by | Integer | 完成人ID |
| completed_at | DateTime | 完成时间 |
| attachments | JSON | 上传的附件列表 |
| approval_record_id | Integer | 关联审批记录ID |
| remark | Text | 备注 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

## 四、核心业务流程

### 4.1 立项流程

```
选择模板 → 预览阶段/节点 → 调整(可选) → 确认生成实例
    │                           │
    │                           ├─ 增加节点
    │                           ├─ 删除节点(非必需)
    │                           ├─ 修改计划时间
    │                           └─ 调整依赖关系
    │
    └─ 支持"另存为新模板"(项目经理权限)
```

### 4.2 节点完成判定

| 节点类型 | completion_method | 完成条件 |
|---------|-------------------|---------|
| 任务类 TASK | MANUAL | 负责人点击「完成」 |
| 审批类 APPROVAL | APPROVAL | 审批流程通过 |
| 交付物 DELIVERABLE | UPLOAD | 上传附件后标记完成 |
| 自动类 | AUTO | 关联业务数据满足条件 |

### 4.3 依赖检查逻辑

```python
def can_start_node(node_instance):
    """检查节点是否可以开始"""
    for dep_id in node_instance.dependency_node_instance_ids:
        dep_node = get_node_instance(dep_id)
        if dep_node.status not in ['COMPLETED', 'SKIPPED']:
            return False, f"前置节点「{dep_node.node_name}」未完成"
    return True, None
```

### 4.4 阶段自动流转

- 当阶段内所有「必需节点」完成 → 阶段状态自动变为 COMPLETED
- 当阶段首个节点开始 → 阶段状态自动变为 IN_PROGRESS

## 五、API 设计

### 5.1 模板管理 API

```
POST   /api/v1/stage-templates              # 创建模板
GET    /api/v1/stage-templates              # 模板列表
GET    /api/v1/stage-templates/{id}         # 模板详情(含阶段和节点)
PUT    /api/v1/stage-templates/{id}         # 更新模板
DELETE /api/v1/stage-templates/{id}         # 删除模板(未被使用时)
POST   /api/v1/stage-templates/{id}/clone   # 复制模板
```

### 5.2 立项时使用

```
GET    /api/v1/stage-templates/available    # 获取可用模板列表
POST   /api/v1/projects/{id}/init-stages    # 基于模板初始化阶段
       Body: { template_id, adjustments: [...] }
```

### 5.3 项目阶段/节点操作

```
GET    /api/v1/projects/{id}/stages                    # 项目阶段列表
GET    /api/v1/projects/{id}/stages/{stage_id}/nodes   # 阶段下节点列表
PUT    /api/v1/projects/{id}/nodes/{node_id}/start     # 开始节点
PUT    /api/v1/projects/{id}/nodes/{node_id}/complete  # 完成节点
PUT    /api/v1/projects/{id}/nodes/{node_id}/skip      # 跳过节点
POST   /api/v1/projects/{id}/nodes/{node_id}/upload    # 上传附件
```

### 5.4 权限控制

| 操作 | 管理员 | 项目经理 | 项目成员 |
|-----|-------|---------|---------|
| 创建/编辑/删除模板 | ✓ | ✓ | ✗ |
| 立项时调整节点 | ✓ | ✓ | ✗ |
| 开始/完成节点 | ✓ | ✓ | ✓ (负责的) |
| 跳过节点 | ✓ | ✓ | ✗ |

## 六、迁移策略

### 6.1 数据迁移步骤

1. 创建默认「标准全流程」模板，包含 S1-S9 阶段定义
2. 为每个现有项目生成阶段实例（基于默认模板）
3. 根据项目当前 `stage` 字段设置实例状态
4. 保留原 `stage` 字段作为冗余，逐步废弃

### 6.2 预置模板

| 模板名称 | 适用场景 | 大阶段数 | 说明 |
|---------|---------|---------|------|
| 标准全流程 | 复杂新产品 | 9 | S1-S9 完整流程 |
| 快速开发 | 简单新产品 | 5 | 跳过售前、简化评审 |
| 重复生产 | 成熟产品 | 4 | 直接进入生产阶段 |

> 注：初期先实现以上 3 个模板，后续可根据业务需要添加更多模板（如更复杂的定制流程）。

### 6.3 标准全流程模板示例

```
S1 需求进入
   ├─ [TASK] 客户需求收集
   ├─ [APPROVAL] 需求评审
   └─ [DELIVERABLE] 需求规格书

S2 方案设计
   ├─ [TASK] 概念设计
   ├─ [TASK] 3D建模
   ├─ [APPROVAL] 方案评审
   └─ [DELIVERABLE] 设计方案书

S3 采购备料
   ├─ [TASK] BOM编制
   ├─ [APPROVAL] BOM审核
   ├─ [AUTO] 采购下单
   └─ [AUTO] 物料到齐

S4 加工制造
   ├─ [TASK] 机加工
   ├─ [TASK] 钣金加工
   └─ [TASK] 外协加工跟踪

S5 装配调试
   ├─ [TASK] 机械装配
   ├─ [TASK] 电气装配
   ├─ [TASK] 程序调试
   └─ [APPROVAL] 内部验收

S6 出厂验收(FAT)
   ├─ [TASK] FAT准备
   ├─ [APPROVAL] 客户FAT验收
   └─ [DELIVERABLE] FAT报告

S7 包装发运
   ├─ [TASK] 拆机包装
   ├─ [TASK] 物流安排
   └─ [DELIVERABLE] 发货清单

S8 现场安装(SAT)
   ├─ [TASK] 现场安装
   ├─ [TASK] 现场调试
   ├─ [APPROVAL] 客户SAT验收
   └─ [DELIVERABLE] SAT报告

S9 质保结项
   ├─ [TASK] 质保期维护
   ├─ [APPROVAL] 终验收
   └─ [DELIVERABLE] 结项报告
```

## 七、实施建议

### 第一阶段：基础功能
1. 数据库迁移（新增6张表）
2. 模板管理 CRUD API
3. 立项时选择模板并生成实例
4. 节点手动完成功能

### 第二阶段：进阶功能
1. 审批类节点对接审批流
2. 交付物上传功能
3. 依赖检查和自动流转
4. 项目进度可视化（甘特图/看板）

### 第三阶段：智能化
1. 自动类节点（关联采购、物料等模块）
2. 节点预警（超期提醒）
3. 模板使用分析和优化建议
