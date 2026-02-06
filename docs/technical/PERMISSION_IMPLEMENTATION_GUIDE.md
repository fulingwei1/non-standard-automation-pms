# 权限检查批量添加指南

> 更新日期：2026-01-20  
> 说明：为29个缺失权限的功能模块批量添加权限检查的完整指南

## 📋 概述

本指南说明如何为缺失权限的29个功能模块批量添加权限检查。已完成：
- ✅ 权限定义SQL迁移脚本（SQLite和MySQL版本）
- ✅ customers模块权限检查示例
- ⏳ 其他28个模块待添加

## 🎯 权限检查添加模式

### 标准模式

根据API端点的HTTP方法，使用对应的权限：

```python
# GET 请求 → read 权限
@router.get("/items")
async def list_items(
    current_user: User = Depends(security.require_permission("module:read"))
):
    ...

# POST 请求 → create 权限
@router.post("/items")
async def create_item(
    current_user: User = Depends(security.require_permission("module:create"))
):
    ...

# PUT/PATCH 请求 → update 权限
@router.put("/items/{id}")
async def update_item(
    current_user: User = Depends(security.require_permission("module:update"))
):
    ...

# DELETE 请求 → delete 权限
@router.delete("/items/{id}")
async def delete_item(
    current_user: User = Depends(security.require_permission("module:delete"))
):
    ...
```

### 特殊操作权限

对于特殊操作（审批、分配、处理等），使用对应的action权限：

```python
# 审批操作
@router.put("/items/{id}/approve")
async def approve_item(
    current_user: User = Depends(security.require_permission("module:approve"))
):
    ...

# 分配操作
@router.put("/items/{id}/assign")
async def assign_item(
    current_user: User = Depends(security.require_permission("module:assign"))
):
    ...

# 处理/解决操作
@router.put("/items/{id}/resolve")
async def resolve_item(
    current_user: User = Depends(security.require_permission("module:resolve"))
):
    ...
```

## 📝 模块权限映射表

| 模块 | 权限前缀 | 文件路径 | 端点数量 | 状态 |
|------|---------|---------|---------|------|
| advantage-products | `advantage_product:` | `advantage_products.py` | 11 | ⏳ 待添加 |
| assembly-kit | `assembly_kit:` | `assembly_kit.py` | 32 | ⏳ 待添加 |
| budgets | `budget:` | `budget.py` | 17 | ⏳ 待添加 |
| business-support | `business_support:` | `business_support.py` | 16 | ⏳ 待添加 |
| costs | `cost:` | `costs.py` | 21 | ⏳ 待添加 |
| customers | `customer:` | `customers.py` | 7 | ✅ 已完成 |
| data-import-export | `data_import:` / `data_export:` | `data_import_export.py` | 10 | ⏳ 待添加 |
| documents | `document:` | `documents.py` | 9 | ⏳ 待添加 |
| engineers | `engineer:` | `engineers.py` | 15 | ⏳ 待添加 |
| hourly-rates | `hourly_rate:` | `hourly_rate.py` | 8 | ⏳ 待添加 |
| hr-management | `hr:` | `hr_management.py` | 14 | ⏳ 待添加 |
| installation-dispatch | `installation_dispatch:` | `installation_dispatch.py` | 11 | ⏳ 待添加 |
| issues | `issue:` | `issues.py` | 29 | ⏳ 待添加 |
| projects-machines | `machine:` | `projects/machines/` | 14 | ⏳ 待添加 |
| materials | `material:` | `materials.py` | 10 | ⏳ 待添加 |
| milestones | `milestone:` | `milestones.py` | 7 | ⏳ 待添加 |
| notifications | `notification:` | `notifications.py` | 8 | ⏳ 待添加 |
| presales-integration | `presales_integration:` | `presales_integration.py` | 7 | ⏳ 待添加 |
| projects-evaluations | `project_evaluation:` | `projects/evaluations/` | 15 | ⏳ 待添加 |
| projects-roles | `project_role:` | `projects/roles/` | 16 | ⏳ 待添加 |
| qualifications | `qualification:` | `qualification.py` | 16 | ⏳ 待添加 |
| reports | `report:` | `report_center.py` | 22 | ⏳ 待添加 |
| shortage-alerts | `shortage_alert:` | `shortage_alerts.py` | 35 | ⏳ 待添加 |
| staff-matching | `staff_matching:` | `staff_matching.py` | 27 | ⏳ 待添加 |
| stages | `stage:` | `stages.py` | 10 | ⏳ 待添加 |
| suppliers | `supplier:` | `suppliers.py` | 6 | ⏳ 待添加 |
| task-center | `task_center:` | `task_center.py` | 21 | ⏳ 待添加 |
| technical-spec | `technical_spec:` | `technical_spec.py` | 8 | ⏳ 待添加 |
| timesheets | `timesheet:` | `timesheet.py` | 22 | ⏳ 待添加 |

