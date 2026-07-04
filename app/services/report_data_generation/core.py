# -*- coding: utf-8 -*-
"""
报表数据生成服务 - 核心类和权限管理
"""

from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.user import User


IMPLEMENTED_REPORT_TYPE_DEFINITIONS: Dict[str, Dict[str, str]] = {
    "PROJECT_WEEKLY": {
        "type": "PROJECT_WEEKLY",
        "name": "项目周报",
        "description": "项目每周进展报告",
    },
    "PROJECT_MONTHLY": {
        "type": "PROJECT_MONTHLY",
        "name": "项目月报",
        "description": "项目每月进展报告",
    },
    "DEPT_WEEKLY": {
        "type": "DEPT_WEEKLY",
        "name": "部门周报",
        "description": "部门每周工作汇总",
    },
    "DEPT_MONTHLY": {
        "type": "DEPT_MONTHLY",
        "name": "部门月报",
        "description": "部门每月工作汇总",
    },
    "COST_ANALYSIS": {
        "type": "COST_ANALYSIS",
        "name": "成本分析",
        "description": "项目成本分析报告",
    },
    "WORKLOAD_ANALYSIS": {
        "type": "WORKLOAD_ANALYSIS",
        "name": "负荷分析",
        "description": "人员负荷分析报告",
    },
}

IMPLEMENTED_REPORT_TYPES = tuple(IMPLEMENTED_REPORT_TYPE_DEFINITIONS.keys())


class ReportDataGenerationCore:
    """报表数据生成服务核心类"""

    IMPLEMENTED_REPORT_TYPES = IMPLEMENTED_REPORT_TYPES
    IMPLEMENTED_REPORT_TYPE_DEFINITIONS = IMPLEMENTED_REPORT_TYPE_DEFINITIONS

    # 角色-报表权限矩阵
    ROLE_REPORT_MATRIX = {
        "PROJECT_MANAGER": ["PROJECT_WEEKLY", "PROJECT_MONTHLY", "COST_ANALYSIS"],
        "DEPARTMENT_MANAGER": ["DEPT_WEEKLY", "DEPT_MONTHLY", "WORKLOAD_ANALYSIS"],
        "ADMINISTRATIVE_MANAGER": ["DEPT_MONTHLY", "WORKLOAD_ANALYSIS"],
        "HR_MANAGER": ["WORKLOAD_ANALYSIS", "DEPT_MONTHLY"],
        "FINANCE_MANAGER": ["COST_ANALYSIS"],
        "ENGINEER": ["PROJECT_WEEKLY"],
        "SALES_MANAGER": [],
        "PROCUREMENT_MANAGER": [],
        "CUSTOM": [],
    }

    @staticmethod
    def check_permission(
        db: Session, user: User, report_type: str, role_code: Optional[str] = None
    ) -> bool:
        """
        检查用户是否有权限生成指定类型的报表

        Args:
            db: 数据库会话
            user: 当前用户
            report_type: 报表类型
            role_code: 指定角色代码（用于多角色场景）

        Returns:
            是否有权限
        """
        # 管理员有所有权限
        if user.is_superuser:
            return True

        # 获取用户的角色代码
        user_role_codes = []
        # User.roles 是 lazy="dynamic" 关系，需要调用 .all() 或遍历
        from app.models.user import Role, UserRole

        user_roles = (
            db.query(UserRole).join(Role).filter(UserRole.user_id == user.id, Role.is_active).all()
        )
        for user_role in user_roles:
            if user_role.role and user_role.role.is_active:
                user_role_codes.append(user_role.role.role_code)

        # 如果没有角色，不允许
        if not user_role_codes:
            return False

        # 检查角色-报表矩阵
        for role_code in user_role_codes:
            allowed_reports = ReportDataGenerationCore.ROLE_REPORT_MATRIX.get(role_code, [])
            if report_type in allowed_reports:
                return True

        return False

    @staticmethod
    def get_allowed_reports(user_role_code: str) -> List[str]:
        """
        获取角色允许生成的报表类型

        Args:
            user_role_code: 用户角色代码

        Returns:
            允许的报表类型列表
        """
        return ReportDataGenerationCore.ROLE_REPORT_MATRIX.get(user_role_code, [])
