# 项目阶段模板系统设计文档

> 创建日期: 2026-01-20
> 状态: 已确认，待实现

## 一、概述

### 1.1 背景

当前系统使用固定的 9 阶段 (S1-S9) 模型，无法满足完整项目生命周期管理需求。原型设计要求支持 22 阶段的完整流程，并提供多种可视化视图。

### 1.2 目标

- 实现可配置的阶段模板系统（支持多套模板 + 项目级微调）
- 新增三种可视化视图：多项目流水线、单项目时间轴、阶段分解树
- 扩展阶段状态：新增"已延期"和"受阻"状态
- 支持阶段下的子节点管理
- 提供项目统计卡片

### 1.3 关键决策

| 决策项 | 选择 | 理由 |
|-------|------|-----|
| 阶段模型策略 | 可配置模板 | 最灵活，支持不同项目类型 |
| 模板配置粒度 | 模板 + 微调 | 平衡规范与灵活 |
| 视图实现顺序 | 流水线 → 时间轴 → 分解树 | 流水线价值最大 |
| 后端集成策略 | 前后端同步实现 | 一步到位 |
| 统计数据来源 | 实时计算 | 数据量可控，准确性优先 |
| 组件复用策略 | 统一容器 + 视图插件 | 状态共享，切换流畅 |

---

## 二、数据模型设计

### 2.1 阶段模板表 (stage_templates)

```python
class StageTemplate(Base, TimestampMixin):
    """阶段模板 - 预定义的阶段流程"""
    __tablename__ = "stage_templates"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)  # 如 "full_lifecycle_22"
    name = Column(String(100), nullable=False)              # 如 "完整22阶段流程"
    description = Column(Text)
    is_system = Column(Boolean, default=False)              # 系统预置 vs 用户自定义
    is_active = Column(Boolean, default=True)

    stages = relationship("StageTemplateItem", back_populates="template")
```

### 2.2 模板阶段项 (stage_template_items)

```python
class StageTemplateItem(Base):
    """模板中的阶段定义"""
    __tablename__ = "stage_template_items"

    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("stage_templates.id"))
    stage_code = Column(String(20), nullable=False)         # 如 "S01", "S02"
    stage_name = Column(String(100), nullable=False)        # 如 "市场开拓"
    stage_order = Column(Integer, nullable=False)           # 顺序号
    category = Column(String(50))                           # 分类：sales/presales/execution/closure
    is_milestone = Column(Boolean, default=False)           # 是否为关键里程碑 ⭐
    is_parallel = Column(Boolean, default=False)            # 是否支持并行执行
    default_duration_days = Column(Integer)                 # 默认工期

    template = relationship("StageTemplate", back_populates="stages")
    nodes = relationship("StageTemplateNode", back_populates="stage")
```

### 2.3 模板节点项 (stage_template_nodes)

```python
class StageTemplateNode(Base):
    """阶段下的子节点定义"""
    __tablename__ = "stage_template_nodes"

    id = Column(Integer, primary_key=True)
    stage_item_id = Column(Integer, ForeignKey("stage_template_items.id"))
    node_code = Column(String(20), nullable=False)          # 如 "S01.1"
    node_name = Column(String(100), nullable=False)         # 如 "市场调研"
    node_order = Column(Integer, nullable=False)
    responsible_dept = Column(String(100))                  # 默认负责部门

    stage = relationship("StageTemplateItem", back_populates="nodes")
```

### 2.4 项目阶段实例 (project_stage_instances)

