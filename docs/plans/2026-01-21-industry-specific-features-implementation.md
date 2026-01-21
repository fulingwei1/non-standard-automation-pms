# 非标自动化行业特定功能实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现资源计划、资源冲突检测、资源利用率分析、技能矩阵四个行业特定功能

**Architecture:** 基于现有 staff_matching 模型扩展，新增 1 张表 + 4 组 API + 2 个服务类

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest

---

## Phase 1: 数据模型与基础设施

### Task 1.1: 创建资源计划数据模型

**Files:**
- Create: `app/models/project/resource_plan.py`
- Modify: `app/models/project/__init__.py`
- Create: `migrations/20260121_resource_plan_sqlite.sql`

**Step 1: 创建资源计划模型文件**

```python
# app/models/project/resource_plan.py
# -*- coding: utf-8 -*-
"""
项目阶段资源计划模型

用于按阶段规划和跟踪项目人员需求与分配
"""
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ProjectStageResourcePlan(Base, TimestampMixin):
    """项目阶段资源计划表"""
    __tablename__ = 'project_stage_resource_plan'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    stage_code = Column(String(10), nullable=False, comment='阶段编码 S1-S9')

    # 关联现有的人员需求表（可选）
    staffing_need_id = Column(
        Integer,
        ForeignKey('mes_project_staffing_need.id'),
        comment='关联人员需求ID'
    )

    # 角色需求
    role_code = Column(String(50), nullable=False, comment='角色编码')
    role_name = Column(String(100), comment='角色名称')
    headcount = Column(Integer, default=1, comment='需求人数')
    allocation_pct = Column(Numeric(5, 2), default=100, comment='分配比例%')

    # 实际分配
    assigned_employee_id = Column(
        Integer,
        ForeignKey('employees.id'),
        comment='已分配员工ID'
    )
    assignment_status = Column(
        String(20),
        default='PENDING',
        comment='分配状态: PENDING/ASSIGNED/CONFLICT/RELEASED'
    )

    # 时间范围
    planned_start = Column(Date, comment='计划开始日期')
    planned_end = Column(Date, comment='计划结束日期')

    # 备注
    remark = Column(Text, comment='备注')

    # 关系
    project = relationship('Project', backref='stage_resource_plans')
    staffing_need = relationship('MesProjectStaffingNeed', backref='resource_plans')
    assigned_employee = relationship('Employee', backref='resource_assignments')

    __table_args__ = (
        Index('idx_stage_plan_project', 'project_id'),
        Index('idx_stage_plan_stage', 'stage_code'),
        Index('idx_stage_plan_employee', 'assigned_employee_id'),
        Index('idx_stage_plan_status', 'assignment_status'),
        Index('idx_stage_plan_dates', 'planned_start', 'planned_end'),
        {'comment': '项目阶段资源计划表'}
    )

    def __repr__(self):
        return f"<ProjectStageResourcePlan project={self.project_id} stage={self.stage_code} role={self.role_code}>"

    @property
    def is_assigned(self) -> bool:
        """是否已分配"""
        return self.assignment_status == 'ASSIGNED' and self.assigned_employee_id is not None

    @property
    def has_conflict(self) -> bool:
        """是否有冲突"""
        return self.assignment_status == 'CONFLICT'
```

**Step 2: 更新 project 模型包导出**

在 `app/models/project/__init__.py` 中添加：

```python
from .resource_plan import ProjectStageResourcePlan

__all__ = [
    # ... 现有导出
    "ProjectStageResourcePlan",
]
```

**Step 3: 创建数据库迁移文件**

