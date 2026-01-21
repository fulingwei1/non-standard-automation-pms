# 项目阶段模板化 - 实施计划

> 分支: feature/stage-template-system
> 创建日期: 2026-01-20

## 实施阶段

### 第一阶段：数据层（预计 2-3 天）

#### 1.1 枚举定义
- [ ] 创建 `app/models/enums/stage.py`
  - `NodeTypeEnum`: TASK / APPROVAL / DELIVERABLE
  - `CompletionMethodEnum`: MANUAL / APPROVAL / UPLOAD / AUTO
  - `StageStatusEnum`: PENDING / IN_PROGRESS / COMPLETED / SKIPPED
  - `ProjectTypeEnum`: NEW / REPEAT / SIMPLE / CUSTOM

#### 1.2 模板层模型
- [ ] 创建 `app/models/stage_template.py`
  - `StageTemplate` 阶段模板表
  - `StageDefinition` 大阶段定义表
  - `NodeDefinition` 小节点定义表

#### 1.3 实例层模型
- [ ] 创建 `app/models/stage_instance.py`
  - `ProjectStageInstance` 项目阶段实例表
  - `ProjectNodeInstance` 项目节点实例表

#### 1.4 数据库迁移
- [ ] 创建迁移文件 `migrations/20260120_stage_template_sqlite.sql`
- [ ] 创建迁移文件 `migrations/20260120_stage_template_mysql.sql`

#### 1.5 Project 表扩展
- [ ] 添加字段: `template_id`, `current_stage_id`, `current_node_id`

---

### 第二阶段：服务层（预计 2-3 天）

#### 2.1 模板服务
- [ ] 创建 `app/services/stage_template_service.py`
  - `create_template()` 创建模板
  - `update_template()` 更新模板
  - `delete_template()` 删除模板
  - `clone_template()` 复制模板
  - `get_template_detail()` 获取模板详情（含阶段和节点）

#### 2.2 实例服务
- [ ] 创建 `app/services/stage_instance_service.py`
  - `init_project_stages()` 基于模板初始化项目阶段
  - `adjust_stages()` 立项时调整阶段/节点
  - `start_node()` 开始节点
  - `complete_node()` 完成节点
  - `skip_node()` 跳过节点
  - `check_dependencies()` 检查前置依赖
  - `auto_update_stage_status()` 自动更新阶段状态

#### 2.3 预置模板数据
- [ ] 创建 `app/services/stage_template_seed.py`
  - 标准全流程模板（9阶段）
  - 快速开发模板（5阶段）
  - 重复生产模板（4阶段）

---

### 第三阶段：API 层（预计 2 天）

#### 3.1 Schemas
- [ ] 创建 `app/schemas/stage_template.py`
  - 模板 CRUD schemas
  - 阶段/节点 schemas
  - 立项调整 schemas

#### 3.2 模板管理 API
- [ ] 创建 `app/api/v1/endpoints/stage_templates.py`
  - `POST /stage-templates` 创建模板
  - `GET /stage-templates` 模板列表
  - `GET /stage-templates/{id}` 模板详情
  - `PUT /stage-templates/{id}` 更新模板
  - `DELETE /stage-templates/{id}` 删除模板
  - `POST /stage-templates/{id}/clone` 复制模板
  - `GET /stage-templates/available` 可用模板列表

#### 3.3 项目阶段 API
- [ ] 创建 `app/api/v1/endpoints/projects/stages.py`
  - `POST /projects/{id}/init-stages` 初始化阶段
  - `GET /projects/{id}/stages` 项目阶段列表
  - `GET /projects/{id}/stages/{stage_id}/nodes` 节点列表
  - `PUT /projects/{id}/nodes/{node_id}/start` 开始节点
  - `PUT /projects/{id}/nodes/{node_id}/complete` 完成节点
  - `PUT /projects/{id}/nodes/{node_id}/skip` 跳过节点
  - `POST /projects/{id}/nodes/{node_id}/upload` 上传附件

#### 3.4 路由注册
- [ ] 更新 `app/api/v1/api.py` 注册新路由

---

### 第四阶段：数据迁移（预计 1 天）

#### 4.1 迁移脚本
- [ ] 创建 `scripts/migrate_stages.py`
  - 初始化预置模板
  - 为现有项目生成阶段实例
  - 根据原 `stage` 字段设置实例状态

#### 4.2 兼容处理
- [ ] 保留原 `Project.stage` 字段
- [ ] 添加状态同步逻辑（新旧字段保持一致）

---

### 第五阶段：测试（预计 1-2 天）

#### 5.1 单元测试
- [ ] `tests/unit/test_stage_template_service.py`
- [ ] `tests/unit/test_stage_instance_service.py`

#### 5.2 API 测试
- [ ] `tests/api/test_stage_templates_api.py`
- [ ] `tests/api/test_project_stages_api.py`

---

## 文件清单

```
新增文件:
├── app/models/enums/stage.py
├── app/models/stage_template.py
├── app/models/stage_instance.py
├── app/schemas/stage_template.py
├── app/services/stage_template_service.py
├── app/services/stage_instance_service.py
├── app/services/stage_template_seed.py
├── app/api/v1/endpoints/stage_templates.py
├── app/api/v1/endpoints/projects/stages.py
├── migrations/20260120_stage_template_sqlite.sql
├── migrations/20260120_stage_template_mysql.sql
├── scripts/migrate_stages.py
├── tests/unit/test_stage_template_service.py
├── tests/unit/test_stage_instance_service.py
├── tests/api/test_stage_templates_api.py
└── tests/api/test_project_stages_api.py

修改文件:
├── app/models/enums/__init__.py
├── app/models/__init__.py
├── app/models/project/core.py (添加新字段)
└── app/api/v1/api.py (注册路由)
```

## 实施顺序

1. 枚举定义 → 2. 模型定义 → 3. 迁移文件 → 4. 服务层 → 5. Schemas → 6. API → 7. 路由注册 → 8. 预置数据 → 9. 迁移脚本 → 10. 测试
