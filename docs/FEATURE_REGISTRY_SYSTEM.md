# 功能注册与维护系统

> 创建日期：2026-01-XX  
> 目的：统一管理系统中所有功能，包括API、权限、前端集成状态

## 📋 系统概述

### 什么是"注册"？

**"注册"**指的是将功能模块的路由注册到 `app/api/v1/api.py` 文件中。

**注册位置**：`app/api/v1/api.py`

**注册方式**：
```python
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
```

**当前已注册的模块**：60+ 个（见 `app/api/v1/api.py`）

---

## 🎯 功能注册表设计

### 数据库表结构

创建 `system_features` 表来维护所有功能：

```sql
CREATE TABLE system_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_code VARCHAR(100) UNIQUE NOT NULL,  -- 功能编码，如 'project', 'material'
    feature_name VARCHAR(200) NOT NULL,          -- 功能名称，如 '项目管理'
    module VARCHAR(50),                          -- 所属模块，如 'project'
    description TEXT,                            -- 功能描述
    api_file VARCHAR(200),                       -- API文件路径，如 'app/api/v1/endpoints/projects.py'
    api_prefix VARCHAR(100),                     -- API前缀，如 '/projects'
    api_endpoint_count INTEGER DEFAULT 0,        -- API端点数量
    has_permission BOOLEAN DEFAULT 0,            -- 是否配置权限
    permission_count INTEGER DEFAULT 0,          -- 权限数量
    has_frontend BOOLEAN DEFAULT 0,              -- 是否有前端页面
    frontend_page_count INTEGER DEFAULT 0,       -- 前端页面数量
    is_enabled BOOLEAN DEFAULT 1,               -- 是否启用
    priority VARCHAR(20) DEFAULT 'medium',       -- 优先级：high/medium/low
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_feature_code ON system_features(feature_code);
CREATE INDEX idx_module ON system_features(module);
CREATE INDEX idx_is_enabled ON system_features(is_enabled);
```

---

## 🔧 自动化工具

### 1. 功能扫描工具

**文件**：`scripts/scan_system_features.py`

**功能**：
- 扫描 `app/api/v1/api.py` 获取所有已注册的模块
- 扫描 `app/api/v1/endpoints/*.py` 统计API端点数量
- 扫描 `migrations/*_permissions*.sql` 统计权限数量
- 扫描 `frontend/src/pages/*.jsx` 统计前端页面数量
- 生成功能注册表数据

### 2. 功能注册工具

**文件**：`scripts/register_feature.py`

**功能**：
- 新增功能时，自动注册到功能表
- 更新功能状态（启用/禁用）
- 更新权限配置
- 更新前端集成状态

### 3. 功能状态报告工具

**文件**：`scripts/generate_feature_report.py`

**功能**：
- 生成功能清单报告
- 显示哪些功能有API
- 显示哪些功能有权限
- 显示哪些功能有前端
- 显示哪些功能已启用

---

## 📝 工作流程

### 新增功能时的标准流程

#### 步骤1：创建API端点文件

```python
# app/api/v1/endpoints/new_feature.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/items")
async def list_items():
    """列表接口"""
    pass

@router.post("/items")
async def create_item():
    """创建接口"""
    pass
```

#### 步骤2：注册API路由

在 `app/api/v1/api.py` 中添加：

```python
from app.api.v1.endpoints import new_feature

api_router.include_router(
    new_feature.router, 
    prefix="/new-feature", 
    tags=["new-feature"]
)
```

#### 步骤3：创建权限迁移脚本

创建 `migrations/YYYYMMDD_new_feature_permissions_sqlite.sql`：

```sql
BEGIN;

-- 插入权限
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('new_feature:item:read', '新功能查看', 'new_feature', 'item', 'read'),
('new_feature:item:create', '新功能创建', 'new_feature', 'item', 'create'),
('new_feature:item:update', '新功能更新', 'new_feature', 'item', 'update'),
('new_feature:item:delete', '新功能删除', 'new_feature', 'item', 'delete');

COMMIT;
```

#### 步骤4：在API端点中添加权限检查

```python
from app.core import security

@router.get("/items")
async def list_items(
    current_user: User = Depends(security.require_permission("new_feature:item:read"))
):
    """列表接口"""
    pass
```

#### 步骤5：注册功能到功能表

运行注册工具：

```bash
python scripts/register_feature.py \
    --code new_feature \
    --name "新功能" \
    --module new_feature \
    --api-file app/api/v1/endpoints/new_feature.py \
    --api-prefix /new-feature \
    --priority high
```

或者手动插入：

```sql
INSERT INTO system_features (
    feature_code, feature_name, module, 
    api_file, api_prefix, 
    has_permission, is_enabled, priority
) VALUES (
    'new_feature', '新功能', 'new_feature',
    'app/api/v1/endpoints/new_feature.py', '/new-feature',
    1, 1, 'high'
);
```

