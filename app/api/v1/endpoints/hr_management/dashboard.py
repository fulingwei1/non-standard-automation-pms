# -*- coding: utf-8 -*-
"""
人事仪表板统计端点
"""

from datetime import date, timedelta
from typing import Any, Dict, List

from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.common.dashboard.base import BaseDashboardEndpoint
from app.common.date_range import get_month_range
from app.core import security
from app.models.organization import (
    ContractReminder,
    Employee,
    EmployeeContract,
    EmployeeHrProfile,
    HrTransaction,
)
from app.models.user import User


class HrManagementDashboardEndpoint(BaseDashboardEndpoint):
    """人事管理Dashboard端点"""
    
    module_name = "hr_management"
    permission_required = "hr:read"
    
    def __init__(self):
        """初始化路由，添加额外端点"""
        super().__init__()
        # 添加待转正员工列表端点
        self.router.add_api_route(
            "/dashboard/pending-confirmations",
            self._get_pending_confirmations_handler,
            methods=["GET"],
            summary="获取待转正员工列表"
        )
    
    def get_dashboard_data(
        self,
        db: Session,
        current_user: User
    ) -> Dict[str, Any]:
        """获取人事管理仪表板概览数据"""
        today = date.today()
        this_month_start, _ = get_month_range(today)

        # 在职员工总数
        total_active = db.query(Employee).filter(Employee.is_active).count()

        # 试用期员工数
        probation_count = db.query(Employee).filter(
            Employee.is_active,
            Employee.employment_type == "probation"
        ).count()

        # 本月入职
        onboarding_this_month = db.query(HrTransaction).filter(
            HrTransaction.transaction_type == "onboarding",
            HrTransaction.transaction_date >= this_month_start,
            HrTransaction.status.in_(["approved", "completed"])
        ).count()

        # 本月离职
        resignation_this_month = db.query(HrTransaction).filter(
            HrTransaction.transaction_type == "resignation",
            HrTransaction.transaction_date >= this_month_start,
            HrTransaction.status.in_(["approved", "completed"])
        ).count()

        # 待处理事务
        pending_transactions = db.query(HrTransaction).filter(
            HrTransaction.status == "pending"
        ).count()

        # 即将到期合同（60天内）
        expiring_contracts = db.query(EmployeeContract).filter(
            EmployeeContract.status == "active",
            EmployeeContract.end_date <= today + timedelta(days=60),
            EmployeeContract.end_date >= today
        ).count()

        # 待处理合同提醒
        pending_reminders = db.query(ContractReminder).filter(
            ContractReminder.status == "pending"
        ).count()

        # 即将转正（30天内）
        confirmation_due = db.query(Employee).join(EmployeeHrProfile).filter(
            Employee.is_active,
            Employee.employment_type == "probation",
            EmployeeHrProfile.probation_end_date <= today + timedelta(days=30),
            EmployeeHrProfile.probation_end_date >= today
        ).count()

        # 按部门统计人数
        dept_stats = db.query(
            EmployeeHrProfile.dept_level1,
            func.count(EmployeeHrProfile.id)
        ).join(Employee).filter(
            Employee.is_active
        ).group_by(EmployeeHrProfile.dept_level1).all()

        # 使用基类方法创建统计卡片
        stats = [
            self.create_stat_card(
                key="total_active",
                label="在职员工",
                value=total_active,
                unit="人",
                icon="employee"
            ),
            self.create_stat_card(
                key="probation_count",
                label="试用期员工",
                value=probation_count,
                unit="人",
                icon="probation"
            ),
            self.create_stat_card(
                key="onboarding_this_month",
                label="本月入职",
                value=onboarding_this_month,
                unit="人",
                icon="onboarding"
            ),
            self.create_stat_card(
                key="resignation_this_month",
                label="本月离职",
                value=resignation_this_month,
                unit="人",
                icon="resignation"
            ),
            self.create_stat_card(
                key="pending_transactions",
                label="待处理事务",
                value=pending_transactions,
                unit="项",
                icon="pending",
                color="warning"
            ),
            self.create_stat_card(
                key="expiring_contracts",
                label="即将到期合同",
                value=expiring_contracts,
                unit="份",
                icon="contract",
                color="warning"
            ),
        ]

        return {
            "stats": stats,
            "total_active": total_active,
            "probation_count": probation_count,
            "onboarding_this_month": onboarding_this_month,
            "resignation_this_month": resignation_this_month,
            "pending_transactions": pending_transactions,
            "expiring_contracts_60days": expiring_contracts,
            "pending_contract_reminders": pending_reminders,
            "confirmation_due_30days": confirmation_due,
            "by_department": [
                {"department": d[0] or "未分配", "count": d[1]}
                for d in dept_stats
            ],
            "alerts": {
                "total": pending_transactions + pending_reminders + confirmation_due,
                "transactions": pending_transactions,
                "contracts": pending_reminders,
                "confirmations": confirmation_due,
            }
        }
    
    def _get_pending_confirmations_handler(
        self,
        db: Session = Depends(deps.get_db),
        current_user: User = Depends(security.require_permission("hr:read")),
    ) -> List[Dict[str, Any]]:
        """获取待转正员工列表"""
        today = date.today()

        employees = db.query(Employee).join(EmployeeHrProfile).filter(
            Employee.is_active,
            Employee.employment_type == "probation",
            EmployeeHrProfile.probation_end_date <= today + timedelta(days=60)
        ).order_by(EmployeeHrProfile.probation_end_date.asc()).limit(20).all()

        result = []
        for emp in employees:
            profile = emp.hr_profile
            days_until = (profile.probation_end_date - today).days if profile and profile.probation_end_date else 0
            result.append(
                self.create_list_item(
                    id=emp.id,
                    title=emp.name,
                    subtitle=f"{emp.employee_code} - {emp.department}",
                    status="overdue" if days_until < 0 else ("urgent" if days_until <= 7 else "normal"),
                    event_date=profile.probation_end_date if profile else None,
                    extra={
                        "employee_code": emp.employee_code,
                        "position": profile.position if profile else None,
                        "hire_date": str(profile.hire_date) if profile and profile.hire_date else None,
                        "days_until_confirmation": days_until,
                    }
                )
            )

        return result


# 创建端点实例并获取路由
dashboard_endpoint = HrManagementDashboardEndpoint()
router = dashboard_endpoint.router
