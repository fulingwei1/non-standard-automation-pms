# -*- coding: utf-8 -*-
"""
营业收入数据获取服务
负责从合同、发票等模块获取项目的营业收入数据
支持多种收入类型：合同金额、已收款金额、已开票金额等
"""

from decimal import Decimal
from datetime import date
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.project import Project
from app.models.sales import Contract, Invoice


class RevenueService:
    """营业收入数据获取服务"""
    
    @staticmethod
    def get_project_revenue(
        db: Session,
        project_id: int,
        revenue_type: str = "CONTRACT"
    ) -> Decimal:
        """
        获取项目营业收入
        
        Args:
            db: 数据库会话
            project_id: 项目ID
            revenue_type: 收入类型
                - CONTRACT: 合同金额（默认）
                - RECEIVED: 已收款金额（从发票中统计已支付金额）
                - INVOICED: 已开票金额（从发票中统计已开票金额）
                - PAID_INVOICE: 已开票且已收款金额
        
        Returns:
            收入金额（元）
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return Decimal("0")
        
        if revenue_type == "CONTRACT":
            # 合同金额
            return Decimal(str(project.contract_amount or 0))
        
        elif revenue_type == "RECEIVED":
            # 已收款金额：从发票中统计已支付金额
            return RevenueService._get_received_amount(db, project_id)
        
        elif revenue_type == "INVOICED":
            # 已开票金额：从发票中统计已开票金额
            return RevenueService._get_invoiced_amount(db, project_id)
        
        elif revenue_type == "PAID_INVOICE":
            # 已开票且已收款金额
            return RevenueService._get_paid_invoice_amount(db, project_id)
        
        else:
            # 默认返回合同金额
            return Decimal(str(project.contract_amount or 0))
    
    @staticmethod
    def _get_received_amount(db: Session, project_id: int) -> Decimal:
        """获取已收款金额"""
        # 方法1：从发票中统计已支付金额
        invoices = db.query(Invoice).filter(
            Invoice.project_id == project_id,
            Invoice.status == "PAID"
        ).all()
        
        received_from_invoices = sum([
            Decimal(str(inv.paid_amount or inv.amount or 0))
            for inv in invoices
        ])
        
        # 方法2：从合同收款计划中统计实际收款
        from app.models.project import ProjectPaymentPlan
        payment_plans = db.query(ProjectPaymentPlan).filter(
            ProjectPaymentPlan.project_id == project_id
        ).all()
        
        received_from_plans = sum([
            Decimal(str(plan.actual_amount or 0))
            for plan in payment_plans
        ])
        
        # 取两者中的较大值（避免重复计算）
        return max(received_from_invoices, received_from_plans)
    
    @staticmethod
    def _get_invoiced_amount(db: Session, project_id: int) -> Decimal:
        """获取已开票金额"""
        invoices = db.query(Invoice).filter(
            Invoice.project_id == project_id,
            Invoice.status.in_(["ISSUED", "PAID", "PARTIAL"])
        ).all()
        
        return sum([
            Decimal(str(inv.total_amount or inv.amount or 0))
            for inv in invoices
        ])
    
    @staticmethod
    def _get_paid_invoice_amount(db: Session, project_id: int) -> Decimal:
        """获取已开票且已收款金额"""
        invoices = db.query(Invoice).filter(
            Invoice.project_id == project_id,
            Invoice.status == "PAID"
        ).all()
        
        return sum([
            Decimal(str(inv.paid_amount or inv.total_amount or inv.amount or 0))
            for inv in invoices
        ])
    
    @staticmethod
    def get_project_revenue_detail(
        db: Session,
        project_id: int
    ) -> Dict:
        """
        获取项目收入详情（包含所有收入类型）
        
        Args:
            db: 数据库会话
            project_id: 项目ID
        
        Returns:
            收入详情字典
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {
                "project_id": project_id,
                "contract_amount": Decimal("0"),
                "received_amount": Decimal("0"),
                "invoiced_amount": Decimal("0"),
                "paid_invoice_amount": Decimal("0"),
                "pending_amount": Decimal("0")
            }
        
        contract_amount = Decimal(str(project.contract_amount or 0))
        received_amount = RevenueService._get_received_amount(db, project_id)
        invoiced_amount = RevenueService._get_invoiced_amount(db, project_id)
        paid_invoice_amount = RevenueService._get_paid_invoice_amount(db, project_id)
        pending_amount = contract_amount - received_amount
        
        return {
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "contract_amount": contract_amount,
            "received_amount": received_amount,
            "invoiced_amount": invoiced_amount,
            "paid_invoice_amount": paid_invoice_amount,
            "pending_amount": pending_amount,
            "receive_rate": (received_amount / contract_amount * 100) if contract_amount > 0 else Decimal("0")
        }
    
    @staticmethod
    def get_projects_revenue(
        db: Session,
        project_ids: List[int],
        revenue_type: str = "CONTRACT"
    ) -> Dict[int, Decimal]:
        """
        批量获取多个项目的营业收入
        
        Args:
            db: 数据库会话
            project_ids: 项目ID列表
            revenue_type: 收入类型
        
        Returns:
            项目ID到收入金额的映射字典
        """
        result = {}
        
        for project_id in project_ids:
            result[project_id] = RevenueService.get_project_revenue(
                db, project_id, revenue_type
            )
        
        return result
    
    @staticmethod
    def get_total_revenue(
        db: Session,
        project_ids: List[int],
        revenue_type: str = "CONTRACT"
    ) -> Decimal:
        """
        获取多个项目的总收入
        
        Args:
            db: 数据库会话
            project_ids: 项目ID列表
            revenue_type: 收入类型
        
        Returns:
            总收入金额
        """
        revenues = RevenueService.get_projects_revenue(db, project_ids, revenue_type)
        return sum(revenues.values())





