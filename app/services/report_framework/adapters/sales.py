# -*- coding: utf-8 -*-
"""
销售报表适配器

将销售报表服务适配到统一报表框架
"""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.report_framework.adapters.base import BaseReportAdapter


class SalesReportAdapter(BaseReportAdapter):
    """销售报表适配器"""
    
    def get_report_code(self) -> str:
        """返回报表代码"""
        return "SALES_MONTHLY"
    
    def generate_data(
        self,
        params: Dict[str, Any],
        user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        生成销售报表数据
        
        Args:
            params: 报表参数（包含month字段，格式：YYYY-MM）
            user: 当前用户
            
        Returns:
            报表数据字典
        """
        from datetime import date, timedelta
        from decimal import Decimal
        from sqlalchemy import func, text

        from app.models.business_support import BiddingProject, SalesOrder
        from app.models.sales import Contract, Invoice

        # 解析月份
        month_str = params.get("month")
        if month_str:
            try:
                year, month_num = map(int, month_str.split("-"))
            except (ValueError, TypeError):
                raise ValueError("月份格式错误，应为YYYY-MM")
        else:
            today = date.today()
            year, month_num = today.year, today.month

        # 计算月份范围
        month_start = date(year, month_num, 1)
        if month_num == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month_num + 1, 1) - timedelta(days=1)

        # 计算合同统计
        new_contracts = (
            self.db.query(Contract)
            .filter(
                Contract.signed_date >= month_start,
                Contract.signed_date <= month_end,
                Contract.status.in_(["SIGNED", "EXECUTING"])
            )
            .all()
        )
        contract_stats = {
            "new_contracts_count": len(new_contracts),
            "new_contracts_amount": sum(c.contract_amount or Decimal("0") for c in new_contracts),
            "active_contracts": self.db.query(Contract).filter(Contract.status.in_(["SIGNED", "EXECUTING"])).count(),
            "completed_contracts": self.db.query(Contract).filter(Contract.status == "COMPLETED").count(),
        }

        # 计算订单统计
        new_orders = (
            self.db.query(SalesOrder)
            .filter(
                func.date(SalesOrder.created_at) >= month_start,
                func.date(SalesOrder.created_at) <= month_end
            )
            .all()
        )
        order_stats = {
            "new_orders_count": len(new_orders),
            "new_orders_amount": sum(o.order_amount or Decimal("0") for o in new_orders),
        }

        # 计算回款统计
        planned_result = self.db.execute(text("""
            SELECT COALESCE(SUM(planned_amount), 0) as planned
            FROM project_payment_plans
            WHERE planned_date >= :start_date
            AND planned_date <= :end_date
        """), {"start_date": month_start.strftime("%Y-%m-%d"), "end_date": month_end.strftime("%Y-%m-%d")}).fetchone()
        planned_receipt_amount = Decimal(str(planned_result[0])) if planned_result and planned_result[0] else Decimal("0")

        actual_result = self.db.execute(text("""
            SELECT COALESCE(SUM(actual_amount), 0) as actual
            FROM project_payment_plans
            WHERE planned_date >= :start_date
            AND planned_date <= :end_date
            AND actual_amount > 0
        """), {"start_date": month_start.strftime("%Y-%m-%d"), "end_date": month_end.strftime("%Y-%m-%d")}).fetchone()
        actual_receipt_amount = Decimal(str(actual_result[0])) if actual_result and actual_result[0] else Decimal("0")

        receipt_completion_rate = (actual_receipt_amount / planned_receipt_amount * 100) if planned_receipt_amount > 0 else Decimal("0")

        overdue_result = self.db.execute(text("""
            SELECT COALESCE(SUM(planned_amount - actual_amount), 0) as overdue
            FROM project_payment_plans
            WHERE planned_date < :end_date
            AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """), {"end_date": month_end.strftime("%Y-%m-%d")}).fetchone()
        overdue_amount = Decimal(str(overdue_result[0])) if overdue_result and overdue_result[0] else Decimal("0")

        receipt_stats = {
            "planned_receipt_amount": planned_receipt_amount,
            "actual_receipt_amount": actual_receipt_amount,
            "receipt_completion_rate": receipt_completion_rate,
            "overdue_amount": overdue_amount,
        }

        # 计算开票统计
        invoices = (
            self.db.query(Invoice)
            .filter(
                func.date(Invoice.issue_date) >= month_start,
                func.date(Invoice.issue_date) <= month_end,
                Invoice.status == "ISSUED"
            )
            .all()
        )
        invoices_count = len(invoices)
        invoices_amount = sum(i.invoice_amount or Decimal("0") for i in invoices)

        total_needed = self.db.execute(text("""
            SELECT COUNT(*) as count
            FROM project_payment_plans
            WHERE planned_date <= :end_date
            AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """), {"end_date": month_end.strftime("%Y-%m-%d")}).fetchone()
        invoice_rate = (Decimal(invoices_count) / Decimal(total_needed[0]) * 100) if total_needed and total_needed[0] > 0 else Decimal("0")

        invoice_stats = {
            "invoices_count": invoices_count,
            "invoices_amount": invoices_amount,
            "invoice_rate": invoice_rate,
        }

        # 计算投标统计
        new_bidding = (
            self.db.query(BiddingProject)
            .filter(
                func.date(BiddingProject.created_at) >= month_start,
                func.date(BiddingProject.created_at) <= month_end
            )
            .count()
        )
        won_bidding = (
            self.db.query(BiddingProject)
            .filter(
                BiddingProject.result_date >= month_start,
                BiddingProject.result_date <= month_end,
                BiddingProject.bid_result == "won"
            )
            .count()
        )
        total_bidding = self.db.query(BiddingProject).count()
        bidding_win_rate = (Decimal(won_bidding) / Decimal(total_bidding) * 100) if total_bidding > 0 else Decimal("0")

        bidding_stats = {
            "new_bidding": new_bidding,
            "won_bidding": won_bidding,
            "bidding_win_rate": bidding_win_rate,
        }
        
        return {
            "report_date": month_str or f"{year}-{month_num:02d}",
            "report_type": "monthly",
            "contract_statistics": contract_stats,
            "order_statistics": order_stats,
            "receipt_statistics": receipt_stats,
            "invoice_statistics": invoice_stats,
            "bidding_statistics": bidding_stats,
        }
