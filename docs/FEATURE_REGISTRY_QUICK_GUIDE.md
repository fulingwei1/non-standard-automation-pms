# 功能注册系统快速指南

> 快速参考：如何维护系统功能清单

## 🎯 核心概念

### 什么是"注册"？

**"注册"** = 在 `app/api/v1/api.py` 中添加路由

```python
# 这就是"注册"
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
```

**注册位置**：`app/api/v1/api.py`（第71-138行）

**当前已注册**：60+ 个功能模块

---

## 📝 新增功能的标准流程

### 1️⃣ 创建API端点文件

```python
# app/api/v1/endpoints/new_feature.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/items")
async def list_items():
    pass
```

### 2️⃣ 注册到 api.py

在 `app/api/v1/api.py` 中添加：

```python
from app.api.v1.endpoints import new_feature

api_router.include_router(
    new_feature.router, 
    prefix="/new-feature", 
    tags=["new-feature"]
)
```

### 3️⃣ 创建权限迁移脚本

```sql
-- migrations/202601XX_new_feature_permissions_sqlite.sql
BEGIN;
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('new_feature:item:read', '新功能查看', 'new_feature', 'item', 'read'),
('new_feature:item:create', '新功能创建', 'new_feature', 'item', 'create');
COMMIT;
```

### 4️⃣ 在API中添加权限检查

```python
from app.core import security

@router.get("/items")
async def list_items(
    current_user: User = Depends(security.require_permission("new_feature:item:read"))
):
    pass
```

### 5️⃣ 扫描并更新功能表

```bash
# 自动扫描所有功能并更新功能表
python scripts/scan_system_features.py
```

### 6️⃣ 生成功能报告

```bash
# 生成功能状态报告
python scripts/generate_feature_report.py
```

查看报告：`docs/SYSTEM_FEATURES_REPORT.md`

---

## 🔍 查看系统功能状态

### 方法1：查看功能报告（推荐）

```bash
python scripts/generate_feature_report.py
cat docs/SYSTEM_FEATURES_REPORT.md
```

**报告内容包括**：
- ✅ 所有功能清单（按模块分组）
- ✅ 每个功能的API端点数量
- ✅ 每个功能的权限配置情况
- ✅ 每个功能的前端集成情况
- ✅ 功能启用状态
- ⚠️ 缺失项提醒（无权限、无前端）

### 方法2：查看API注册中心

```bash
cat app/api/v1/api.py
```

可以看到所有已注册的API模块。

### 方法3：查询数据库

```sql
-- 查看所有功能
SELECT * FROM system_features ORDER BY module, feature_code;

-- 查看有API但无权限的功能
SELECT * FROM system_features 
WHERE api_endpoint_count > 0 AND has_permission = 0;

-- 查看有API但无前端的功能
SELECT * FROM system_features 
WHERE api_endpoint_count > 0 AND has_frontend = 0;
```

---

## 📊 功能状态说明

### 功能完整度

| 状态 | API | 权限 | 前端 | 说明 |
|------|-----|------|------|------|
| ✅ **完整** | ✅ | ✅ | ✅ | 功能完整，可正常使用 |
| ⚠️ **部分** | ✅ | ❌ | ✅ | 有API和前端，但缺少权限 |
| ⚠️ **部分** | ✅ | ✅ | ❌ | 有API和权限，但缺少前端 |
| ❌ **未启用** | - | - | - | 功能已禁用 |

---

## 🛠️ 常用命令

### 扫描系统功能

```bash
# 扫描所有功能并更新功能表
python scripts/scan_system_features.py
```

**功能**：
- 扫描 `app/api/v1/api.py` 获取已注册模块
- 统计每个模块的API端点数量
- 统计每个模块的权限数量
- 统计每个模块的前端页面数量
- 更新 `system_features` 表

### 生成功能报告

```bash
# 生成功能状态报告
python scripts/generate_feature_report.py
```

**输出**：
- `docs/SYSTEM_FEATURES_REPORT.md` - 完整的功能状态报告

---

## 📋 维护清单

### 新增功能时

- [ ] 创建API端点文件
- [ ] 在 `api.py` 中注册路由
- [ ] 创建权限迁移脚本
- [ ] 在API中添加权限检查
- [ ] 运行 `scan_system_features.py` 更新功能表
- [ ] 创建前端页面（如需要）
- [ ] 运行 `generate_feature_report.py` 生成报告

### 定期维护（每周）

- [ ] 运行 `scan_system_features.py` 更新功能表
- [ ] 运行 `generate_feature_report.py` 生成报告
- [ ] 检查缺失权限的功能
- [ ] 检查缺失前端的功能
- [ ] 更新功能启用状态

---

## ❓ 常见问题

### Q1: 如何知道系统有哪些功能？

**A**: 运行 `python scripts/generate_feature_report.py`，查看 `docs/SYSTEM_FEATURES_REPORT.md`

### Q2: 如何知道哪些功能有前端？

**A**: 查看功能报告，`has_frontend = 1` 的功能有前端页面

### Q3: 如何知道哪些功能启用了？

**A**: 查看功能报告，`is_enabled = 1` 的功能已启用

### Q4: 新增功能后如何更新功能表？

**A**: 运行 `python scripts/scan_system_features.py`，会自动扫描并更新

### Q5: "注册"是什么意思？

**A**: "注册"指的是在 `app/api/v1/api.py` 中使用 `api_router.include_router()` 添加路由

---

## 📚 相关文档

- `docs/FEATURE_REGISTRY_SYSTEM.md` - 完整的功能注册系统文档
- `docs/SYSTEM_FEATURES_REPORT.md` - 功能状态报告（自动生成）
- `app/api/v1/api.py` - API路由注册中心
- `scripts/scan_system_features.py` - 功能扫描工具
- `scripts/generate_feature_report.py` - 报告生成工具
