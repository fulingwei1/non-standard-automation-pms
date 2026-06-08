# -*- coding: utf-8 -*-
"""合同签订状态处理器"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.presale import PresaleSolution, PresaleSupportTicket
from app.models.project import Customer, Project, ProjectStatusLog
from app.models.sales import Contract, Opportunity, QuoteVersion
from app.services.sales.presale_quote_context import resolve_presale_context_for_quote_version
from app.utils.project_utils import generate_project_code, init_project_stages

if TYPE_CHECKING:
    from app.services.status_transition_service import StatusTransitionService


def _load_project_contract(db: Session, project: Project) -> Optional[Contract]:
    if getattr(project, "contract_id", None):
        contract = db.query(Contract).filter(Contract.id == project.contract_id).first()
        if contract:
            return contract

    return db.query(Contract).filter(Contract.project_id == project.id).first()


def _load_quote_selected_presale_context(
    db: Session, project: Project
) -> tuple[list[PresaleSolution], set[int]]:
    contract = _load_project_contract(db, project)
    if not contract or not contract.quote_id:
        return [], set()

    quote_version = db.query(QuoteVersion).filter(QuoteVersion.id == contract.quote_id).first()
    if not quote_version:
        return [], set()

    return resolve_presale_context_for_quote_version(db, quote_version)


def bind_presale_context_to_project(db: Session, project: Project) -> None:
    """把签约前的售前工单和方案正式绑定到新项目，避免交接数据只靠商机旁路查询。"""
    if not project or not project.id:
        return

    quote_selected_solutions, selected_ticket_ids = _load_quote_selected_presale_context(
        db, project
    )
    selected_solution_ids = {solution.id for solution in quote_selected_solutions}

    ticket_scope_filters = []
    if project.opportunity_id:
        ticket_scope_filters.append(PresaleSupportTicket.opportunity_id == project.opportunity_id)
    if project.lead_id:
        ticket_scope_filters.append(PresaleSupportTicket.lead_id == project.lead_id)

    ticket_filters = [PresaleSupportTicket.project_id == project.id]
    if selected_ticket_ids:
        ticket_filters.append(PresaleSupportTicket.id.in_(selected_ticket_ids))
    elif ticket_scope_filters:
        ticket_filters.append(
            and_(
                PresaleSupportTicket.project_id.is_(None),
                or_(*ticket_scope_filters),
            )
        )

    tickets = db.query(PresaleSupportTicket).filter(or_(*ticket_filters)).all()
    ticket_project_by_id = {ticket.id: ticket.project_id for ticket in tickets}
    bound_ticket_ids = set()
    for ticket in tickets:
        if ticket.project_id is None:
            ticket.project_id = project.id
        if ticket.project_id == project.id:
            bound_ticket_ids.add(ticket.id)
            ticket_project_by_id[ticket.id] = project.id

    solution_scope_filters = [PresaleSolution.project_id == project.id]
    if selected_solution_ids:
        solution_scope_filters.append(PresaleSolution.id.in_(selected_solution_ids))
    else:
        unbound_solution_filters = []
        if project.opportunity_id:
            unbound_solution_filters.append(PresaleSolution.opportunity_id == project.opportunity_id)
        if bound_ticket_ids:
            unbound_solution_filters.append(PresaleSolution.ticket_id.in_(bound_ticket_ids))

        if unbound_solution_filters:
            solution_scope_filters.append(
                and_(
                    PresaleSolution.project_id.is_(None),
                    or_(*unbound_solution_filters),
                )
            )

    solutions = db.query(PresaleSolution).filter(or_(*solution_scope_filters)).all()
    missing_ticket_ids = {
        solution.ticket_id
        for solution in solutions
        if solution.ticket_id and solution.ticket_id not in ticket_project_by_id
    }
    if missing_ticket_ids:
        existing_ticket_projects = (
            db.query(PresaleSupportTicket.id, PresaleSupportTicket.project_id)
            .filter(PresaleSupportTicket.id.in_(missing_ticket_ids))
            .all()
        )
        ticket_project_by_id.update(dict(existing_ticket_projects))

    for solution in solutions:
        if solution.project_id == project.id:
            continue
        if solution.project_id is not None:
            continue
        ticket_project_id = (
            ticket_project_by_id.get(solution.ticket_id) if solution.ticket_id else None
        )
        if ticket_project_id not in (None, project.id):
            continue
        solution.project_id = project.id


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

        customer = self.db.query(Customer).filter(Customer.id == contract.customer_id).first()
        quote_version = None
        if contract.quote_id:
            quote_version = (
                self.db.query(QuoteVersion).filter(QuoteVersion.id == contract.quote_id).first()
            )

        opportunity = None
        if contract.opportunity_id:
            opportunity = (
                self.db.query(Opportunity).filter(Opportunity.id == contract.opportunity_id).first()
            )

        salesperson_id = contract.sales_owner_id or (opportunity.owner_id if opportunity else None)

        # 如果项目已存在，更新项目信息
        if contract.project_id:
            project = self.db.query(Project).filter(Project.id == contract.project_id).first()
            if project:
                # 更新项目状态为 S3/ST08（合同签订后）
                old_stage = project.stage
                old_status = project.status

                project.stage = "S3"
                project.status = "ST08"
                project.contract_date = contract.signing_date
                project.contract_amount = contract.contract_amount or project.contract_amount
                if quote_version and quote_version.cost_total is not None:
                    project.budget_amount = quote_version.cost_total
                if opportunity:
                    project.lead_id = project.lead_id or opportunity.lead_id
                    project.opportunity_id = project.opportunity_id or opportunity.id
                    project.project_type = project.project_type or opportunity.project_type
                    project.product_category = project.product_category or opportunity.equipment_type
                if customer:
                    project.industry = project.industry or customer.industry
                project.salesperson_id = project.salesperson_id or salesperson_id
                bind_presale_context_to_project(self.db, project)
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

        # 创建项目
        fallback_name = getattr(contract, "contract_name", None)
        if not fallback_name:
            if customer and getattr(customer, "customer_name", None):
                fallback_name = f"{customer.customer_name}项目"
            else:
                fallback_name = f"项目-{contract.contract_code}"

        planned_end_date = getattr(contract, "delivery_deadline", None)

        # 获取线索ID（通过商机关联）
        lead_id = opportunity.lead_id if opportunity else None

        project = Project(
            project_code=project_code,
            project_name=fallback_name,
            customer_id=contract.customer_id,
            contract_no=contract.contract_code,
            customer_contract_no=getattr(contract, "customer_contract_no", None),
            contract_amount=contract.contract_amount or 0,
            budget_amount=(
                quote_version.cost_total
                if quote_version and quote_version.cost_total is not None
                else 0
            ),
            contract_date=contract.signing_date,
            planned_end_date=planned_end_date,
            project_type=opportunity.project_type if opportunity else None,
            product_category=opportunity.equipment_type if opportunity else None,
            industry=customer.industry if customer else None,
            stage="S3",
            status="ST08",
            health="H1",
            lead_id=lead_id,
            opportunity_id=contract.opportunity_id,
            contract_id=contract.id,
            salesperson_id=salesperson_id,
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
        bind_presale_context_to_project(self.db, project)

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
