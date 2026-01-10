# -*- coding: utf-8 -*-
"""
项目状态联动规则引擎

实现设计文档中定义的状态自动流转规则，支持事件驱动的状态联动
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.project import Project, ProjectStatusLog, Machine
from app.models.sales import Contract
from app.models.acceptance import AcceptanceOrder
from app.models.ecn import Ecn
from app.services.health_calculator import HealthCalculator


class StatusTransitionService:
    """项目状态联动服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.health_calculator = HealthCalculator(db)
    
    def handle_contract_signed(self, contract_id: int, auto_create_project: bool = True) -> Optional[Project]:
        """
        处理合同签订事件
        
        规则：合同签订 → 自动创建项目，状态→S3/ST08
        
        Args:
            contract_id: 合同ID
            auto_create_project: 是否自动创建项目
            
        Returns:
            Project: 创建的项目对象，如果已存在则返回现有项目
        """
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return None
        
        # 如果项目已存在，更新项目信息
        if contract.project_id:
            project = self.db.query(Project).filter(Project.id == contract.project_id).first()
            if project:
                # 更新项目状态为 S3/ST08（合同签订后）
                old_stage = project.stage
                old_status = project.status
                
                project.stage = "S3"
                project.status = "ST08"
                project.contract_date = contract.signed_date
                project.contract_amount = contract.contract_amount or project.contract_amount
                
                # 记录状态变更
                self._log_status_change(
                    project.id,
                    old_stage=old_stage,
                    new_stage="S3",
                    old_status=old_status,
                    new_status="ST08",
                    change_type="CONTRACT_SIGNED",
                    change_reason="合同签订，自动更新项目状态"
                )
                
                self.db.commit()
                return project
        
        # 如果未启用自动创建，返回None
        if not auto_create_project:
            return None
        
        # 自动创建项目
        from app.utils.project_utils import generate_project_code, init_project_stages
        from app.models.user import User
        
        # 生成项目编码
        project_code = generate_project_code(self.db)
        
        # 获取客户信息
        from app.models.project import Customer
        customer = self.db.query(Customer).filter(Customer.id == contract.customer_id).first()
        
        # 创建项目
        fallback_name = getattr(contract, "contract_name", None)
        if not fallback_name:
            if customer and getattr(customer, "customer_name", None):
                fallback_name = f"{customer.customer_name}项目"
            else:
                fallback_name = f"项目-{contract.contract_code}"

        planned_end_date = getattr(contract, "delivery_deadline", None)

        project = Project(
            project_code=project_code,
            project_name=fallback_name,
            customer_id=contract.customer_id,
            contract_no=contract.contract_code,
            contract_amount=contract.contract_amount or 0,
            contract_date=contract.signed_date,
            planned_end_date=planned_end_date,
            stage="S3",
            status="ST08",
            health="H1",
        )
        
        # 填充客户信息
        if customer:
            project.customer_name = customer.customer_name
            project.customer_contact = customer.contact_person
            project.customer_phone = customer.contact_phone
        
        self.db.add(project)
        self.db.flush()
        
        # 关联合同和项目
        contract.project_id = project.id
        
        # 初始化项目阶段
        init_project_stages(self.db, project.id)
        
        # 记录状态变更
        self._log_status_change(
            project.id,
            old_stage=None,
            new_stage="S3",
            old_status=None,
            new_status="ST08",
            change_type="PROJECT_CREATED_FROM_CONTRACT",
            change_reason=f"合同签订自动创建项目，合同ID: {contract_id}"
        )
        
        self.db.commit()
        return project
    
    def handle_bom_published(self, project_id: int, machine_id: Optional[int] = None) -> bool:
        """
        处理BOM发布完成事件
        
        规则：BOM发布完成 → 项目状态自动更新为 S5/ST12
        
        Args:
            project_id: 项目ID
            machine_id: 设备ID（可选）
            
        Returns:
            bool: 是否成功更新
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        
        # 检查是否可以从S4推进到S5
        if project.stage != "S4":
            return False
        
        old_stage = project.stage
        old_status = project.status
        
        # 更新项目状态
        project.stage = "S5"
        project.status = "ST12"
        
        # 记录状态变更
        self._log_status_change(
            project_id,
            old_stage=old_stage,
            new_stage="S5",
            old_status=old_status,
            new_status="ST12",
            change_type="BOM_PUBLISHED",
            change_reason="BOM发布完成，自动推进至采购阶段"
        )
        
        self.db.commit()
        return True
    
    def handle_material_shortage(self, project_id: int, is_critical: bool = True) -> bool:
        """
        处理关键物料缺货事件
        
        规则：关键物料缺货 → 项目状态→ST14，健康度→H3
        
        Args:
            project_id: 项目ID
            is_critical: 是否为关键物料
            
        Returns:
            bool: 是否成功更新
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        
        if not is_critical:
            return False
        
        old_status = project.status
        old_health = project.health
        
        # 更新项目状态和健康度
        project.status = "ST14"
        project.health = "H3"
        
        # 记录状态变更
        self._log_status_change(
            project_id,
            old_stage=project.stage,
            new_stage=project.stage,
            old_status=old_status,
            new_status="ST14",
            old_health=old_health,
            new_health="H3",
            change_type="MATERIAL_SHORTAGE",
            change_reason="关键物料缺货，自动更新为阻塞状态"
        )
        
        self.db.commit()
        return True
    
    def handle_material_ready(self, project_id: int) -> bool:
        """
        处理物料齐套事件
        
        规则：物料齐套 → 项目状态→ST16，健康度→H1，可推进至S6
        
        Args:
            project_id: 项目ID
            
        Returns:
            bool: 是否成功更新
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        
        # 检查是否在S5阶段
        if project.stage != "S5":
            return False
        
        old_status = project.status
        old_health = project.health
        
        # 更新项目状态和健康度
        project.status = "ST16"
        project.health = "H1"
        
        # 记录状态变更
        self._log_status_change(
            project_id,
            old_stage=project.stage,
            new_stage=project.stage,
            old_status=old_status,
            new_status="ST16",
            old_health=old_health,
            new_health="H1",
            change_type="MATERIAL_READY",
            change_reason="物料齐套，可推进至装配阶段"
        )
        
        self.db.commit()
        return True
    
    def handle_fat_passed(self, project_id: int, machine_id: Optional[int] = None) -> bool:
        """
        处理FAT验收通过事件
        
        规则：FAT通过 → 状态→ST23，可推进至S8，健康度→H1
        
        Args:
            project_id: 项目ID
            machine_id: 设备ID（可选）
            
        Returns:
            bool: 是否成功更新
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        
        # 检查是否在S7阶段
        if project.stage != "S7":
            return False
        
        old_stage = project.stage
        old_status = project.status
        old_health = project.health
        
        # 更新项目状态
        project.stage = "S8"
        project.status = "ST23"
        if old_health == "H2":
            project.health = "H1"
        
        # 记录状态变更
        self._log_status_change(
            project_id,
            old_stage=old_stage,
            new_stage="S8",
            old_status=old_status,
            new_status="ST23",
            old_health=old_health,
            new_health=project.health,
            change_type="FAT_PASSED",
            change_reason="FAT验收通过，自动推进至现场交付阶段"
        )
        
        self.db.commit()
        return True
    
    def handle_fat_failed(self, project_id: int, machine_id: Optional[int] = None, issues: Optional[List[str]] = None) -> bool:
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
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        
        old_status = project.status
        old_health = project.health
        
        # 更新项目状态和健康度
        project.status = "ST22"
        project.health = "H2"
        
        # 记录整改项到项目风险信息
        if issues:
            risk_desc = f"FAT验收不通过，整改项：{', '.join(issues)}"
            if project.description:
                project.description += f"\n{risk_desc}"
            else:
                project.description = risk_desc
        
        # 记录状态变更
        self._log_status_change(
            project_id,
            old_stage=project.stage,
            new_stage=project.stage,
            old_status=old_status,
            new_status="ST22",
            old_health=old_health,
            new_health="H2",
            change_type="FAT_FAILED",
            change_reason="FAT验收不通过，需要整改"
        )
        
        self.db.commit()
        return True
    
    def handle_sat_passed(self, project_id: int, machine_id: Optional[int] = None) -> bool:
        """
        处理SAT验收通过事件
        
        规则：SAT通过 → 状态→ST27，可推进至S9
        
        Args:
            project_id: 项目ID
            machine_id: 设备ID（可选）
            
        Returns:
            bool: 是否成功更新
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        
        # 检查是否在S8阶段
        if project.stage != "S8":
            return False
        
        old_status = project.status
        
        # 更新项目状态
        project.status = "ST27"
        
        # 记录状态变更
        self._log_status_change(
            project_id,
            old_stage=project.stage,
            new_stage=project.stage,
            old_status=old_status,
            new_status="ST27",
            change_type="SAT_PASSED",
            change_reason="SAT验收通过，可推进至质保结项阶段"
        )
        
        self.db.commit()
        return True
    
    def handle_sat_failed(self, project_id: int, machine_id: Optional[int] = None, issues: Optional[List[str]] = None) -> bool:
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
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        
        old_status = project.status
        old_health = project.health
        
        # 更新项目状态和健康度
        project.status = "ST26"
        project.health = "H2"
        
        # 记录整改项到项目风险信息
        if issues:
            risk_desc = f"SAT验收不通过，整改项：{', '.join(issues)}"
            if project.description:
                project.description += f"\n{risk_desc}"
            else:
                project.description = risk_desc
        
        # 记录状态变更
        self._log_status_change(
            project_id,
            old_stage=project.stage,
            new_stage=project.stage,
            old_status=old_status,
            new_status="ST26",
            old_health=old_health,
            new_health="H2",
            change_type="SAT_FAILED",
            change_reason="SAT验收不通过，需要整改"
        )
        
        self.db.commit()
        return True
    
    def handle_final_acceptance_passed(self, project_id: int) -> bool:
        """
        处理终验收通过事件
        
        规则：终验收通过 → 可推进至S9
        
        Args:
            project_id: 项目ID
            
        Returns:
            bool: 是否成功更新
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        
        # 检查是否在S8阶段
        if project.stage != "S8":
            return False
        
        # 终验收通过后，项目可以推进至S9，但不自动推进
        # 需要检查回款达标等其他条件
        # 这里只记录状态变更，不自动推进阶段
        
        return True
    
    def handle_ecn_schedule_impact(self, project_id: int, ecn_id: int, impact_days: int) -> bool:
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
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        
        ecn = self.db.query(Ecn).filter(Ecn.id == ecn_id).first()
        if not ecn:
            return False
        
        # 更新协商交期（使用planned_end_date作为协商交期）
        if project.planned_end_date and impact_days > 0:
            from datetime import timedelta
            # 更新计划结束日期（作为协商交期）
            project.planned_end_date = project.planned_end_date + timedelta(days=impact_days)
        
        # 记录风险信息
        risk_desc = f"ECN变更影响交期：{impact_days}天，ECN编号：{ecn.ecn_no}"
        if project.description:
            project.description += f"\n{risk_desc}"
        else:
            project.description = risk_desc
        
        # 如果延期超过阈值（如7天），更新健康度为H2
        if impact_days > 7:
            old_health = project.health
            project.health = "H2"
            
            # 记录健康度变更
            self._log_status_change(
                project_id,
                old_stage=project.stage,
                new_stage=project.stage,
                old_status=project.status,
                new_status=project.status,
                old_health=old_health,
                new_health="H2",
                change_type="ECN_SCHEDULE_IMPACT",
                change_reason=risk_desc
            )
        
        self.db.commit()
        return True
    
    def check_auto_stage_transition(self, project_id: int, auto_advance: bool = False) -> Dict[str, Any]:
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
            execute_stage_transition
        )
        
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {
                "can_advance": False,
                "message": "项目不存在",
                "current_stage": None,
                "target_stage": None,
                "missing_items": []
            }
        
        current_stage = project.stage or "S1"
        can_advance = False
        target_stage = None
        missing_items = []
        transition_reason = ""
        
        # 根据当前阶段检查流转条件
        if current_stage == "S3":
            can_advance, target_stage, missing_items = check_s3_to_s4_transition(self.db, project)
            if can_advance:
                transition_reason = "合同已签订，自动推进至方案设计阶段"
        
        elif current_stage == "S4":
            can_advance, target_stage, missing_items = check_s4_to_s5_transition(self.db, project_id)
            if can_advance:
                transition_reason = "BOM已发布，自动推进至采购制造阶段"
        
        elif current_stage == "S5":
            can_advance, target_stage, missing_items = check_s5_to_s6_transition(self.db, project)
            if can_advance:
                transition_reason = "物料齐套率≥80%，可推进至装配联调阶段"
        
        elif current_stage == "S7":
            can_advance, target_stage, missing_items = check_s7_to_s8_transition(self.db, project_id)
            if can_advance:
                transition_reason = "FAT验收已通过，自动推进至现场交付阶段"
        
        elif current_stage == "S8":
            can_advance, target_stage, missing_items = check_s8_to_s9_transition(self.db, project)
            if can_advance:
                transition_reason = "终验收已通过且回款达标，可推进至质保结项阶段"
        
        # 如果满足自动推进条件且auto_advance=True，执行自动推进
        if can_advance and auto_advance and target_stage:
            success, result = execute_stage_transition(self.db, project, target_stage, transition_reason)
            
            if success:
                # 记录状态变更
                self._log_status_change(
                    project_id,
                    old_stage=result["current_stage"],
                    new_stage=target_stage,
                    old_status=project.status,
                    new_status=project.status,
                    change_type="AUTO_STAGE_TRANSITION",
                    change_reason=transition_reason
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
            "transition_reason": transition_reason if can_advance else None
        }
    
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
        changed_by: Optional[int] = None
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
            changed_at=datetime.now()
        )
        self.db.add(log)
