# -*- coding: utf-8 -*-
"""
项目阶段状态机 - 统一状态机框架示例

展示如何使用新的状态机框架替换现有的项目阶段状态机实现
"""

from typing import TYPE_CHECKING
from sqlalchemy.orm import Session

from app.core.state_machine import StateMachine

if TYPE_CHECKING:
    from app.models.project import Project


class ProjectStageStateMachine(StateMachine):
    """
    项目阶段状态机

    定义项目从 S1 到 S9 的状态转换规则
    """

    def __init__(self, model: "Project", db: Session):
        super().__init__(model, db, state_field="stage")
        self._stage_status_map = self._get_stage_status_map()

    def _get_stage_status_map(self) -> dict:
        """获取阶段到状态的映射"""
        return {
            "S1": "ST01",
            "S2": "ST03",
            "S3": "ST05",
            "S4": "ST07",
            "S5": "ST10",
            "S6": "ST15",
            "S7": "ST20",
            "S8": "ST25",
            "S9": "ST30",
        }

    @transition(from_state="S1", to_state="S2")
    def advance_s1_to_s2(self, from_state: str, to_state: str, **kwargs):
        """S1 需求进入 → S2 方案设计"""
        pass

    @transition(from_state="S2", to_state="S3")
    def advance_s2_to_s3(self, from_state: str, to_state: str, **kwargs):
        """S2 方案设计 → S3 采购备料"""
        pass

    @transition(
        from_state="S3",
        to_state="S4",
        validator=lambda sm, f, t: (sm.model.contract_no is not None, "合同未签订"),
    )
    def advance_s3_to_s4(self, from_state: str, to_state: str, **kwargs):
        """S3 采购备料 → S4 加工制造（需合同已签订）"""
        pass

    @transition(from_state="S4", to_state="S5")
    def advance_s4_to_s5(self, from_state: str, to_state: str, **kwargs):
        """S4 加工制造 → S5 装配调试（需BOM已发布）"""
        from app.models.material import BomHeader
        from sqlalchemy import and_

        project_id = self.model.id
        released_boms = (
            self.db.query(BomHeader)
            .filter(
                and_(BomHeader.project_id == project_id, BomHeader.status == "RELEASED")
            )
            .count()
        )

        if released_boms == 0:
            raise ValueError("BOM未发布（请发布至少一个BOM）")

    @transition(from_state="S5", to_state="S6")
    def advance_s5_to_s6(self, from_state: str, to_state: str, **kwargs):
        """S5 装配调试 → S6 出厂验收（需物料齐套）"""
        pass

    @transition(from_state="S6", to_state="S7")
    def advance_s6_to_s7(self, from_state: str, to_state: str, **kwargs):
        """S6 出厂验收 → S7 包装发运"""
        pass

    @transition(from_state="S7", to_state="S8")
    def advance_s7_to_s8(self, from_state: str, to_state: str, **kwargs):
        """S7 包装发运 → S8 现场安装（需FAT通过）"""
        from app.models.acceptance import AcceptanceOrder

        project_id = self.model.id
        fat_orders = (
            self.db.query(AcceptanceOrder)
            .filter(
                AcceptanceOrder.project_id == project_id,
                AcceptanceOrder.acceptance_type == "FAT",
                AcceptanceOrder.status == "COMPLETED",
                AcceptanceOrder.overall_result == "PASSED",
            )
            .count()
        )

        if fat_orders == 0:
            raise ValueError("FAT验收未通过（请完成FAT验收流程）")

    @transition(from_state="S8", to_state="S9")
    def advance_s8_to_s9(self, from_state: str, to_state: str, **kwargs):
        """S8 现场安装 → S9 质保结项（需终验收通过且回款达标）"""
        from app.models.acceptance import AcceptanceOrder
        from app.models.project import ProjectPaymentPlan

        project_id = self.model.id

        final_orders = (
            self.db.query(AcceptanceOrder)
            .filter(
                AcceptanceOrder.project_id == project_id,
                AcceptanceOrder.acceptance_type.in_(["FINAL", "SAT"]),
                AcceptanceOrder.status == "COMPLETED",
                AcceptanceOrder.overall_result == "PASSED",
            )
            .count()
        )

        if final_orders == 0:
            raise ValueError("终验收未通过（请完成终验收流程）")

        payment_plans = (
            self.db.query(ProjectPaymentPlan)
            .filter(ProjectPaymentPlan.project_id == project_id)
            .all()
        )

        if not payment_plans:
            raise ValueError("收款计划未设置")

        total_paid = sum(
            float(plan.actual_amount or 0)
            for plan in payment_plans
            if plan.status == "PAID"
        )
        total_planned = sum(float(plan.planned_amount or 0) for plan in payment_plans)
        contract_amount = float(self.model.contract_amount or 0)
        base_amount = (
            max(contract_amount, total_planned)
            if total_planned > 0
            else contract_amount
        )

        if base_amount == 0:
            raise ValueError("合同金额未设置")

        payment_rate = (total_paid / base_amount) * 100
        if payment_rate < 80:
            raise ValueError(f"回款率 {payment_rate:.1f}%，需≥80%")

    def get_status_for_stage(self, stage: str) -> str:
        """获取阶段对应的状态"""
        return self._stage_status_map.get(stage, "")

    @before_transition
    def log_before_transition(self, from_state: str, to_state: str, **kwargs):
        """状态转换前日志"""
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"项目 {self.model.project_code} 即将从 {from_state} 推进至 {to_state}"
        )

    @after_transition
    def log_after_transition(self, from_state: str, to_state: str, **kwargs):
        """状态转换后日志"""
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"项目 {self.model.project_code} 已从 {from_state} 推进至 {to_state}"
        )

        new_status = self.get_status_for_stage(to_state)
        if new_status and new_status != self.model.status:
            self.model.status = new_status


def create_project_stage_state_machine(
    project: "Project", db: Session
) -> ProjectStageStateMachine:
    """
    工厂函数：创建项目阶段状态机实例

    Args:
        project: 项目模型实例
        db: 数据库会话

    Returns:
        ProjectStageStateMachine: 项目阶段状态机实例
    """
    return ProjectStageStateMachine(project, db)
