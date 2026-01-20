# -*- coding: utf-8 -*-
"""
报表数据生成服务 - 核心类和权限管理
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.user import User


class ReportDataGenerationCore:
    """报表数据生成服务核心类"""

    # 角色-报表权限矩阵
    ROLE_REPORT_MATRIX = {
        "PROJECT_MANAGER": ["PROJECT_WEEKLY", "PROJECT_MONTHLY", "COST_ANALYSIS", "RISK_REPORT"],
        "DEPARTMENT_MANAGER": ["DEPT_WEEKLY", "DEPT_MONTHLY", "WORKLOAD_ANALYSIS"],
        "ADMINISTRATIVE_MANAGER": ["COMPANY_MONTHLY", "DEPT_MONTHLY", "WORKLOAD_ANALYSIS"],
        "HR_MANAGER": ["WORKLOAD_ANALYSIS", "DEPT_MONTHLY"],
        "FINANCE_MANAGER": ["COST_ANALYSIS", "COMPANY_MONTHLY"],
        "ENGINEER": ["PROJECT_WEEKLY"],
        "SALES_MANAGER": ["SALES_FUNNEL", "CONTRACT_ANALYSIS"],
        "PROCUREMENT_MANAGER": ["PROCUREMENT_ANALYSIS", "MATERIAL_ANALYSIS"],
        "CUSTOM": ["CUSTOM"]
    }

    @staticmethod
    def check_permission(
        db: Session,
        user: User,
        report_type: str,
        role_code: Optional[str] = None
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
        user_roles = db.query(User).filter(User.id == user.id).first()
        if user_roles:
            # 这里假设用户模型有 roles 关系
            for user_role in getattr(user_roles, 'user_roles', []):
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
