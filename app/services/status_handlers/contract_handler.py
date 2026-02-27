# -*- coding: utf-8 -*-
"""合同签订状态处理器"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatusLog, Customer
from app.models.sales import Contract
from app.utils.project_utils import generate_project_code, init_project_stages

if TYPE_CHECKING:
    from app.services.status_transition_service import StatusTransitionService


class ContractStatusHandler:
    """合同签订事件处理器"""

    def __init__(self, db: Session, parent: "StatusTransitionService" = None):
        self.db = db
        self._parent = parent

    def handle_contract_signed(
        self,
        contract_id: int,
        auto_create_project: bool = True,
        log_status_change=None,
    ) -> Optional[Project]:
        """
        处理合同签订事件

        规则：合同签订 → 自动创建项目，状态→S3/ST08

        Args:
            contract_id: 合同ID
            auto_create_project: 是否自动创建项目
            log_status_change: 状态变更日志记录函数

        Returns:
            Project: 创建的项目对象，如果已存在则返回现有项目
        """
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return None

        # 如果项目已存在，更新项目信息
        if contract.project_id:
            project = (
                self.db.query(Project).filter(Project.id == contract.project_id).first()
            )
            if project:
                # 更新项目状态为 S3/ST08（合同签订后）
                old_stage = project.stage
                old_status = project.status

                project.stage = "S3"
                project.status = "ST08"
                project.contract_date = contract.signing_date
                project.contract_amount = (
                    contract.contract_amount or project.contract_amount
                )
                # 同步客户合同编号
                if hasattr(contract, "customer_contract_no") and contract.customer_contract_no:
                    project.customer_contract_no = contract.customer_contract_no

                # 记录状态变更
                self._log_status_change(
                    project.id,
                    old_stage=old_stage,
                    new_stage="S3",
                    old_status=old_status,
                    new_status="ST08",
                    change_type="CONTRACT_SIGNED",
                    change_reason="合同签订，自动更新项目状态",
                    log_status_change=log_status_change,
                )

                self.db.commit()
                return project

        # 如果未启用自动创建，返回None
        if not auto_create_project:
            return None

        # 自动创建项目

        # 生成项目编码
        project_code = generate_project_code(self.db)

        # 获取客户信息
        customer = (
            self.db.query(Customer).filter(Customer.id == contract.customer_id).first()
        )

        # 创建项目
        fallback_name = getattr(contract, "contract_name", None)
        if not fallback_name:
            if customer and getattr(customer, "customer_name", None):
                fallback_name = f"{customer.customer_name}项目"
            else:
                fallback_name = f"项目-{contract.contract_code}"

        planned_end_date = getattr(contract, "delivery_deadline", None)

        # 获取线索ID（通过商机关联）
        lead_id = None
        if contract.opportunity_id:
            from app.models.sales import Opportunity
            opportunity = (
                self.db.query(Opportunity)
                .filter(Opportunity.id == contract.opportunity_id)
                .first()
            )
            if opportunity and hasattr(opportunity, "lead_id"):
                lead_id = opportunity.lead_id

        project = Project(
            project_code=project_code,
            project_name=fallback_name,
            customer_id=contract.customer_id,
            contract_no=contract.contract_code,
            customer_contract_no=getattr(contract, "customer_contract_no", None),
            contract_amount=contract.contract_amount or 0,
            contract_date=contract.signing_date,
            planned_end_date=planned_end_date,
            stage="S3",
            status="ST08",
            health="H1",
            lead_id=lead_id,
            opportunity_id=contract.opportunity_id,
            contract_id=contract.id,
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
            change_reason=f"合同签订自动创建项目，合同ID: {contract_id}",
            log_status_change=log_status_change,
        )

        self.db.commit()
        return project

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
        log_status_change=None,
    ):
        """记录状态变更历史"""
        if log_status_change:
            log_status_change(
                project_id,
                old_stage=old_stage,
                new_stage=new_stage,
                old_status=old_status,
                new_status=new_status,
                old_health=old_health,
                new_health=new_health,
                change_type=change_type,
                change_reason=change_reason,
                changed_by=changed_by,
            )
            return

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
