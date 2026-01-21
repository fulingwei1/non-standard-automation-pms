# 项目管理模块整合实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 13 个分散的项目相关 API 模块整合为 4 个聚合模块，支持矩阵式管理

**Architecture:** 采用按项目聚合 + 跨项目顶级路由的混合模式。项目内操作统一在 `/projects/{id}/*` 下，跨项目查询保留 `/my/*`、`/departments/*`、`/analytics/*` 顶级路由。

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest

---

## Phase 1: 基础设施准备

### Task 1.1: 创建新目录结构

**Files:**
- Create: `app/api/v1/endpoints/my/__init__.py`
- Create: `app/api/v1/endpoints/departments/__init__.py`
- Create: `app/api/v1/endpoints/analytics/__init__.py`
- Create: `app/services/project/__init__.py`

**Step 1: 创建 /my/ 模块骨架**

```python
# app/api/v1/endpoints/my/__init__.py
# -*- coding: utf-8 -*-
"""
个人维度 API 模块

提供当前用户视角的数据访问：
- /my/projects - 我参与的项目
- /my/timesheet - 我的工时记录
- /my/workload - 我的工作量
- /my/tasks - 我的任务
- /my/work-logs - 我的工作日志
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/projects")
async def get_my_projects():
    """我参与的项目列表 - 待实现"""
    return {"message": "Coming soon"}


@router.get("/workload")
async def get_my_workload():
    """我的工作量 - 待实现"""
    return {"message": "Coming soon"}
```

**Step 2: 创建 /departments/ 模块骨架**

```python
# app/api/v1/endpoints/departments/__init__.py
# -*- coding: utf-8 -*-
"""
部门维度 API 模块

提供部门管理者视角的数据访问：
- /departments/{dept_id}/workload - 部门工作量汇总
- /departments/{dept_id}/projects - 部门相关项目
- /departments/{dept_id}/timesheet - 部门工时统计
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/{dept_id}/workload")
async def get_department_workload(dept_id: int):
    """部门工作量汇总 - 待实现"""
    return {"message": "Coming soon", "dept_id": dept_id}


@router.get("/{dept_id}/projects")
async def get_department_projects(dept_id: int):
    """部门相关项目 - 待实现"""
    return {"message": "Coming soon", "dept_id": dept_id}
```

**Step 3: 创建 /analytics/ 模块骨架**

```python
# app/api/v1/endpoints/analytics/__init__.py
# -*- coding: utf-8 -*-
"""
组织/PMO 维度 API 模块

提供全局分析视角的数据访问：
- /analytics/projects/health - 项目健康度汇总
- /analytics/projects/progress - 跨项目进度对比
- /analytics/workload/overview - 全局工作量概览
- /analytics/costs/summary - 成本汇总
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/projects/health")
async def get_projects_health():
    """项目健康度汇总 - 待实现"""
    return {"message": "Coming soon"}


@router.get("/workload/overview")
async def get_workload_overview():
    """全局工作量概览 - 待实现"""
    return {"message": "Coming soon"}
```

**Step 4: 创建新服务目录**

```python
# app/services/project/__init__.py
# -*- coding: utf-8 -*-
"""
项目管理聚合服务

整合原有分散的服务为 5 个核心服务：
- core_service: 项目核心 CRUD + 状态管理
- execution_service: 阶段 + 进度 + 里程碑
- resource_service: 成员 + 工时 + 工作量
- finance_service: 成本 + 预算 + 付款
- analytics_service: 仪表盘 + 统计 + 报表
"""

# 服务将在后续任务中逐步实现
```

**Step 5: 运行验证**

Run: `python -c "from app.api.v1.endpoints import my, departments, analytics; print('Import OK')"`
Expected: `Import OK`

**Step 6: 提交**

```bash
git add app/api/v1/endpoints/my/ app/api/v1/endpoints/departments/ app/api/v1/endpoints/analytics/ app/services/project/
git commit -m "feat: 创建项目模块整合基础目录结构"
```

