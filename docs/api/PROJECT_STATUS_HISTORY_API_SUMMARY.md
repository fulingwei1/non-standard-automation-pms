# 项目三维状态管理和状态变更历史 API 实现总结

## 概述

本文档总结了项目三维状态管理（阶段、状态、健康度）和状态变更历史功能的 API 实现情况。

## 实现时间

2025-01-XX

## 1. 数据模型

### 1.1 ProjectStatusLog 模型

**文件**: `app/models/project.py`

新增了 `ProjectStatusLog` 模型，用于记录项目状态变更历史：

```python
class ProjectStatusLog(Base):
    """项目状态变更日志表"""
    
    __tablename__ = "project_status_logs"
    
    # 基本信息
    id: int
    project_id: int
    machine_id: Optional[int]
    
    # 变更前状态
    old_stage: Optional[str]
    old_status: Optional[str]
    old_health: Optional[str]
    
    # 变更后状态
    new_stage: Optional[str]
    new_status: Optional[str]
    new_health: Optional[str]
    
    # 变更信息
    change_type: str  # STAGE_CHANGE/STATUS_CHANGE/HEALTH_CHANGE
    change_reason: Optional[str]
    change_note: Optional[str]
    
    # 操作信息
    changed_by: Optional[int]
    changed_at: datetime
```

**特性**:
- ✅ 支持记录阶段、状态、健康度的变更
- ✅ 记录变更前后状态对比
- ✅ 记录变更人、变更时间
- ✅ 支持关联机台（可选）
- ✅ 索引优化（project_id, machine_id, changed_at）

## 2. API 端点

### 2.1 更新项目阶段

**端点**: `PUT /api/v1/projects/{project_id}/stage`

**功能**:
- 更新项目阶段（S1-S9）
- 自动记录状态变更历史
- 如果阶段没有变化，直接返回

**请求参数**:
- `project_id`: 项目ID（路径参数）
- `stage`: 阶段编码（查询参数，S1-S9）

**响应**: `ProjectResponse`

**历史记录**:
- 自动创建 `ProjectStatusLog` 记录
- `change_type`: `STAGE_CHANGE`
- 记录变更前后的阶段、状态、健康度

### 2.2 更新项目状态

**端点**: `PUT /api/v1/projects/{project_id}/status`

**功能**:
- 更新项目状态（ST01-ST30）
- 自动记录状态变更历史
- 如果状态没有变化，直接返回

**请求参数**:
- `project_id`: 项目ID（路径参数）
- `status`: 状态编码（查询参数，ST01-ST30）

**响应**: `ProjectResponse`

**历史记录**:
- 自动创建 `ProjectStatusLog` 记录
- `change_type`: `STATUS_CHANGE`
- 记录变更前后的阶段、状态、健康度

### 2.3 更新项目健康度

**端点**: `PUT /api/v1/projects/{project_id}/health`

**功能**:
- 更新项目健康度（H1-H4）
- 自动记录状态变更历史
- 如果健康度没有变化，直接返回

**请求参数**:
- `project_id`: 项目ID（路径参数）
- `health`: 健康度编码（查询参数，H1-H4）

**响应**: `ProjectResponse`

**历史记录**:
- 自动创建 `ProjectStatusLog` 记录
- `change_type`: `HEALTH_CHANGE`
- 记录变更前后的阶段、状态、健康度

### 2.4 获取状态变更历史

**端点**: `GET /api/v1/projects/{project_id}/status-history`

**功能**:
- 获取项目的状态变更历史记录
- 支持按变更类型筛选
- 支持限制返回记录数

**请求参数**:
- `project_id`: 项目ID（路径参数）
- `change_type`: 变更类型筛选（查询参数，可选）
  - `STAGE_CHANGE`: 阶段变更
  - `STATUS_CHANGE`: 状态变更
  - `HEALTH_CHANGE`: 健康度变更
- `limit`: 返回记录数（查询参数，默认50，最大200）

**响应**: `List[ProjectStatusLogResponse]`

**响应字段**:
- `id`: 记录ID
- `project_id`: 项目ID
- `machine_id`: 机台ID（可选）
- `old_stage`, `old_status`, `old_health`: 变更前状态
- `new_stage`, `new_status`, `new_health`: 变更后状态
- `change_type`: 变更类型
- `change_reason`: 变更原因
- `change_note`: 变更备注
- `changed_by`: 变更人ID
- `changed_by_name`: 变更人姓名
- `changed_at`: 变更时间

