# -*- coding: utf-8 -*-
"""
枚举模块测试
"""
import pytest
from app.models.enums import (
    ProjectStageEnum,
    ProjectHealthEnum,
    MachineStatusEnum,
    MilestoneTypeEnum,
    ProjectNoveltyLevelEnum,
    ProjectEvaluationLevelEnum,
    ProjectEvaluationStatusEnum,
    PaymentStatusEnum,
    TaskImportance,
    TaskStatus,
    TaskPriority,
    ApprovalDecision,
    AssemblyStageEnum,
)
from app.models.enums.sales import (
    LeadStatusEnum,
    OpportunityStageEnum,
    GateStatusEnum,
    QuoteStatusEnum,
    ContractStatusEnum,
    InvoiceStatusEnum,
)
from app.models.enums.material import (
    MaterialTypeEnum,
    MaterialSourceEnum,
    PurchaseOrderStatusEnum,
    SupplierLevelEnum,
)
from app.models.enums.others import (
    StatusEnum,
    AlertLevelEnum,
    AlertStatusEnum,
)
from app.models.enums.workflow import (
    BonusTypeEnum,
    BonusCalculationStatusEnum,
    EcnStatusEnum,
    EcnTypeEnum,
    PriorityEnum,
)


class TestProjectEnums:
    """项目相关枚举测试"""

    def test_project_stage_enum_values(self):
        """测试项目阶段枚举值"""
        assert ProjectStageEnum.S1.value == "S1"
        assert ProjectStageEnum.S2.value == "S2"
        assert ProjectStageEnum.S9.value == "S9"

    def test_project_stage_enum_iteration(self):
        """测试项目阶段枚举迭代"""
        stages = list(ProjectStageEnum)
        assert len(stages) == 9

    def test_project_health_enum(self):
        """测试项目健康度枚举"""
        assert ProjectHealthEnum.H1.value == "H1"
        assert ProjectHealthEnum.H4.value == "H4"

    def test_machine_status_enum(self):
        """测试机器状态枚举"""
        assert MachineStatusEnum.DESIGN.value == "DESIGN"
        assert MachineStatusEnum.FAT_PASSED.value == "FAT_PASSED"
        assert MachineStatusEnum.ACCEPTED.value == "ACCEPTED"

    def test_milestone_type_enum(self):
        """测试里程碑类型枚举"""
        assert MilestoneTypeEnum.KICKOFF.value == "KICKOFF"
        assert MilestoneTypeEnum.FAT.value == "FAT"
        assert MilestoneTypeEnum.FINAL_ACCEPTANCE.value == "FINAL_ACCEPTANCE"

    def test_project_novelty_level_enum(self):
        """测试项目新颖度枚举"""
        assert ProjectNoveltyLevelEnum.STANDARD.value == "STANDARD"
        assert ProjectNoveltyLevelEnum.NEW.value == "NEW"
        assert ProjectNoveltyLevelEnum.MODIFIED.value == "MODIFIED"

    def test_project_evaluation_level_enum(self):
        """测试项目评估等级枚举"""
        assert ProjectEvaluationLevelEnum.S.value == "S"
        assert ProjectEvaluationLevelEnum.A.value == "A"
        assert ProjectEvaluationLevelEnum.D.value == "D"

    def test_project_evaluation_status_enum(self):
        """测试项目评估状态枚举"""
        assert ProjectEvaluationStatusEnum.PENDING.value == "PENDING"
        assert ProjectEvaluationStatusEnum.COMPLETED.value == "COMPLETED"
        assert ProjectEvaluationStatusEnum.CANCELLED.value == "CANCELLED"

    def test_payment_status_enum(self):
        """测试付款状态枚举"""
        assert PaymentStatusEnum.PENDING.value == "PENDING"
        assert PaymentStatusEnum.PARTIAL.value == "PARTIAL"
        assert PaymentStatusEnum.PAID.value == "PAID"
        assert PaymentStatusEnum.OVERDUE.value == "OVERDUE"

    def test_task_importance_enum(self):
        """测试任务重要性枚举"""
        assert TaskImportance.CRITICAL.value == "CRITICAL"
        assert TaskImportance.LOW.value == "LOW"

    def test_task_status_enum(self):
        """测试任务状态枚举"""
        assert TaskStatus.TODO.value == "TODO"
        assert TaskStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert TaskStatus.DONE.value == "DONE"
        assert TaskStatus.CANCELLED.value == "CANCELLED"
        assert TaskStatus.BLOCKED.value == "BLOCKED"

    def test_task_priority_enum(self):
        """测试任务优先级枚举"""
        assert TaskPriority.URGENT.value == "URGENT"
        assert TaskPriority.MEDIUM.value == "MEDIUM"

    def test_approval_decision_enum(self):
        """测试审批决定枚举"""
        assert ApprovalDecision.APPROVED.value == "APPROVED"
        assert ApprovalDecision.REJECTED.value == "REJECTED"
        assert ApprovalDecision.PENDING.value == "PENDING"

    def test_assembly_stage_enum(self):
        """测试装配阶段枚举"""
        assert AssemblyStageEnum.DESIGN.value == "DESIGN"
        assert AssemblyStageEnum.ASSEMBLY.value == "ASSEMBLY"
        assert AssemblyStageEnum.SHIPPED.value == "SHIPPED"


