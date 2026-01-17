# -*- coding: utf-8 -*-
"""
项目成员批量操作端点
"""

from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project, ProjectMember
from app.models.user import User

from .conflicts import check_member_conflicts_internal

router = APIRouter()


class BatchAddMembersRequest(BaseModel):
    """批量添加成员请求"""
    user_ids: List[int] = Body(..., description="用户ID列表")
    role_code: str = Body(..., description="角色编码")
    allocation_pct: float = Body(100, ge=0, le=100, description="分配比例")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    commitment_level: Optional[str] = Body(None, description="投入级别：FULL/PARTIAL/ADVISORY")
    reporting_to_pm: bool = Body(True, description="是否向项目经理汇报")


@router.post("/projects/{project_id}/members/batch", response_model=dict)
def batch_add_project_members(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    request: BatchAddMembersRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量添加项目成员
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id, "您没有权限在该项目中添加成员")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    added_count = 0
    skipped_count = 0
    conflicts = []

    for user_id in request.user_ids:
        # 检查是否已是成员
        existing = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        ).first()

        if existing:
            skipped_count += 1
            continue

        # 检查时间冲突
        conflict_info = check_member_conflicts_internal(
            db, user_id, request.start_date, request.end_date, project_id
        )
        if conflict_info['has_conflict']:
            conflicts.append({
                'user_id': user_id,
                'user_name': conflict_info.get('user_name', f'User {user_id}'),
                'conflicting_projects': conflict_info.get('conflicting_projects', [])
            })
            continue

        # 创建成员
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role_code=request.role_code,
            allocation_pct=request.allocation_pct,
            start_date=request.start_date,
            end_date=request.end_date,
            commitment_level=request.commitment_level,
            reporting_to_pm=request.reporting_to_pm,
            dept_manager_notified=False,  # 需要通知部门经理
            created_by=current_user.id
        )

        db.add(member)
        added_count += 1

        # 通知部门经理（异步，这里只标记）
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.department:
            # 标记需要通知，实际通知可以通过后台任务处理
            member.dept_manager_notified = False

    db.commit()

    return {
        'added_count': added_count,
        'skipped_count': skipped_count,
        'conflicts': conflicts,
        'message': f'成功添加 {added_count} 位成员，跳过 {skipped_count} 位，发现 {len(conflicts)} 个时间冲突'
    }