---

### Task 1.2: 注册新路由到主路由器

**Files:**
- Modify: `app/api/v1/api.py`

**Step 1: 添加新路由导入和注册**

在 `app/api/v1/api.py` 文件末尾（最后一个 `include_router` 之后）添加：

```python
# === 项目模块整合：新增跨项目维度路由 ===
from app.api.v1.endpoints import my, departments, analytics

api_router.include_router(my.router, prefix="/my", tags=["my"])
api_router.include_router(departments.router, prefix="/departments", tags=["departments"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
```

**Step 2: 验证路由注册**

Run: `python -c "from app.api.v1.api import api_router; routes = [r.path for r in api_router.routes]; print('/my/projects' in str(routes) and '/departments/{dept_id}/workload' in str(routes))"`
Expected: `True`

**Step 3: 启动服务验证**

Run: `timeout 5 uvicorn app.main:app --host 127.0.0.1 --port 8001 2>&1 | head -20 || true`
Expected: 应包含 "Uvicorn running" 且无错误

**Step 4: 提交**

```bash
git add app/api/v1/api.py
git commit -m "feat: 注册 /my, /departments, /analytics 路由"
```

---

## Phase 2: 迁移简单模块（概念验证）

### Task 2.1: 迁移里程碑模块到项目下

**Files:**
- Create: `app/api/v1/endpoints/projects/milestones/__init__.py`
- Create: `app/api/v1/endpoints/projects/milestones/crud.py`
- Create: `app/api/v1/endpoints/projects/milestones/workflow.py`
- Modify: `app/api/v1/endpoints/projects/__init__.py`
- Modify: `app/api/v1/endpoints/milestones/crud.py` (添加废弃警告)

**Step 1: 创建项目下的里程碑目录**

```python
# app/api/v1/endpoints/projects/milestones/__init__.py
# -*- coding: utf-8 -*-
"""
项目里程碑管理模块

路由: /projects/{project_id}/milestones/
- GET / - 获取项目里程碑列表
- POST / - 创建里程碑
- GET /{milestone_id} - 获取里程碑详情
- PUT /{milestone_id} - 更新里程碑
- POST /{milestone_id}/complete - 完成里程碑
- DELETE /{milestone_id} - 删除里程碑
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .workflow import router as workflow_router

router = APIRouter()

router.include_router(crud_router, tags=["项目里程碑"])
router.include_router(workflow_router, tags=["里程碑工作流"])
```

**Step 2: 创建 CRUD 路由（从旧模块适配）**

```python
# app/api/v1/endpoints/projects/milestones/crud.py
# -*- coding: utf-8 -*-
"""
项目里程碑 CRUD 操作

适配自 app/api/v1/endpoints/milestones/crud.py
变更: 路由从 /milestones/ 改为 /projects/{project_id}/milestones/
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project, ProjectMilestone
from app.models.user import User
from app.schemas.project import MilestoneCreate, MilestoneResponse, MilestoneUpdate
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


@router.get("/", response_model=List[MilestoneResponse])
def read_project_milestones(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None, description="里程碑状态筛选"),
    current_user: User = Depends(security.require_permission("milestone:read")),
) -> Any:
    """获取项目的里程碑列表"""
    # 检查项目访问权限
    check_project_access_or_raise(db, current_user, project_id)

    query = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id
    )

    if status:
        query = query.filter(ProjectMilestone.status == status)

    milestones = (
        query.order_by(desc(ProjectMilestone.planned_date))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return milestones


@router.post("/", response_model=MilestoneResponse)
def create_project_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_in: MilestoneCreate = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:create")),
) -> Any:
    """为项目创建里程碑"""
    check_project_access_or_raise(db, current_user, project_id)

    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    milestone = ProjectMilestone(
        project_id=project_id,
        name=milestone_in.name,
        description=milestone_in.description,
        planned_date=milestone_in.planned_date,
        milestone_type=milestone_in.milestone_type,
        status="pending",
        created_by=current_user.id,
    )
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone


@router.get("/{milestone_id}", response_model=MilestoneResponse)
def read_project_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:read")),
) -> Any:
    """获取项目里程碑详情"""
    check_project_access_or_raise(db, current_user, project_id)

    milestone = db.query(ProjectMilestone).filter(
        ProjectMilestone.id == milestone_id,
        ProjectMilestone.project_id == project_id,
    ).first()

    if not milestone:
        raise HTTPException(status_code=404, detail="里程碑不存在")

    return milestone


@router.put("/{milestone_id}", response_model=MilestoneResponse)
def update_project_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    milestone_in: MilestoneUpdate = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:update")),
) -> Any:
    """更新项目里程碑"""
    check_project_access_or_raise(db, current_user, project_id)

    milestone = db.query(ProjectMilestone).filter(
        ProjectMilestone.id == milestone_id,
        ProjectMilestone.project_id == project_id,
    ).first()

    if not milestone:
        raise HTTPException(status_code=404, detail="里程碑不存在")

    update_data = milestone_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(milestone, field, value)

    db.commit()
    db.refresh(milestone)
    return milestone
```

