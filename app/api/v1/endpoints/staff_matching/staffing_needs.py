# -*- coding: utf-8 -*-
"""
人员需求 API端点
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.staff_matching import MesProjectStaffingNeed
from app.models.user import User
from app.schemas import staff_matching as schemas
from app.common.pagination import PaginationParams, get_pagination_query
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/", response_model=List[schemas.StaffingNeedResponse])
def list_staffing_needs(
    project_id: Optional[int] = Query(None, description="项目ID"),
    status: Optional[str] = Query(None, description="状态筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取人员需求列表"""
    query = db.query(MesProjectStaffingNeed)

    if project_id:
        query = query.filter(MesProjectStaffingNeed.project_id == project_id)
    if status:
        query = query.filter(MesProjectStaffingNeed.status == status)
    if priority:
        query = query.filter(MesProjectStaffingNeed.priority == priority)

    needs = apply_pagination(query.order_by(
        MesProjectStaffingNeed.priority,
        MesProjectStaffingNeed.created_at.desc()
    ), pagination.offset, pagination.limit).all()

    result = []
    for need in needs:
        result.append({
            'id': need.id,
            'project_id': need.project_id,
            'role_code': need.role_code,
            'role_name': need.role_name,
            'headcount': need.headcount,
            'required_skills': need.required_skills,
            'preferred_skills': need.preferred_skills,
            'required_domains': need.required_domains,
            'required_attitudes': need.required_attitudes,
            'min_level': need.min_level,
            'priority': need.priority,
            'start_date': need.start_date,
            'end_date': need.end_date,
            'allocation_pct': need.allocation_pct,
            'status': need.status,
            'requester_id': need.requester_id,
            'filled_count': need.filled_count,
            'remark': need.remark,
            'created_at': need.created_at,
            'project_name': need.project.name if need.project else None,
            'requester_name': need.requester.real_name if need.requester else None
        })

    return result


@router.get("/{need_id}", response_model=schemas.StaffingNeedResponse)
def get_staffing_need(
    need_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取人员需求详情"""
    need = get_or_404(db, MesProjectStaffingNeed, need_id, "人员需求不存在")

    return {
        'id': need.id,
        'project_id': need.project_id,
        'role_code': need.role_code,
        'role_name': need.role_name,
        'headcount': need.headcount,
        'required_skills': need.required_skills,
        'preferred_skills': need.preferred_skills,
        'required_domains': need.required_domains,
        'required_attitudes': need.required_attitudes,
        'min_level': need.min_level,
        'priority': need.priority,
        'start_date': need.start_date,
        'end_date': need.end_date,
        'allocation_pct': need.allocation_pct,
        'status': need.status,
        'requester_id': need.requester_id,
        'filled_count': need.filled_count,
        'remark': need.remark,
        'created_at': need.created_at,
        'project_name': need.project.name if need.project else None,
        'requester_name': need.requester.real_name if need.requester else None
    }


@router.post("/", response_model=schemas.StaffingNeedResponse, status_code=status.HTTP_201_CREATED)
def create_staffing_need(
    need_data: schemas.StaffingNeedCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:create"))
):
    """创建人员需求"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == need_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 转换技能要求为JSON
    required_skills_json = [req.model_dump() for req in need_data.required_skills]
    preferred_skills_json = [req.model_dump() for req in need_data.preferred_skills] if need_data.preferred_skills else None
    required_domains_json = [req.model_dump() for req in need_data.required_domains] if need_data.required_domains else None
    required_attitudes_json = [req.model_dump() for req in need_data.required_attitudes] if need_data.required_attitudes else None

    need = MesProjectStaffingNeed(
        project_id=need_data.project_id,
        role_code=need_data.role_code,
        role_name=need_data.role_name,
        headcount=need_data.headcount,
        required_skills=required_skills_json,
        preferred_skills=preferred_skills_json,
        required_domains=required_domains_json,
        required_attitudes=required_attitudes_json,
        min_level=need_data.min_level,
        priority=need_data.priority,
        start_date=need_data.start_date,
        end_date=need_data.end_date,
        allocation_pct=need_data.allocation_pct,
        requester_id=current_user.id,
        remark=need_data.remark
    )
    db.add(need)
    db.commit()
    db.refresh(need)

    return {
        'id': need.id,
        'project_id': need.project_id,
        'role_code': need.role_code,
        'role_name': need.role_name,
        'headcount': need.headcount,
        'required_skills': need.required_skills,
        'preferred_skills': need.preferred_skills,
        'required_domains': need.required_domains,
        'required_attitudes': need.required_attitudes,
        'min_level': need.min_level,
        'priority': need.priority,
        'start_date': need.start_date,
        'end_date': need.end_date,
        'allocation_pct': need.allocation_pct,
        'status': need.status,
        'requester_id': need.requester_id,
        'filled_count': need.filled_count,
        'remark': need.remark,
        'created_at': need.created_at,
        'project_name': project.name,
        'requester_name': current_user.real_name
    }


@router.put("/{need_id}", response_model=schemas.StaffingNeedResponse)
def update_staffing_need(
    need_id: int,
    need_data: schemas.StaffingNeedUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:update"))
):
    """更新人员需求"""
    need = get_or_404(db, MesProjectStaffingNeed, need_id, "人员需求不存在")

    update_data = need_data.model_dump(exclude_unset=True)

    # 转换技能要求
    if 'required_skills' in update_data and update_data['required_skills']:
        update_data['required_skills'] = [req.model_dump() if hasattr(req, 'model_dump') else req for req in update_data['required_skills']]
    if 'preferred_skills' in update_data and update_data['preferred_skills']:
        update_data['preferred_skills'] = [req.model_dump() if hasattr(req, 'model_dump') else req for req in update_data['preferred_skills']]
    if 'required_domains' in update_data and update_data['required_domains']:
        update_data['required_domains'] = [req.model_dump() if hasattr(req, 'model_dump') else req for req in update_data['required_domains']]
    if 'required_attitudes' in update_data and update_data['required_attitudes']:
        update_data['required_attitudes'] = [req.model_dump() if hasattr(req, 'model_dump') else req for req in update_data['required_attitudes']]

    for field, value in update_data.items():
        setattr(need, field, value)

    db.commit()
    db.refresh(need)

    return {
        'id': need.id,
        'project_id': need.project_id,
        'role_code': need.role_code,
        'role_name': need.role_name,
        'headcount': need.headcount,
        'required_skills': need.required_skills,
        'preferred_skills': need.preferred_skills,
        'required_domains': need.required_domains,
        'required_attitudes': need.required_attitudes,
        'min_level': need.min_level,
        'priority': need.priority,
        'start_date': need.start_date,
        'end_date': need.end_date,
        'allocation_pct': need.allocation_pct,
        'status': need.status,
        'requester_id': need.requester_id,
        'filled_count': need.filled_count,
        'remark': need.remark,
        'created_at': need.created_at,
        'project_name': need.project.name if need.project else None,
        'requester_name': need.requester.real_name if need.requester else None
    }


@router.delete("/{need_id}")
def cancel_staffing_need(
    need_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """取消人员需求"""
    need = get_or_404(db, MesProjectStaffingNeed, need_id, "人员需求不存在")

    need.status = 'CANCELLED'
    db.commit()
    return {"message": "人员需求已取消"}