class TestSalesEnums:
    """销售相关枚举测试"""

    def test_lead_status_enum(self):
        """测试线索状态枚举"""
        assert LeadStatusEnum.NEW.value == "NEW"
        assert LeadStatusEnum.CONVERTED.value == "CONVERTED"
        assert LeadStatusEnum.LOST.value == "LOST"

    def test_opportunity_stage_enum(self):
        """测试商机阶段枚举"""
        assert OpportunityStageEnum.DISCOVERY.value == "DISCOVERY"
        assert OpportunityStageEnum.NEGOTIATION.value == "NEGOTIATION"
        assert OpportunityStageEnum.WON.value == "WON"
        assert OpportunityStageEnum.LOST.value == "LOST"

    def test_gate_status_enum(self):
        """测试门状态枚举"""
        assert GateStatusEnum.PENDING.value == "PENDING"
        assert GateStatusEnum.PASSED.value == "PASSED"
        assert GateStatusEnum.FAILED.value == "FAILED"

    def test_quote_status_enum(self):
        """测试报价状态枚举"""
        assert QuoteStatusEnum.DRAFT.value == "DRAFT"
        assert QuoteStatusEnum.SUBMITTED.value == "SUBMITTED"
        assert QuoteStatusEnum.ACCEPTED.value == "ACCEPTED"

    def test_contract_status_enum(self):
        """测试合同状态枚举"""
        assert ContractStatusEnum.DRAFT.value == "DRAFT"
        assert ContractStatusEnum.SIGNED.value == "SIGNED"
        assert ContractStatusEnum.ACTIVE.value == "ACTIVE"

    def test_invoice_status_enum(self):
        """测试发票状态枚举"""
        assert InvoiceStatusEnum.DRAFT.value == "DRAFT"
        assert InvoiceStatusEnum.ISSUED.value == "ISSUED"
        assert InvoiceStatusEnum.PAID.value == "PAID"


class TestMaterialEnums:
    """物料相关枚举测试"""

    def test_material_type_enum(self):
        """测试物料类型枚举"""
        # 检查枚举存在
        values = list(MaterialTypeEnum)
        assert len(values) > 0

    def test_material_source_enum(self):
        """测试物料来源枚举"""
        values = list(MaterialSourceEnum)
        assert len(values) > 0

    def test_purchase_order_status_enum(self):
        """测试采购订单状态枚举"""
        values = list(PurchaseOrderStatusEnum)
        assert len(values) > 0

    def test_supplier_level_enum(self):
        """测试供应商等级枚举"""
        values = list(SupplierLevelEnum)
        assert len(values) > 0


class TestOtherEnums:
    """其他枚举测试"""

    def test_status_enum(self):
        """测试状态枚举"""
        assert StatusEnum.ACTIVE.value == "ACTIVE"
        assert StatusEnum.INACTIVE.value == "INACTIVE"

    def test_alert_level_enum(self):
        """测试告警级别枚举"""
        values = list(AlertLevelEnum)
        assert len(values) > 0

    def test_alert_status_enum(self):
        """测试告警状态枚举"""
        values = list(AlertStatusEnum)
        assert len(values) > 0

    def test_priority_enum(self):
        """测试优先级枚举"""
        assert PriorityEnum.LOW.value == "LOW"
        assert PriorityEnum.HIGH.value == "HIGH"


class TestWorkflowEnums:
    """工作流相关枚举测试"""

    def test_bonus_type_enum(self):
        """测试奖金类型枚举"""
        values = list(BonusTypeEnum)
        assert len(values) > 0

    def test_bonus_calculation_status_enum(self):
        """测试奖金计算状态枚举"""
        values = list(BonusCalculationStatusEnum)
        assert len(values) > 0

    def test_ecn_status_enum(self):
        """测试ECN状态枚举"""
        assert EcnStatusEnum.DRAFT.value == "DRAFT"
        values = list(EcnStatusEnum)
        assert len(values) > 0

    def test_ecn_type_enum(self):
        """测试ECN类型枚举"""
        values = list(EcnTypeEnum)
        assert len(values) > 0


class TestEnumComparisons:
    """枚举比较测试"""

    def test_enum_string_comparison(self):
        """测试枚举字符串比较"""
        assert ProjectStageEnum.S1 == "S1"
        assert ProjectHealthEnum.H1 == "H1"

    def test_enum_value_access(self):
        """测试枚举值访问"""
        stage = ProjectStageEnum.S5
        assert stage.value == "S5"
        assert stage.name == "S5"

    def test_enum_isinstance(self):
        """测试枚举 isinstance"""
        assert isinstance(ProjectStageEnum.S1, ProjectStageEnum)
        assert isinstance(MachineStatusEnum.DESIGN, MachineStatusEnum)