#### 步骤6：创建前端页面（可选）

如果功能需要前端页面：

1. 创建前端页面：`frontend/src/pages/NewFeature.jsx`
2. 添加API调用：在 `frontend/src/services/api.js` 中添加API定义
3. 更新功能表：

```sql
UPDATE system_features 
SET has_frontend = 1, 
    frontend_page_count = 1
WHERE feature_code = 'new_feature';
```

#### 步骤7：更新功能状态报告

运行报告生成工具：

```bash
python scripts/generate_feature_report.py
```

查看报告：`docs/SYSTEM_FEATURES_REPORT.md`

---

## 📊 功能状态查看

### 方法1：查看功能注册表

```sql
-- 查看所有功能
SELECT 
    feature_code,
    feature_name,
    api_endpoint_count,
    has_permission,
    permission_count,
    has_frontend,
    frontend_page_count,
    is_enabled
FROM system_features
ORDER BY module, feature_code;

-- 查看有API但无权限的功能
SELECT * FROM system_features 
WHERE api_endpoint_count > 0 AND has_permission = 0;

-- 查看有API但无前端的功能
SELECT * FROM system_features 
WHERE api_endpoint_count > 0 AND has_frontend = 0;

-- 查看已禁用的功能
SELECT * FROM system_features WHERE is_enabled = 0;
```

### 方法2：查看自动生成的报告

运行脚本生成报告：

```bash
python scripts/generate_feature_report.py
```

报告位置：`docs/SYSTEM_FEATURES_REPORT.md`

报告内容包括：
- 功能清单（按模块分组）
- API端点统计
- 权限配置统计
- 前端集成统计
- 启用状态统计
- 缺失项提醒

### 方法3：查看API注册中心

直接查看 `app/api/v1/api.py` 文件，可以看到所有已注册的API模块。

---

## 🔍 功能状态说明

### 功能状态字段

| 字段 | 说明 | 可能值 |
|------|------|--------|
| `api_endpoint_count` | API端点数量 | 0, 1, 2, ... |
| `has_permission` | 是否配置权限 | 0 (否), 1 (是) |
| `permission_count` | 权限数量 | 0, 1, 2, ... |
| `has_frontend` | 是否有前端页面 | 0 (否), 1 (是) |
| `frontend_page_count` | 前端页面数量 | 0, 1, 2, ... |
| `is_enabled` | 是否启用 | 0 (禁用), 1 (启用) |

### 功能完整度判断

**完整功能**（所有项都有）：
- ✅ `api_endpoint_count > 0`
- ✅ `has_permission = 1`
- ✅ `has_frontend = 1`
- ✅ `is_enabled = 1`

**部分功能**（缺少某些项）：
- ⚠️ 有API但无权限
- ⚠️ 有API但无前端
- ⚠️ 有前端但无API（前端使用Mock数据）

**未启用功能**：
- ❌ `is_enabled = 0`

---

## 🛠️ 工具使用指南

### 扫描系统功能

```bash
# 扫描所有功能并更新功能表
python scripts/scan_system_features.py

# 输出：
# - 扫描结果
# - 更新功能表
# - 生成差异报告
```

### 注册新功能

```bash
# 注册新功能
python scripts/register_feature.py \
    --code new_feature \
    --name "新功能" \
    --module new_feature \
    --api-file app/api/v1/endpoints/new_feature.py \
    --api-prefix /new-feature \
    --priority high

# 输出：
# - 功能已注册到功能表
# - 功能编码：new_feature
```

### 生成功能报告

```bash
# 生成完整的功能状态报告
python scripts/generate_feature_report.py

# 输出文件：
# - docs/SYSTEM_FEATURES_REPORT.md
```

---

## 📋 维护清单

### 新增功能时

- [ ] 创建API端点文件
- [ ] 在 `api.py` 中注册路由
- [ ] 创建权限迁移脚本
- [ ] 在API端点中添加权限检查
- [ ] 运行 `register_feature.py` 注册功能
- [ ] 创建前端页面（如需要）
- [ ] 更新功能表的前端状态
- [ ] 运行 `generate_feature_report.py` 生成报告

### 定期维护

- [ ] 每周运行 `scan_system_features.py` 更新功能表
- [ ] 每月运行 `generate_feature_report.py` 生成报告
- [ ] 检查缺失权限的功能
- [ ] 检查缺失前端的功能
- [ ] 更新功能启用状态

---

## 📚 相关文档

- `docs/API_PERMISSIONS_AUDIT_REPORT.md` - API权限审计报告
- `docs/FRONTEND_API_INTEGRATION_STATUS_SUMMARY.md` - 前端API集成状态
- `app/api/v1/api.py` - API路由注册中心
- `migrations/*_permissions*.sql` - 权限迁移脚本
