# -*- coding: utf-8 -*-
"""
ECN模块公共工具函数

包含编码生成、公共辅助函数等
"""

from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.project import Project, Machine
from app.models.ecn import Ecn
from app.schemas.ecn import EcnResponse, EcnListResponse


def generate_ecn_no(db: Session) -> str:
    """生成ECN编号：ECN-yymmdd-xxx"""
    from app.utils.number_generator import generate_sequential_no
    from app.models.ecn import Ecn

    return generate_sequential_no(
        db=db,
        model_class=Ecn,
        no_field='ecn_no',
        prefix='ECN',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def build_ecn_response(db: Session, ecn: Ecn) -> EcnResponse:
    """构建ECN详情响应"""
    project_name = None
    if ecn.project_id:
        project = db.query(Project).filter(Project.id == ecn.project_id).first()
        project_name = project.project_name if project else None

    machine_name = None
    if ecn.machine_id:
        machine = db.query(Machine).filter(Machine.id == ecn.machine_id).first()
        machine_name = machine.machine_name if machine else None

    applicant_name = None
    if ecn.applicant_id:
        applicant = db.query(User).filter(User.id == ecn.applicant_id).first()
        applicant_name = applicant.real_name or applicant.username if applicant else None

    return EcnResponse(
        id=ecn.id,
        ecn_no=ecn.ecn_no,
        ecn_title=ecn.ecn_title,
        ecn_type=ecn.ecn_type,
        source_type=ecn.source_type,
        source_no=ecn.source_no,
        project_id=ecn.project_id,
        project_name=project_name,
        machine_id=ecn.machine_id,
        machine_name=machine_name,
        change_reason=ecn.change_reason,
        change_description=ecn.change_description,
        change_scope=ecn.change_scope,
        priority=ecn.priority,
        urgency=ecn.urgency,
        cost_impact=ecn.cost_impact or Decimal("0"),
        schedule_impact_days=ecn.schedule_impact_days or 0,
        status=ecn.status,
        current_step=ecn.current_step,
        applicant_id=ecn.applicant_id,
        applicant_name=applicant_name,
        applied_at=ecn.applied_at,
        approval_result=ecn.approval_result,
        created_at=ecn.created_at,
        updated_at=ecn.updated_at
    )


def build_ecn_list_response(db: Session, ecn: Ecn) -> EcnListResponse:
    """构建ECN列表项响应"""
    project_name = None
    if ecn.project_id:
        project = db.query(Project).filter(Project.id == ecn.project_id).first()
        project_name = project.project_name if project else None

    applicant_name = None
    if ecn.applicant_id:
        applicant = db.query(User).filter(User.id == ecn.applicant_id).first()
        applicant_name = applicant.real_name or applicant.username if applicant else None

    return EcnListResponse(
        id=ecn.id,
        ecn_no=ecn.ecn_no,
        ecn_title=ecn.ecn_title,
        ecn_type=ecn.ecn_type,
        project_id=ecn.project_id,
        project_name=project_name,
        status=ecn.status,
        priority=ecn.priority,
        applicant_name=applicant_name,
        applied_at=ecn.applied_at,
        created_at=ecn.created_at
    )


def get_user_display_name(db: Session, user_id: Optional[int]) -> Optional[str]:
    """获取用户显示名称"""
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    return user.real_name or user.username if user else None
