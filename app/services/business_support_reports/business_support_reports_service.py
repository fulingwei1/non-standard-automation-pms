# -*- coding: utf-8 -*-
"""
商务支持报表服务
负责销售报表（日报、周报、月报）的业务逻辑
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional, Tuple

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models.business_support import BiddingProject, SalesOrder
from app.models.sales import Contract, Invoice


class BusinessSupportReportsService:
    """商务支持报表服务"""

    def __init__(self, db: Session):
        self.db = db

    # ========== 日期解析辅助方法 ==========

    def parse_week_string(self, week: str) -> Tuple[int, int, date, date]:
        """解析周字符串，返回(年, 周数, 周开始日期, 周结束日期)"""
        year, week_num = map(int, week.split("-W"))
        jan1 = date(year, 1, 1)
        days_offset = (week_num - 1) * 7
        week_start = jan1 + timedelta(days=-jan1.weekday() + days_offset)
        week_end = week_start + timedelta(days=6)
        return year, week_num, week_start, week_end

    def get_current_week_range(self) -> Tuple[int, int, date, date]:
        """获取当前周范围"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        year = today.year
        week_num = (today - date(today.year, 1, 1)).days // 7 + 1
        return year, week_num, week_start, week_end

    # ========== 统计计算方法 ==========

    def calculate_contract_stats(
        self, start_date: date, end_date: date
    ) -> Dict[str, any]:
        """计算合同统计"""
        new_contracts = (
            self.db.query(Contract)
            .filter(
                Contract.signing_date >= start_date,
                Contract.signing_date <= end_date,
                Contract.status.in_(["SIGNED", "EXECUTING"]),
            )
            .all()
        )
        return {
            "new_count": len(new_contracts),
            "new_amount": sum(c.contract_amount or Decimal("0") for c in new_contracts),
            "active_count": self.db.query(Contract)
            .filter(Contract.status.in_(["SIGNED", "EXECUTING"]))
            .count(),
            "completed_count": self.db.query(Contract)
            .filter(Contract.status == "COMPLETED")
            .count(),
        }

    def calculate_order_stats(
        self, start_date: date, end_date: date
    ) -> Dict[str, any]:
        """计算订单统计"""
        new_orders = (
            self.db.query(SalesOrder)
            .filter(
                func.date(SalesOrder.created_at) >= start_date,
                func.date(SalesOrder.created_at) <= end_date,
            )
            .all()
        )
        return {
            "new_count": len(new_orders),
            "new_amount": sum(o.order_amount or Decimal("0") for o in new_orders),
        }

    def calculate_receipt_stats(
        self, start_date: date, end_date: date
    ) -> Dict[str, Decimal]:
        """计算回款统计"""
        params = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }

        planned = self.db.execute(
            text(
                """
            SELECT COALESCE(SUM(planned_amount), 0) FROM project_payment_plans
            WHERE planned_date >= :start_date AND planned_date <= :end_date
        """
            ),
            params,
        ).fetchone()
        planned_amount = (
            Decimal(str(planned[0])) if planned and planned[0] else Decimal("0")
        )

        actual = self.db.execute(
            text(
                """
            SELECT COALESCE(SUM(actual_amount), 0) FROM project_payment_plans
            WHERE planned_date >= :start_date AND planned_date <= :end_date AND actual_amount > 0
        """
            ),
            params,
        ).fetchone()
        actual_amount = (
            Decimal(str(actual[0])) if actual and actual[0] else Decimal("0")
        )

        overdue = self.db.execute(
            text(
                """
            SELECT COALESCE(SUM(planned_amount - actual_amount), 0) FROM project_payment_plans
            WHERE planned_date < :end_date AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """
            ),
            {"end_date": end_date.strftime("%Y-%m-%d")},
        ).fetchone()
        overdue_amount = (
            Decimal(str(overdue[0])) if overdue and overdue[0] else Decimal("0")
        )

        return {
            "planned": planned_amount,
            "actual": actual_amount,
            "rate": (actual_amount / planned_amount * 100)
            if planned_amount > 0
            else Decimal("0"),
            "overdue": overdue_amount,
        }

    def calculate_invoice_stats(
        self, start_date: date, end_date: date
    ) -> Dict[str, any]:
        """计算开票统计"""
        invoices = (
            self.db.query(Invoice)
            .filter(
                func.date(Invoice.issue_date) >= start_date,
                func.date(Invoice.issue_date) <= end_date,
                Invoice.status == "ISSUED",
            )
            .all()
        )
        invoices_count = len(invoices)
        invoices_amount = sum(i.invoice_amount or Decimal("0") for i in invoices)

        total_needed = self.db.execute(
            text(
                """
            SELECT COUNT(*) FROM project_payment_plans
            WHERE planned_date <= :end_date AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """
            ),
            {"end_date": end_date.strftime("%Y-%m-%d")},
        ).fetchone()
        rate = (
            (Decimal(invoices_count) / Decimal(total_needed[0]) * 100)
            if total_needed and total_needed[0] > 0
            else Decimal("0")
        )

        return {"count": invoices_count, "amount": invoices_amount, "rate": rate}

    def calculate_bidding_stats(
        self, start_date: date, end_date: date
    ) -> Dict[str, any]:
        """计算投标统计"""
        new_bidding = (
            self.db.query(BiddingProject)
            .filter(
                func.date(BiddingProject.created_at) >= start_date,
                func.date(BiddingProject.created_at) <= end_date,
            )
            .count()
        )

        won_bidding = (
            self.db.query(BiddingProject)
            .filter(
                BiddingProject.result_date >= start_date,
                BiddingProject.result_date <= end_date,
                BiddingProject.bid_result == "won",
            )
            .count()
        )

        total = self.db.query(BiddingProject).count()
        win_rate = (
            (Decimal(won_bidding) / Decimal(total) * 100)
            if total > 0
            else Decimal("0")
        )

        return {"new_count": new_bidding, "won_count": won_bidding, "win_rate": win_rate}

    # ========== 日报业务逻辑 ==========

    def get_daily_report(self, report_date: Optional[str] = None) -> Dict:
        """获取销售日报数据"""
        # 确定报表日期
        if report_date:
            report_dt = datetime.strptime(report_date, "%Y-%m-%d").date()
        else:
            report_dt = date.today()

        report_date_str = report_dt.strftime("%Y-%m-%d")

        # 1. 合同统计
        new_contracts = (
            self.db.query(Contract)
            .filter(
                func.date(Contract.signing_date) == report_dt,
                Contract.status.in_(["SIGNED", "EXECUTING"]),
            )
            .all()
        )
        new_contracts_count = len(new_contracts)
        new_contracts_amount = sum(
            c.contract_amount or Decimal("0") for c in new_contracts
        )

        active_contracts = (
            self.db.query(Contract)
            .filter(Contract.status.in_(["SIGNED", "EXECUTING"]))
            .count()
        )

        completed_contracts = (
            self.db.query(Contract).filter(Contract.status == "COMPLETED").count()
        )

        # 2. 订单统计
        new_orders = (
            self.db.query(SalesOrder)
            .filter(func.date(SalesOrder.created_at) == report_dt)
            .all()
        )
        new_orders_count = len(new_orders)
        new_orders_amount = sum(o.order_amount or Decimal("0") for o in new_orders)

        # 3. 回款统计
        planned_result = self.db.execute(
            text(
                """
            SELECT COALESCE(SUM(planned_amount), 0) as planned
            FROM project_payment_plans
            WHERE planned_date = :report_date
        """
            ),
            {"report_date": report_date_str},
        ).fetchone()
        planned_receipt_amount = (
            Decimal(str(planned_result[0]))
            if planned_result and planned_result[0]
            else Decimal("0")
        )

        actual_result = self.db.execute(
            text(
                """
            SELECT COALESCE(SUM(actual_amount), 0) as actual
            FROM project_payment_plans
            WHERE planned_date = :report_date
            AND actual_amount > 0
        """
            ),
            {"report_date": report_date_str},
        ).fetchone()
        actual_receipt_amount = (
            Decimal(str(actual_result[0]))
            if actual_result and actual_result[0]
            else Decimal("0")
        )

        receipt_completion_rate = (
            (actual_receipt_amount / planned_receipt_amount * 100)
            if planned_receipt_amount > 0
            else Decimal("0")
        )

        overdue_result = self.db.execute(
            text(
                """
            SELECT COALESCE(SUM(planned_amount - actual_amount), 0) as overdue
            FROM project_payment_plans
            WHERE planned_date < :report_date
            AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """
            ),
            {"report_date": report_date_str},
        ).fetchone()
        overdue_amount = (
            Decimal(str(overdue_result[0]))
            if overdue_result and overdue_result[0]
            else Decimal("0")
        )

        # 4. 开票统计
        invoices = (
            self.db.query(Invoice)
            .filter(
                func.date(Invoice.issue_date) == report_dt, Invoice.status == "ISSUED"
            )
            .all()
        )
        invoices_count = len(invoices)
        invoices_amount = sum(i.invoice_amount or Decimal("0") for i in invoices)

        total_needed = self.db.execute(
            text(
                """
            SELECT COUNT(*) as count
            FROM project_payment_plans
            WHERE planned_date <= :report_date
            AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """
            ),
            {"report_date": report_date_str},
        ).fetchone()
        invoice_rate = (
            (Decimal(invoices_count) / Decimal(total_needed[0]) * 100)
            if total_needed and total_needed[0] > 0
            else Decimal("0")
        )

        # 5. 投标统计
        new_bidding = (
            self.db.query(BiddingProject)
            .filter(func.date(BiddingProject.created_at) == report_dt)
            .count()
        )

        won_bidding = (
            self.db.query(BiddingProject)
            .filter(
                func.date(BiddingProject.result_date) == report_dt,
                BiddingProject.bid_result == "won",
            )
            .count()
        )

        total_bidding = self.db.query(BiddingProject).count()
        bidding_win_rate = (
            (Decimal(won_bidding) / Decimal(total_bidding) * 100)
            if total_bidding > 0
            else Decimal("0")
        )

        return {
            "report_date": report_date_str,
            "report_type": "daily",
            "new_contracts_count": new_contracts_count,
            "new_contracts_amount": new_contracts_amount,
            "active_contracts_count": active_contracts,
            "completed_contracts_count": completed_contracts,
            "new_orders_count": new_orders_count,
            "new_orders_amount": new_orders_amount,
            "planned_receipt_amount": planned_receipt_amount,
            "actual_receipt_amount": actual_receipt_amount,
            "receipt_completion_rate": receipt_completion_rate,
            "overdue_amount": overdue_amount,
            "invoices_count": invoices_count,
            "invoices_amount": invoices_amount,
            "invoice_rate": invoice_rate,
            "new_bidding_count": new_bidding,
            "won_bidding_count": won_bidding,
            "bidding_win_rate": bidding_win_rate,
        }

    # ========== 周报业务逻辑 ==========

    def get_weekly_report(self, week: Optional[str] = None) -> Dict:
        """获取销售周报数据"""
        # 确定报表周期
        if week:
            year, week_num, week_start, week_end = self.parse_week_string(week)
        else:
            year, week_num, week_start, week_end = self.get_current_week_range()

        week_str = f"{year}-W{week_num:02d}"

        # 使用辅助函数计算各类统计
        contract_stats = self.calculate_contract_stats(week_start, week_end)
        order_stats = self.calculate_order_stats(week_start, week_end)
        receipt_stats = self.calculate_receipt_stats(week_start, week_end)
        invoice_stats = self.calculate_invoice_stats(week_start, week_end)
        bidding_stats = self.calculate_bidding_stats(week_start, week_end)

        return {
            "report_date": week_str,
            "report_type": "weekly",
            "new_contracts_count": contract_stats["new_count"],
            "new_contracts_amount": contract_stats["new_amount"],
            "active_contracts_count": contract_stats["active_count"],
            "completed_contracts_count": contract_stats["completed_count"],
            "new_orders_count": order_stats["new_count"],
            "new_orders_amount": order_stats["new_amount"],
            "planned_receipt_amount": receipt_stats["planned"],
            "actual_receipt_amount": receipt_stats["actual"],
            "receipt_completion_rate": receipt_stats["rate"],
            "overdue_amount": receipt_stats["overdue"],
            "invoices_count": invoice_stats["count"],
            "invoices_amount": invoice_stats["amount"],
            "invoice_rate": invoice_stats["rate"],
            "new_bidding_count": bidding_stats["new_count"],
            "won_bidding_count": bidding_stats["won_count"],
            "bidding_win_rate": bidding_stats["win_rate"],
        }
