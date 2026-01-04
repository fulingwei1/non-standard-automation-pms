# -*- coding: utf-8 -*-
"""
数据模型包

导出所有ORM模型供外部使用
"""

from .base import Base, TimestampMixin, get_engine, get_session, init_db
from .enums import *
from .user import User, Role, Permission, RolePermission, UserRole
from .project import (
    Project, Machine, ProjectStage, ProjectStatus,
    ProjectMember, ProjectMilestone, ProjectCost, ProjectDocument, Customer
)
from .material import (
    Material, MaterialCategory, Supplier, MaterialSupplier,
    BomHeader, BomItem, MaterialShortage
)
from .purchase import (
    PurchaseOrder, PurchaseOrderItem, GoodsReceipt, GoodsReceiptItem
)
from .ecn import (
    Ecn, EcnEvaluation, EcnApproval, EcnTask,
    EcnAffectedMaterial, EcnAffectedOrder, EcnLog,
    EcnType, EcnApprovalMatrix
)
from .acceptance import (
    AcceptanceTemplate, TemplateCategory, TemplateCheckItem,
    AcceptanceOrder, AcceptanceOrderItem, AcceptanceIssue,
    IssueFollowUp, AcceptanceSignature, AcceptanceReport
)
from .outsourcing import (
    OutsourcingVendor, OutsourcingOrder, OutsourcingOrderItem,
    OutsourcingDelivery, OutsourcingDeliveryItem, OutsourcingInspection,
    OutsourcingPayment, OutsourcingEvaluation, OutsourcingProgress
)
from .alert import (
    AlertRule, AlertRecord, AlertNotification,
    ExceptionEvent, ExceptionAction, ExceptionEscalation,
    AlertStatistics, ProjectHealthSnapshot, AlertRuleTemplate
)
from .production import (
    Workshop, Workstation, Worker, WorkerSkill, ProcessDict,
    Equipment, EquipmentMaintenance, ProductionPlan,
    WorkOrder, WorkReport, ProductionException,
    MaterialRequisition, MaterialRequisitionItem, ProductionDailyReport
)

__all__ = [
    # Base
    'Base', 'TimestampMixin', 'get_engine', 'get_session', 'init_db',
    # User
    'User', 'Role', 'Permission', 'RolePermission', 'UserRole',
    # Project
    'Project', 'Machine', 'ProjectStage', 'ProjectStatus',
    'ProjectMember', 'ProjectMilestone', 'ProjectCost', 'ProjectDocument', 'Customer',
    # Material
    'Material', 'MaterialCategory', 'Supplier', 'MaterialSupplier',
    'BomHeader', 'BomItem', 'MaterialShortage',
    # Purchase
    'PurchaseOrder', 'PurchaseOrderItem', 'GoodsReceipt', 'GoodsReceiptItem',
    # ECN
    'Ecn', 'EcnEvaluation', 'EcnApproval', 'EcnTask',
    'EcnAffectedMaterial', 'EcnAffectedOrder', 'EcnLog',
    'EcnType', 'EcnApprovalMatrix',
    # Acceptance
    'AcceptanceTemplate', 'TemplateCategory', 'TemplateCheckItem',
    'AcceptanceOrder', 'AcceptanceOrderItem', 'AcceptanceIssue',
    'IssueFollowUp', 'AcceptanceSignature', 'AcceptanceReport',
    # Outsourcing
    'OutsourcingVendor', 'OutsourcingOrder', 'OutsourcingOrderItem',
    'OutsourcingDelivery', 'OutsourcingDeliveryItem', 'OutsourcingInspection',
    'OutsourcingPayment', 'OutsourcingEvaluation', 'OutsourcingProgress',
    # Alert
    'AlertRule', 'AlertRecord', 'AlertNotification',
    'ExceptionEvent', 'ExceptionAction', 'ExceptionEscalation',
    'AlertStatistics', 'ProjectHealthSnapshot', 'AlertRuleTemplate',
    # Production
    'Workshop', 'Workstation', 'Worker', 'WorkerSkill', 'ProcessDict',
    'Equipment', 'EquipmentMaintenance', 'ProductionPlan',
    'WorkOrder', 'WorkReport', 'ProductionException',
    'MaterialRequisition', 'MaterialRequisitionItem', 'ProductionDailyReport',
]
