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
from app.models.enums import AssessmentSourceTypeEnum, OpenItemStatusEnum
from app.models.pmo import PmoProjectInitiation
from app.models.presale import PresaleSolution, PresaleSupportTicket
from app.models.project import Customer, Project
from app.models.sales import Contract, OpenItem, Opportunity, QuoteVersion
from app.models.task_center import (
    TaskPriorityEnum,
    TaskStatusEnum,
    TaskTypeEnum,
    TaskUnified,
)
from app.models.user import User
from app.schemas.pmo import (
    InitiationApproveRequest,
    InitiationCreate,
    InitiationRejectRequest,
    InitiationUpdate,
)
from app.services.sales.presale_quote_context import (
    resolve_presale_context_for_quote_version,
)
from app.utils.domain_codes import pmo as pmo_codes, task_center as task_center_codes


def _has_meaningful_assessment_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    text = str(value).strip()
    return bool(text) and text.lower() not in {"null", "none", "[]", "{}"}


def _has_substantive_technical_assessment(assessment: Optional[Dict[str, Any]]) -> bool:
    if not assessment:
        return False
    if bool(assessment.get("auto_generated")):
        return False
    if assessment.get("total_score") is not None:
        return True
    evidence_fields = (
        "dimension_scores",
        "item_scores",
        "risks",
        "similar_cases",
        "conditions",
        "ai_analysis",
        "veto_rules",
    )
    return any(
        _has_meaningful_assessment_value(assessment.get(field))
        for field in evidence_fields
    )


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
        solution = self._find_solution_for_initiation(initiation, contract)
        ticket = self._find_ticket_for_solution(solution)

        opportunity = getattr(contract, "opportunity", None) if contract else None
        if not opportunity and solution and getattr(solution, "opportunity_id", None):
            opportunity = (
                self.db.query(Opportunity)
                .filter(Opportunity.id == solution.opportunity_id)
                .first()
            )
        lead_id = getattr(opportunity, "lead_id", None) if opportunity else None
        if not lead_id and ticket:
            lead_id = getattr(ticket, "lead_id", None)
        technical_assessment = build_technical_assessment_handover_context(
            self.db,
            opportunity=opportunity,
            tickets=[ticket] if ticket else [],
            lead_id=lead_id,
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
        if not _has_substantive_technical_assessment(technical_assessment["current"]):
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

        # 售前技术支持关卡：缺少售前技术评估不允许提交立项评审
        # （非标自动化项目常因技术需求不清晰而失败，立项前必须由售前技术支持部完成初评）
        from app.core.config import settings

        if getattr(settings, "PMO_REQUIRE_PRESALE_ASSESSMENT", True):
            try:
                handover = self.build_presale_handover_context(initiation)
                missing = handover.get("handover_status", {}).get("missing", [])
                current_assessment = (
                    handover.get("technical_assessment") or {}
                ).get("current") or {}
            except Exception as exc:
                raise ValueError(
                    "售前技术评估检查失败，无法提交立项。请确认售前交接信息完整后重试。"
                ) from exc
            if "technical_assessment" in missing:
                raise ValueError(
                    "缺少售前技术评估，无法提交立项。请先向售前技术支持部申请技术支持并完成技术初评后再提交立项。"
                )
            # 仅有评估申请（PENDING/IN_PROGRESS）不算完成初评，必须评估执行完毕才能提交
            assessment_status = current_assessment.get("status")
            if assessment_status and assessment_status != "COMPLETED":
                raise ValueError(
                    f"售前技术评估尚未完成（当前状态：{assessment_status}），"
                    "请等售前技术支持部完成技术初评后再提交立项。"
                )
            if not _has_substantive_technical_assessment(current_assessment):
                raise ValueError(
                    "售前技术评估缺少实际评估内容，无法提交立项。"
                    "请完成评分、风险、条件或AI分析后再提交。"
                )

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

        if not approve_request.approved_pm_id:
            raise ValueError("审批通过必须指定项目经理，否则不会创建项目")

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
            self._sync_presale_open_items_to_project_tasks(
                project,
                approve_request.approved_pm_id,
                current_user,
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
        presale_solution = self._find_solution_for_initiation(initiation, contract)
        presale_ticket = self._find_ticket_for_solution(presale_solution)
        if contract and contract.project_id:
            existing_project = (
                self.db.query(Project).filter(Project.id == contract.project_id).first()
            )
            if existing_project:
                self._backfill_existing_project_sales_context(
                    existing_project,
                    contract,
                    presale_solution,
                    presale_ticket,
                )
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

        if not customer and presale_ticket and getattr(presale_ticket, "customer_id", None):
            customer = (
                self.db.query(Customer)
                .filter(Customer.id == presale_ticket.customer_id)
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
        if not opportunity_id and presale_ticket:
            opportunity_id = getattr(presale_ticket, "opportunity_id", None)
        lead_id = None
        if opportunity_id:
            opportunity = (
                self.db.query(Opportunity)
                .filter(Opportunity.id == opportunity_id)
                .first()
            )
            lead_id = getattr(opportunity, "lead_id", None) if opportunity else None
        if not lead_id and presale_ticket:
            lead_id = getattr(presale_ticket, "lead_id", None)

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

    def _backfill_existing_project_sales_context(
        self,
        project: Project,
        contract: Optional[Contract],
        presale_solution: Optional[PresaleSolution],
        presale_ticket: Optional[PresaleSupportTicket] = None,
    ) -> None:
        """复用已有项目时补齐销售/售前来源，保证后续交接同步能追溯。"""
        if contract:
            if not getattr(project, "contract_id", None):
                project.contract_id = getattr(contract, "id", None)
            if not getattr(project, "contract_no", None):
                project.contract_no = getattr(contract, "contract_code", None)
            if not getattr(project, "customer_contract_no", None):
                project.customer_contract_no = getattr(contract, "customer_contract_no", None)
            if not getattr(project, "opportunity_id", None):
                project.opportunity_id = getattr(contract, "opportunity_id", None)

        if presale_solution and not getattr(project, "opportunity_id", None):
            project.opportunity_id = getattr(presale_solution, "opportunity_id", None)

        if presale_ticket and not getattr(project, "opportunity_id", None):
            project.opportunity_id = getattr(presale_ticket, "opportunity_id", None)

        if getattr(project, "opportunity_id", None) and not getattr(project, "lead_id", None):
            opportunity = (
                self.db.query(Opportunity)
                .filter(Opportunity.id == project.opportunity_id)
                .first()
            )
            project.lead_id = getattr(opportunity, "lead_id", None) if opportunity else None

        if presale_ticket and not getattr(project, "lead_id", None):
            project.lead_id = getattr(presale_ticket, "lead_id", None)

        self.db.add(project)

    def _sync_presale_open_items_to_project_tasks(
        self,
        project: Optional[Project],
        pm_id: Optional[int],
        current_user: Optional[User],
    ) -> int:
        """把销售/售前未闭环事项沉淀成项目侧可执行任务。"""
        if not project or not getattr(project, "id", None):
            return 0

        source_filters = []
        opportunity_id = getattr(project, "opportunity_id", None)
        lead_id = getattr(project, "lead_id", None)

        if opportunity_id:
            source_filters.append(
                (
                    OpenItem.source_type == AssessmentSourceTypeEnum.OPPORTUNITY.value,
                    OpenItem.source_id == opportunity_id,
                )
            )
            if not lead_id:
                opportunity = (
                    self.db.query(Opportunity)
                    .filter(Opportunity.id == opportunity_id)
                    .first()
                )
                lead_id = getattr(opportunity, "lead_id", None) if opportunity else None

        if lead_id:
            source_filters.append(
                (
                    OpenItem.source_type == AssessmentSourceTypeEnum.LEAD.value,
                    OpenItem.source_id == lead_id,
                )
            )

        if not source_filters:
            return 0

        closed_statuses = (
            OpenItemStatusEnum.CLOSED.value,
            OpenItemStatusEnum.CANCELLED.value,
            OpenItemStatusEnum.RESOLVED.value,
        )
        query_filters = [
            (source_type_filter & source_id_filter)
            for source_type_filter, source_id_filter in source_filters
        ]
        open_items = (
            self.db.query(OpenItem)
            .filter(
                or_(*query_filters),
                or_(OpenItem.status.is_(None), OpenItem.status.notin_(closed_statuses)),
            )
            .order_by(
                desc(OpenItem.blocks_quotation),
                OpenItem.due_date.asc(),
                desc(OpenItem.updated_at),
                desc(OpenItem.id),
            )
            .all()
        )

        if not open_items:
            return 0

        pm = self.db.query(User).filter(User.id == pm_id).first() if pm_id else None
        created_count = 0
        assigner_id = getattr(current_user, "id", None) or getattr(pm, "id", None)
        assigner_name = (
            getattr(current_user, "real_name", None)
            or getattr(current_user, "username", None)
            or getattr(pm, "real_name", None)
            or getattr(pm, "username", None)
        )

        for item in open_items:
            existing_task = (
                self.db.query(TaskUnified)
                .filter(
                    TaskUnified.project_id == project.id,
                    TaskUnified.source_type == "PRESALE_OPEN_ITEM",
                    TaskUnified.source_id == item.id,
                    TaskUnified.is_active.is_(True),
                )
                .first()
            )
            if existing_task:
                continue

            assignee = getattr(item, "responsible_person", None)
            if not assignee and getattr(item, "responsible_person_id", None):
                assignee = (
                    self.db.query(User)
                    .filter(User.id == item.responsible_person_id)
                    .first()
                )
            if not assignee:
                assignee = pm
            if not assignee:
                continue

            description = (item.description or "").strip()
            title_suffix = description[:80] if description else (item.item_type or item.item_code)
            task = TaskUnified(
                task_code=task_center_codes.generate_task_code(self.db),
                title=f"跟进售前遗留事项：{title_suffix}"[:200],
                description="\n".join(
                    part
                    for part in [
                        f"来源未决事项：{item.item_code}",
                        f"事项类型：{item.item_type}",
                        f"责任方：{item.responsible_party}",
                        f"原始描述：{description}" if description else None,
                        "该事项阻塞报价/项目交接" if item.blocks_quotation else None,
                    ]
                    if part
                ),
                task_type=TaskTypeEnum.WORKFLOW.value,
                source_type="PRESALE_OPEN_ITEM",
                source_id=item.id,
                source_name=item.item_code,
                project_id=project.id,
                project_code=project.project_code,
                project_name=project.project_name,
                assignee_id=assignee.id,
                assignee_name=assignee.real_name or assignee.username,
                assigner_id=assigner_id,
                assigner_name=assigner_name,
                plan_end_date=item.due_date.date() if item.due_date else None,
                deadline=item.due_date,
                status=TaskStatusEnum.PENDING.value,
                progress=0,
                priority=(
                    TaskPriorityEnum.HIGH.value
                    if item.blocks_quotation
                    else TaskPriorityEnum.MEDIUM.value
                ),
                is_urgent=bool(item.blocks_quotation),
                tags=["售前交接", "未闭环事项", item.item_type],
                category="PRESALE_HANDOVER",
                created_by=assigner_id,
                updated_by=assigner_id,
            )
            self.db.add(task)
            self.db.flush()
            created_count += 1

        return created_count

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
        self,
        initiation: PmoProjectInitiation,
        contract: Optional[Contract] = None,
    ) -> Optional[PresaleSolution]:
        """按立项申请或合同报价版本回找售前技术方案。"""
        solution_id = getattr(initiation, "technical_solution_id", None)
        if not isinstance(solution_id, int) or solution_id <= 0:
            quote_version = self._find_quote_version_for_contract(
                contract or self._find_contract_for_initiation(initiation)
            )
            solutions, _ticket_ids = resolve_presale_context_for_quote_version(
                self.db,
                quote_version,
            )
            return solutions[0] if solutions else None

        return (
            self.db.query(PresaleSolution)
            .filter(PresaleSolution.id == solution_id)
            .first()
        )

    def _find_quote_version_for_contract(
        self, contract: Optional[Contract]
    ) -> Optional[QuoteVersion]:
        """从合同关联的报价版本中取得售前方案绑定上下文。"""
        if not contract:
            return None

        quote_version = getattr(contract, "quote_version", None)
        if quote_version is not None:
            return quote_version

        quote_version_id = getattr(contract, "quote_id", None)
        if not isinstance(quote_version_id, int) or quote_version_id <= 0:
            return None

        return (
            self.db.query(QuoteVersion)
            .filter(QuoteVersion.id == quote_version_id)
            .first()
        )

    def _find_ticket_for_solution(
        self, presale_solution: Optional[PresaleSolution]
    ) -> Optional[PresaleSupportTicket]:
        """按售前方案关联的工单补齐线索/商机上下文。"""
        ticket_id = getattr(presale_solution, "ticket_id", None)
        if not ticket_id:
            return None

        return (
            self.db.query(PresaleSupportTicket)
            .filter(PresaleSupportTicket.id == ticket_id)
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