```sql
-- migrations/20260121_resource_plan_sqlite.sql
-- 项目阶段资源计划表

CREATE TABLE IF NOT EXISTS project_stage_resource_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    stage_code VARCHAR(10) NOT NULL,
    staffing_need_id INTEGER,
    role_code VARCHAR(50) NOT NULL,
    role_name VARCHAR(100),
    headcount INTEGER DEFAULT 1,
    allocation_pct DECIMAL(5,2) DEFAULT 100,
    assigned_employee_id INTEGER,
    assignment_status VARCHAR(20) DEFAULT 'PENDING',
    planned_start DATE,
    planned_end DATE,
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (staffing_need_id) REFERENCES mes_project_staffing_need(id),
    FOREIGN KEY (assigned_employee_id) REFERENCES employees(id)
);

CREATE INDEX IF NOT EXISTS idx_stage_plan_project ON project_stage_resource_plan(project_id);
CREATE INDEX IF NOT EXISTS idx_stage_plan_stage ON project_stage_resource_plan(stage_code);
CREATE INDEX IF NOT EXISTS idx_stage_plan_employee ON project_stage_resource_plan(assigned_employee_id);
CREATE INDEX IF NOT EXISTS idx_stage_plan_status ON project_stage_resource_plan(assignment_status);
CREATE INDEX IF NOT EXISTS idx_stage_plan_dates ON project_stage_resource_plan(planned_start, planned_end);
```

**Step 4: 验证模型导入**

Run: `python -c "from app.models.project.resource_plan import ProjectStageResourcePlan; print('Model OK')"`
Expected: `Model OK`

**Step 5: 执行数据库迁移**

Run: `sqlite3 data/app.db < migrations/20260121_resource_plan_sqlite.sql`
Expected: 无错误输出

**Step 6: 验证表创建**

Run: `sqlite3 data/app.db ".schema project_stage_resource_plan"`
Expected: 显示表结构

**Step 7: 提交**

```bash
git add app/models/project/resource_plan.py app/models/project/__init__.py migrations/20260121_resource_plan_sqlite.sql
git commit -m "feat: 添加项目阶段资源计划模型"
```

---

### Task 1.2: 创建 Pydantic Schema

**Files:**
- Create: `app/schemas/resource_plan.py`

**Step 1: 创建 Schema 文件**

```python
# app/schemas/resource_plan.py
# -*- coding: utf-8 -*-
"""
资源计划相关的 Pydantic Schema
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


# ==================== 基础 Schema ====================

class ResourcePlanBase(BaseModel):
    """资源计划基础字段"""
    stage_code: str = Field(..., description="阶段编码 S1-S9", pattern="^S[1-9]$")
    role_code: str = Field(..., description="角色编码")
    role_name: Optional[str] = Field(None, description="角色名称")
    headcount: int = Field(1, ge=1, description="需求人数")
    allocation_pct: Decimal = Field(100, ge=0, le=100, description="分配比例%")
    planned_start: Optional[date] = Field(None, description="计划开始日期")
    planned_end: Optional[date] = Field(None, description="计划结束日期")
    remark: Optional[str] = Field(None, description="备注")


class ResourcePlanCreate(ResourcePlanBase):
    """创建资源计划"""
    staffing_need_id: Optional[int] = Field(None, description="关联人员需求ID")


class ResourcePlanUpdate(BaseModel):
    """更新资源计划"""
    role_name: Optional[str] = None
    headcount: Optional[int] = Field(None, ge=1)
    allocation_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    remark: Optional[str] = None


# ==================== 分配相关 ====================

class ResourceAssignment(BaseModel):
    """人员分配请求"""
    employee_id: int = Field(..., description="员工ID")
    force: bool = Field(False, description="是否强制分配（忽略冲突警告）")


class EmployeeBrief(BaseModel):
    """员工简要信息"""
    id: int
    name: str
    department: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== 响应 Schema ====================

class ResourcePlanResponse(ResourcePlanBase):
    """资源计划响应"""
    id: int
    project_id: int
    staffing_need_id: Optional[int] = None
    assigned_employee_id: Optional[int] = None
    assignment_status: str
    assigned_employee: Optional[EmployeeBrief] = None

    class Config:
        from_attributes = True


class StageResourceSummary(BaseModel):
    """阶段资源汇总"""
    stage_code: str
    stage_name: str
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    requirements: List[ResourcePlanResponse]
    total_headcount: int
    filled_count: int
    fill_rate: float = Field(..., description="填充率 0-100")


class ProjectResourcePlanSummary(BaseModel):
    """项目资源计划汇总"""
    project_id: int
    project_name: str
    stages: List[StageResourceSummary]
    overall_fill_rate: float


# ==================== 冲突相关 ====================

class ConflictProject(BaseModel):
    """冲突项目信息"""
    project_id: int
    project_name: str
    stage_code: str
    stage_name: Optional[str] = None
    allocation_pct: Decimal
    period: str  # "2026-03-01 ~ 2026-03-31"


class ResourceConflict(BaseModel):
    """资源冲突"""
    id: Optional[int] = None
    employee: EmployeeBrief
    this_project: ConflictProject
    conflict_with: ConflictProject
    overlap_period: str
    total_allocation: Decimal
    over_allocation: Decimal
    severity: str = Field(..., description="严重度: HIGH/MEDIUM/LOW")
    resolved: bool = False


class ProjectConflictSummary(BaseModel):
    """项目冲突汇总"""
    project_id: int
    conflicts: List[ResourceConflict]
    conflict_count: int
    affected_employees: int


# ==================== 候选人相关 ====================

class CandidateAvailability(BaseModel):
    """候选人可用性"""
    current_allocation: Decimal
    available_pct: Decimal
    available_hours: Decimal
    current_projects: List[dict]


class ResourceCandidate(BaseModel):
    """资源候选人"""
    employee: EmployeeBrief
    skill_match: dict  # {skill_code: {score, level}}
    availability: CandidateAvailability
    match_score: float
    recommendation: str = Field(..., description="STRONG/RECOMMENDED/ACCEPTABLE/WEAK")
    potential_conflict: Optional[ResourceConflict] = None
```