**Step 3: 创建工作流路由**

```python
# app/api/v1/endpoints/projects/milestones/workflow.py
# -*- coding: utf-8 -*-
"""
项目里程碑工作流操作
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import ProjectMilestone
from app.models.user import User
from app.schemas.project import MilestoneResponse
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


@router.post("/{milestone_id}/complete", response_model=MilestoneResponse)
def complete_project_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:update")),
) -> Any:
    """完成项目里程碑"""
    check_project_access_or_raise(db, current_user, project_id)

    milestone = db.query(ProjectMilestone).filter(
        ProjectMilestone.id == milestone_id,
        ProjectMilestone.project_id == project_id,
    ).first()

    if not milestone:
        raise HTTPException(status_code=404, detail="里程碑不存在")

    if milestone.status == "completed":
        raise HTTPException(status_code=400, detail="里程碑已完成")

    milestone.status = "completed"
    db.commit()
    db.refresh(milestone)
    return milestone


@router.delete("/{milestone_id}")
def delete_project_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:delete")),
) -> Any:
    """删除项目里程碑"""
    check_project_access_or_raise(db, current_user, project_id)

    milestone = db.query(ProjectMilestone).filter(
        ProjectMilestone.id == milestone_id,
        ProjectMilestone.project_id == project_id,
    ).first()

    if not milestone:
        raise HTTPException(status_code=404, detail="里程碑不存在")

    db.delete(milestone)
    db.commit()
    return {"message": "里程碑已删除"}
```

**Step 4: 在 projects/__init__.py 中注册里程碑路由**

在 `app/api/v1/endpoints/projects/__init__.py` 中添加导入和注册：

```python
# 在其他导入之后添加
from .milestones import router as milestones_router

# 在其他 include_router 之后添加
# 里程碑路由（项目内操作）
router.include_router(
    milestones_router,
    prefix="/{project_id}/milestones",
    tags=["projects-milestones"]
)
```

**Step 5: 验证新路由**

Run: `python -c "from app.api.v1.endpoints.projects import router; routes = [r.path for r in router.routes]; print('/{project_id}/milestones/' in str(routes))"`
Expected: `True`

**Step 6: 提交**

```bash
git add app/api/v1/endpoints/projects/milestones/
git add app/api/v1/endpoints/projects/__init__.py
git commit -m "feat: 迁移里程碑模块到 /projects/{id}/milestones/"
```

---

### Task 2.2: 为旧里程碑路由添加废弃警告和代理

**Files:**
- Modify: `app/api/v1/endpoints/milestones/crud.py`
- Modify: `app/api/v1/endpoints/milestones/workflow.py`

**Step 1: 修改旧 CRUD 路由添加废弃标记**

