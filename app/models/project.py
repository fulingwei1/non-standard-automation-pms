# -*- coding: utf-8 -*-
"""
项目管理模块模型 - 兼容层

此文件保持向后兼容性，从拆分后的模块导入所有模型。
原有功能已拆分为 models/project/ 目录下的模块。
"""

# 从项目模块导入所有模型
from app.models.project import (  # 客户相关; 项目核心; 项目生命周期; 项目团队; 项目财务; 项目文档和模板
    Customer,
    FinancialProjectCost,
    Machine,
    Project,
    ProjectCost,
    ProjectDocument,
    ProjectMember,
    ProjectMemberContribution,
    ProjectMilestone,
    ProjectPaymentPlan,
    ProjectStage,
    ProjectStatus,
    ProjectStatusLog,
    ProjectTemplate,
    ProjectTemplateVersion,
)

__all__ = [
    "Customer",
    "Project",
    "Machine",
    "ProjectStage",
    "ProjectStatus",
    "ProjectStatusLog",
    "ProjectMember",
    "ProjectMemberContribution",
    "ProjectMilestone",
    "ProjectPaymentPlan",
    "ProjectCost",
    "FinancialProjectCost",
    "ProjectDocument",
    "ProjectTemplate",
    "ProjectTemplateVersion",
]
