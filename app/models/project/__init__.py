# -*- coding: utf-8 -*-
"""
项目管理模块 - 按业务域聚合
"""

# 项目核心
from .core import Machine, Project

# 客户相关
from .customer import Customer

# 项目文档和模板
from .document import ProjectDocument, ProjectTemplate, ProjectTemplateVersion

# 项目扩展模型（表拆分）
from .extensions import (
    ProjectERP,
    ProjectFinancial,
    ProjectImplementation,
    ProjectPresale,
    ProjectWarranty,
)

# 项目财务
from .financial import (
    FinancialProjectCost,
    ProjectCost,
    ProjectMilestone,
    ProjectPaymentPlan,
)

# 项目生命周期
from .lifecycle import ProjectStage, ProjectStatus, ProjectStatusLog

# 项目团队
from .team import ProjectMember, ProjectMemberContribution

# 资源计划
from .resource_plan import (
    AssignmentStatusEnum,
    ConflictSeverityEnum,
    ProjectStageResourcePlan,
    ResourceConflict,
)

# 风险历史
from .risk_history import ProjectRiskHistory, ProjectRiskSnapshot

__all__ = [
    # 客户相关
    "Customer",
    # 项目核心
    "Project",
    "Machine",
    # 项目生命周期
    "ProjectStage",
    "ProjectStatus",
    "ProjectStatusLog",
    # 项目团队
    "ProjectMember",
    "ProjectMemberContribution",
    # 项目财务
    "ProjectMilestone",
    "ProjectPaymentPlan",
    "ProjectCost",
    "FinancialProjectCost",
    # 项目文档和模板
    "ProjectDocument",
    "ProjectTemplate",
    "ProjectTemplateVersion",
    # 资源计划
    "ProjectStageResourcePlan",
    "ResourceConflict",
    "AssignmentStatusEnum",
    "ConflictSeverityEnum",
    # 项目扩展模型
    "ProjectFinancial",
    "ProjectERP",
    "ProjectWarranty",
    "ProjectImplementation",
    "ProjectPresale",
    # 风险历史
    "ProjectRiskHistory",
    "ProjectRiskSnapshot",
]
