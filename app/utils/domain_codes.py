# -*- coding: utf-8 -*-
"""
领域编码生成工具

为各业务模块提供统一的编码生成函数，消除重复代码。
所有模块应从此文件导入编码生成函数，而不是自行实现。

使用示例：
    from app.utils.domain_codes import outsourcing, presale, pmo, task_center

    order_no = outsourcing.generate_order_no(db)
    ticket_no = presale.generate_ticket_no(db)
    risk_no = pmo.generate_risk_no(db)
    task_code = task_center.generate_task_code(db)
"""

from sqlalchemy.orm import Session

from app.utils.number_generator import generate_sequential_no


# ==================== 外协管理 (Outsourcing) ====================

class OutsourcingCodes:
    """外协管理编码生成"""

    @staticmethod
    def generate_order_no(db: Session) -> str:
        """生成外协订单号：OS-yymmdd-xxx"""
        from app.models.outsourcing import OutsourcingOrder
        return generate_sequential_no(
            db, OutsourcingOrder, 'order_no', 'OS',
            date_format='%y%m%d', separator='-', seq_length=3
        )

    @staticmethod
    def generate_delivery_no(db: Session) -> str:
        """生成送货单号：DL-yymmdd-xxx"""
        from app.models.outsourcing import OutsourcingDelivery
        return generate_sequential_no(
            db, OutsourcingDelivery, 'delivery_no', 'DL',
            date_format='%y%m%d', separator='-', seq_length=3
        )

    @staticmethod
    def generate_inspection_no(db: Session) -> str:
        """生成检验单号：IQ-yymmdd-xxx"""
        from app.models.outsourcing import OutsourcingInspection
        return generate_sequential_no(
            db, OutsourcingInspection, 'inspection_no', 'IQ',
            date_format='%y%m%d', separator='-', seq_length=3
        )


# ==================== 售前管理 (Presale) ====================

class PresaleCodes:
    """售前管理编码生成"""

    @staticmethod
    def generate_ticket_no(db: Session) -> str:
        """生成支持工单号：TICKET-yymmdd-xxx"""
        from app.models.presale import PresaleSupportTicket
        return generate_sequential_no(
            db, PresaleSupportTicket, 'ticket_no', 'TICKET',
            date_format='%y%m%d', separator='-', seq_length=3
        )

    @staticmethod
    def generate_solution_no(db: Session) -> str:
        """生成方案编号：SOL-yymmdd-xxx"""
        from app.models.presale import PresaleSolution
        return generate_sequential_no(
            db, PresaleSolution, 'solution_no', 'SOL',
            date_format='%y%m%d', separator='-', seq_length=3
        )

    @staticmethod
    def generate_tender_no(db: Session) -> str:
        """生成投标编号：TENDER-yymmdd-xxx"""
        from app.models.presale import PresaleTenderRecord
        return generate_sequential_no(
            db, PresaleTenderRecord, 'tender_no', 'TENDER',
            date_format='%y%m%d', separator='-', seq_length=3
        )


# ==================== PMO 管理 ====================

class PmoCodes:
    """PMO 编码生成"""

    @staticmethod
    def generate_initiation_no(db: Session) -> str:
        """生成立项编号：INIT-yymmdd-xxx"""
        from app.models.pmo import PmoProjectInitiation
        return generate_sequential_no(
            db, PmoProjectInitiation, 'application_no', 'INIT',
            date_format='%y%m%d', separator='-', seq_length=3
        )

    @staticmethod
    def generate_risk_no(db: Session) -> str:
        """生成风险编号：RISK-yymmdd-xxx"""
        from app.models.pmo import PmoProjectRisk
        return generate_sequential_no(
            db, PmoProjectRisk, 'risk_no', 'RISK',
            date_format='%y%m%d', separator='-', seq_length=3
        )

    @staticmethod
    def generate_meeting_no(db: Session) -> str:
        """生成会议编号：MTG-yymmdd-xxx"""
        from app.models.pmo import PmoMeeting
        return generate_sequential_no(
            db, PmoMeeting, 'meeting_no', 'MTG',
            date_format='%y%m%d', separator='-', seq_length=3
        )


# ==================== 任务中心 (Task Center) ====================

class TaskCenterCodes:
    """任务中心编码生成"""

    @staticmethod
    def generate_task_code(db: Session) -> str:
        """生成任务编码：TASK-yymmdd-xxx"""
        from app.models.task_center import TaskUnified
        return generate_sequential_no(
            db, TaskUnified, 'task_code', 'TASK',
            date_format='%y%m%d', separator='-', seq_length=3
        )


# ==================== 采购管理 (Purchase) ====================

class PurchaseCodes:
    """采购管理编码生成"""

    @staticmethod
    def generate_order_no(db: Session) -> str:
        """生成采购订单号：PO-YYYYMMDD-xxx"""
        from app.models.purchase import PurchaseOrder
        return generate_sequential_no(
            db, PurchaseOrder, 'order_no', 'PO',
            date_format='%Y%m%d', separator='-', seq_length=3
        )

    @staticmethod
    def generate_request_no(db: Session) -> str:
        """生成采购申请号：PR-YYYYMMDD-xxx"""
        from app.models.purchase import PurchaseRequest
        return generate_sequential_no(
            db, PurchaseRequest, 'request_no', 'PR',
            date_format='%Y%m%d', separator='-', seq_length=3
        )

    @staticmethod
    def generate_receipt_no(db: Session) -> str:
        """生成收货单号：GR-YYYYMMDD-xxx"""
        from app.models.purchase import GoodsReceipt
        return generate_sequential_no(
            db, GoodsReceipt, 'receipt_no', 'GR',
            date_format='%Y%m%d', separator='-', seq_length=3
        )