```python
class ProjectStageInstance(Base, TimestampMixin):
    """项目的阶段实例 - 基于模板生成，可微调"""
    __tablename__ = "project_stage_instances"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("stage_templates.id"))
    stage_code = Column(String(20), nullable=False)
    stage_name = Column(String(100), nullable=False)
    stage_order = Column(Integer, nullable=False)
    category = Column(String(50))
    is_milestone = Column(Boolean, default=False)

    status = Column(Enum(StageStatus), default=StageStatus.PENDING)

    plan_start_date = Column(Date)
    plan_end_date = Column(Date)
    actual_start_date = Column(Date)
    actual_end_date = Column(Date)
    progress = Column(Integer, default=0)

    entry_criteria = Column(Text)
    exit_criteria = Column(Text)
    entry_check_result = Column(Text)
    exit_check_result = Column(Text)
    review_required = Column(Boolean, default=False)
    review_result = Column(Enum(ReviewResult))
    review_date = Column(DateTime)
    review_notes = Column(Text)

    project = relationship("Project", back_populates="stage_instances")
    nodes = relationship("ProjectStageNode", back_populates="stage_instance")
```

### 2.5 项目阶段节点 (project_stage_nodes)

```python
class ProjectStageNode(Base, TimestampMixin):
    """项目阶段下的子节点实例"""
    __tablename__ = "project_stage_nodes"

    id = Column(Integer, primary_key=True)
    stage_instance_id = Column(Integer, ForeignKey("project_stage_instances.id"))
    node_code = Column(String(20), nullable=False)
    node_name = Column(String(100), nullable=False)
    node_order = Column(Integer, nullable=False)

    status = Column(Enum(StageStatus), default=StageStatus.PENDING)
    progress = Column(Integer, default=0)

    responsible_dept = Column(String(100))
    responsible_user_id = Column(Integer, ForeignKey("users.id"))

    plan_start_date = Column(Date)
    plan_end_date = Column(Date)
    actual_start_date = Column(Date)
    actual_end_date = Column(Date)

    stage_instance = relationship("ProjectStageInstance", back_populates="nodes")
    responsible_user = relationship("User")
```

### 2.6 状态枚举扩展

```python
class StageStatus(str, Enum):
    """阶段状态 - 扩展支持延期和受阻"""
    PENDING = "PENDING"          # 未开始 - 灰色
    IN_PROGRESS = "IN_PROGRESS"  # 进行中 - 蓝色
    COMPLETED = "COMPLETED"      # 已完成 - 绿色
    DELAYED = "DELAYED"          # 已延期 - 红色 (新增)
    BLOCKED = "BLOCKED"          # 受阻 - 橙色 (新增)
    SKIPPED = "SKIPPED"          # 已跳过 - 灰色
```

---

## 三、API 设计

### 3.1 阶段模板 API

```
GET    /api/v1/stage-templates                    # 获取所有模板列表
GET    /api/v1/stage-templates/{id}               # 获取模板详情
POST   /api/v1/stage-templates                    # 创建自定义模板
PUT    /api/v1/stage-templates/{id}               # 更新模板
DELETE /api/v1/stage-templates/{id}               # 删除模板
POST   /api/v1/stage-templates/{id}/apply/{project_id}  # 应用模板到项目
```

### 3.2 项目阶段实例 API

```
GET    /api/v1/projects/{project_id}/stages                  # 获取项目阶段
POST   /api/v1/projects/{project_id}/stages                  # 添加自定义阶段
PUT    /api/v1/projects/{project_id}/stages/{stage_id}       # 更新阶段
DELETE /api/v1/projects/{project_id}/stages/{stage_id}       # 删除阶段

POST   /api/v1/projects/{project_id}/stages/{stage_id}/entry-check   # 入口检查
POST   /api/v1/projects/{project_id}/stages/{stage_id}/exit-check    # 出口检查
POST   /api/v1/projects/{project_id}/stages/{stage_id}/review        # 阶段评审
POST   /api/v1/projects/{project_id}/stages/{stage_id}/advance       # 推进阶段
POST   /api/v1/projects/{project_id}/stages/{stage_id}/mark-delayed  # 标记延期
POST   /api/v1/projects/{project_id}/stages/{stage_id}/mark-blocked  # 标记受阻

GET    /api/v1/projects/{project_id}/stages/{stage_id}/nodes         # 获取节点
PUT    /api/v1/projects/{project_id}/stages/{stage_id}/nodes/{node_id}  # 更新节点
```

