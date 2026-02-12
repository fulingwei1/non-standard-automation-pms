# -*- coding: utf-8 -*-
"""
人员智能匹配服务 - 员工档案聚合
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.project import ProjectMember
from app.models.staff_matching import (
    HrEmployeeProfile,
    HrEmployeeTagEvaluation,
    HrProjectPerformance,
    HrTagDict,
    TagTypeEnum,
)
from app.models.user import User

from .base import StaffMatchingBase


class ProfileAggregator(StaffMatchingBase):
    """员工档案聚合器"""

    @classmethod
    def aggregate_employee_profile(cls, db: Session, employee_id: int) -> HrEmployeeProfile:
        """
        聚合员工标签到档案
        """
        # 获取或创建档案
        profile = db.query(HrEmployeeProfile).filter(
            HrEmployeeProfile.employee_id == employee_id
        ).first()

        if not profile:
            profile = HrEmployeeProfile(employee_id=employee_id)
            db.add(profile)

        # 按类型聚合标签
        tag_types = [
            (TagTypeEnum.SKILL.value, 'skill_tags'),
            (TagTypeEnum.DOMAIN.value, 'domain_tags'),
            (TagTypeEnum.ATTITUDE.value, 'attitude_tags'),
            (TagTypeEnum.CHARACTER.value, 'character_tags'),
            (TagTypeEnum.SPECIAL.value, 'special_tags')
        ]

        for tag_type, field_name in tag_types:
            evals = db.query(HrEmployeeTagEvaluation).join(HrTagDict).filter(
                HrEmployeeTagEvaluation.employee_id == employee_id,
                HrEmployeeTagEvaluation.is_valid,
                HrTagDict.tag_type == tag_type
            ).all()

            tags_data = []
            for eval in evals:
                tags_data.append({
                    'tag_id': eval.tag_id,
                    'tag_code': eval.tag.tag_code if eval.tag else '',
                    'tag_name': eval.tag.tag_name if eval.tag else '',
                    'score': eval.score,
                    'weight': float(eval.tag.weight) if eval.tag else 1.0
                })

            setattr(profile, field_name, tags_data)

        # 计算态度聚合分
        attitude_evals = db.query(HrEmployeeTagEvaluation).join(HrTagDict).filter(
            HrEmployeeTagEvaluation.employee_id == employee_id,
            HrEmployeeTagEvaluation.is_valid,
            HrTagDict.tag_type == TagTypeEnum.ATTITUDE.value
        ).all()

        if attitude_evals:
            avg_attitude = sum(e.score for e in attitude_evals) / len(attitude_evals)
            profile.attitude_score = Decimal(str(round((avg_attitude / 5.0) * 100, 2)))

        # 计算质量聚合分（从项目绩效）
        performances = db.query(HrProjectPerformance).filter(
            HrProjectPerformance.employee_id == employee_id
        ).all()

        if performances:
            quality_scores = [float(p.quality_score) for p in performances if p.quality_score]
            if quality_scores:
                profile.quality_score = Decimal(str(round(sum(quality_scores) / len(quality_scores), 2)))

            # 统计项目数
            profile.total_projects = len(performances)

            # 计算平均绩效
            perf_scores = [float(p.performance_score) for p in performances if p.performance_score]
            if perf_scores:
                profile.avg_performance_score = Decimal(str(round(sum(perf_scores) / len(perf_scores), 2)))

        profile.profile_updated_at = datetime.now()
        db.commit()

        return profile

    @classmethod
    def update_employee_workload(cls, db: Session, employee_id: int) -> None:
        """
        更新员工当前工作负载
        基于ProjectMember的分配比例
        """
        # 获取或创建档案
        profile = db.query(HrEmployeeProfile).filter(
            HrEmployeeProfile.employee_id == employee_id
        ).first()

        if not profile:
            profile = HrEmployeeProfile(employee_id=employee_id)
            db.add(profile)

        # 获取员工关联的User
        user = db.query(User).filter(User.employee_id == employee_id).first()

        if user:
            # 计算当前活跃项目的分配比例总和
            today = datetime.now().date()
            active_assignments = db.query(ProjectMember).filter(
                ProjectMember.user_id == user.id,
                ProjectMember.is_active,
                or_(
                    ProjectMember.end_date is None,
                    ProjectMember.end_date >= today
                )
            ).all()

            total_allocation = sum(
                float(a.allocation_pct or 0) for a in active_assignments
            )
            profile.current_workload_pct = Decimal(str(min(100, total_allocation)))

            # 计算可用工时 (假设每月160小时)
            available_pct = max(0, 100 - total_allocation)
            profile.available_hours = Decimal(str(round(160 * available_pct / 100, 2)))

        profile.profile_updated_at = datetime.now()
        db.commit()