## 🔧 批量添加步骤

### 步骤1：查找需要修改的端点

使用以下命令查找所有需要添加权限的端点：

```bash
# 查找所有使用 get_current_active_user 的端点（需要替换为权限检查）
grep -r "get_current_active_user" app/api/v1/endpoints/customers.py

# 查找所有路由装饰器
grep -r "@router\.\(get\|post\|put\|delete\|patch\)" app/api/v1/endpoints/customers.py
```

### 步骤2：替换权限检查

将 `Depends(security.get_current_active_user)` 替换为对应的权限检查：

```python
# 替换前
current_user: User = Depends(security.get_current_active_user)

# 替换后（根据操作类型选择）
current_user: User = Depends(security.require_permission("module:read"))
current_user: User = Depends(security.require_permission("module:create"))
current_user: User = Depends(security.require_permission("module:update"))
current_user: User = Depends(security.require_permission("module:delete"))
```

### 步骤3：处理无用户参数的端点

对于没有 `current_user` 参数的端点，需要添加：

```python
# 替换前
@router.get("/{id}")
def get_item(
    *,
    db: Session = Depends(deps.get_db),
    item_id: int,
) -> Any:
    ...

# 替换后
@router.get("/{id}")
def get_item(
    *,
    db: Session = Depends(deps.get_db),
    item_id: int,
    current_user: User = Depends(security.require_permission("module:read")),
) -> Any:
    ...
```

## 📚 示例：customers模块（已完成）

参考 `app/api/v1/endpoints/customers.py` 的实现：

1. **列表查询** → `customer:read`
2. **详情查询** → `customer:read`
3. **创建** → `customer:create`
4. **更新** → `customer:update`
5. **删除** → `customer:delete`
6. **关联查询** → `customer:read`

## ⚠️ 注意事项

### 1. 个人数据API

对于用户查看自己数据的API（如 `/my/timesheets`），可以保持使用 `get_current_active_user`，因为已经在函数内部做了数据范围限制。

### 2. 公开API

以下API不需要权限检查：
- `/auth/login` - 登录接口
- `/auth/logout` - 登出接口
- `/health` - 健康检查

### 3. 权限编码一致性

确保使用的权限编码与迁移脚本中定义的完全一致：
- ✅ `customer:read`
- ❌ `customers:read` (错误：复数形式)
- ❌ `customer:view` (错误：action不一致)

## 🚀 快速批量替换脚本

可以使用以下Python脚本辅助批量替换：

```python
#!/usr/bin/env python3
# 批量替换权限检查的辅助脚本

import re
from pathlib import Path

def add_permission_check(file_path: Path, module_prefix: str):
    """为文件添加权限检查"""
    content = file_path.read_text(encoding='utf-8')
    
    # 替换模式
    patterns = [
        # GET 请求
        (r'@router\.get\([^)]+\)\s+def\s+(\w+)\([^)]*current_user:\s*User\s*=\s*Depends\(security\.get_current_active_user\)', 
         lambda m: m.group(0).replace('get_current_active_user', f'require_permission("{module_prefix}:read")')),
        
        # POST 请求
        (r'@router\.post\([^)]+\)\s+def\s+(\w+)\([^)]*current_user:\s*User\s*=\s*Depends\(security\.get_current_active_user\)',
         lambda m: m.group(0).replace('get_current_active_user', f'require_permission("{module_prefix}:create")')),
        
        # PUT/PATCH 请求
        (r'@router\.(put|patch)\([^)]+\)\s+def\s+(\w+)\([^)]*current_user:\s*User\s*=\s*Depends\(security\.get_current_active_user\)',
         lambda m: m.group(0).replace('get_current_active_user', f'require_permission("{module_prefix}:update")')),
        
        # DELETE 请求
        (r'@router\.delete\([^)]+\)\s+def\s+(\w+)\([^)]*current_user:\s*User\s*=\s*Depends\(security\.get_current_active_user\)',
         lambda m: m.group(0).replace('get_current_active_user', f'require_permission("{module_prefix}:delete")')),
    ]
    
    # 执行替换
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    file_path.write_text(content, encoding='utf-8')
    print(f"✅ 已更新: {file_path}")

# 使用示例
# add_permission_check(Path("app/api/v1/endpoints/issues.py"), "issue")
```

## 📊 进度跟踪

- ✅ customers (7个端点) - 已完成
- ⏳ 其他28个模块 - 待处理

## 🔗 相关文档

- `migrations/20260120_comprehensive_permissions_sqlite.sql` - 权限定义（SQLite）
- `migrations/20260120_comprehensive_permissions_mysql.sql` - 权限定义（MySQL）
- `docs/PERMISSION_ALLOCATION_PLAN.md` - 权限分配方案
- `app/api/v1/endpoints/customers.py` - 参考实现