### 3.3 统计与概览 API

```
GET    /api/v1/project-stages/statistics   # 统计数据
GET    /api/v1/project-stages/overview     # 多项目阶段概览
```

---

## 四、前端组件架构

### 4.1 目录结构

```
src/pages/ProjectStageBoard/
├── index.jsx                      # 主容器组件
├── hooks/
│   ├── useProjectStages.js        # 数据获取和状态管理
│   ├── useStageStatistics.js      # 统计数据
│   └── useStageFilters.js         # 筛选逻辑
├── components/
│   ├── StageStatisticsCards.jsx   # 顶部统计卡片
│   ├── ViewSwitcher.jsx           # 视图切换按钮组
│   ├── StageFilters.jsx           # 筛选器
│   └── StageLegend.jsx            # 颜色图例
└── views/
    ├── PipelineView/              # 多项目流水线视图
    ├── TimelineView/              # 单项目时间轴视图
    └── TreeView/                  # 阶段分解树视图
```

### 4.2 状态颜色配置

```javascript
export const STAGE_STATUS_CONFIG = {
  COMPLETED:   { label: '已完成', color: '#52c41a', bgClass: 'bg-emerald-500/20' },
  IN_PROGRESS: { label: '进行中', color: '#1890ff', bgClass: 'bg-blue-500/20' },
  PENDING:     { label: '未开始', color: '#6b7280', bgClass: 'bg-slate-500/20' },
  DELAYED:     { label: '已延期', color: '#ff4d4f', bgClass: 'bg-red-500/20' },
  BLOCKED:     { label: '受阻',   color: '#faad14', bgClass: 'bg-amber-500/20' },
  SKIPPED:     { label: '已跳过', color: '#9ca3af', bgClass: 'bg-slate-600/20' },
};
```

---

## 五、预置模板

### 5.1 完整22阶段模板 (full_lifecycle_22)

| 类别 | 阶段 |
|-----|------|
| 销售阶段 (1-4) | 市场开拓、线索获取、商机培育、需求评审 |
| 售前阶段 (5-8) | 初立项⭐、售前方案、报价投标、合同签订 |
| 执行阶段 (9-20) | 正式立项⭐、方案设计、详细设计、采购外协、机械装配、电气装配、软件开发、整机联调、内部验收、出厂发运、现场安装、客户验收 |
| 收尾阶段 (21-22) | 项目收尾、质保服务 |

### 5.2 标准9阶段模板 (standard_9)

兼容现有系统的 S1-S9 阶段定义。

---

## 六、实现计划

| Phase | 任务 | 产出 |
|-------|------|-----|
| Phase 1 | 后端数据模型、枚举扩展、数据库迁移 | 5 张表 + 状态枚举 |
| Phase 2 | 模板服务、CRUD API、预置模板初始化 | 模板管理功能 |
| Phase 3 | 项目阶段实例 API、统计 API | 阶段管理 API |
| Phase 4 | 前端容器、Hooks、统计卡片、筛选器 | 页面框架 |
| Phase 5 | 流水线视图全部组件 | 核心视图 |
| Phase 6 | 时间轴视图全部组件 | 详情视图 |
| Phase 7 | 分解树视图全部组件 | 辅助视图 |
| Phase 8 | 集成测试、数据迁移验证 | 质量保障 |

---

## 七、风险与注意事项

1. **数据迁移**: 现有 `project_phases` 表数据需迁移到新的 `project_stage_instances` 表
2. **向后兼容**: 保留 `standard_9` 模板确保现有项目正常运行
3. **性能**: 多项目概览接口需要优化查询，避免 N+1 问题
4. **UI 适配**: 保持深色主题风格一致性