**Step 2: 验证 Schema**

Run: `python -c "from app.schemas.resource_plan import *; print('Schema OK')"`
Expected: `Schema OK`

**Step 3: 提交**

```bash
git add app/schemas/resource_plan.py
git commit -m "feat: 添加资源计划 Pydantic Schema"
```

---

## Phase 2: 资源计划服务与 API

### Task 2.1: 创建资源计划服务

**Files:**
- Create: `app/services/resource_plan_service.py`
- Create: `tests/unit/test_resource_plan_service.py`

**Step 1: 编写测试（TDD）**

```python
# tests/unit/test_resource_plan_service.py
# -*- coding: utf-8 -*-
"""
资源计划服务单元测试
"""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.resource_plan_service import ResourcePlanService


class TestResourcePlanService:
    """资源计划服务测试"""

    def test_calculate_fill_rate_empty(self):
        """测试空需求的填充率"""
        result = ResourcePlanService.calculate_fill_rate([], [])
        assert result == 100.0  # 无需求时视为100%

    def test_calculate_fill_rate_partial(self):
        """测试部分填充的填充率"""
        requirements = [
            MagicMock(headcount=2, assignment_status='ASSIGNED'),
            MagicMock(headcount=1, assignment_status='PENDING'),
        ]
        result = ResourcePlanService.calculate_fill_rate(requirements)
        # 2 assigned / 3 total = 66.67%
        assert abs(result - 66.67) < 0.01

    def test_detect_date_overlap_no_overlap(self):
        """测试无重叠日期"""
        result = ResourcePlanService.calculate_date_overlap(
            date(2026, 1, 1), date(2026, 1, 31),
            date(2026, 2, 1), date(2026, 2, 28)
        )
        assert result is None

    def test_detect_date_overlap_with_overlap(self):
        """测试有重叠日期"""
        result = ResourcePlanService.calculate_date_overlap(
            date(2026, 1, 15), date(2026, 2, 15),
            date(2026, 2, 1), date(2026, 2, 28)
        )
        assert result == (date(2026, 2, 1), date(2026, 2, 15))

    def test_calculate_conflict_severity_high(self):
        """测试高严重度冲突"""
        severity = ResourcePlanService.calculate_conflict_severity(Decimal('180'))
        assert severity == 'HIGH'

    def test_calculate_conflict_severity_medium(self):
        """测试中严重度冲突"""
        severity = ResourcePlanService.calculate_conflict_severity(Decimal('130'))
        assert severity == 'MEDIUM'

    def test_calculate_conflict_severity_low(self):
        """测试低严重度冲突"""
        severity = ResourcePlanService.calculate_conflict_severity(Decimal('110'))
        assert severity == 'LOW'
```