# ==================== 商务支持 (Business Support) ====================

class BusinessSupportCodes:
    """商务支持编码生成"""

    @staticmethod
    def generate_bidding_no(db: Session) -> str:
        """生成招标编号：BID-yymmdd-xxx"""
        from app.models.business_support import Bidding
        return generate_sequential_no(
            db, Bidding, 'bidding_no', 'BID',
            date_format='%y%m%d', separator='-', seq_length=3
        )

    @staticmethod
    def generate_archive_no(db: Session) -> str:
        """生成归档编号：AR-yymmdd-xxx"""
        from app.models.business_support import DocumentArchive
        return generate_sequential_no(
            db, DocumentArchive, 'archive_no', 'AR',
            date_format='%y%m%d', separator='-', seq_length=3
        )


# ==================== 服务管理 (Service) ====================

class ServiceCodes:
    """服务管理编码生成"""

    @staticmethod
    def generate_ticket_no(db: Session) -> str:
        """生成服务工单号：SRV-yymmdd-xxx"""
        from app.models.service import ServiceTicket
        return generate_sequential_no(
            db, ServiceTicket, 'ticket_no', 'SRV',
            date_format='%y%m%d', separator='-', seq_length=3
        )

    @staticmethod
    def generate_record_no(db: Session) -> str:
        """生成服务记录号：REC-yymmdd-xxx"""
        from app.models.service import ServiceRecord
        return generate_sequential_no(
            db, ServiceRecord, 'record_no', 'REC',
            date_format='%y%m%d', separator='-', seq_length=3
        )

    @staticmethod
    def generate_communication_no(db: Session) -> str:
        """生成沟通记录号：COM-yymmdd-xxx"""
        from app.models.service import ServiceCommunication
        return generate_sequential_no(
            db, ServiceCommunication, 'communication_no', 'COM',
            date_format='%y%m%d', separator='-', seq_length=3
        )

    @staticmethod
    def generate_survey_no(db: Session) -> str:
        """生成满意度调查号：SUR-yymmdd-xxx"""
        from app.models.service import SatisfactionSurvey
        return generate_sequential_no(
            db, SatisfactionSurvey, 'survey_no', 'SUR',
            date_format='%y%m%d', separator='-', seq_length=3
        )


# ==================== 研发项目 (R&D Project) ====================

class RdProjectCodes:
    """研发项目编码生成"""

    @staticmethod
    def generate_project_no(db: Session) -> str:
        """生成研发项目号：RDP-yymmdd-xxx"""
        from app.models.rd_project import RdProject
        return generate_sequential_no(
            db, RdProject, 'project_no', 'RDP',
            date_format='%y%m%d', separator='-', seq_length=3
        )

    @staticmethod
    def generate_cost_no(db: Session) -> str:
        """生成研发费用号：RDC-yymmdd-xxx"""
        from app.models.rd_project import RdCost
        return generate_sequential_no(
            db, RdCost, 'cost_no', 'RDC',
            date_format='%y%m%d', separator='-', seq_length=3
        )


# ==================== 预算管理 (Budget) ====================

class BudgetCodes:
    """预算管理编码生成"""

    @staticmethod
    def generate_budget_no(db: Session) -> str:
        """生成预算编号：BG-yymmdd-xxx"""
        from app.models.budget import Budget
        return generate_sequential_no(
            db, Budget, 'budget_no', 'BG',
            date_format='%y%m%d', separator='-', seq_length=3
        )


# ==================== 装配派工 (Installation Dispatch) ====================

class InstallationDispatchCodes:
    """装配派工编码生成"""

    @staticmethod
    def generate_order_no(db: Session) -> str:
        """生成派工单号：IDO-yymmdd-xxx"""
        from app.models.installation_dispatch import DispatchOrder
        return generate_sequential_no(
            db, DispatchOrder, 'order_no', 'IDO',
            date_format='%y%m%d', separator='-', seq_length=3
        )


# ==================== 套件检查 (Kit Check) ====================

class KitCheckCodes:
    """套件检查编码生成"""

    @staticmethod
    def generate_check_no(db: Session) -> str:
        """生成检查单号：KC-yymmdd-xxx"""
        from app.models.kit_check import KitCheck
        return generate_sequential_no(
            db, KitCheck, 'check_no', 'KC',
            date_format='%y%m%d', separator='-', seq_length=3
        )


# ==================== 导出便捷实例 ====================

outsourcing = OutsourcingCodes()
presale = PresaleCodes()
pmo = PmoCodes()
task_center = TaskCenterCodes()
purchase = PurchaseCodes()
business_support = BusinessSupportCodes()
service = ServiceCodes()
rd_project = RdProjectCodes()
budget = BudgetCodes()
installation_dispatch = InstallationDispatchCodes()
kit_check = KitCheckCodes()


__all__ = [
    # 类
    'OutsourcingCodes',
    'PresaleCodes',
    'PmoCodes',
    'TaskCenterCodes',
    'PurchaseCodes',
    'BusinessSupportCodes',
    'ServiceCodes',
    'RdProjectCodes',
    'BudgetCodes',
    'InstallationDispatchCodes',
    'KitCheckCodes',
    # 便捷实例
    'outsourcing',
    'presale',
    'pmo',
    'task_center',
    'purchase',
    'business_support',
    'service',
    'rd_project',
    'budget',
    'installation_dispatch',
    'kit_check',
]
