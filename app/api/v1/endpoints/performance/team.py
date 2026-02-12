# -*- coding: utf-8 -*-
"""
团队/部门绩效 - 自动生成
从 performance.py 拆分
"""

# -*- coding: utf-8 -*-
"""
绩效管理 API endpoints
核心功能：多层级绩效视图、绩效对比、趋势分析、排行榜
"""

from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.organization import Department
from app.models.performance import (  # New Performance System
    PerformancePeriod,
    PerformanceResult,
)
from app.models.project import Project
from app.models.user import User
from app.schemas.performance import (  # New Performance System
    DepartmentPerformanceResponse,
    PerformanceRankingResponse,
    TeamPerformanceResponse,
)

router = APIRouter()


def _check_performance_view_permission(current_user: User, target_user_id: int, db: Session) -> bool:
    """
    检查用户是否有权限查看指定用户的绩效

    规则：
    1. 可以查看自己的绩效
    2. 部门经理可以查看本部门员工的绩效
    3. 项目经理可以查看项目成员的绩效
    4. 管理员可以查看所有人的绩效

    Returns:
        bool: 是否有权限查看
    """
    if current_user.is_superuser:
        return True

    # 查看自己的绩效
    if current_user.id == target_user_id:
        return True

    # 检查是否是部门经理
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        return False

    # 检查是否有管理角色
    manager_roles = ['dept_manager', 'department_manager', '部门经理',
                     'pm', 'project_manager', '项目经理',
                     'admin', 'super_admin', '管理员']

    has_manager_role = False
    for user_role in (current_user.roles or []):
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ''
        if role_code in manager_roles or role_name in manager_roles:
            has_manager_role = True
            break

    if not has_manager_role:
        return False

    # 检查是否是同一部门
    if target_user.department_id and current_user.department_id == target_user.department_id:
        return True

    # 检查是否管理同一项目
    user_projects = db.query(Project).filter(Project.pm_id == current_user.id).all()
    project_ids = [p.id for p in user_projects]

    target_projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
    for project in target_projects:
        # 检查目标用户是否是项目成员
        from app.models.progress import Task
        member_task = db.query(Task).filter(
            Task.project_id == project.id,
            Task.owner_id == target_user_id
        ).first()
        if member_task:
            return True

    return False


def _get_team_members(db: Session, team_id: int) -> List[int]:
    """
    获取团队成员ID列表

    Args:
        db: 数据库会话
        team_id: 团队ID（暂时使用department_id作为team_id）

    Returns:
        List[int]: 成员ID列表
    """
    # 临时使用部门作为团队
    users = db.query(User).filter(
        User.department_id == team_id,
        User.is_active
    ).all()
    return [u.id for u in users]


def _get_department_members(db: Session, dept_id: int) -> List[int]:
    """
    获取部门成员ID列表

    Args:
        db: 数据库会话
        dept_id: 部门ID

    Returns:
        List[int]: 成员ID列表
    """
    users = db.query(User).filter(
        User.department_id == dept_id,
        User.is_active
    ).all()
    return [u.id for u in users]


def _get_evaluator_type(user: User, db: Session) -> str:
    """
    判断评价人类型（部门经理/项目经理）

    Args:
        user: 用户对象
        db: 数据库会话

    Returns:
        str: 评价人类型（DEPT_MANAGER/PROJECT_MANAGER/BOTH）
    """
    is_dept_manager = False
    is_project_manager = False

    for user_role in (user.roles or []):
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ''

        if role_code in ['dept_manager', 'department_manager', '部门经理'] or role_name in ['dept_manager', 'department_manager', '部门经理']:
            is_dept_manager = True
        if role_code in ['pm', 'project_manager', '项目经理'] or role_name in ['pm', 'project_manager', '项目经理']:
            is_project_manager = True

    if is_dept_manager and is_project_manager:
        return 'BOTH'
    elif is_dept_manager:
        return 'DEPT_MANAGER'
    elif is_project_manager:
        return 'PROJECT_MANAGER'
    else:
        return 'OTHER'


def _get_team_name(db: Session, team_id: int) -> str:
    """获取团队名称"""
    dept = db.query(Department).filter(Department.id == team_id).first()
    return dept.name if dept else f"团队{team_id}"


