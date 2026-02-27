# -*- coding: utf-8 -*-
"""
商务支持工作台统计 API endpoints
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Query
from sqlalchemy import desc, text
from sqlalchemy.orm import Session

from app.api import deps
from app.common.dashboard.base import BaseDashboardEndpoint
from app.common.date_range import get_month_range_by_ym
from app.core import security
from app.models.business_support import (
    BiddingProject,
    ContractReview,
    ContractSealRecord,
    DocumentArchive,
    PaymentReminder,
)
from app.models.sales import Contract, Invoice
from app.models.user import User
from app.schemas.business_support import (
    BiddingProjectResponse,
    BusinessSupportDashboardResponse,
    PerformanceMetricsResponse,
)
from app.schemas.common import ResponseModel


class BusinessSupportDashboardEndpoint(BaseDashboardEndpoint):
    """商务支持Dashboard端点"""
    
    module_name = "business_support"
    permission_required = "business_support:read"
    
    def __init__(self):
        """初始化路由，添加额外端点"""
        super().__init__()
        # 添加其他端点
        self.router.add_api_route(
            "/business_support/dashboard/active-contracts",
            self._get_active_contracts_handler,
            methods=["GET"],
            summary="获取进行中的合同列表",
            response_model=ResponseModel[List[dict]]
        )
        self.router.add_api_route(
            "/business_support/dashboard/active-bidding",
            self._get_active_bidding_handler,
            methods=["GET"],
            summary="获取进行中的投标列表",
            response_model=ResponseModel[List[BiddingProjectResponse]]
        )
        self.router.add_api_route(
            "/business_support/dashboard/performance",
            self._get_performance_metrics_handler,
            methods=["GET"],
            summary="获取本月绩效指标",
            response_model=ResponseModel[PerformanceMetricsResponse]
        )
    
    def get_dashboard_data(
        self,
        db: Session,
        current_user: User
    ) -> Dict[str, Any]:
        """
        获取商务支持工作台统计数据
        包括：进行中合同数、待回款金额、逾期款项、开票率、投标数、验收率等
        """
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

        # 计算各项统计
        active_contracts = count_active_contracts(db)
        pending_amount = calculate_pending_amount(db, today)
        overdue_amount = calculate_overdue_amount(db, today)
        invoice_rate = calculate_invoice_rate(db, today)
        active_bidding = count_active_bidding(db)
        acceptance_rate = calculate_acceptance_rate(db)
        urgent_tasks = get_urgent_tasks(db, current_user.id, today)
        today_todos = get_today_todos(db, current_user.id, today)

        # 使用基类方法创建统计卡片
        stats = [
            self.create_stat_card(
                key="active_contracts",
                label="进行中合同",
                value=active_contracts,
                unit="个",
                icon="contract"
            ),
            self.create_stat_card(
                key="pending_amount",
                label="待回款金额",
                value=float(pending_amount),
                unit="元",
                icon="payment",
                color="warning"
            ),
            self.create_stat_card(
                key="overdue_amount",
                label="逾期款项",
                value=float(overdue_amount),
                unit="元",
                icon="overdue",
                color="danger"
            ),
            self.create_stat_card(
                key="invoice_rate",
                label="开票率",
                value=float(invoice_rate),
                unit="%",
                icon="invoice"
            ),
            self.create_stat_card(
                key="active_bidding",
                label="进行中投标",
                value=active_bidding,
                unit="个",
                icon="bidding"
            ),
            self.create_stat_card(
                key="acceptance_rate",
                label="验收率",
                value=float(acceptance_rate),
                unit="%",
                icon="acceptance"
            ),
        ]

        dashboard_data = BusinessSupportDashboardResponse(
            active_contracts_count=active_contracts,
            pending_amount=pending_amount,
            overdue_amount=overdue_amount,
            invoice_rate=invoice_rate,
            active_bidding_count=active_bidding,
            acceptance_rate=acceptance_rate,
            urgent_tasks=urgent_tasks,
            today_todos=today_todos
        )

        # 将Pydantic模型转换为字典并添加stats
        result = dashboard_data.model_dump()
        result["stats"] = stats
        return result
    
    def _get_active_contracts_handler(
        self,
        limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
        db: Session = Depends(deps.get_db),
        current_user: User = Depends(security.require_permission("business_support:read"))
    ):
        """获取进行中的合同列表（用于工作台展示）"""
        try:
            # 查询进行中的合同
            contracts = (
                db.query(Contract)
                .filter(Contract.status.in_(["SIGNED", "EXECUTING"]))
                .order_by(desc(Contract.signing_date))
                .limit(limit)
                .all()
            )

            # 使用原生SQL查询回款信息
            contract_list = []
            for contract in contracts:
                # 查询回款计划
                payment_result = None
                if contract.project_id:
                    payment_result = db.execute(text("""
                        SELECT
                            COALESCE(SUM(planned_amount), 0) as total_planned,
                            COALESCE(SUM(actual_amount), 0) as total_actual
                        FROM project_payment_plans
                        WHERE project_id = :project_id
                    """), {"project_id": contract.project_id}).fetchone()

                total_planned = Decimal(str(payment_result[0])) if payment_result and payment_result[0] else Decimal("0")
                total_actual = Decimal(str(payment_result[1])) if payment_result and payment_result[1] else Decimal("0")
                payment_progress = (total_actual / total_planned * 100) if total_planned > 0 else Decimal("0")

                # 查询发票数量
                invoice_count = db.query(Invoice).filter(Invoice.contract_id == contract.id).count()

                contract_list.append({
                    "id": contract.contract_code,
                    "projectId": contract.project.project_code if contract.project else None,
                    "projectName": contract.project.project_name if contract.project else None,
                    "customerName": contract.customer.customer_name if contract.customer else None,
                    "contractAmount": float(contract.contract_amount) if contract.contract_amount else 0,
                    "signedDate": contract.signing_date.strftime("%Y-%m-%d") if contract.signing_date else None,
                    "paidAmount": float(total_actual),
                    "paymentProgress": float(payment_progress),
                    "invoiceCount": invoice_count,
                    "invoiceStatus": "complete" if invoice_count > 0 else "partial",
                    "acceptanceStatus": "in_progress"  # 简化处理，实际应从验收模块查询
                })

            return ResponseModel(
                code=200,
                message="获取进行中的合同列表成功",
                data=contract_list
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取进行中的合同列表失败: {str(e)}")
    
    def _get_active_bidding_handler(
        self,
        limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
        db: Session = Depends(deps.get_db),
        current_user: User = Depends(security.require_permission("business_support:read"))
    ):
        """获取进行中的投标列表（用于工作台展示）"""
        try:
            # 查询进行中的投标
            bidding_projects = (
                db.query(BiddingProject)
                .filter(BiddingProject.status.in_(["draft", "preparing", "submitted"]))
                .order_by(BiddingProject.deadline_date.asc())
                .limit(limit)
                .all()
            )

            bidding_list = [
                BiddingProjectResponse(
                    id=item.id,
                    bidding_no=item.bidding_no,
                    project_name=item.project_name,
                    customer_id=item.customer_id,
                    customer_name=item.customer_name,
                    tender_no=item.tender_no,
                    tender_type=item.tender_type,
                    tender_platform=item.tender_platform,
                    tender_url=item.tender_url,
                    publish_date=item.publish_date,
                    deadline_date=item.deadline_date,
                    bid_opening_date=item.bid_opening_date,
                    bid_bond=item.bid_bond,
                    bid_bond_status=item.bid_bond_status,
                    estimated_amount=item.estimated_amount,
                    bid_document_status=item.bid_document_status,
                    technical_doc_ready=item.technical_doc_ready,
                    commercial_doc_ready=item.commercial_doc_ready,
                    qualification_doc_ready=item.qualification_doc_ready,
                    submission_method=item.submission_method,
                    submission_address=item.submission_address,
                    sales_person_id=item.sales_person_id,
                    sales_person_name=item.sales_person_name,
                    support_person_id=item.support_person_id,
                    support_person_name=item.support_person_name,
                    bid_result=item.bid_result,
                    bid_price=item.bid_price,
                    win_price=item.win_price,
                    result_date=item.result_date,
                    result_remark=item.result_remark,
                    status=item.status,
                    remark=item.remark,
                    created_at=item.created_at,
                    updated_at=item.updated_at
                )
                for item in bidding_projects
            ]

            return ResponseModel(
                code=200,
                message="获取进行中的投标列表成功",
                data=bidding_list
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取进行中的投标列表失败: {str(e)}")
    
    def _get_performance_metrics_handler(
        self,
        month: Optional[str] = Query(None, description="统计月份（YYYY-MM格式），不提供则使用当前月份"),
        db: Session = Depends(deps.get_db),
        current_user: User = Depends(security.require_permission("business_support:read"))
    ):
        """获取本月绩效指标（用于工作台右侧展示）"""
        try:
            # 确定统计月份
            if month:
                try:
                    year, month_num = map(int, month.split("-"))
                except (ValueError, TypeError):
                    raise HTTPException(status_code=400, detail="月份格式错误，应为YYYY-MM")
            else:
                today = date.today()
                year = today.year
                month_num = today.month

            month_start, month_end = get_month_range_by_ym(year, month_num)
            month_str = f"{year}-{month_num:02d}"

            # 1. 新签合同数（本月签订的合同）
            new_contracts = (
                db.query(Contract)
                .filter(
                    Contract.signing_date >= month_start,
                    Contract.signing_date <= month_end,
                    Contract.status.in_(["SIGNED", "EXECUTING"])
                )
                .count()
            )

            # 2. 回款完成率（本月实际回款/计划回款）
            # 本月计划回款金额
            planned_result = db.execute(text("""
                SELECT COALESCE(SUM(planned_amount), 0) as planned
                FROM project_payment_plans
                WHERE planned_date >= :start_date
                AND planned_date <= :end_date
            """), {"start_date": month_start.strftime("%Y-%m-%d"), "end_date": month_end.strftime("%Y-%m-%d")}).fetchone()
            planned_amount = Decimal(str(planned_result[0])) if planned_result and planned_result[0] else Decimal("0")

            # 本月实际回款金额（从回款记录表查询，如果有的话）
            # 这里简化处理，从project_payment_plans表的actual_amount字段计算
            actual_result = db.execute(text("""
                SELECT COALESCE(SUM(actual_amount), 0) as actual
                FROM project_payment_plans
                WHERE planned_date >= :start_date
                AND planned_date <= :end_date
                AND actual_amount > 0
            """), {"start_date": month_start.strftime("%Y-%m-%d"), "end_date": month_end.strftime("%Y-%m-%d")}).fetchone()
            actual_amount = Decimal(str(actual_result[0])) if actual_result and actual_result[0] else Decimal("0")

            payment_completion_rate = (actual_amount / planned_amount * 100) if planned_amount > 0 else Decimal("0")

            # 3. 开票及时率（按时开票数/应开票数）
            # 应开票数：本月计划回款中需要开票的数量
            # 按时开票数：在计划日期前或当天开票的数量
            # 这里简化处理，使用发票表的issue_date和状态
            total_invoices_needed = db.execute(text("""
                SELECT COUNT(*) as count
                FROM project_payment_plans
                WHERE planned_date >= :start_date
                AND planned_date <= :end_date
                AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
            """), {"start_date": month_start.strftime("%Y-%m-%d"), "end_date": month_end.strftime("%Y-%m-%d")}).fetchone()
            total_needed = total_invoices_needed[0] if total_invoices_needed else 0

            # 本月已开票数（在计划日期前或当天开票）
            on_time_invoices = (
                db.query(Invoice)
                .join(Contract, Invoice.contract_id == Contract.id)
                .filter(
                    Invoice.issue_date >= month_start,
                    Invoice.issue_date <= month_end,
                    Invoice.status == "ISSUED"
                )
                .count()
            )

            invoice_timeliness_rate = (Decimal(on_time_invoices) / Decimal(total_needed) * 100) if total_needed > 0 else Decimal("0")

            # 4. 文件流转数（本月处理的文件数）
            # 包括：文件归档、合同审核、合同盖章、回款催收等
            document_flow_count = (
                db.query(DocumentArchive)
                .filter(
                    DocumentArchive.created_at >= datetime.combine(month_start, datetime.min.time()),
                    DocumentArchive.created_at <= datetime.combine(month_end, datetime.max.time())
                )
                .count()
            )

            # 加上合同审核记录
            document_flow_count += (
                db.query(ContractReview)
                .filter(
                    ContractReview.created_at >= datetime.combine(month_start, datetime.min.time()),
                    ContractReview.created_at <= datetime.combine(month_end, datetime.max.time())
                )
                .count()
            )

            # 加上合同盖章记录
            document_flow_count += (
                db.query(ContractSealRecord)
                .filter(
                    ContractSealRecord.created_at >= datetime.combine(month_start, datetime.min.time()),
                    ContractSealRecord.created_at <= datetime.combine(month_end, datetime.max.time())
                )
                .count()
            )

            # 加上回款催收记录
            document_flow_count += (
                db.query(PaymentReminder)
                .filter(
                    PaymentReminder.created_at >= datetime.combine(month_start, datetime.min.time()),
                    PaymentReminder.created_at <= datetime.combine(month_end, datetime.max.time())
                )
                .count()
            )

            performance_data = PerformanceMetricsResponse(
                new_contracts_count=new_contracts,
                payment_completion_rate=payment_completion_rate,
                invoice_timeliness_rate=invoice_timeliness_rate,
                document_flow_count=document_flow_count,
                month=month_str
            )

            return ResponseModel(
                code=200,
                message="获取本月绩效指标成功",
                data=performance_data
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取本月绩效指标失败: {str(e)}")


# 创建端点实例并获取路由
dashboard_endpoint = BusinessSupportDashboardEndpoint()
router = dashboard_endpoint.router
