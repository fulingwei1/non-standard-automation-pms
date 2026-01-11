# projects.py 文件拆分方案

> **文件大小**: 6,818行  
> **模块数**: 31个功能模块

## 拆分策略

按业务功能将 `projects.py` 拆分为多个独立模块，每个模块负责一个业务领域。

## 拆分方案

### 1. 核心业务模块

| 新文件 | 包含模块 | 预计行数 | 优先级 |
|--------|---------|---------|--------|
| `projects_crud.py` | 基础CRUD操作 | ~1,200行 | P0 |
| `projects_payment_plans.py` | 项目收款计划 | ~250行 | P0 |
| `projects_templates.py` | 项目模板管理、版本管理、推荐功能、使用统计 | ~700行 | P1 |
| `projects_stages.py` | 阶段推进（含阶段门校验）、阶段自动流转 | ~850行 | P0 |
| `projects_relations.py` | 项目关联分析 | ~150行 | P1 |
| `projects_risk.py` | 项目风险矩阵 | ~100行 | P1 |
| `projects_change.py` | 项目变更影响分析 | ~50行 | P1 |
| `projects_dashboard.py` | 项目概览数据、在产项目进度汇总、项目时间线、项目仪表盘 | ~400行 | P0 |
| `projects_batch.py` | 项目批量操作 | ~350行 | P1 |
| `projects_cost.py` | 项目成本管理 | ~220行 | P1 |
| `projects_review.py` | 项目复盘模块（新模型） | ~380行 | P1 |
| `projects_lessons.py` | 经验教训管理、经验教训高级管理 | ~450行 | P1 |
| `projects_best_practices.py` | 最佳实践管理、最佳实践高级管理、最佳实践库 | ~450行 | P1 |
| `projects_clone.py` | 项目复制/克隆 | ~150行 | P1 |
| `projects_archive.py` | 项目归档管理 | ~110行 | P1 |
| `projects_resource.py` | 项目资源分配优化 | ~150行 | P1 |
| `projects_erp.py` | ERP集成、数据同步 | ~200行 | P2 |
| `projects_cache.py` | 缓存监控和管理 | ~100行 | P2 |
| `projects_utils.py` | 公共工具函数 | ~200行 | P0 |

### 2. 拆分步骤

#### 第一步：提取公共工具（projects_utils.py）
- 公共辅助函数
- 数据同步函数

#### 第二步：拆分核心业务模块（P0优先级）
1. `projects_crud.py` - 基础CRUD（列表、详情、创建、更新、删除）
2. `projects_stages.py` - 阶段推进
3. `projects_dashboard.py` - 仪表盘和时间线
4. `projects_payment_plans.py` - 收款计划

#### 第三步：拆分扩展模块（P1优先级）
5. `projects_templates.py` - 模板管理
6. `projects_batch.py` - 批量操作
7. `projects_cost.py` - 成本管理
8. `projects_review.py` - 项目复盘
9. `projects_lessons.py` - 经验教训
10. `projects_best_practices.py` - 最佳实践
11. `projects_relations.py` - 关联分析
12. `projects_risk.py` - 风险矩阵
13. `projects_change.py` - 变更影响

#### 第四步：拆分其他模块（P2优先级）
14. `projects_erp.py` - ERP集成
15. `projects_cache.py` - 缓存管理

## 文件结构

```
app/api/v1/endpoints/projects/
├── __init__.py              # 路由聚合（~50行）
├── utils.py                 # 公共工具函数（~200行）
├── crud.py                  # 基础CRUD（~1,200行）
├── payment_plans.py         # 收款计划（~250行）
├── templates.py             # 模板管理（~700行）
├── stages.py                # 阶段推进（~850行）
├── relations.py             # 关联分析（~150行）
├── risk.py                  # 风险矩阵（~100行）
├── change.py                # 变更影响（~50行）
├── dashboard.py             # 仪表盘和时间线（~400行）
├── batch.py                 # 批量操作（~350行）
├── cost.py                  # 成本管理（~220行）
├── review.py                # 项目复盘（~380行）
├── lessons.py               # 经验教训（~450行）
├── best_practices.py        # 最佳实践（~450行）
├── clone.py                 # 项目复制（~150行）
├── archive.py               # 项目归档（~110行）
├── resource.py              # 资源分配（~150行）
├── erp.py                   # ERP集成（~200行）
└── cache.py                 # 缓存管理（~100行）
```

## 路由聚合方式

在 `projects/__init__.py` 中：

```python
from fastapi import APIRouter
from . import crud, payment_plans, templates, stages
from . import relations, risk, change, dashboard
from . import batch, cost, review, lessons, best_practices
from . import clone, archive, resource, erp, cache

router = APIRouter()

# 聚合所有子路由
router.include_router(crud.router, tags=["projects-crud"])
router.include_router(stages.router, tags=["projects-stages"])
router.include_router(dashboard.router, tags=["projects-dashboard"])
# ... 其他路由
```

## 注意事项

1. **共享导入**: 公共导入放在 `utils.py` 或 `__init__.py`
2. **共享函数**: 公共工具函数放在 `utils.py`
3. **路由前缀**: 保持原有路由路径不变（通过 `api.py` 中的 `prefix="/projects"`）
4. **向后兼容**: 确保API路径不变
