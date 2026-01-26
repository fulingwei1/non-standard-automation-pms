# -*- coding: utf-8 -*-
"""
跨部门协作评价服务 - 合作人员选择器
"""
import secrets
from typing import List

from app.models.engineer_performance import EngineerProfile
from app.models.performance import PerformancePeriod
from app.models.project import Project, ProjectMember


class CollaboratorSelector:
    """合作人员选择器"""

    def __init__(self, db, service):
        self.db = db
        self.service = service

    def auto_select_collaborators(
        self,
        engineer_id: int,
        period_id: int,
        target_count: int = 5
    ) -> List[int]:
        """
        自动匿名抽取合作人员

        Args:
            engineer_id: 被评价工程师ID
            period_id: 考核周期ID
            target_count: 目标抽取数量（默认5人）

        Returns:
            合作人员ID列表（已匿名处理，不包含被评价人）
        """
        # 获取考核周期
        period = self.db.query(PerformancePeriod).filter(
            PerformancePeriod.id == period_id
        ).first()

        if not period:
            raise ValueError(f"考核周期不存在: {period_id}")

        # 获取工程师档案
        profile = self.db.query(EngineerProfile).filter(
            EngineerProfile.user_id == engineer_id
        ).first()

        if not profile:
            raise ValueError(f"工程师档案不存在: {engineer_id}")

        engineer_job_type = profile.job_type

        # 获取工程师在考核周期内参与的项目
        projects = self.db.query(Project).join(
            ProjectMember, Project.id == ProjectMember.project_id
        ).filter(
            ProjectMember.user_id == engineer_id,
            Project.created_at.between(period.start_date, period.end_date)
        ).all()

        if not projects:
            return []

        project_ids = [p.id for p in projects]

        # 获取所有合作人员（同项目但不同岗位）
        collaborators = self._get_collaborators_from_projects(
            engineer_id, engineer_job_type, project_ids
        )

        if not collaborators:
            return []

        # 去重
        unique_collaborators = list(set(collaborators))

        # 随机抽取（如果数量不足则全部抽取）
        if len(unique_collaborators) <= target_count:
            selected = unique_collaborators
        else:
            selected = secrets.SystemRandom().sample(unique_collaborators, target_count)

        return selected

    def _get_collaborators_from_projects(
        self,
        engineer_id: int,
        engineer_job_type: str,
        project_ids: List[int]
    ) -> List[int]:
        """
        从项目中获取合作人员

        根据岗位类型识别跨部门合作：
        - 机械工程师：抽取电气、测试工程师
        - 电气工程师：抽取机械、测试工程师
        - 测试工程师：抽取机械、电气工程师
        """
        # 获取所有项目成员
        all_members = self.db.query(ProjectMember).filter(
            ProjectMember.project_id.in_(project_ids),
            ProjectMember.user_id != engineer_id
        ).all()

        # 获取这些成员的岗位类型
        user_ids = [m.user_id for m in all_members]
        profiles = self.db.query(EngineerProfile).filter(
            EngineerProfile.user_id.in_(user_ids)
        ).all()

        # 构建用户ID到岗位类型的映射
        user_job_type_map = {p.user_id: p.job_type for p in profiles}

        # 根据岗位类型筛选合作人员
        target_job_types = self._get_target_job_types(engineer_job_type)

        collaborators = []
        for member in all_members:
            job_type = user_job_type_map.get(member.user_id)
            if job_type and job_type in target_job_types:
                collaborators.append(member.user_id)

        return collaborators

    def _get_target_job_types(self, engineer_job_type: str) -> List[str]:
        """根据工程师岗位类型获取目标合作岗位类型"""
        if engineer_job_type == 'mechanical':
            return ['electrical', 'test']
        elif engineer_job_type == 'electrical':
            return ['mechanical', 'test']
        elif engineer_job_type == 'test':
            return ['mechanical', 'electrical']
        elif engineer_job_type == 'solution':
            # 方案工程师可以与所有岗位合作
            return ['mechanical', 'electrical', 'test']
        else:
            # 默认返回所有岗位
            return ['mechanical', 'electrical', 'test']