def _get_department_name(db: Session, dept_id: int) -> str:
    """获取部门名称"""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    return dept.name if dept else f"部门{dept_id}"



from fastapi import APIRouter

router = APIRouter(
    prefix="/performance/team",
    tags=["team"]
)

# 共 3 个路由

# ==================== 团队/部门绩效 ====================

@router.get("/team/{team_id}", response_model=TeamPerformanceResponse, status_code=status.HTTP_200_OK)
def get_team_performance(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    period_id: Optional[int] = Query(None, description="周期ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    团队绩效汇总（平均分/排名）
    注：当前使用部门作为团队，team_id 对应 department.id
    """
    # 获取团队名称
    team_name = _get_team_name(db, team_id)

    # 获取团队成员
    member_ids = _get_team_members(db, team_id)

    # 获取周期
    if period_id:
        period = db.query(PerformancePeriod).filter(PerformancePeriod.id == period_id).first()
    else:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.status == "FINALIZED"
        ).order_by(desc(PerformancePeriod.end_date)).first()

    # 获取团队成员绩效
    results = db.query(PerformanceResult).filter(
        PerformanceResult.period_id == period.id,
        PerformanceResult.user_id.in_(member_ids)
    ).all()

    if not results:
        return TeamPerformanceResponse(
            team_id=team_id,
            team_name=team_name,
            period_id=period.id,
            period_name=period.period_name,
            member_count=len(member_ids),
            avg_score=Decimal("0"),
            max_score=Decimal("0"),
            min_score=Decimal("0"),
            level_distribution={},
            members=[]
        )

    scores = [float(r.total_score) if r.total_score else 0 for r in results]
    avg_score = Decimal(str(sum(scores) / len(scores))) if scores else Decimal("0")
    max_score = Decimal(str(max(scores))) if scores else Decimal("0")
    min_score = Decimal(str(min(scores))) if scores else Decimal("0")

    # 等级分布
    level_distribution = {}
    for r in results:
        level = r.level or "QUALIFIED"
        level_distribution[level] = level_distribution.get(level, 0) + 1

    # 成员列表
    members = []
    for r in results:
        user = db.query(User).filter(User.id == r.user_id).first()
        members.append({
            "user_id": r.user_id,
            "user_name": user.real_name or user.username if user else None,
            "score": float(r.total_score) if r.total_score else 0,
            "level": r.level or "QUALIFIED"
        })

    # 按分数排序
    members.sort(key=lambda x: x["score"], reverse=True)

    return TeamPerformanceResponse(
        team_id=team_id,
        team_name=team_name,
        period_id=period.id,
        period_name=period.period_name,
        member_count=len(results),
        avg_score=avg_score,
        max_score=max_score,
        min_score=min_score,
        level_distribution=level_distribution,
        members=members
    )


@router.get("/department/{dept_id}", response_model=DepartmentPerformanceResponse, status_code=status.HTTP_200_OK)
def get_department_performance(
    *,
    db: Session = Depends(deps.get_db),
    dept_id: int,
    period_id: Optional[int] = Query(None, description="周期ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    部门绩效汇总（等级分布）
    """
    # 获取部门名称
    department_name = _get_department_name(db, dept_id)

    # 获取部门成员
    member_ids = _get_department_members(db, dept_id)

    if period_id:
        period = db.query(PerformancePeriod).filter(PerformancePeriod.id == period_id).first()
    else:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.status == "FINALIZED"
        ).order_by(desc(PerformancePeriod.end_date)).first()

    if not period:
        raise HTTPException(status_code=404, detail="未找到考核周期")

    results = db.query(PerformanceResult).filter(
        PerformanceResult.period_id == period.id,
        PerformanceResult.department_id == dept_id
    ).all()

    if not results:
        return DepartmentPerformanceResponse(
            department_id=dept_id,
            department_name=department_name,
            period_id=period.id,
            period_name=period.period_name,
            member_count=len(member_ids),
            avg_score=Decimal("0"),
            level_distribution={},
            teams=[]
        )

    scores = [float(r.total_score) if r.total_score else 0 for r in results]
    avg_score = Decimal(str(sum(scores) / len(scores))) if scores else Decimal("0")

    # 等级分布
    level_distribution = {}
    for r in results:
        level = r.level or "QUALIFIED"
        level_distribution[level] = level_distribution.get(level, 0) + 1

    # 获取团队列表（使用子部门）
    sub_teams = db.query(Department).filter(
        Department.parent_id == dept_id
    ).all()
    teams = [{"team_id": t.id, "team_name": t.name} for t in sub_teams]

    return DepartmentPerformanceResponse(
        department_id=dept_id,
        department_name=department_name,
        period_id=period.id,
        period_name=period.period_name,
        member_count=len(results),
        avg_score=avg_score,
        level_distribution=level_distribution,
        teams=teams
    )


@router.get("/ranking", response_model=PerformanceRankingResponse, status_code=status.HTTP_200_OK)
def get_performance_ranking(
    *,
    db: Session = Depends(deps.get_db),
    ranking_type: str = Query("COMPANY", description="排行榜类型：TEAM/DEPARTMENT/COMPANY"),
    period_id: Optional[int] = Query(None, description="周期ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    绩效排行榜（团队/部门/公司）
    """
    if period_id:
        period = db.query(PerformancePeriod).filter(PerformancePeriod.id == period_id).first()
    else:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.status == "FINALIZED"
        ).order_by(desc(PerformancePeriod.end_date)).first()

    if not period:
        raise HTTPException(status_code=404, detail="未找到考核周期")

    rankings = []

    if ranking_type == "COMPANY":
        # 公司排行榜
        results = db.query(PerformanceResult).filter(
            PerformanceResult.period_id == period.id
        ).order_by(desc(PerformanceResult.total_score)).limit(100).all()

        for idx, result in enumerate(results, 1):
            user = db.query(User).filter(User.id == result.user_id).first()
            rankings.append({
                "rank": idx,
                "user_id": result.user_id,
                "user_name": user.real_name or user.username if user else None,
                "department_name": result.department_name,
                "score": float(result.total_score) if result.total_score else 0,
                "level": result.level or "QUALIFIED"
            })

    elif ranking_type == "TEAM":
        # 团队排行榜：按部门统计平均分
        from app.models.organization import Department
        departments = db.query(Department).all()

        for dept in departments:
            dept_results = db.query(PerformanceResult).filter(
                PerformanceResult.period_id == period.id,
                PerformanceResult.department_id == dept.id
            ).all()

            if dept_results:
                avg_score = sum(float(r.total_score or 0) for r in dept_results) / len(dept_results)
                rankings.append({
                    "rank": 0,  # 稍后填充
                    "entity_id": dept.id,
                    "entity_name": dept.name,
                    "score": round(avg_score, 2),
                    "member_count": len(dept_results)
                })

        # 排序并填充排名
        rankings.sort(key=lambda x: x["score"], reverse=True)
        for idx, r in enumerate(rankings, 1):
            r["rank"] = idx

    elif ranking_type == "DEPARTMENT":
        # 部门排行榜：与团队排行榜类似，但包含更多信息
        from app.models.organization import Department
        departments = db.query(Department).all()

        for dept in departments:
            dept_results = db.query(PerformanceResult).filter(
                PerformanceResult.period_id == period.id,
                PerformanceResult.department_id == dept.id
            ).all()

            if dept_results:
                avg_score = sum(float(r.total_score or 0) for r in dept_results) / len(dept_results)

                # 等级分布
                level_dist = {}
                for r in dept_results:
                    level = r.level or "QUALIFIED"
                    level_dist[level] = level_dist.get(level, 0) + 1

                rankings.append({
                    "rank": 0,  # 稍后填充
                    "entity_id": dept.id,
                    "entity_name": dept.name,
                    "score": round(avg_score, 2),
                    "member_count": len(dept_results),
                    "level_distribution": level_dist
                })

        # 排序并填充排名
        rankings.sort(key=lambda x: x["score"], reverse=True)
        for idx, r in enumerate(rankings, 1):
            r["rank"] = idx

    return PerformanceRankingResponse(
        ranking_type=ranking_type,
        period_id=period.id,
        period_name=period.period_name,
        rankings=rankings
    )



