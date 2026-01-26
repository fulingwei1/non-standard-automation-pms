# -*- coding: utf-8 -*-
"""
项目状态联动规则引擎

实现设计文档中定义的状态自动流转规则，支持事件驱动的状态联动

此模块作为协调者，将具体的状态变更委托给专门的处理器：
- ContractStatusHandler: 处理合同签订相关事件
- MaterialStatusHandler: 处理BOM发布、物料齐套/缺货
- AcceptanceStatusHandler: 处理FAT/SAT验收
- ECNStatusHandler: 处理ECN变更影响
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatusLog

# 处理器延迟导入，避免循环依赖
# from app.services.status_handlers import ...


class StatusTransitionService:
    """项目状态联动服务（协调者）"""

    def __init__(self, db: Session):
        self.db = db

        # 延迟导入处理器，避免循环依赖
        from app.services.status_handlers.contract_handler import ContractStatusHandler
        from app.services.status_handlers.material_handler import MaterialStatusHandler
        from app.services.status_handlers.acceptance_handler import AcceptanceStatusHandler
        from app.services.status_handlers.ecn_handler import ECNStatusHandler

        # 初始化各个处理器
        self.contract_handler = ContractStatusHandler(db, self)
        self.material_handler = MaterialStatusHandler(db, self)
        self.acceptance_handler = AcceptanceStatusHandler(db, self)
        self.ecn_handler = ECNStatusHandler(db, self)

    # === 合同相关事件 ===

    def handle_contract_signed(
        self, contract_id: int, auto_create_project: bool = True
    ) -> Optional[Project]:
        """
        处理合同签订事件

        规则：合同签订 → 自动创建项目，状态→S3/ST08

        Args:
            contract_id: 合同ID
            auto_create_project: 是否自动创建项目

        Returns:
            Project: 创建的项目对象，如果已存在则返回现有项目
        """
        return self.contract_handler.handle_contract_signed(
            contract_id=contract_id,
            auto_create_project=auto_create_project,
            log_status_change=self._log_status_change,
        )

    # === BOM和物料相关事件 ===

    def handle_bom_published(
        self, project_id: int, machine_id: Optional[int] = None
    ) -> bool:
        """
        处理BOM发布完成事件

        规则：BOM发布完成 → 项目状态自动更新为 S5/ST12

        Args:
            project_id: 项目ID
            machine_id: 设备ID（可选）

        Returns:
            bool: 是否成功更新
        """
        return self.material_handler.handle_bom_published(
            project_id=project_id,
            machine_id=machine_id,
            log_status_change=self._log_status_change,
        )

    def handle_material_shortage(
        self, project_id: int, is_critical: bool = True
    ) -> bool:
        """
        处理关键物料缺货事件

        规则：关键物料缺货 → 项目状态→ST14，健康度→H3

        Args:
            project_id: 项目ID
            is_critical: 是否为关键物料

        Returns:
            bool: 是否成功更新
        """
        return self.material_handler.handle_material_shortage(
            project_id=project_id,
            is_critical=is_critical,
            log_status_change=self._log_status_change,
        )

    def handle_material_ready(self, project_id: int) -> bool:
        """
        处理物料齐套事件

        规则：物料齐套 → 项目状态→ST16，健康度→H1，可推进至S6

        Args:
            project_id: 项目ID

        Returns:
            bool: 是否成功更新
        """
        return self.material_handler.handle_material_ready(
            project_id=project_id,
            log_status_change=self._log_status_change,
        )

    # === 验收相关事件 ===

    def handle_fat_passed(
        self, project_id: int, machine_id: Optional[int] = None
    ) -> bool:
        """
        处理FAT验收通过事件

        规则：FAT通过 → 状态→ST23，可推进至S8，健康度→H1

        Args:
            project_id: 项目ID
            machine_id: 设备ID（可选）

        Returns:
            bool: 是否成功更新
        """
        return self.acceptance_handler.handle_fat_passed(
            project_id=project_id,
            machine_id=machine_id,
            log_status_change=self._log_status_change,
        )

    def handle_fat_failed(
        self,
        project_id: int,
        machine_id: Optional[int] = None,
        issues: Optional[List[str]] = None,
    ) -> bool:
        """
        处理FAT验收不通过事件

        规则：FAT不通过 → 状态→ST22，健康度→H2

        Args:
            project_id: 项目ID
            machine_id: 设备ID（可选）
            issues: 问题列表（可选）

        Returns:
            bool: 是否成功更新
        """
        return self.acceptance_handler.handle_fat_failed(
            project_id=project_id,
            machine_id=machine_id,
            issues=issues,
            log_status_change=self._log_status_change,
        )

    def handle_sat_passed(
        self, project_id: int, machine_id: Optional[int] = None
    ) -> bool:
        """
        处理SAT验收通过事件

        规则：SAT通过 → 状态→ST27，可推进至S9

        Args:
            project_id: 项目ID
            machine_id: 设备ID（可选）

        Returns:
            bool: 是否成功更新
        """
        return self.acceptance_handler.handle_sat_passed(
            project_id=project_id,
            machine_id=machine_id,
            log_status_change=self._log_status_change,
        )

    def handle_sat_failed(
        self,
        project_id: int,
        machine_id: Optional[int] = None,
        issues: Optional[List[str]] = None,
    ) -> bool:
        """
        处理SAT验收不通过事件

        规则：SAT不通过 → 状态→ST26，健康度→H2

        Args:
            project_id: 项目ID
            machine_id: 设备ID（可选）
            issues: 问题列表（可选）

        Returns:
            bool: 是否成功更新
        """
        return self.acceptance_handler.handle_sat_failed(
            project_id=project_id,
            machine_id=machine_id,
            issues=issues,
            log_status_change=self._log_status_change,
        )

    def handle_final_acceptance_passed(self, project_id: int) -> bool:
        """
        处理终验收通过事件

        规则：终验收通过 → 可推进至S9

        Args:
            project_id: 项目ID

        Returns:
            bool: 是否成功更新
        """
        return self.acceptance_handler.handle_final_acceptance_passed(
            project_id=project_id,
            log_status_change=self._log_status_change,
        )

    # === ECN相关事件 ===

    def handle_ecn_schedule_impact(
        self, project_id: int, ecn_id: int, impact_days: int
    ) -> bool:
        """
        处理ECN变更影响交期事件

        规则：ECN影响交期 → 更新协商交期，记录风险

        Args:
            project_id: 项目ID
            ecn_id: ECN ID
            impact_days: 影响天数（正数表示延期）

        Returns:
            bool: 是否成功更新
        """
        return self.ecn_handler.handle_ecn_schedule_impact(
            project_id=project_id,
            ecn_id=ecn_id,
            impact_days=impact_days,
            log_status_change=self._log_status_change,
        )

    # === 阶段自动流转 ===

    def check_auto_stage_transition(
        self, project_id: int, auto_advance: bool = False
    ) -> Dict[str, Any]:
        """
        Issue 1.2: 检查阶段自动流转条件

        当满足条件时自动推进项目阶段

        Args:
            project_id: 项目ID
            auto_advance: 是否自动推进（True=自动推进，False=仅检查并提示）

        Returns:
            dict: 检查结果，包含是否可推进、目标阶段、缺失项等
        """
        from app.services.stage_transition_checks import (
            check_s3_to_s4_transition,
            check_s4_to_s5_transition,
            check_s5_to_s6_transition,
            check_s7_to_s8_transition,
            check_s8_to_s9_transition,
            execute_stage_transition,
        )

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {
                "can_advance": False,
                "message": "项目不存在",
                "current_stage": None,
                "target_stage": None,
                "missing_items": [],
            }

        current_stage = project.stage or "S1"
        can_advance = False
        target_stage = None
        missing_items = []
        transition_reason = ""

        # 根据当前阶段检查流转条件
        if current_stage == "S3":
            can_advance, target_stage, missing_items = check_s3_to_s4_transition(
                self.db, project
            )
            if can_advance:
                transition_reason = "合同已签订，自动推进至方案设计阶段"

        elif current_stage == "S4":
            can_advance, target_stage, missing_items = check_s4_to_s5_transition(
                self.db, project_id
            )
            if can_advance:
                transition_reason = "BOM已发布，自动推进至采购制造阶段"

        elif current_stage == "S5":
            can_advance, target_stage, missing_items = check_s5_to_s6_transition(
                self.db, project
            )
            if can_advance:
                transition_reason = "物料齐套率≥80%，可推进至装配联调阶段"

        elif current_stage == "S7":
            can_advance, target_stage, missing_items = check_s7_to_s8_transition(
                self.db, project_id
            )
            if can_advance:
                transition_reason = "FAT验收已通过，自动推进至现场交付阶段"

        elif current_stage == "S8":
            can_advance, target_stage, missing_items = check_s8_to_s9_transition(
                self.db, project
            )
            if can_advance:
                transition_reason = "终验收已通过且回款达标，可推进至质保结项阶段"

        # 如果满足自动推进条件且auto_advance=True，执行自动推进
        if can_advance and auto_advance and target_stage:
            success, result = execute_stage_transition(
                self.db, project, target_stage, transition_reason
            )

            if success:
                # 记录状态变更
                self._log_status_change(
                    project_id,
                    old_stage=result["current_stage"],
                    new_stage=target_stage,
                    old_status=project.status,
                    new_status=project.status,
                    change_type="AUTO_STAGE_TRANSITION",
                    change_reason=transition_reason,
                )

                self.db.commit()

            return result

        return {
            "can_advance": can_advance,
            "auto_advanced": False,
            "message": "可推进" if can_advance else "不满足自动推进条件",
            "current_stage": current_stage,
            "target_stage": target_stage,
            "missing_items": missing_items,
            "transition_reason": transition_reason if can_advance else None,
        }

    # === 内部方法 ===

    def _log_status_change(
        self,
        project_id: int,
        old_stage: Optional[str] = None,
        new_stage: Optional[str] = None,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        old_health: Optional[str] = None,
        new_health: Optional[str] = None,
        change_type: str = "AUTO_TRANSITION",
        change_reason: Optional[str] = None,
        changed_by: Optional[int] = None,
    ):
        """记录状态变更历史"""
        log = ProjectStatusLog(
            project_id=project_id,
            old_stage=old_stage,
            new_stage=new_stage,
            old_status=old_status,
            new_status=new_status,
            old_health=old_health,
            new_health=new_health,
            change_type=change_type,
            change_reason=change_reason,
            changed_by=changed_by,
            changed_at=datetime.now(),
        )
        self.db.add(log)