在 `app/api/v1/endpoints/milestones/crud.py` 的每个路由函数添加 `deprecated=True`：

```python
@router.get("/", response_model=List[MilestoneResponse], deprecated=True)
def read_milestones(
    # ... 保持原有参数不变
) -> Any:
    """
    ⚠️ Deprecated: 请使用 GET /projects/{project_id}/milestones/

    Retrieve milestones.
    """
    # ... 保持原有逻辑不变
```

对 `read_milestone`, `create_milestone`, `update_milestone` 同样添加 `deprecated=True`。

**Step 2: 修改旧工作流路由添加废弃标记**

在 `app/api/v1/endpoints/milestones/workflow.py` 的每个路由函数添加 `deprecated=True`。

**Step 3: 验证废弃标记**

Run: `python -c "from app.api.v1.endpoints.milestones.crud import router; print(any(r.deprecated for r in router.routes))"`
Expected: `True`

**Step 4: 提交**

```bash
git add app/api/v1/endpoints/milestones/
git commit -m "deprecate: 标记旧里程碑路由为废弃"
```

---

### Task 2.3: 迁移设备模块到项目下

**Files:**
- Create: `app/api/v1/endpoints/projects/machines/__init__.py`
- Create: `app/api/v1/endpoints/projects/machines/crud.py`
- Modify: `app/api/v1/endpoints/projects/__init__.py`

**Step 1: 创建项目设备模块**

```python
# app/api/v1/endpoints/projects/machines/__init__.py
# -*- coding: utf-8 -*-
"""
项目设备/机台管理模块

路由: /projects/{project_id}/machines/
"""

from fastapi import APIRouter

from .crud import router as crud_router

router = APIRouter()

router.include_router(crud_router, tags=["项目设备"])
```

**Step 2: 创建设备 CRUD（从旧模块适配）**

```python
# app/api/v1/endpoints/projects/machines/crud.py
# -*- coding: utf-8 -*-
"""
项目设备 CRUD 操作
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.project import MachineCreate, MachineResponse, MachineUpdate
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


@router.get("/", response_model=List[MachineResponse])
def read_project_machines(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """获取项目的设备列表"""
    check_project_access_or_raise(db, current_user, project_id)

    machines = db.query(Machine).filter(Machine.project_id == project_id).all()
    return machines


@router.get("/{machine_id}", response_model=MachineResponse)
def read_project_machine(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="设备ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """获取项目设备详情"""
    check_project_access_or_raise(db, current_user, project_id)

    machine = db.query(Machine).filter(
        Machine.id == machine_id,
        Machine.project_id == project_id,
    ).first()

    if not machine:
        raise HTTPException(status_code=404, detail="设备不存在")

    return machine


@router.post("/", response_model=MachineResponse)
def create_project_machine(
    project_id: int = Path(..., description="项目ID"),
    machine_in: MachineCreate = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:create")),
) -> Any:
    """为项目创建设备"""
    check_project_access_or_raise(db, current_user, project_id)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    machine = Machine(
        project_id=project_id,
        **machine_in.model_dump(),
    )
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine


@router.put("/{machine_id}", response_model=MachineResponse)
def update_project_machine(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="设备ID"),
    machine_in: MachineUpdate = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:update")),
) -> Any:
    """更新项目设备"""
    check_project_access_or_raise(db, current_user, project_id)

    machine = db.query(Machine).filter(
        Machine.id == machine_id,
        Machine.project_id == project_id,
    ).first()

    if not machine:
        raise HTTPException(status_code=404, detail="设备不存在")

    update_data = machine_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(machine, field, value)

    db.commit()
    db.refresh(machine)
    return machine
```

**Step 3: 注册设备路由到 projects**

在 `app/api/v1/endpoints/projects/__init__.py` 中添加：

```python
from .machines import router as machines_router

router.include_router(
    machines_router,
    prefix="/{project_id}/machines",
    tags=["projects-machines"]
)
```

**Step 4: 提交**