**Step 2: 运行测试确认失败**

Run: `pytest tests/unit/test_resource_plan_service.py -v`
Expected: FAIL (模块不存在)

**Step 3: 实现服务**

```python
# app/services/resource_plan_service.py
# -*- coding: utf-8 -*-
"""
资源计划服务

提供资源计划的创建、查询、分配、冲突检测等功能
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStage
from app.models.project.resource_plan import ProjectStageResourcePlan
from app.models.staff_matching import MesProjectStaffingNeed, HrEmployeeProfile
from app.schemas.resource_plan import (
    ResourceConflict,
    ResourcePlanCreate,
    ConflictProject,
    EmployeeBrief,
)


class ResourcePlanService:
    """资源计划服务"""

    # ==================== 工具方法 ====================

    @staticmethod
    def calculate_fill_rate(requirements: List[ProjectStageResourcePlan]) -> float:
        """
        计算填充率

        Args:
            requirements: 资源需求列表

        Returns:
            填充率百分比 (0-100)
        """
        if not requirements:
            return 100.0

        total_headcount = sum(r.headcount for r in requirements)
        if total_headcount == 0:
            return 100.0

        filled_count = sum(
            r.headcount for r in requirements
            if r.assignment_status == 'ASSIGNED'
        )

        return round(filled_count / total_headcount * 100, 2)

    @staticmethod
    def calculate_date_overlap(
        start1: date, end1: date,
        start2: date, end2: date
    ) -> Optional[Tuple[date, date]]:
        """
        计算两个日期范围的重叠部分

        Returns:
            重叠的 (开始日期, 结束日期)，无重叠返回 None
        """
        if not all([start1, end1, start2, end2]):
            return None

        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)

        if overlap_start <= overlap_end:
            return (overlap_start, overlap_end)
        return None

    @staticmethod
    def calculate_conflict_severity(total_allocation: Decimal) -> str:
        """
        计算冲突严重度

        Args:
            total_allocation: 总分配比例

        Returns:
            严重度: HIGH (>150%), MEDIUM (>120%), LOW (>100%)
        """
        if total_allocation >= 150:
            return 'HIGH'
        elif total_allocation >= 120:
            return 'MEDIUM'
        else:
            return 'LOW'

    # ==================== CRUD 操作 ====================

    @staticmethod
    def get_project_resource_plans(
        db: Session,
        project_id: int,
        stage_code: Optional[str] = None
    ) -> List[ProjectStageResourcePlan]:
        """获取项目资源计划"""
        query = db.query(ProjectStageResourcePlan).filter(
            ProjectStageResourcePlan.project_id == project_id
        )
        if stage_code:
            query = query.filter(ProjectStageResourcePlan.stage_code == stage_code)
        return query.order_by(
            ProjectStageResourcePlan.stage_code,
            ProjectStageResourcePlan.role_code
        ).all()

    @staticmethod
    def create_resource_plan(
        db: Session,
        project_id: int,
        plan_in: ResourcePlanCreate
    ) -> ProjectStageResourcePlan:
        """创建资源计划"""
        plan = ProjectStageResourcePlan(
            project_id=project_id,
            **plan_in.model_dump()
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def assign_employee(
        db: Session,
        plan_id: int,
        employee_id: int,
        force: bool = False
    ) -> Tuple[ProjectStageResourcePlan, Optional[ResourceConflict]]:
        """
        分配员工到资源计划

        Args:
            db: 数据库会话
            plan_id: 资源计划ID
            employee_id: 员工ID
            force: 是否强制分配（忽略冲突）

        Returns:
            (更新后的计划, 冲突信息或None)
        """
        plan = db.query(ProjectStageResourcePlan).filter(
            ProjectStageResourcePlan.id == plan_id
        ).first()

        if not plan:
            raise ValueError("资源计划不存在")

        # 检查冲突
        conflict = ResourcePlanService.check_assignment_conflict(
            db, employee_id, plan.project_id,
            plan.planned_start, plan.planned_end,
            plan.allocation_pct
        )

        if conflict and not force:
            plan.assignment_status = 'CONFLICT'
            db.commit()
            return plan, conflict

        # 执行分配
        plan.assigned_employee_id = employee_id
        plan.assignment_status = 'ASSIGNED'
        db.commit()
        db.refresh(plan)

        return plan, None

    @staticmethod
    def release_employee(db: Session, plan_id: int) -> ProjectStageResourcePlan:
        """释放员工分配"""
        plan = db.query(ProjectStageResourcePlan).filter(
            ProjectStageResourcePlan.id == plan_id
        ).first()

        if not plan:
            raise ValueError("资源计划不存在")

        plan.assigned_employee_id = None
        plan.assignment_status = 'RELEASED'
        db.commit()
        db.refresh(plan)

        return plan

    # ==================== 冲突检测 ====================

    @staticmethod
    def check_assignment_conflict(
        db: Session,
        employee_id: int,
        project_id: int,
        start_date: Optional[date],
        end_date: Optional[date],
        allocation_pct: Decimal
    ) -> Optional[ResourceConflict]:
        """
        检查分配是否会产生冲突

        Returns:
            冲突信息，无冲突返回 None
        """
        if not start_date or not end_date:
            return None

        # 获取员工在时间范围内的其他分配
        existing = db.query(ProjectStageResourcePlan).filter(
            ProjectStageResourcePlan.assigned_employee_id == employee_id,
            ProjectStageResourcePlan.assignment_status == 'ASSIGNED',
            ProjectStageResourcePlan.project_id != project_id,
            ProjectStageResourcePlan.planned_end >= start_date,
            ProjectStageResourcePlan.planned_start <= end_date,
        ).all()

        for assignment in existing:
            overlap = ResourcePlanService.calculate_date_overlap(
                start_date, end_date,
                assignment.planned_start, assignment.planned_end
            )
            if overlap:
                total = allocation_pct + assignment.allocation_pct
                if total > 100:
                    # 构建冲突信息
                    employee = db.query(Employee).filter(
                        Employee.id == employee_id
                    ).first()
                    project = db.query(Project).filter(
                        Project.id == assignment.project_id
                    ).first()

                    return ResourceConflict(
                        employee=EmployeeBrief(
                            id=employee.id,
                            name=employee.name,
                            department=employee.department
                        ),
                        this_project=ConflictProject(
                            project_id=project_id,
                            project_name="当前项目",
                            stage_code="",
                            allocation_pct=allocation_pct,
                            period=f"{start_date} ~ {end_date}"
                        ),
                        conflict_with=ConflictProject(
                            project_id=project.id,
                            project_name=project.name,
                            stage_code=assignment.stage_code,
                            allocation_pct=assignment.allocation_pct,
                            period=f"{assignment.planned_start} ~ {assignment.planned_end}"
                        ),
                        overlap_period=f"{overlap[0]} ~ {overlap[1]}",
                        total_allocation=total,
                        over_allocation=total - 100,
                        severity=ResourcePlanService.calculate_conflict_severity(total)
                    )

        return None

    @staticmethod
    def detect_employee_conflicts(
        db: Session,
        employee_id: int
    ) -> List[ResourceConflict]:
        """检测员工的所有资源冲突"""
        assignments = db.query(ProjectStageResourcePlan).filter(
            ProjectStageResourcePlan.assigned_employee_id == employee_id,
            ProjectStageResourcePlan.assignment_status == 'ASSIGNED',
        ).all()

        conflicts = []

        for i, a1 in enumerate(assignments):
            for a2 in assignments[i+1:]:
                overlap = ResourcePlanService.calculate_date_overlap(
                    a1.planned_start, a1.planned_end,
                    a2.planned_start, a2.planned_end
                )
                if overlap:
                    total = a1.allocation_pct + a2.allocation_pct
                    if total > 100:
                        # 获取相关信息
                        employee = db.query(Employee).filter(
                            Employee.id == employee_id
                        ).first()
                        project1 = db.query(Project).filter(
                            Project.id == a1.project_id
                        ).first()
                        project2 = db.query(Project).filter(
                            Project.id == a2.project_id
                        ).first()

                        conflicts.append(ResourceConflict(
                            employee=EmployeeBrief(
                                id=employee.id,
                                name=employee.name,
                                department=getattr(employee, 'department', None)
                            ),
                            this_project=ConflictProject(
                                project_id=project1.id,
                                project_name=project1.name,
                                stage_code=a1.stage_code,
                                allocation_pct=a1.allocation_pct,
                                period=f"{a1.planned_start} ~ {a1.planned_end}"
                            ),
                            conflict_with=ConflictProject(
                                project_id=project2.id,
                                project_name=project2.name,
                                stage_code=a2.stage_code,
                                allocation_pct=a2.allocation_pct,
                                period=f"{a2.planned_start} ~ {a2.planned_end}"
                            ),
                            overlap_period=f"{overlap[0]} ~ {overlap[1]}",
                            total_allocation=total,
                            over_allocation=total - 100,
                            severity=ResourcePlanService.calculate_conflict_severity(total)
                        ))

        return conflicts
```