**排序**: 按变更时间倒序（最新的在前）

## 3. Schema 定义

### 3.1 ProjectStatusLogResponse

**文件**: `app/schemas/project.py`

```python
class ProjectStatusLogResponse(BaseSchema):
    """项目状态变更历史响应"""
    
    id: int
    project_id: int
    machine_id: Optional[int]
    
    # 变更前状态
    old_stage: Optional[str]
    old_status: Optional[str]
    old_health: Optional[str]
    
    # 变更后状态
    new_stage: Optional[str]
    new_status: Optional[str]
    new_health: Optional[str]
    
    # 变更信息
    change_type: str
    change_reason: Optional[str]
    change_note: Optional[str]
    
    # 操作信息
    changed_by: Optional[int]
    changed_by_name: Optional[str]
    changed_at: datetime
```

## 4. 实现特性

### 4.1 自动历史记录

- ✅ 所有状态变更（阶段、状态、健康度）自动记录历史
- ✅ 记录变更前后完整状态
- ✅ 记录变更人和变更时间
- ✅ 避免重复记录（如果状态没有变化，不创建历史记录）

### 4.2 数据完整性

- ✅ 外键约束（project_id, machine_id, changed_by）
- ✅ 索引优化（project_id, machine_id, changed_at）
- ✅ 自动补充变更人姓名

### 4.3 查询优化

- ✅ 支持按变更类型筛选
- ✅ 支持限制返回记录数
- ✅ 按时间倒序排列（最新的在前）

## 5. 使用示例

### 5.1 更新项目阶段

```bash
PUT /api/v1/projects/1/stage?stage=S2
```

**响应**:
```json
{
  "id": 1,
  "project_code": "PJ20250101001",
  "project_name": "测试项目",
  "stage": "S2",
  "status": "ST01",
  "health": "H1",
  ...
}
```

**自动创建历史记录**:
```json
{
  "project_id": 1,
  "old_stage": "S1",
  "new_stage": "S2",
  "change_type": "STAGE_CHANGE",
  "changed_by": 1,
  "changed_at": "2025-01-XX 10:00:00"
}
```

### 5.2 获取状态变更历史

```bash
GET /api/v1/projects/1/status-history?change_type=STAGE_CHANGE&limit=20
```

**响应**:
```json
[
  {
    "id": 1,
    "project_id": 1,
    "old_stage": "S1",
    "new_stage": "S2",
    "change_type": "STAGE_CHANGE",
    "changed_by": 1,
    "changed_by_name": "admin",
    "changed_at": "2025-01-XX 10:00:00"
  },
  ...
]
```

## 6. 安全特性

- ✅ JWT 认证（所有端点）
- ✅ 用户权限检查
- ✅ 数据验证（阶段/状态/健康度编码验证）

## 7. 错误处理

- ✅ 404：项目不存在
- ✅ 400：无效的阶段/状态/健康度编码
- ✅ 400：无效的变更类型
- ✅ 401：未认证
- ✅ 403：无权限

## 8. 后续优化建议

1. **批量查询**: 支持批量查询多个项目的状态变更历史
2. **时间范围筛选**: 支持按时间范围筛选历史记录
3. **变更原因必填**: 对于重要状态变更（如健康度变为H4），要求填写变更原因
4. **变更通知**: 状态变更时发送通知给相关人员
5. **变更统计**: 提供状态变更统计API（如某个项目状态变更次数、平均变更间隔等）
6. **变更回滚**: 支持查看历史记录并恢复到某个历史状态（需谨慎实现）

## 9. 相关文件

- `app/models/project.py` - ProjectStatusLog 模型定义
- `app/api/v1/endpoints/projects.py` - API 端点实现
- `app/schemas/project.py` - ProjectStatusLogResponse Schema 定义
- `app/models/__init__.py` - 模型导出

## 10. 数据库表

**表名**: `project_status_logs`

**索引**:
- `idx_project_status_logs_project`: project_id
- `idx_project_status_logs_machine`: machine_id
- `idx_project_status_logs_time`: changed_at

**外键**:
- `project_id` -> `projects.id`
- `machine_id` -> `machines.id`
- `changed_by` -> `users.id`



