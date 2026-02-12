# -*- coding: utf-8 -*-
"""
人事管理 Dashboard 适配器
"""

from datetime import date, datetime, timedelta
from typing import List

from sqlalchemy import func

from app.models.organization import (
    Employee,
    EmployeeContract,
    EmployeeHrProfile,
    HrTransaction,
)
from app.schemas.dashboard import (
    DashboardListItem,
    DashboardStatCard,
    DashboardWidget,
    DetailedDashboardResponse,
)
from app.services.dashboard_adapter import DashboardAdapter, register_dashboard


@register_dashboard
class HrDashboardAdapter(DashboardAdapter):
    """人事管理工作台适配器"""

    @property
    def module_id(self) -> str:
        return "hr_management"

    @property
    def module_name(self) -> str:
        return "人事管理"

    @property
    def supported_roles(self) -> List[str]:
        return ["hr", "admin"]

    def get_stats(self) -> List[DashboardStatCard]:
        """获取统计卡片"""
        today = date.today()
        this_month_start = date(today.year, today.month, 1)

        # 在职员工总数
        total_active = (
            self.db.query(Employee).filter(Employee.is_active).count()
        )

        # 试用期员工数
        probation_count = (
            self.db.query(Employee)
            .filter(Employee.is_active, Employee.employment_type == "probation")
            .count()
        )

        # 本月入职
        onboarding_this_month = (
            self.db.query(HrTransaction)
            .filter(
                HrTransaction.transaction_type == "onboarding",
                HrTransaction.transaction_date >= this_month_start,
                HrTransaction.status.in_(["approved", "completed"]),
            )
            .count()
        )

        # 本月离职
        resignation_this_month = (
            self.db.query(HrTransaction)
            .filter(
                HrTransaction.transaction_type == "resignation",
                HrTransaction.transaction_date >= this_month_start,
                HrTransaction.status.in_(["approved", "completed"]),
            )
            .count()
        )

        # 待处理事务
        pending_transactions = (
            self.db.query(HrTransaction)
            .filter(HrTransaction.status == "pending")
            .count()
        )

        # 即将到期合同（60天内）
        expiring_contracts = (
            self.db.query(EmployeeContract)
            .filter(
                EmployeeContract.status == "active",
                EmployeeContract.end_date <= today + timedelta(days=60),
                EmployeeContract.end_date >= today,
            )
            .count()
        )

        # 即将转正（30天内）
        confirmation_due = (
            self.db.query(Employee)
            .join(EmployeeHrProfile)
            .filter(
                Employee.is_active,
                Employee.employment_type == "probation",
                EmployeeHrProfile.probation_end_date <= today + timedelta(days=30),
                EmployeeHrProfile.probation_end_date >= today,
            )
            .count()
        )

        return [
            DashboardStatCard(
                key="total_active",
                label="在职员工",
                value=total_active,
                unit="人",
                icon="users",
                color="blue",
            ),
            DashboardStatCard(
                key="probation_count",
                label="试用期员工",
                value=probation_count,
                unit="人",
                icon="probation",
                color="orange",
            ),
            DashboardStatCard(
                key="onboarding_this_month",
                label="本月入职",
                value=onboarding_this_month,
                unit="人",
                trend=(
                    onboarding_this_month - resignation_this_month
                    if resignation_this_month
                    else 0
                ),
                icon="join",
                color="green",
            ),
            DashboardStatCard(
                key="pending_transactions",
                label="待处理事务",
                value=pending_transactions,
                unit="项",
                icon="pending",
                color="red",
            ),
            DashboardStatCard(
                key="expiring_contracts",
                label="即将到期合同",
                value=expiring_contracts,
                unit="个",
                icon="contract-expire",
                color="purple",
            ),
            DashboardStatCard(
                key="confirmation_due",
                label="即将转正",
                value=confirmation_due,
                unit="人",
                icon="confirm",
                color="cyan",
            ),
        ]

    def get_widgets(self) -> List[DashboardWidget]:
        """获取Widget列表"""
        today = date.today()

        # 待转正员工列表
        employees = (
            self.db.query(Employee)
            .join(EmployeeHrProfile)
            .filter(
                Employee.is_active,
                Employee.employment_type == "probation",
                EmployeeHrProfile.probation_end_date <= today + timedelta(days=60),
            )
            .order_by(EmployeeHrProfile.probation_end_date.asc())
            .limit(10)
            .all()
        )

        pending_confirmations = []
        for emp in employees:
            profile = emp.hr_profile
            days_until = (
                (profile.probation_end_date - today).days
                if profile and profile.probation_end_date
                else 0
            )
            pending_confirmations.append(
                DashboardListItem(
                    id=emp.id,
                    title=emp.name,
                    subtitle=f"{emp.department} - {profile.position if profile else ''}",
                    status="urgent" if days_until <= 7 else "normal",
                    date=profile.probation_end_date if profile else None,
                    extra={
                        "employee_code": emp.employee_code,
                        "days_until": days_until,
                    },
                )
            )

        return [
            DashboardWidget(
                widget_id="pending_confirmations",
                widget_type="list",
                title="待转正员工",
                data=pending_confirmations,
                order=1,
                span=24,
            )
        ]

    def get_detailed_data(self) -> DetailedDashboardResponse:
        """获取详细数据"""
        today = date.today()
        date(today.year, today.month, 1)

        # 汇总数据
        stats_cards = self.get_stats()
        summary = {card.key: card.value for card in stats_cards}

        # 按部门统计人数
        dept_stats = (
            self.db.query(
                EmployeeHrProfile.dept_level1, func.count(EmployeeHrProfile.id)
            )
            .join(Employee)
            .filter(Employee.is_active)
            .group_by(EmployeeHrProfile.dept_level1)
            .all()
        )

        by_department = [
            {"department": d[0] or "未分配", "count": d[1]} for d in dept_stats
        ]

        details = {"by_department": by_department}

        return DetailedDashboardResponse(
            module=self.module_id,
            module_name=self.module_name,
            summary=summary,
            details=details,
            generated_at=datetime.now(),
        )