**Step 4: 运行测试确认通过**

Run: `pytest tests/unit/test_resource_plan_service.py -v`
Expected: All tests PASS

**Step 5: 提交**

```bash
git add app/services/resource_plan_service.py tests/unit/test_resource_plan_service.py
git commit -m "feat: 添加资源计划服务（含冲突检测）"
```

---

### Task 2.2: 创建资源计划 API

**Files:**
- Create: `app/api/v1/endpoints/projects/resource_plan/__init__.py`
- Create: `app/api/v1/endpoints/projects/resource_plan/crud.py`
- Create: `app/api/v1/endpoints/projects/resource_plan/assignment.py`
- Modify: `app/api/v1/endpoints/projects/__init__.py`

**Step 1: 创建 API 目录结构**

```python
# app/api/v1/endpoints/projects/resource_plan/__init__.py
# -*- coding: utf-8 -*-
"""
项目资源计划 API 模块

路由: /projects/{project_id}/resource-plan/
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .assignment import router as assignment_router

router = APIRouter()

router.include_router(crud_router, tags=["资源计划"])
router.include_router(assignment_router, tags=["资源分配"])
```

**Step 2: 创建 CRUD 路由**

```python
# app/api/v1/endpoints/projects/resource_plan/crud.py
# -*- coding: utf-8 -*-
"""
资源计划 CRUD 操作
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project, ProjectStage
from app.models.user import User
from app.schemas.resource_plan import (
    ResourcePlanCreate,
    ResourcePlanResponse,
    ResourcePlanUpdate,
    ProjectResourcePlanSummary,
    StageResourceSummary,
)
from app.services.resource_plan_service import ResourcePlanService
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()

# 阶段名称映射
STAGE_NAMES = {
    'S1': '需求进入', 'S2': '方案设计', 'S3': '采购备料',
    'S4': '加工制造', 'S5': '装配调试', 'S6': '出厂验收',
    'S7': '包装发运', 'S8': '现场安装', 'S9': '质保结项',
}


@router.get("/", response_model=List[ResourcePlanResponse])
def get_resource_plans(
    project_id: int = Path(..., description="项目ID"),
    stage_code: Optional[str] = Query(None, description="阶段编码筛选"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取项目资源计划列表"""
    check_project_access_or_raise(db, current_user, project_id)

    plans = ResourcePlanService.get_project_resource_plans(
        db, project_id, stage_code
    )
    return plans


@router.get("/summary", response_model=ProjectResourcePlanSummary)
def get_resource_plan_summary(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取项目资源计划汇总"""
    check_project_access_or_raise(db, current_user, project_id)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    plans = ResourcePlanService.get_project_resource_plans(db, project_id)

    # 按阶段分组
    stages_dict = {}
    for plan in plans:
        if plan.stage_code not in stages_dict:
            stages_dict[plan.stage_code] = []
        stages_dict[plan.stage_code].append(plan)

    # 构建阶段汇总
    stages = []
    for stage_code in sorted(stages_dict.keys()):
        stage_plans = stages_dict[stage_code]
        total_headcount = sum(p.headcount for p in stage_plans)
        filled_count = sum(
            p.headcount for p in stage_plans
            if p.assignment_status == 'ASSIGNED'
        )
        fill_rate = (filled_count / total_headcount * 100) if total_headcount > 0 else 100

        stages.append(StageResourceSummary(
            stage_code=stage_code,
            stage_name=STAGE_NAMES.get(stage_code, stage_code),
            planned_start=min((p.planned_start for p in stage_plans if p.planned_start), default=None),
            planned_end=max((p.planned_end for p in stage_plans if p.planned_end), default=None),
            requirements=stage_plans,
            total_headcount=total_headcount,
            filled_count=filled_count,
            fill_rate=round(fill_rate, 2)
        ))

    overall_fill_rate = ResourcePlanService.calculate_fill_rate(plans)

    return ProjectResourcePlanSummary(
        project_id=project_id,
        project_name=project.name,
        stages=stages,
        overall_fill_rate=overall_fill_rate
    )


@router.post("/", response_model=ResourcePlanResponse)
def create_resource_plan(
    project_id: int = Path(..., description="项目ID"),
    plan_in: ResourcePlanCreate = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """创建资源计划"""
    check_project_access_or_raise(db, current_user, project_id)

    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    plan = ResourcePlanService.create_resource_plan(db, project_id, plan_in)
    return plan


@router.get("/stages/{stage_code}", response_model=List[ResourcePlanResponse])
def get_stage_resource_plans(
    project_id: int = Path(..., description="项目ID"),
    stage_code: str = Path(..., description="阶段编码"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取特定阶段的资源计划"""
    check_project_access_or_raise(db, current_user, project_id)

    plans = ResourcePlanService.get_project_resource_plans(
        db, project_id, stage_code
    )
    return plans
```