```bash
git add app/api/v1/endpoints/projects/machines/
git add app/api/v1/endpoints/projects/__init__.py
git commit -m "feat: 迁移设备模块到 /projects/{id}/machines/"
```

---

## Phase 3: 迁移中等复杂度模块

> 注：此阶段包含 members, costs, work_log, project_roles, project_evaluation
>
> 每个模块遵循与 Phase 2 相同的模式：
> 1. 创建 `app/api/v1/endpoints/projects/{module}/` 目录
> 2. 适配路由代码，添加 `project_id` Path 参数
> 3. 注册到 projects router
> 4. 标记旧路由为废弃

### Task 3.1: 迁移成员模块

**预计文件:**
- Create: `app/api/v1/endpoints/projects/members/` (4 files)
- Modify: `app/api/v1/endpoints/projects/__init__.py`
- Modify: `app/api/v1/endpoints/members/` (添加废弃标记)

*详细步骤参考 Task 2.1 模式*

### Task 3.2: 迁移成本模块

**预计文件:**
- Create: `app/api/v1/endpoints/projects/costs/` (适配现有 costs 模块)
- Modify: `app/api/v1/endpoints/projects/__init__.py`

### Task 3.3: 迁移工作日志模块

### Task 3.4: 迁移项目角���模块

### Task 3.5: 迁移项目评价模块

---

## Phase 4: 迁移复杂模块

> 此阶段包含 progress, project_stages, timesheet, workload
>
> 这些模块需要拆分：项目维度操作迁移到 /projects/{id}/，跨项目查询迁移到 /my/、/departments/、/analytics/

### Task 4.1: 迁移进度模块

**拆分策略:**
- `/projects/{id}/progress/` - 项目进度详情
- `/analytics/progress/` - 跨项目进度汇总

### Task 4.2: 迁移阶段模块

### Task 4.3: 迁移工时模块

**拆分策略:**
- `/projects/{id}/timesheet/` - 项目工时
- `/my/timesheet/` - 个人工时
- `/departments/{id}/timesheet/` - 部门工时

### Task 4.4: 迁移工作量模块

**拆分策略:**
- `/projects/{id}/workload/` - 项目工作量
- `/my/workload/` - 个人工作量
- `/departments/{id}/workload/` - 部门工作量
- `/analytics/workload/` - 全局工作量

---

## Phase 5: 服务层整合

### Task 5.1: 创建 ProjectExecutionService

整合原有服务：
- `stage_instance_service.py`
- `stage_advance_service.py`
- `progress_aggregation_service.py`
- `progress_auto_service.py`

### Task 5.2: 创建 ProjectResourceService

整合原有服务：
- `project_contribution_service.py`
- `workload` 相关服务

### Task 5.3: 创建 ProjectFinanceService

整合原有服务：
- 成本相关服务
- `project_bonus_service.py`

### Task 5.4: 创建 ProjectAnalyticsService

整合原有服务：
- `project_dashboard_service.py`
- `project_statistics_service.py`
- `project_timeline_service.py`

---

## Phase 6: 清理

### Task 6.1: 移除旧路由

在确认前端已完全切换后：
- 删除 `app/api/v1/endpoints/milestones/`
- 删除 `app/api/v1/endpoints/machines/`
- 更新 `app/api/v1/api.py` 移除旧路由注册

### Task 6.2: 移除旧服务

### Task 6.3: 更新文档

- 更新 `CLAUDE.md`
- 更新 API 文档

---

## 检查点

| 检查点 | 完成标准 |
|--------|----------|
| Phase 1 完成 | 新路由骨架可访问 |
| Phase 2 完成 | milestones, machines 迁移完成且旧路由标记废弃 |
| Phase 3 完成 | 所有简单模块迁移完成 |
| Phase 4 完成 | 复杂模块拆分迁移完成 |
| Phase 5 完成 | 服务层整合完成 |
| Phase 6 完成 | 旧代码清理完成 |
