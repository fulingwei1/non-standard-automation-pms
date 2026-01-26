# -*- coding: utf-8 -*-
"""
商务支持 Dashboard 适配器
"""

from datetime import date
from typing import List

from app.schemas.dashboard import (
    DashboardStatCard,
    DashboardWidget,
    DetailedDashboardResponse,
)
from app.services.dashboard_adapter import DashboardAdapter, register_dashboard


@register_dashboard
class BusinessSupportDashboardAdapter(DashboardAdapter):
    """商务支持工作台适配器"""

    @property
    def module_id(self) -> str:
        return "business_support"

    @property
    def module_name(self) -> str:
        return "商务支持"

    @property
    def supported_roles(self) -> List[str]:
        return ["business_support", "admin"]

    def get_stats(self) -> List[DashboardStatCard]:
        """获取统计卡片"""
        from app.services.business_support_dashboard_service import (
            calculate_acceptance_rate,
            calculate_invoice_rate,
            calculate_overdue_amount,
            calculate_pending_amount,
            count_active_bidding,
            count_active_contracts,
        )

        today = date.today()

        # 计算各项统计
        active_contracts = count_active_contracts(self.db)
        pending_amount = calculate_pending_amount(self.db, today)
        overdue_amount = calculate_overdue_amount(self.db, today)
        invoice_rate = calculate_invoice_rate(self.db, today)
        active_bidding = count_active_bidding(self.db)
        acceptance_rate = calculate_acceptance_rate(self.db)

        return [
            DashboardStatCard(
                key="active_contracts",
                label="进行中合同",
                value=active_contracts,
                unit="个",
                icon="contract",
                color="blue",
            ),
            DashboardStatCard(
                key="pending_amount",
                label="待回款金额",
                value=f"¥{pending_amount:,.2f}",
                icon="money",
                color="green",
            ),
            DashboardStatCard(
                key="overdue_amount",
                label="逾期款项",
                value=f"¥{overdue_amount:,.2f}",
                icon="warning",
                color="red",
            ),
            DashboardStatCard(
                key="invoice_rate",
                label="开票率",
                value=f"{invoice_rate:.1f}%",
                icon="invoice",
                color="purple",
            ),
            DashboardStatCard(
                key="active_bidding",
                label="进行中投标",
                value=active_bidding,
                unit="个",
                icon="bidding",
                color="orange",
            ),
            DashboardStatCard(
                key="acceptance_rate",
                label="验收率",
                value=f"{acceptance_rate:.1f}%",
                icon="check",
                color="cyan",
            ),
        ]

    def get_widgets(self) -> List[DashboardWidget]:
        """获取Widget列表"""
        from app.services.business_support_dashboard_service import (
            get_today_todos,
            get_urgent_tasks,
        )

        today = date.today()
        urgent_tasks = get_urgent_tasks(self.db, self.current_user.id, today)
        today_todos = get_today_todos(self.db, self.current_user.id, today)

        return [
            DashboardWidget(
                widget_id="urgent_tasks",
                widget_type="list",
                title="紧急任务",
                data=urgent_tasks,
                order=1,
                span=12,
            ),
            DashboardWidget(
                widget_id="today_todos",
                widget_type="list",
                title="今日待办",
                data=today_todos,
                order=2,
                span=12,
            ),
        ]

    def get_detailed_data(self) -> DetailedDashboardResponse:
        """获取详细数据"""
        from datetime import datetime

        from app.services.business_support_dashboard_service import (
            calculate_acceptance_rate,
            calculate_invoice_rate,
            calculate_overdue_amount,
            calculate_pending_amount,
            count_active_bidding,
            count_active_contracts,
            get_today_todos,
            get_urgent_tasks,
        )

        today = date.today()

        # 汇总数据
        active_contracts = count_active_contracts(self.db)
        pending_amount = calculate_pending_amount(self.db, today)
        overdue_amount = calculate_overdue_amount(self.db, today)
        invoice_rate = calculate_invoice_rate(self.db, today)
        active_bidding = count_active_bidding(self.db)
        acceptance_rate = calculate_acceptance_rate(self.db)

        summary = {
            "active_contracts_count": active_contracts,
            "pending_amount": float(pending_amount),
            "overdue_amount": float(overdue_amount),
            "invoice_rate": float(invoice_rate),
            "active_bidding_count": active_bidding,
            "acceptance_rate": float(acceptance_rate),
        }

        # 详细数据（可以包含更多业务逻辑）
        urgent_tasks = get_urgent_tasks(self.db, self.current_user.id, today)
        today_todos = get_today_todos(self.db, self.current_user.id, today)

        details = {
            "urgent_tasks": urgent_tasks,
            "today_todos": today_todos,
        }

        return DetailedDashboardResponse(
            module=self.module_id,
            module_name=self.module_name,
            summary=summary,
            details=details,
            generated_at=datetime.now(),
        )