**Step 3: 创建分配路由**

```python
# app/api/v1/endpoints/projects/resource_plan/assignment.py
# -*- coding: utf-8 -*-
"""
资源分配操作
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.resource_plan import (
    ResourceAssignment,
    ResourcePlanResponse,
    ResourceConflict,
    ResourceCandidate,
)
from app.services.resource_plan_service import ResourcePlanService
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


@router.post("/{plan_id}/assign", response_model=ResourcePlanResponse)
def assign_employee(
    project_id: int = Path(..., description="项目ID"),
    plan_id: int = Path(..., description="资源计划ID"),
    assignment: ResourceAssignment = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """分配员工到资源计划"""
    check_project_access_or_raise(db, current_user, project_id)

    try:
        plan, conflict = ResourcePlanService.assign_employee(
            db, plan_id, assignment.employee_id, assignment.force
        )

        if conflict and not assignment.force:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "存在资源冲突",
                    "conflict": conflict.model_dump()
                }
            )

        return plan
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{plan_id}/release", response_model=ResourcePlanResponse)
def release_employee(
    project_id: int = Path(..., description="项目ID"),
    plan_id: int = Path(..., description="资源计划ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """释放员工分配"""
    check_project_access_or_raise(db, current_user, project_id)

    try:
        plan = ResourcePlanService.release_employee(db, plan_id)
        return plan
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{plan_id}/candidates", response_model=List[ResourceCandidate])
def get_candidates(
    project_id: int = Path(..., description="项目ID"),
    plan_id: int = Path(..., description="资源计划ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取资源计划的候选人员"""
    check_project_access_or_raise(db, current_user, project_id)

    # 此处可调用现有的 AI 匹配服务
    # 暂时返回空列表，后续集成
    return []
```

