# -*- coding: utf-8 -*-
"""
项目匹配模块
提供用户项目查询和关键词提取功能
"""

from typing import Any, Dict, List

from app.models.project import Project, ProjectMember
from app.models.timesheet import Timesheet


class ProjectMatchingMixin:
    """项目匹配功能混入类"""

    def _get_user_projects(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户参与的项目列表

        Returns:
            项目列表，包含项目ID、编码、名称等信息
        """
        # 查询用户作为成员的项目
        members = self.db.query(ProjectMember).filter(
            ProjectMember.user_id == user_id,
            ProjectMember.is_active == True
        ).all()

        project_ids = [m.project_id for m in members]

        # 查询项目详情
        projects = self.db.query(Project).filter(
            Project.id.in_(project_ids),
            Project.is_active == True
        ).all()

        # 构建项目列表（包含历史填报频率，用于智能推荐）
        project_list = []
        for project in projects:
            # 查询用户在该项目的历史工时记录数（用于推荐排序）
            timesheet_count = self.db.query(Timesheet).filter(
                Timesheet.user_id == user_id,
                Timesheet.project_id == project.id,
                Timesheet.status == 'APPROVED'
            ).count()

            project_list.append({
                'id': project.id,
                'code': project.project_code,
                'name': project.project_name,
                'timesheet_count': timesheet_count,  # 历史填报次数，用于推荐排序
                'keywords': self._extract_project_keywords(project)  # 提取关键词用于匹配
            })

        # 按历史填报频率排序（最常用的项目排在前面）
        project_list.sort(key=lambda x: x['timesheet_count'], reverse=True)

        return project_list

    def _extract_project_keywords(self, project: Project) -> List[str]:
        """提取项目关键词用于匹配"""
        keywords = []

        # 项目名称关键词
        if project.project_name:
            # 提取项目名称中的关键词（去除常见词）
            name_words = project.project_name.replace('设备', '').replace('测试', '').replace('系统', '')
            keywords.extend([w for w in name_words.split() if len(w) > 1])

        # 项目编码
        if project.project_code:
            keywords.append(project.project_code)

        # 客户名称（如果有）
        if project.customer_name:
            keywords.append(project.customer_name)

        return keywords

    def get_user_projects_for_suggestion(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户参与的项目列表（用于前端显示建议）

        Returns:
            项目列表，包含ID、编码、名称、历史填报次数
        """
        return self._get_user_projects(user_id)
