# -*- coding: utf-8 -*-
"""
PMO 立项管理服务层
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.models.pmo import PmoProjectInitiation
from app.models.presale import PresaleSolution, PresaleSupportTicket
from app.models.project import Customer, Project
from app.models.sales import Contract, Opportunity
from app.models.user import User
from app.schemas.pmo import (
    InitiationApproveRequest,
    InitiationCreate,
    InitiationRejectRequest,
    InitiationUpdate,
)
from app.utils.domain_codes import pmo as pmo_codes


class PmoInitiationService:
    """PMO 立项管理服务"""

    ACTIVE_INITIATION_STATUSES = ("DRAFT", "SUBMITTED", "REVIEWING")

    def __init__(self, db: Session):
        self.db = db

    def get_initiations(
        self,
        offset: int,
        limit: int,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        applicant_id: Optional[int] = None,
        contract_no: Optional[str] = None,
    ) -> Tuple[List[PmoProjectInitiation], int]:
        """
        获取立项申请列表

        Args:
            offset: 偏移量
            limit: 每页数量
            keyword: 关键词搜索
            status: 状态筛选
            applicant_id: 申请人ID筛选
            contract_no: 合同编号筛选

        Returns:
            (立项申请列表, 总数)
        """
        query = self.db.query(PmoProjectInitiation)

        # 应用关键词搜索
        query = apply_keyword_filter(
            query,
            PmoProjectInitiation,
            keyword,
            ["application_no", "project_name", "contract_no"],
        )

        # 状态筛选
        if status:
            query = query.filter(PmoProjectInitiation.status == status)

        # 申请人筛选
        if applicant_id:
            query = query.filter(PmoProjectInitiation.applicant_id == applicant_id)

        # 合同编号筛选，用于合同详情页避免重复创建立项申请
        if contract_no:
            query = query.filter(PmoProjectInitiation.contract_no == contract_no)

        # 计算总数
        total = query.count()

        # 分页查询
        initiations = apply_pagination(
            query.order_by(desc(PmoProjectInitiation.created_at)), offset, limit
        ).all()

        return initiations, total

    def get_initiation(self, initiation_id: int) -> Optional[PmoProjectInitiation]:
        """
        获取立项申请详情

        Args:
            initiation_id: 立项申请ID

        Returns:
            立项申请对象，不存在返回 None
        """
        return (
            self.db.query(PmoProjectInitiation)
            .filter(PmoProjectInitiation.id == initiation_id)
            .first()
        )

    def get_project_manager_candidates(self, limit: int = 200) -> List[User]:
        """获取立项审批可选项目经理。"""
        users = (
            self.db.query(User)
            .filter(User.is_active.is_(True))
            .order_by(User.id)
            .limit(limit)
            .all()
        )

        candidates = []
        for user in users:
            role_codes = {str(code).lower() for code in (user.role_codes or []) if code}
            profile_text = " ".join(
                str(value).lower()
                for value in [
                    user.position,
                    user.department,
                    user.real_name,
                    user.username,
                ]
                if value
            )

            if (
                role_codes.intersection({"pm", "pmc", "pmo", "pmo_dir"})
                or "项目经理" in profile_text
                or "pm" in profile_text
                or "pmc" in profile_text
            ):
                candidates.append(user)

        return candidates or users

    def build_presale_handover_context(
        self, initiation: PmoProjectInitiation
    ) -> Dict[str, Any]:
        """构建立项审批前可查看的销售/售前交接包。"""
        from app.services.project_workspace_service import (
            _build_contract_payload,
            _build_opportunity_payload,
            _build_presale_solution_payload,
            _build_presale_ticket_payload,
            _num,
            build_technical_assessment_handover_context,
        )

        contract = self._find_contract_for_initiation(initiation)
        solution = self._find_solution_for_initiation(initiation)
        ticket = None
        if solution and getattr(solution, "ticket_id", None):
            ticket = (
                self.db.query(PresaleSupportTicket)
                .filter(PresaleSupportTicket.id == solution.ticket_id)
                .first()
            )

        opportunity = getattr(contract, "opportunity", None) if contract else None
        if not opportunity and solution and getattr(solution, "opportunity_id", None):
            opportunity = (
                self.db.query(Opportunity)
                .filter(Opportunity.id == solution.opportunity_id)
                .first()
            )
        technical_assessment = build_technical_assessment_handover_context(
            self.db,
            opportunity=opportunity,
            tickets=[ticket] if ticket else [],
            lead_id=getattr(opportunity, "lead_id", None) if opportunity else None,
        )

        presale_estimated_cost = (
            getattr(solution, "estimated_cost", None) if solution else None
        )
        baseline_cost = {
            "contract_amount": _num(
                getattr(contract, "total_amount", None)
                if contract
                else initiation.contract_amount
            ),
            "presale_estimated_cost": _num(presale_estimated_cost),
            "presale_suggested_price": _num(
                getattr(solution, "suggested_price", None) if solution else None
            ),
            "estimated_hours": (
                getattr(solution, "estimated_hours", None)
                if solution and getattr(solution, "estimated_hours", None) is not None
                else initiation.estimated_hours
            ),
        }

        missing = []
        if not contract:
            missing.append("contract")
        if not opportunity:
            missing.append("opportunity")
        if not solution:
            missing.append("presale_solution")
        if not ticket:
            missing.append("presale_ticket")
        if not technical_assessment["current"]:
            missing.append("technical_assessment")
        if (
            baseline_cost["contract_amount"] is None
            and baseline_cost["presale_estimated_cost"] is None
        ):
            missing.append("baseline_cost")

        return {
            "contract": _build_contract_payload(contract),
            "opportunity": _build_opportunity_payload(opportunity),
            "presale_solution": (
                _build_presale_solution_payload(solution) if solution else None
            ),
            "presale_ticket": _build_presale_ticket_payload(ticket) if ticket else None,
            "technical_assessment": technical_assessment,
            "baseline_cost": baseline_cost,
            "handover_status": {
                "ready": not missing,
                "missing": missing,
            },
        }

    def create_initiation(
        self, initiation_in: InitiationCreate, current_user: User
    ) -> PmoProjectInitiation:
        """
        创建立项申请

        Args:
            initiation_in: 创建数据
            current_user: 当前用户

        Returns:
            创建的立项申请对象
        """
        contract_no = (initiation_in.contract_no or "").strip() or None
        if contract_no:
            existing_initiation = self._find_active_initiation_by_contract_no(contract_no)
            if existing_initiation:
                application_no = (
                    getattr(existing_initiation, "application_no", None)
                    or f"ID {existing_initiation.id}"
                )
                raise ValueError(
                    f"合同 {contract_no} 已存在未完成的立项申请（{application_no}），请继续处理原申请"
                )

        initiation = PmoProjectInitiation(
            application_no=pmo_codes.generate_initiation_no(self.db),
            project_name=initiation_in.project_name,
            project_type=initiation_in.project_type,
            project_level=initiation_in.project_level,
            customer_name=initiation_in.customer_name,
            contract_no=contract_no,
            contract_amount=initiation_in.contract_amount,
            required_start_date=initiation_in.required_start_date,
            required_end_date=initiation_in.required_end_date,
            technical_solution_id=initiation_in.technical_solution_id,
            requirement_summary=initiation_in.requirement_summary,
            technical_difficulty=initiation_in.technical_difficulty,
            estimated_hours=initiation_in.estimated_hours,
            resource_requirements=initiation_in.resource_requirements,
            risk_assessment=initiation_in.risk_assessment,
            applicant_id=current_user.id,
            applicant_name=current_user.real_name or current_user.username,
            apply_time=datetime.now(),
            status="DRAFT",
        )

        self.db.add(initiation)
        self.db.commit()
        self.db.refresh(initiation)

        return initiation

    def update_initiation(
        self, initiation_id: int, initiation_in: InitiationUpdate
    ) -> PmoProjectInitiation:
        """
        更新立项申请

        Args:
            initiation_id: 立项申请ID
            initiation_in: 更新数据

        Returns:
            更新后的立项申请对象

        Raises:
            ValueError: 立项申请不存在或状态不允许修改
        """
        initiation = self.get_initiation(initiation_id)
        if not initiation:
            raise ValueError("立项申请不存在")

        if initiation.status != "DRAFT":
            raise ValueError("只有草稿状态的申请才能修改")

        update_data = initiation_in.model_dump(exclude_unset=True)
        if "contract_no" in update_data:
            contract_no = (update_data["contract_no"] or "").strip() or None
            if contract_no:
                existing_initiation = self._find_active_initiation_by_contract_no(
                    contract_no, exclude_id=initiation_id
                )
                if existing_initiation:
                    application_no = (
                        getattr(existing_initiation, "application_no", None)
                        or f"ID {existing_initiation.id}"
                    )
                    raise ValueError(
                        f"合同 {contract_no} 已存在未完成的立项申请（{application_no}），不能重复关联"
                    )
            update_data["contract_no"] = contract_no

        for field, value in update_data.items():
            setattr(initiation, field, value)

        self.db.add(initiation)
        self.db.commit()
        self.db.refresh(initiation)

        return initiation

    def submit_initiation(self, initiation_id: int) -> PmoProjectInitiation:
        """
        提交立项评审

        Args:
            initiation_id: 立项申请ID

        Returns:
            更新后的立项申请对象

        Raises:
            ValueError: 立项申请不存在或状态不允许提交
        """
        initiation = self.get_initiation(initiation_id)
        if not initiation:
            raise ValueError("立项申请不存在")

        if initiation.status != "DRAFT":
            raise ValueError("只有草稿状态的申请才能提交")

        initiation.status = "SUBMITTED"
        self.db.add(initiation)
        self.db.commit()
        self.db.refresh(initiation)

        return initiation

    def approve_initiation(
        self,
        initiation_id: int,
        approve_request: InitiationApproveRequest,
        current_user: User,
    ) -> PmoProjectInitiation:
        """
        立项评审通过

        Args:
            initiation_id: 立项申请ID
            approve_request: 审批请求数据
            current_user: 当前用户

        Returns:
            更新后的立项申请对象

        Raises:
            ValueError: 立项申请不存在或状态不允许审批
        """
        initiation = self.get_initiation(initiation_id)
        if not initiation:
            raise ValueError("立项申请不存在")

        if initiation.status not in ["SUBMITTED", "REVIEWING"]:
            raise ValueError("只有已提交或评审中的申请才能审批")

        # 更新审批信息
        initiation.status = "APPROVED"
        initiation.review_result = approve_request.review_result
        initiation.approved_pm_id = approve_request.approved_pm_id
        initiation.approved_level = approve_request.approved_level
        initiation.approved_at = datetime.now()
        initiation.approved_by = current_user.id

        # 如果指定了项目经理，创建项目
        if approve_request.approved_pm_id:
            project = self._create_project_from_initiation(
                initiation, approve_request.approved_pm_id
            )
            initiation.project_id = project.id

        self.db.add(initiation)
        self.db.commit()
        self.db.refresh(initiation)

        return initiation

    def reject_initiation(
        self,
        initiation_id: int,
        reject_request: InitiationRejectRequest,
        current_user: User,
    ) -> PmoProjectInitiation:
        """
        立项评审驳回

        Args:
            initiation_id: 立项申请ID
            reject_request: 驳回请求数据
            current_user: 当前用户

        Returns:
            更新后的立项申请对象

        Raises:
            ValueError: 立项申请不存在或状态不允许驳回
        """
        initiation = self.get_initiation(initiation_id)
        if not initiation:
            raise ValueError("立项申请不存在")

        if initiation.status not in ["SUBMITTED", "REVIEWING"]:
            raise ValueError("只有已提交或评审中的申请才能驳回")

        initiation.status = "REJECTED"
        initiation.review_result = reject_request.review_result
        initiation.approved_at = datetime.now()
        initiation.approved_by = current_user.id

        self.db.add(initiation)
        self.db.commit()
        self.db.refresh(initiation)

        return initiation

    def _create_project_from_initiation(
        self, initiation: PmoProjectInitiation, pm_id: int
    ) -> Project:
        """
        从立项申请创建项目（内部方法）

        Args:
            initiation: 立项申请对象
            pm_id: 项目经理ID

        Returns:
            创建的项目对象
        """
        # 生成项目编码
        today = date.today()
        project_code = f"PJ{today.strftime('%y%m%d')}{initiation.id:03d}"

        # 检查项目编码是否已存在
        existing = self.db.query(Project).filter(Project.project_code == project_code).first()
        if existing:
            project_code = f"PJ{today.strftime('%y%m%d')}{initiation.id:04d}"

        contract = self._find_contract_for_initiation(initiation)
        presale_solution = self._find_solution_for_initiation(initiation)
        if contract and contract.project_id:
            existing_project = (
                self.db.query(Project).filter(Project.id == contract.project_id).first()
            )
            if existing_project:
                self._bind_presale_solution_to_project(presale_solution, existing_project.id)
                self._ensure_payment_plans_for_contract(contract)
                return existing_project

        customer = None
        if contract and contract.customer_id:
            customer = (
                self.db.query(Customer)
                .filter(Customer.id == contract.customer_id)
                .first()
            )

        if not customer and presale_solution and getattr(presale_solution, "customer_id", None):
            customer = (
                self.db.query(Customer)
                .filter(Customer.id == presale_solution.customer_id)
                .first()
            )

        if not customer:
            customer = (
                self.db.query(Customer)
                .filter(Customer.customer_name == initiation.customer_name)
                .first()
            )

        customer_id = customer.id if customer else None
        solution_amount = None
        if presale_solution:
            solution_amount = (
                getattr(presale_solution, "suggested_price", None)
                or getattr(presale_solution, "estimated_cost", None)
            )
        contract_amount = (
            getattr(contract, "total_amount", None)
            if contract
            else None
        ) or initiation.contract_amount or solution_amount or Decimal("0")
        contract_no = (
            getattr(contract, "contract_code", None)
            if contract
            else None
        ) or initiation.contract_no
        opportunity_id = getattr(contract, "opportunity_id", None) if contract else None
        if not opportunity_id and presale_solution:
            opportunity_id = getattr(presale_solution, "opportunity_id", None)
        lead_id = None
        if opportunity_id:
            opportunity = (
                self.db.query(Opportunity)
                .filter(Opportunity.id == opportunity_id)
                .first()
            )
            lead_id = getattr(opportunity, "lead_id", None) if opportunity else None

        # 创建项目
        project = Project(
            project_code=project_code,
            project_name=initiation.project_name,
            customer_id=customer_id,
            customer_name=(
                getattr(customer, "customer_name", None)
                if customer
                else initiation.customer_name
            ),
            customer_contact=getattr(customer, "contact_person", None) if customer else None,
            customer_phone=getattr(customer, "contact_phone", None) if customer else None,
            contract_no=contract_no,
            customer_contract_no=(
                getattr(contract, "customer_contract_no", None)
                if contract
                else None
            ),
            contract_amount=contract_amount,
            contract_date=(
                getattr(contract, "signing_date", None)
                if contract
                else None
            ) or initiation.required_start_date,
            planned_start_date=initiation.required_start_date,
            planned_end_date=initiation.required_end_date,
            pm_id=pm_id,
            project_type=initiation.project_type,
            stage="S1",
            status="ST01",
            health="H1",
            lead_id=lead_id,
            opportunity_id=opportunity_id,
            contract_id=getattr(contract, "id", None) if contract else None,
        )

        # 填充项目经理信息
        pm = self.db.query(User).filter(User.id == pm_id).first()
        if pm:
            project.pm_name = pm.real_name or pm.username

        self.db.add(project)
        self.db.flush()

        self._bind_presale_solution_to_project(presale_solution, project.id)

        if contract:
            contract.project_id = project.id
            self.db.add(contract)

        # 初始化项目阶段
        from app.utils.project_utils import init_project_stages

        init_project_stages(self.db, project.id)
        if contract:
            self._ensure_payment_plans_for_contract(contract)

        return project

    def _find_contract_for_initiation(
        self, initiation: PmoProjectInitiation
    ) -> Optional[Contract]:
        """按立项申请中的合同编号回找销售合同。"""
        if not initiation.contract_no:
            return None

        return (
            self.db.query(Contract)
            .filter(
                or_(
                    Contract.contract_code == initiation.contract_no,
                    Contract.customer_contract_no == initiation.contract_no,
                )
            )
            .first()
        )

    def _find_solution_for_initiation(
        self, initiation: PmoProjectInitiation
    ) -> Optional[PresaleSolution]:
        """按立项申请中的售前技术方案ID回找方案。"""
        solution_id = getattr(initiation, "technical_solution_id", None)
        if not isinstance(solution_id, int) or solution_id <= 0:
            return None

        return (
            self.db.query(PresaleSolution)
            .filter(PresaleSolution.id == solution_id)
            .first()
        )

    def _bind_presale_solution_to_project(
        self, presale_solution: Optional[PresaleSolution], project_id: Optional[int]
    ) -> None:
        """审批立项创建项目后，把售前方案和原工单反向绑定到项目。"""
        if not presale_solution or not project_id:
            return

        if not getattr(presale_solution, "project_id", None):
            presale_solution.project_id = project_id

        ticket_id = getattr(presale_solution, "ticket_id", None)
        if not ticket_id:
            return

        ticket = (
            self.db.query(PresaleSupportTicket)
            .filter(PresaleSupportTicket.id == ticket_id)
            .first()
        )
        if ticket and not getattr(ticket, "project_id", None):
            ticket.project_id = project_id

    def _find_active_initiation_by_contract_no(
        self, contract_no: str, exclude_id: Optional[int] = None
    ) -> Optional[PmoProjectInitiation]:
        """查找同合同号的未终态立项申请，防止销售重复发起。"""
        query = self.db.query(PmoProjectInitiation).filter(
            PmoProjectInitiation.contract_no == contract_no,
            PmoProjectInitiation.status.in_(self.ACTIVE_INITIATION_STATUSES),
        )
        if exclude_id is not None:
            query = query.filter(PmoProjectInitiation.id != exclude_id)
        return query.first()

    def _ensure_payment_plans_for_contract(self, contract: Contract) -> None:
        """PMO 审批创建项目后，为已签订合同补齐收款计划。"""
        if not contract or not getattr(contract, "project_id", None):
            return

        if str(getattr(contract, "status", "")).upper() != "SIGNED":
            return

        from app.services.sales.payment_plan_service import PaymentPlanService

        PaymentPlanService(self.db).generate_payment_plans_from_contract(contract)