**Step 4: 注册路由到 projects**

在 `app/api/v1/endpoints/projects/__init__.py` 中添加：

```python
from .resource_plan import router as resource_plan_router

router.include_router(
    resource_plan_router,
    prefix="/{project_id}/resource-plan",
    tags=["projects-resource-plan"]
)
```

**Step 5: 验证路由注册**

Run: `python -c "from app.api.v1.endpoints.projects import router; print([r.path for r in router.routes if 'resource-plan' in r.path])"`
Expected: 显示资源计划相关路由

**Step 6: 提交**

```bash
git add app/api/v1/endpoints/projects/resource_plan/
git add app/api/v1/endpoints/projects/__init__.py
git commit -m "feat: 添加资源计划 API 路由"
```

---

## Phase 3: 资源冲突检测 API

### Task 3.1: 创建资源冲突 API

**Files:**
- Create: `app/api/v1/endpoints/projects/resource_conflicts.py`
- Create: `app/api/v1/endpoints/analytics/resource_conflicts.py`
- Modify: `app/api/v1/endpoints/projects/__init__.py`
- Modify: `app/api/v1/endpoints/analytics/__init__.py`

*详细步骤参考 Task 2.2 模式*

---

## Phase 4: 资源利用率分析 API

### Task 4.1: 创建工作量分析服务

**Files:**
- Create: `app/services/workload_analytics_service.py`
- Create: `tests/unit/test_workload_analytics_service.py`

### Task 4.2: 增强部门工作量 API

**Files:**
- Modify: `app/api/v1/endpoints/departments/__init__.py`
- Create: `app/api/v1/endpoints/departments/workload.py`

### Task 4.3: 创建全局工作量分析 API

**Files:**
- Create: `app/api/v1/endpoints/analytics/workload.py`
- Modify: `app/api/v1/endpoints/analytics/__init__.py`

---

## Phase 5: 技能矩阵 API

### Task 5.1: 创建技能矩阵服务

**Files:**
- Create: `app/services/skill_matrix_service.py`
- Create: `tests/unit/test_skill_matrix_service.py`

### Task 5.2: 创建技能矩阵 API

**Files:**
- Create: `app/api/v1/endpoints/analytics/skill_matrix.py`
- Create: `app/api/v1/endpoints/departments/skill_matrix.py`

---

## Phase 6: 前端集成

### Task 6.1: 更新前端 API 模块

**Files:**
- Create: `frontend/src/services/api/resourcePlan.js`
- Modify: `frontend/src/services/api/analytics.js`

---

## 检查点

| 检查点 | 完成标准 |
|--------|----------|
| Phase 1 完成 | 数据模型可用，迁移执行成功 |
| Phase 2 完成 | 资源计划 CRUD 和分配 API 可用 |
| Phase 3 完成 | 冲突检测 API 可用 |
| Phase 4 完成 | 工作量分析 API 可用 |
| Phase 5 完成 | 技能矩阵 API 可用 |
| Phase 6 完成 | 前端集成完成 |

---

## 预计工作量

| Phase | 任务数 | 预计文件数 |
|-------|--------|------------|
| Phase 1 | 2 | 4 |
| Phase 2 | 2 | 6 |
| Phase 3 | 1 | 3 |
| Phase 4 | 3 | 5 |
| Phase 5 | 2 | 4 |
| Phase 6 | 1 | 2 |
| **Total** | **11** | **24** |
