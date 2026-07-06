# -*- coding: utf-8 -*-
"""PERM-07: 销售业务写操作必须落销售操作日志。"""

import asyncio
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.api.v1.endpoints.sales import router as sales_router
from app.api.v1.endpoints.sales.contracts.basic import (
    ContractFromQuoteRequest,
    archive_contract,
    create_contract,
    create_contract_from_quote,
    delete_contract,
    update_contract,
)
from app.api.v1.endpoints.sales.contracts.contracts import create_project_from_contract
from app.api.v1.endpoints.sales.contracts import enhanced as enhanced_contracts
from app.api.v1.endpoints.sales.contracts.deliverables import (
    create_contract_amendment,
)
from app.api.v1.endpoints.sales.contracts.sign_project import sign_contract
from app.api.v1.endpoints.sales.customers import (
    create_customer,
    delete_customer,
    update_customer,
)
from app.api.v1.endpoints.sales.customer_tags import (
    create_customer_tag,
    create_customer_tags_batch,
    delete_customer_tag,
    delete_customer_tags_by_name,
)
from app.api.v1.endpoints.sales.data_audit import (
    CancelAuditRequest,
    ReviewActionRequest,
    SubmitAuditRequest,
    cancel_audit_request,
    review_audit_request,
    submit_audit_request,
)
from app.api.v1.endpoints.sales.disputes import create_dispute
from app.api.v1.endpoints.sales.expenses import ExpenseLostProjectsRequest, expense_lost_projects
from app.api.v1.endpoints.sales.contacts import (
    create_contact,
    delete_contact,
    set_primary_contact,
    update_contact,
)
from app.api.v1.endpoints.sales.cost_templates import (
    create_cost_template,
    delete_cost_template,
    update_cost_template,
)
from app.api.v1.endpoints.sales.activity_minutes import (
    ConfirmMinutesRequest,
    QuickActivityRequest,
    confirm_minutes,
    quick_activity,
)
from app.api.v1.endpoints.sales.invoices.basic import (
    create_invoice,
    delete_invoice,
    update_invoice,
)
from app.api.v1.endpoints.sales.invoices.workflow import (
    invoice_approval_action,
    start_invoice_approval,
)
from app.api.v1.endpoints.sales.invoices.operations import issue_invoice, void_invoice
from app.api.v1.endpoints.sales.leads.actions import (
    convert_lead_to_opportunity,
    mark_lead_invalid,
)
from app.api.v1.endpoints.sales.leads.batch import (
    BatchAssignRequest,
    BatchConvertRequest,
    BatchUpdateStatusRequest,
    batch_assign_owner,
    batch_convert_leads,
    batch_update_status,
)
from app.api.v1.endpoints.sales.leads.crud import create_lead, delete_lead, update_lead
from app.api.v1.endpoints.sales.leads.follow_ups import create_lead_follow_up
from app.api.v1.endpoints.sales.opportunity_crud import (
    create_opportunity,
    delete_opportunity,
    update_opportunity,
)
from app.api.v1.endpoints.sales.opportunity_batch import (
    BatchUpdateOwnerRequest,
    BatchUpdateStageRequest,
    BatchWinLoseRequest,
    batch_close_opportunities,
    batch_update_owner,
    batch_update_stage,
)
from app.api.v1.endpoints.sales.opportunity_workflow import (
    OpportunityAdvanceRequest,
    OpportunityGateSubmitRequest,
    OpportunityLossRequest,
    advance_opportunity,
    lose_opportunity,
    lose_opportunity_post_compat,
    loss_opportunity_post,
    submit_opportunity_gate,
    update_opportunity_stage,
    update_opportunity_score,
    win_opportunity,
    win_opportunity_post,
)
from app.api.v1.endpoints.sales.priority import (
    calculate_lead_priority,
    calculate_opportunity_priority,
)
from app.api.v1.endpoints.sales.payments.payment_records import (
    PaymentRecordCreate,
    PaymentRecordUpdate,
    create_payment_record,
    delete_payment_record,
    match_payment_to_invoice,
    update_payment_record,
)
from app.api.v1.endpoints.sales.payments.payment_plans import (
    LegacyPaymentPlanCreateRequest,
    LegacyPaymentStageCreate,
    create_payment_plans,
)
from app.api.v1.endpoints.sales.purchase_material_costs import (
    create_purchase_material_cost,
    delete_purchase_material_cost,
    update_purchase_material_cost,
)
from app.api.v1.endpoints.sales.quotes import create_quote
from app.api.v1.endpoints.sales.quote_per_id_approval import (
    QuoteApproveRejectRequest,
    approve_quote,
)
from app.api.v1.endpoints.sales.quote_quotes_crud import delete_quote, update_quote
from app.api.v1.endpoints.sales.quote_status import change_quote_status
from app.api.v1.endpoints.sales.quote_versions import create_quote_version
from app.api.v1.endpoints.sales.quote_delivery import update_quote_delivery
from app.api.v1.endpoints.sales.quote_items import (
    create_quote_item,
    delete_quote_item,
    update_quote_item,
)
from app.api.v1.endpoints.sales.quote_costs import (
    QuoteCostBatchUpdateRequest,
    QuoteCostMatchApplyRequest,
    apply_quote_cost_match_suggestions,
    batch_update_prices,
    recalculate_cost,
    update_cost_item as update_quote_cost_item,
)
from app.api.v1.endpoints.sales.cost_matching import match_material_cost
from app.api.v1.endpoints.sales.cost_reminder import (
    acknowledge_cost_update_reminder,
    update_cost_update_reminder,
)
from app.api.v1.endpoints.sales.quote_templates import (
    create_quote_template,
    create_template_version,
    delete_quote_template,
    publish_template,
    update_quote_template,
)
from app.api.v1.endpoints.sales.templates.contract_templates import (
    create_contract_template,
    create_contract_template_version,
    publish_contract_template_version,
    update_contract_template,
)
from app.api.v1.endpoints.sales.templates.cpq_rules import (
    create_cpq_rule_set,
    update_cpq_rule_set,
)
from app.api.v1.endpoints.sales.templates.quote_templates import (
    create_quote_template as create_structured_quote_template,
    create_quote_template_version as create_structured_quote_template_version,
    publish_quote_template_version as publish_structured_quote_template_version,
    update_quote_template as update_structured_quote_template,
)
from app.api.v1.endpoints.sales.targets import create_sales_target, update_sales_target
from app.api.v1.endpoints.sales.team.crud import (
    create_sales_team,
    delete_sales_team,
    update_sales_team,
)
from app.api.v1.endpoints.sales.team.members import (
    add_team_member,
    batch_add_team_members,
    remove_team_member,
    update_team_member,
)
from app.api.v1.endpoints.sales.team.pk import (
    complete_team_pk,
    create_team_pk,
    update_team_pk,
)
from app.api.v1.endpoints.sales.requirement_details import (
    create_lead_requirement_detail,
    update_lead_requirement_detail,
)
from app.api.v1.endpoints.sales.requirement_freezes import (
    create_lead_requirement_freeze,
    create_opportunity_requirement_freeze,
)
from app.api.v1.endpoints.sales.ai_clarifications import (
    create_ai_clarification_for_lead,
    create_ai_clarification_for_opportunity,
    update_ai_clarification,
)
from app.api.v1.endpoints.sales.assessments.open_items import (
    close_open_item,
    create_open_item,
    create_open_item_for_opportunity,
    update_open_item,
)
from app.api.v1.endpoints.sales.assessments.failure_cases import (
    create_failure_case,
    update_failure_case,
)
from app.api.v1.endpoints.sales.assessments.scoring_rules import (
    activate_scoring_rule,
    create_scoring_rule,
)
from app.api.v1.endpoints.sales.assessments.assessments import (
    apply_lead_assessment,
    apply_opportunity_assessment,
    evaluate_assessment,
)
from app.api.v1.endpoints.sales.assessment_templates import (
    ItemBatchCreateRequest,
    ItemCreateRequest,
    RiskCreateRequest,
    RiskStatusUpdateRequest,
    TemplateCreateRequest,
    TemplateUpdateRequest,
    VersionCreateRequest,
    add_assessment_item,
    batch_add_assessment_items,
    create_assessment_risk,
    create_assessment_template,
    create_assessment_version,
    set_default_template,
    update_assessment_template,
    update_risk_status,
)
from app.api.v1.endpoints.sales.utils.solution_review import (
    persist_solution_review,
    resolve_solution_review,
)
from app.services.contract_approval import ContractApprovalService
from app.services.quote_approval import QuoteApprovalService
from app.models.approval import (
    ApprovalFlowDefinition,
    ApprovalInstance,
    ApprovalNodeDefinition,
    ApprovalTask,
    ApprovalTemplate,
)
from app.models.ai_job import AIGenerationJob
from app.models.enums import (
    AssessmentSourceTypeEnum,
    AssessmentStatusEnum,
    InvoiceStatusEnum,
    WorkflowTypeEnum,
)
from app.models.presale_expense import PresaleExpense
from app.models.project import Customer
from app.models.sales.margin_alert import MarginAlertConfig
from app.models.sales import (
    Contact,
    Contract,
    ContractDeliverable,
    CustomerTag,
    FailureCase,
    Invoice,
    Lead,
    LeadRequirementDetail,
    Opportunity,
    OpportunityRequirement,
    MaterialCostUpdateReminder,
    PurchaseMaterialCost,
    Quote,
    QuoteItem,
    QuoteVersion,
    SalesTeam,
    ScoringRule,
    TechnicalAssessment,
)
from app.models.sales.operation_log import (
    SalesEntityType,
    SalesOperationLog,
    SalesOperationType,
)
from app.models.user import User
from app.schemas.sales import (
    ApprovalActionRequest,
    ApprovalStartRequest,
    ContactCreate,
    ContactUpdate,
    QuoteCostTemplateCreate,
    QuoteCostTemplateUpdate,
    PurchaseMaterialCostCreate,
    PurchaseMaterialCostUpdate,
    MaterialCostMatchRequest,
    MaterialCostUpdateReminderUpdate,
    CustomerTagBatchCreate,
    CustomerTagCreate,
    ContractCreate,
    ContractAmendmentCreate,
    ContractUpdate,
    CustomerCreate,
    CustomerUpdate,
    InvoiceCreate,
    InvoiceIssueRequest,
    InvoiceUpdate,
    ReceivableDisputeCreate,
    LeadCreate,
    LeadFollowUpCreate,
    LeadRequirementDetailCreate,
    LeadRequirementDetailUpdate,
    RequirementFreezeCreate,
    FailureCaseCreate,
    FailureCaseUpdate,
    AIClarificationCreate,
    AIClarificationUpdate,
    OpenItemCreate,
    LeadUpdate,
    OpportunityCreate,
    OpportunityUpdate,
    ContractTemplateCreate,
    ContractTemplateUpdate,
    ContractTemplateVersionCreate,
    CpqRuleSetCreate,
    CpqRuleSetUpdate,
    QuoteTemplateCreate,
    QuoteTemplateUpdate,
    QuoteTemplateVersionCreate,
    SalesTargetCreate,
    SalesTargetUpdate,
    SalesTeamCreate,
    SalesTeamUpdate,
    ScoringRuleCreate,
    TechnicalAssessmentApplyRequest,
    TechnicalAssessmentEvaluateRequest,
    TeamPKCreateRequest,
    TeamPKUpdateRequest,
    TeamMemberAddRequest,
    TeamMemberBatchAddRequest,
    TeamMemberUpdateRequest,
    ContractSignRequest,
)
from app.schemas.sales.contract_enhanced import (
    ContractAttachmentCreate as EnhancedContractAttachmentCreate,
    ContractCreate as EnhancedContractCreate,
    ContractTermCreate as EnhancedContractTermCreate,
    ContractTermUpdate as EnhancedContractTermUpdate,
    ContractUpdate as EnhancedContractUpdate,
)


def _create_quote_version_with_item(
    db: Session, current_user: User
) -> tuple[Quote, QuoteVersion, QuoteItem]:
    suffix = uuid.uuid4().hex[:8]

    customer = Customer(
        customer_code=f"CUST-PERM07-{suffix}",
        customer_name=f"PERM07 客户-{suffix}",
        status="ACTIVE",
        created_by=current_user.id,
        sales_owner_id=current_user.id,
    )
    db.add(customer)
    db.flush()

    opportunity = Opportunity(
        opp_code=f"OPP-PERM07-{suffix}",
        customer_id=customer.id,
        opp_name=f"PERM07 商机-{suffix}",
        owner_id=current_user.id,
    )
    db.add(opportunity)
    db.flush()

    quote = Quote(
        quote_code=f"QT-PERM07-{suffix}",
        opportunity_id=opportunity.id,
        customer_id=customer.id,
        owner_id=current_user.id,
        status="DRAFT",
    )
    db.add(quote)
    db.flush()

    version = QuoteVersion(
        quote_id=quote.id,
        version_no="V1",
        total_price=Decimal("100.00"),
        cost_total=Decimal("20.00"),
        gross_margin=Decimal("80.00"),
        status="DRAFT",
        created_by=current_user.id,
    )
    db.add(version)
    db.flush()
    quote.current_version_id = version.id

    item = QuoteItem(
        quote_version_id=version.id,
        item_type="MATERIAL",
        item_name="标准件",
        qty=Decimal("1"),
        unit_price=Decimal("100.00"),
        cost=Decimal("20.00"),
        unit="件",
    )
    db.add(item)
    db.commit()
    return quote, version, item


def _create_issued_invoice(db: Session, current_user: User) -> tuple[Contract, Invoice]:
    suffix = uuid.uuid4().hex[:8]

    customer = Customer(
        customer_code=f"CUST-PAY-PERM07-{suffix}",
        customer_name=f"PERM07 回款客户-{suffix}",
        status="ACTIVE",
        created_by=current_user.id,
        sales_owner_id=current_user.id,
    )
    db.add(customer)
    db.flush()

    contract = Contract(
        contract_code=f"CT-PAY-PERM07-{suffix}",
        contract_name=f"PERM07 回款合同-{suffix}",
        contract_type="sales",
        customer_id=customer.id,
        total_amount=Decimal("100.00"),
        status="SIGNED",
        sales_owner_id=current_user.id,
    )
    db.add(contract)
    db.flush()

    invoice = Invoice(
        invoice_code=f"INV-PAY-PERM07-{suffix}",
        contract_id=contract.id,
        amount=Decimal("100.00"),
        total_amount=Decimal("100.00"),
        status="ISSUED",
        payment_status="PENDING",
        issue_date=date(2026, 7, 5),
        due_date=date(2026, 8, 5),
        paid_amount=Decimal("0.00"),
    )
    db.add(invoice)
    db.commit()
    return contract, invoice


def _create_invoiceable_contract(db: Session, current_user: User) -> Contract:
    suffix = uuid.uuid4().hex[:8]

    customer = Customer(
        customer_code=f"CUST-INV-PERM07-{suffix}",
        customer_name=f"PERM07 发票客户-{suffix}",
        status="ACTIVE",
        created_by=current_user.id,
        sales_owner_id=current_user.id,
    )
    db.add(customer)
    db.flush()

    contract = Contract(
        contract_code=f"CT-INV-PERM07-{suffix}",
        contract_name=f"PERM07 发票合同-{suffix}",
        contract_type="sales",
        customer_id=customer.id,
        total_amount=Decimal("1000.00"),
        status="SIGNED",
        sales_owner_id=current_user.id,
    )
    db.add(contract)
    db.commit()
    return contract


def _create_contract_customer_and_opportunity(
    db: Session, current_user: User
) -> tuple[Customer, Opportunity]:
    suffix = uuid.uuid4().hex[:8]

    customer = Customer(
        customer_code=f"CUST-CT-PERM07-{suffix}",
        customer_name=f"PERM07 合同客户-{suffix}",
        status="ACTIVE",
        created_by=current_user.id,
        sales_owner_id=current_user.id,
    )
    db.add(customer)
    db.flush()

    opportunity = Opportunity(
        opp_code=f"OPP-CT-PERM07-{suffix}",
        customer_id=customer.id,
        opp_name=f"PERM07 合同商机-{suffix}",
        owner_id=current_user.id,
    )
    db.add(opportunity)
    db.commit()
    return customer, opportunity


def _create_approved_contract(db: Session, current_user: User) -> Contract:
    suffix = uuid.uuid4().hex[:8]
    customer, opportunity = _create_contract_customer_and_opportunity(db, current_user)
    contract = Contract(
        contract_code=f"CT-SIGN-PERM07-{suffix}",
        contract_name=f"PERM07 待签合同-{suffix}",
        contract_type="sales",
        customer_id=customer.id,
        opportunity_id=opportunity.id,
        total_amount=Decimal("600.00"),
        amount_with_tax=Decimal("600.00"),
        status="APPROVED",
        sales_owner_id=current_user.id,
    )
    db.add(contract)
    db.commit()
    return contract


def _create_approved_invoice(db: Session, current_user: User) -> Invoice:
    suffix = uuid.uuid4().hex[:8]
    contract = _create_invoiceable_contract(db, current_user)
    invoice = Invoice(
        invoice_code=f"INV-ISSUE-PERM07-{suffix}",
        contract_id=contract.id,
        invoice_type="SPECIAL",
        amount=Decimal("120.00"),
        tax_rate=Decimal("13.00"),
        tax_amount=Decimal("15.60"),
        total_amount=Decimal("135.60"),
        status=InvoiceStatusEnum.APPROVED.value,
        payment_status=None,
        buyer_name="PERM07 开票客户",
        approval_status="APPROVED",
    )
    db.add(invoice)
    db.flush()

    template = ApprovalTemplate(
        template_code=f"TPL-INV-PERM07-{suffix}",
        template_name=f"PERM07 发票审批模板-{suffix}",
        category="BUSINESS",
        entity_type=WorkflowTypeEnum.INVOICE.value,
        is_active=True,
        is_published=True,
        created_by=current_user.id,
    )
    db.add(template)
    db.flush()

    flow = ApprovalFlowDefinition(
        template_id=template.id,
        flow_name=f"PERM07 发票审批流程-{suffix}",
        is_default=True,
        is_active=True,
        created_by=current_user.id,
    )
    db.add(flow)
    db.flush()

    instance = ApprovalInstance(
        instance_no=f"AP-PERM07-{suffix}",
        template_id=template.id,
        flow_id=flow.id,
        entity_type=WorkflowTypeEnum.INVOICE.value,
        entity_id=invoice.id,
        initiator_id=current_user.id,
        initiator_name=current_user.real_name or current_user.username,
        status="APPROVED",
        title=f"PERM07 发票审批-{suffix}",
        summary=f"PERM07 发票审批-{suffix}",
    )
    db.add(instance)
    db.flush()

    invoice.approval_instance_id = instance.id
    db.commit()
    return invoice


def _create_invoice_pending_approval_task(
    db: Session,
    current_user: User,
    *,
    suffix_prefix: str,
    invoice_status: str = "PENDING_APPROVAL",
) -> tuple[Invoice, ApprovalTask]:
    suffix = f"{suffix_prefix}-{uuid.uuid4().hex[:8]}"
    contract = _create_invoiceable_contract(db, current_user)
    invoice = Invoice(
        invoice_code=f"INV-APP-PERM07-{suffix}",
        contract_id=contract.id,
        invoice_type="SPECIAL",
        amount=Decimal("120.00"),
        tax_rate=Decimal("13.00"),
        tax_amount=Decimal("15.60"),
        total_amount=Decimal("135.60"),
        status=invoice_status,
        payment_status=None,
        buyer_name="PERM07 审批客户",
    )
    db.add(invoice)
    db.flush()

    template = ApprovalTemplate(
        template_code=f"TPL-INV-APP-PERM07-{suffix}",
        template_name=f"PERM07 发票动作审批模板-{suffix}",
        category="BUSINESS",
        entity_type=WorkflowTypeEnum.INVOICE.value,
        is_active=True,
        is_published=True,
        created_by=current_user.id,
    )
    db.add(template)
    db.flush()

    flow = ApprovalFlowDefinition(
        template_id=template.id,
        flow_name=f"PERM07 发票动作审批流程-{suffix}",
        is_default=True,
        is_active=True,
        created_by=current_user.id,
    )
    db.add(flow)
    db.flush()

    node = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_code=f"INV-APP-PERM07-NODE-{suffix}",
        node_name="发票审批",
        node_order=1,
        node_type="APPROVAL",
        approval_mode="SINGLE",
        approver_type="FIXED_USER",
        approver_config={"user_ids": [current_user.id]},
        is_active=True,
    )
    db.add(node)
    db.flush()

    instance = ApprovalInstance(
        instance_no=f"AP-INV-APP-PERM07-{suffix}",
        template_id=template.id,
        flow_id=flow.id,
        entity_type=WorkflowTypeEnum.INVOICE.value,
        entity_id=invoice.id,
        initiator_id=current_user.id,
        initiator_name=current_user.real_name or current_user.username,
        status="PENDING",
        current_node_id=node.id,
        title=f"PERM07 发票动作审批-{suffix}",
        summary=f"PERM07 发票动作审批-{suffix}",
    )
    db.add(instance)
    db.flush()

    task = ApprovalTask(
        instance_id=instance.id,
        node_id=node.id,
        task_type="APPROVAL",
        task_order=1,
        assignee_id=current_user.id,
        assignee_name=current_user.real_name or current_user.username,
        status="PENDING",
    )
    db.add(task)
    db.flush()
    invoice.approval_instance_id = instance.id
    db.commit()
    return invoice, task


def _create_quote_approval_task(
    db: Session,
    quote: Quote,
    current_user: User,
    *,
    suffix_prefix: str,
) -> ApprovalTask:
    suffix = f"{suffix_prefix}-{uuid.uuid4().hex[:8]}"
    template = ApprovalTemplate(
        template_code=f"QT-PERM07-{suffix}",
        template_name=f"PERM07 报价审批-{suffix}",
        entity_type="QUOTE",
        is_active=True,
        created_by=current_user.id,
    )
    db.add(template)
    db.flush()

    flow = ApprovalFlowDefinition(
        template_id=template.id,
        flow_name=f"PERM07 报价审批流程-{suffix}",
        is_default=True,
        is_active=True,
        created_by=current_user.id,
    )
    db.add(flow)
    db.flush()

    node = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_code=f"QT-PERM07-NODE-{suffix}",
        node_name="报价审批",
        node_order=1,
        node_type="APPROVAL",
        approver_type="FIXED_USER",
        approver_config={"user_ids": [current_user.id]},
    )
    db.add(node)
    db.flush()

    instance = ApprovalInstance(
        instance_no=f"AP-QT-PERM07-{suffix}",
        template_id=template.id,
        flow_id=flow.id,
        entity_type="QUOTE",
        entity_id=quote.id,
        initiator_id=current_user.id,
        initiator_name=current_user.real_name or current_user.username,
        status="PENDING",
        title=f"PERM07 报价审批-{suffix}",
        summary=f"PERM07 报价审批-{suffix}",
    )
    db.add(instance)
    db.flush()

    task = ApprovalTask(
        instance_id=instance.id,
        node_id=node.id,
        assignee_id=current_user.id,
        assignee_name=current_user.real_name or current_user.username,
        status="PENDING",
    )
    db.add(task)
    db.flush()
    return task


def _create_contract_approval_task(
    db: Session,
    contract: Contract,
    current_user: User,
    *,
    suffix_prefix: str,
) -> ApprovalTask:
    suffix = f"{suffix_prefix}-{uuid.uuid4().hex[:8]}"
    template = ApprovalTemplate(
        template_code=f"CT-PERM07-{suffix}",
        template_name=f"PERM07 合同审批-{suffix}",
        entity_type="CONTRACT",
        is_active=True,
        created_by=current_user.id,
    )
    db.add(template)
    db.flush()

    flow = ApprovalFlowDefinition(
        template_id=template.id,
        flow_name=f"PERM07 合同审批流程-{suffix}",
        is_default=True,
        is_active=True,
        created_by=current_user.id,
    )
    db.add(flow)
    db.flush()

    node = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_code=f"CT-PERM07-NODE-{suffix}",
        node_name="合同审批",
        node_order=1,
        node_type="APPROVAL",
        approver_type="FIXED_USER",
        approver_config={"user_ids": [current_user.id]},
    )
    db.add(node)
    db.flush()

    instance = ApprovalInstance(
        instance_no=f"AP-CT-PERM07-{suffix}",
        template_id=template.id,
        flow_id=flow.id,
        entity_type="CONTRACT",
        entity_id=contract.id,
        initiator_id=current_user.id,
        initiator_name=current_user.real_name or current_user.username,
        status="PENDING",
        title=f"PERM07 合同审批-{suffix}",
        summary=f"PERM07 合同审批-{suffix}",
    )
    db.add(instance)
    db.flush()

    task = ApprovalTask(
        instance_id=instance.id,
        node_id=node.id,
        assignee_id=current_user.id,
        assignee_name=current_user.real_name or current_user.username,
        status="PENDING",
    )
    db.add(task)
    db.flush()
    return task


def test_sales_operation_log_query_route_is_registered():
    paths = {getattr(route, "path", "") for route in sales_router.routes}

    assert "/operation-logs/{entity_type}/{entity_id}" in paths
    assert "/operation-logs/" in paths
    assert "/leads/batch/status" in paths


def test_opportunity_batch_routes_are_registered():
    paths = {getattr(route, "path", "") for route in sales_router.routes}

    assert "/opportunities/batch/stage" in paths
    assert "/opportunities/batch/owner" in paths
    assert "/opportunities/batch/close" in paths


def test_quote_create_writes_quote_operation_log(
    db_session: Session, test_admin: User
):
    customer, opportunity = _create_contract_customer_and_opportunity(
        db_session, test_admin
    )
    response = create_quote(
        quote_data={
            "quote_code": f"QT-PERM07-AUDIT-{uuid.uuid4().hex[:4]}",
            "opportunity_id": opportunity.id,
            "customer_id": customer.id,
            "valid_until": "2026-08-31",
            "version": {
                "version_no": "V1",
                "total_price": "300000.00",
                "cost_total": "210000.00",
                "gross_margin": "30.00",
            },
        },
        db=db_session,
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE,
            SalesOperationLog.entity_id == response["id"],
        )
        .one()
    )

    assert log.operation_type == SalesOperationType.CREATE
    assert log.new_value["quote_code"] == response["quote_code"]
    assert log.new_value["opportunity_id"] == opportunity.id
    assert log.new_value["customer_id"] == customer.id
    assert log.new_value["status"] == "DRAFT"
    assert log.new_value["current_version_id"] == response["current_version_id"]
    assert log.new_value["current_version"]["total_price"] == "300000.00"


def test_quote_update_writes_quote_operation_log(
    db_session: Session, test_admin: User
):
    quote, _version, _item = _create_quote_version_with_item(db_session, test_admin)

    update_quote(
        quote_id=quote.id,
        quote_data={"valid_until": "2026-09-30"},
        db=db_session,
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE,
            SalesOperationLog.entity_id == quote.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )

    assert log.old_value["valid_until"] is None
    assert log.new_value["valid_until"] == "2026-09-30"
    assert "valid_until" in log.changed_fields


def test_quote_delivery_update_writes_quote_operation_log(
    db_session: Session, test_admin: User
):
    quote, _version, _item = _create_quote_version_with_item(db_session, test_admin)

    update_quote_delivery(
        quote_id=quote.id,
        delivery_data={"delivery_date": "2026-10-15"},
        db=db_session,
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE,
            SalesOperationLog.entity_id == quote.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )

    assert log.old_value["delivery_date"] is None
    assert log.new_value["delivery_date"] == "2026-10-15"
    assert "delivery_date" in log.changed_fields


def test_quote_delete_writes_quote_operation_log(
    db_session: Session, test_admin: User
):
    quote, version, _item = _create_quote_version_with_item(db_session, test_admin)
    quote_id = quote.id
    quote_code = quote.quote_code

    delete_quote(quote_id=quote_id, db=db_session, current_user=test_admin)

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE,
            SalesOperationLog.entity_id == quote_id,
            SalesOperationLog.operation_type == SalesOperationType.DELETE,
        )
        .one()
    )

    assert log.old_value["quote_code"] == quote_code
    assert log.old_value["status"] == "DRAFT"
    assert log.old_value["current_version_id"] == version.id
    assert log.new_value == {}


def test_quote_version_create_writes_version_and_current_quote_logs(
    db_session: Session, test_admin: User
):
    quote, old_version, _item = _create_quote_version_with_item(db_session, test_admin)
    db_session.commit()

    response = create_quote_version(
        quote_id=quote.id,
        version_data={
            "version_no": "V2",
            "total_price": "150000.00",
            "cost_total": "90000.00",
            "gross_margin": "40.00",
            "set_as_current": True,
        },
        db=db_session,
        current_user=test_admin,
    )
    new_version_id = response.data["id"]

    version_log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE_VERSION,
            SalesOperationLog.entity_id == new_version_id,
            SalesOperationLog.operation_type == SalesOperationType.CREATE,
        )
        .one()
    )
    quote_log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE,
            SalesOperationLog.entity_id == quote.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )

    assert version_log.new_value["quote_id"] == quote.id
    assert version_log.new_value["version_no"] == "V2"
    assert version_log.new_value["total_price"] == "150000.00"
    assert quote_log.old_value["current_version_id"] == old_version.id
    assert quote_log.new_value["current_version_id"] == new_version_id
    assert "current_version_id" in quote_log.changed_fields


def test_quote_status_change_writes_quote_status_change_log(
    db_session: Session, test_admin: User
):
    quote, _version, _item = _create_quote_version_with_item(db_session, test_admin)
    db_session.commit()

    change_quote_status(
        quote_id=quote.id,
        status_data={"new_status": "PENDING_APPROVAL", "reason": "提交审批"},
        db=db_session,
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE,
            SalesOperationLog.entity_id == quote.id,
            SalesOperationLog.operation_type == SalesOperationType.STATUS_CHANGE,
        )
        .one()
    )

    assert log.old_value["status"] == "DRAFT"
    assert log.new_value["status"] == "PENDING_APPROVAL"
    assert "status" in log.changed_fields
    assert log.remark == "提交审批"


def test_quote_direct_approval_writes_quote_and_version_approval_logs(
    db_session: Session, test_admin: User
):
    quote, version, _item = _create_quote_version_with_item(db_session, test_admin)
    db_session.commit()

    approve_quote(
        quote_id=quote.id,
        db=db_session,
        request=QuoteApproveRejectRequest(comment="同意报价"),
        current_user=test_admin,
    )

    quote_log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE,
            SalesOperationLog.entity_id == quote.id,
            SalesOperationLog.operation_type == SalesOperationType.APPROVE,
        )
        .one()
    )
    version_log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE_VERSION,
            SalesOperationLog.entity_id == version.id,
            SalesOperationLog.operation_type == SalesOperationType.APPROVE,
        )
        .one()
    )

    assert quote_log.old_value["status"] == "DRAFT"
    assert quote_log.new_value["status"] == "APPROVED"
    assert "status" in quote_log.changed_fields
    assert quote_log.remark == "同意报价"
    assert version_log.old_value["approved_by"] is None
    assert version_log.new_value["approved_by"] == test_admin.id
    assert version_log.new_value["approved_at"] is not None


def test_quote_formal_submit_writes_quote_submit_log(
    db_session: Session, test_admin: User
):
    quote, version, _item = _create_quote_version_with_item(db_session, test_admin)
    db_session.commit()

    class FakeApprovalEngine:
        def submit(self, **kwargs):
            assert kwargs["entity_type"] == "QUOTE"
            assert kwargs["entity_id"] == quote.id
            quote.status = "PENDING_APPROVAL"
            db_session.flush()

            class Instance:
                id = 72001
                status = "PENDING"

            return Instance()

    service = QuoteApprovalService(db_session)
    service.approval_engine = FakeApprovalEngine()

    result = service.submit_quotes_for_approval(
        quote_ids=[quote.id],
        initiator_id=test_admin.id,
        version_ids=[version.id],
        urgency="HIGH",
        comment="正式提交审批",
    )

    assert result["errors"] == []
    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE,
            SalesOperationLog.entity_id == quote.id,
            SalesOperationLog.operation_type == SalesOperationType.SUBMIT,
        )
        .one()
    )

    assert log.old_value["status"] == "DRAFT"
    assert log.new_value["status"] == "PENDING_APPROVAL"
    assert log.new_value["current_version_id"] == version.id
    assert "status" in log.changed_fields
    assert log.remark == "正式提交审批"


def test_quote_formal_approve_action_writes_quote_approve_log(
    db_session: Session, test_admin: User
):
    quote, _version, _item = _create_quote_version_with_item(db_session, test_admin)
    quote.status = "PENDING_APPROVAL"

    suffix = uuid.uuid4().hex[:8]
    template = ApprovalTemplate(
        template_code=f"QT-ACTION-PERM07-{suffix}",
        template_name=f"PERM07 报价审批-{suffix}",
        entity_type="QUOTE",
        is_active=True,
        created_by=test_admin.id,
    )
    db_session.add(template)
    db_session.flush()
    flow = ApprovalFlowDefinition(
        template_id=template.id,
        flow_name=f"PERM07 报价审批流程-{suffix}",
        is_default=True,
        is_active=True,
        created_by=test_admin.id,
    )
    db_session.add(flow)
    db_session.flush()
    node = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_code=f"QT-ACTION-NODE-{suffix}",
        node_name="报价审批",
        node_order=1,
        node_type="APPROVAL",
        approver_type="FIXED_USER",
        approver_config={"user_ids": [test_admin.id]},
    )
    db_session.add(node)
    db_session.flush()
    instance = ApprovalInstance(
        instance_no=f"AP-QT-ACTION-{suffix}",
        template_id=template.id,
        flow_id=flow.id,
        entity_type="QUOTE",
        entity_id=quote.id,
        initiator_id=test_admin.id,
        initiator_name=test_admin.real_name or test_admin.username,
        status="PENDING",
        title=f"PERM07 报价审批-{suffix}",
        summary=f"PERM07 报价审批-{suffix}",
    )
    db_session.add(instance)
    db_session.flush()
    task = ApprovalTask(
        instance_id=instance.id,
        node_id=node.id,
        assignee_id=test_admin.id,
        assignee_name=test_admin.real_name or test_admin.username,
        status="PENDING",
    )
    db_session.add(task)
    db_session.commit()

    class FakeApprovalEngine:
        def approve(self, **kwargs):
            assert kwargs["task_id"] == task.id
            quote.status = "APPROVED"
            db_session.flush()

            class Result:
                status = "APPROVED"

            return Result()

    service = QuoteApprovalService(db_session)
    service.approval_engine = FakeApprovalEngine()

    result = service.perform_action(
        task_id=task.id,
        action="approve",
        approver_id=test_admin.id,
        comment="正式审批通过",
    )

    assert result["instance_status"] == "APPROVED"
    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE,
            SalesOperationLog.entity_id == quote.id,
            SalesOperationLog.operation_type == SalesOperationType.APPROVE,
        )
        .one()
    )

    assert log.old_value["status"] == "PENDING_APPROVAL"
    assert log.new_value["status"] == "APPROVED"
    assert "status" in log.changed_fields
    assert log.remark == "正式审批通过"


def test_quote_formal_reject_action_writes_quote_reject_log(
    db_session: Session, test_admin: User
):
    quote, _version, _item = _create_quote_version_with_item(db_session, test_admin)
    quote.status = "PENDING_APPROVAL"

    suffix = uuid.uuid4().hex[:8]
    template = ApprovalTemplate(
        template_code=f"QT-REJECT-PERM07-{suffix}",
        template_name=f"PERM07 报价驳回-{suffix}",
        entity_type="QUOTE",
        is_active=True,
        created_by=test_admin.id,
    )
    db_session.add(template)
    db_session.flush()
    flow = ApprovalFlowDefinition(
        template_id=template.id,
        flow_name=f"PERM07 报价驳回流程-{suffix}",
        is_default=True,
        is_active=True,
        created_by=test_admin.id,
    )
    db_session.add(flow)
    db_session.flush()
    node = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_code=f"QT-REJECT-NODE-{suffix}",
        node_name="报价审批",
        node_order=1,
        node_type="APPROVAL",
        approver_type="FIXED_USER",
        approver_config={"user_ids": [test_admin.id]},
    )
    db_session.add(node)
    db_session.flush()
    instance = ApprovalInstance(
        instance_no=f"AP-QT-REJECT-{suffix}",
        template_id=template.id,
        flow_id=flow.id,
        entity_type="QUOTE",
        entity_id=quote.id,
        initiator_id=test_admin.id,
        initiator_name=test_admin.real_name or test_admin.username,
        status="PENDING",
        title=f"PERM07 报价驳回-{suffix}",
        summary=f"PERM07 报价驳回-{suffix}",
    )
    db_session.add(instance)
    db_session.flush()
    task = ApprovalTask(
        instance_id=instance.id,
        node_id=node.id,
        assignee_id=test_admin.id,
        assignee_name=test_admin.real_name or test_admin.username,
        status="PENDING",
    )
    db_session.add(task)
    db_session.commit()

    class FakeApprovalEngine:
        def reject(self, **kwargs):
            assert kwargs["task_id"] == task.id
            quote.status = "REJECTED"
            db_session.flush()

            class Result:
                status = "REJECTED"

            return Result()

    service = QuoteApprovalService(db_session)
    service.approval_engine = FakeApprovalEngine()

    result = service.perform_action(
        task_id=task.id,
        action="reject",
        approver_id=test_admin.id,
        comment="价格需要重做",
    )

    assert result["instance_status"] == "REJECTED"
    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE,
            SalesOperationLog.entity_id == quote.id,
            SalesOperationLog.operation_type == SalesOperationType.REJECT,
        )
        .one()
    )

    assert log.old_value["status"] == "PENDING_APPROVAL"
    assert log.new_value["status"] == "REJECTED"
    assert "status" in log.changed_fields
    assert log.remark == "价格需要重做"


def test_quote_batch_approve_writes_quote_approve_logs(
    db_session: Session, test_admin: User
):
    quote_a, _version_a, _item_a = _create_quote_version_with_item(db_session, test_admin)
    quote_b, _version_b, _item_b = _create_quote_version_with_item(db_session, test_admin)
    quote_a.status = "PENDING_APPROVAL"
    quote_b.status = "PENDING_APPROVAL"

    task_a = _create_quote_approval_task(
        db_session, quote_a, test_admin, suffix_prefix="BATCH-A"
    )
    task_b = _create_quote_approval_task(
        db_session, quote_b, test_admin, suffix_prefix="BATCH-B"
    )
    db_session.commit()

    task_to_quote = {task_a.id: quote_a, task_b.id: quote_b}

    class FakeApprovalEngine:
        def approve(self, **kwargs):
            quote = task_to_quote[kwargs["task_id"]]
            quote.status = "APPROVED"
            db_session.flush()

            class Result:
                status = "APPROVED"

            return Result()

    service = QuoteApprovalService(db_session)
    service.approval_engine = FakeApprovalEngine()

    result = service.perform_batch_actions(
        task_ids=[task_a.id, task_b.id],
        action="approve",
        approver_id=test_admin.id,
        comment="批量审批通过",
    )

    assert len(result["success"]) == 2
    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE,
            SalesOperationLog.entity_id.in_([quote_a.id, quote_b.id]),
            SalesOperationLog.operation_type == SalesOperationType.APPROVE,
        )
        .order_by(SalesOperationLog.entity_id)
        .all()
    )

    assert len(logs) == 2
    assert {log.old_value["status"] for log in logs} == {"PENDING_APPROVAL"}
    assert {log.new_value["status"] for log in logs} == {"APPROVED"}
    assert all(log.remark == "批量审批通过" for log in logs)


def test_quote_batch_reject_writes_quote_reject_logs(
    db_session: Session, test_admin: User
):
    quote_a, _version_a, _item_a = _create_quote_version_with_item(db_session, test_admin)
    quote_b, _version_b, _item_b = _create_quote_version_with_item(db_session, test_admin)
    quote_a.status = "PENDING_APPROVAL"
    quote_b.status = "PENDING_APPROVAL"

    task_a = _create_quote_approval_task(
        db_session, quote_a, test_admin, suffix_prefix="BATCH-REJECT-A"
    )
    task_b = _create_quote_approval_task(
        db_session, quote_b, test_admin, suffix_prefix="BATCH-REJECT-B"
    )
    db_session.commit()

    task_to_quote = {task_a.id: quote_a, task_b.id: quote_b}

    class FakeApprovalEngine:
        def reject(self, **kwargs):
            quote = task_to_quote[kwargs["task_id"]]
            quote.status = "REJECTED"
            db_session.flush()

            class Result:
                status = "REJECTED"

            return Result()

    service = QuoteApprovalService(db_session)
    service.approval_engine = FakeApprovalEngine()

    result = service.perform_batch_actions(
        task_ids=[task_a.id, task_b.id],
        action="reject",
        approver_id=test_admin.id,
        comment="批量驳回",
    )

    assert len(result["success"]) == 2
    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE,
            SalesOperationLog.entity_id.in_([quote_a.id, quote_b.id]),
            SalesOperationLog.operation_type == SalesOperationType.REJECT,
        )
        .order_by(SalesOperationLog.entity_id)
        .all()
    )

    assert len(logs) == 2
    assert {log.old_value["status"] for log in logs} == {"PENDING_APPROVAL"}
    assert {log.new_value["status"] for log in logs} == {"REJECTED"}
    assert all(log.remark == "批量驳回" for log in logs)


def test_quote_withdraw_approval_writes_quote_status_change_log(
    db_session: Session, test_admin: User
):
    quote, _version, _item = _create_quote_version_with_item(db_session, test_admin)
    quote.status = "PENDING_APPROVAL"
    task = _create_quote_approval_task(
        db_session, quote, test_admin, suffix_prefix="WITHDRAW"
    )
    instance_id = task.instance_id
    db_session.commit()

    class FakeApprovalEngine:
        def withdraw(self, **kwargs):
            assert kwargs["instance_id"] == instance_id
            assert kwargs["initiator_id"] == test_admin.id
            quote.status = "DRAFT"
            instance = db_session.get(ApprovalInstance, instance_id)
            instance.status = "CANCELLED"
            db_session.flush()
            return instance

    service = QuoteApprovalService(db_session)
    service.approval_engine = FakeApprovalEngine()

    result = service.withdraw_approval(
        quote_id=quote.id,
        user_id=test_admin.id,
        reason="客户要求重提",
    )

    assert result["status"] == "withdrawn"
    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE,
            SalesOperationLog.entity_id == quote.id,
            SalesOperationLog.operation_type == SalesOperationType.STATUS_CHANGE,
        )
        .one()
    )

    assert log.old_value["status"] == "PENDING_APPROVAL"
    assert log.new_value["status"] == "DRAFT"
    assert "status" in log.changed_fields
    assert log.remark == "客户要求重提"


def test_contract_formal_approve_action_writes_contract_approve_log(
    db_session: Session, test_admin: User
):
    contract = _create_approved_contract(db_session, test_admin)
    contract.status = "PENDING_APPROVAL"
    task = _create_contract_approval_task(
        db_session, contract, test_admin, suffix_prefix="APPROVE"
    )
    db_session.commit()

    class FakeApprovalEngine:
        def approve(self, **kwargs):
            assert kwargs["task_id"] == task.id
            contract.status = "APPROVED"
            db_session.flush()

            class Result:
                status = "APPROVED"

            return Result()

    service = ContractApprovalService(db_session)
    service.engine = FakeApprovalEngine()

    result = service.approve_task(
        task_id=task.id,
        approver_id=test_admin.id,
        comment="合同正式审批通过",
    )

    assert result.status == "APPROVED"
    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.CONTRACT,
            SalesOperationLog.entity_id == contract.id,
            SalesOperationLog.operation_type == SalesOperationType.APPROVE,
        )
        .one()
    )

    assert log.old_value["status"] == "PENDING_APPROVAL"
    assert log.new_value["status"] == "APPROVED"
    assert "status" in log.changed_fields
    assert log.remark == "合同正式审批通过"


def test_contract_formal_submit_writes_contract_submit_log(
    db_session: Session, test_admin: User
):
    contract = _create_approved_contract(db_session, test_admin)
    contract.status = "DRAFT"
    db_session.commit()

    class FakeApprovalEngine:
        def submit(self, **kwargs):
            assert kwargs["entity_id"] == contract.id
            contract.status = "PENDING_APPROVAL"
            db_session.flush()

            class Instance:
                id = 307

            return Instance()

    service = ContractApprovalService(db_session)
    service.engine = FakeApprovalEngine()

    results, errors = service.submit_contracts_for_approval(
        contract_ids=[contract.id],
        initiator_id=test_admin.id,
        urgency="HIGH",
        comment="合同正式提交审批",
    )

    assert errors == []
    assert results[0]["status"] == "submitted"
    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.CONTRACT,
            SalesOperationLog.entity_id == contract.id,
            SalesOperationLog.operation_type == SalesOperationType.SUBMIT,
        )
        .one()
    )

    assert log.old_value["status"] == "DRAFT"
    assert log.new_value["status"] == "PENDING_APPROVAL"
    assert "status" in log.changed_fields
    assert log.remark == "合同正式提交审批"


def test_contract_formal_reject_action_writes_contract_reject_log(
    db_session: Session, test_admin: User
):
    contract = _create_approved_contract(db_session, test_admin)
    contract.status = "PENDING_APPROVAL"
    task = _create_contract_approval_task(
        db_session, contract, test_admin, suffix_prefix="REJECT"
    )
    db_session.commit()

    class FakeApprovalEngine:
        def reject(self, **kwargs):
            assert kwargs["task_id"] == task.id
            contract.status = "REJECTED"
            db_session.flush()

            class Result:
                status = "REJECTED"

            return Result()

    service = ContractApprovalService(db_session)
    service.engine = FakeApprovalEngine()

    result = service.reject_task(
        task_id=task.id,
        approver_id=test_admin.id,
        comment="合同条款需重改",
    )

    assert result.status == "REJECTED"
    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.CONTRACT,
            SalesOperationLog.entity_id == contract.id,
            SalesOperationLog.operation_type == SalesOperationType.REJECT,
        )
        .one()
    )

    assert log.old_value["status"] == "PENDING_APPROVAL"
    assert log.new_value["status"] == "REJECTED"
    assert "status" in log.changed_fields
    assert log.remark == "合同条款需重改"


def test_contract_batch_approve_writes_contract_approve_logs(
    db_session: Session, test_admin: User
):
    contract_a = _create_approved_contract(db_session, test_admin)
    contract_b = _create_approved_contract(db_session, test_admin)
    contract_a.status = "PENDING_APPROVAL"
    contract_b.status = "PENDING_APPROVAL"
    task_a = _create_contract_approval_task(
        db_session, contract_a, test_admin, suffix_prefix="BATCH-A"
    )
    task_b = _create_contract_approval_task(
        db_session, contract_b, test_admin, suffix_prefix="BATCH-B"
    )
    db_session.commit()

    task_to_contract = {task_a.id: contract_a, task_b.id: contract_b}

    class FakeApprovalEngine:
        def approve(self, **kwargs):
            contract = task_to_contract[kwargs["task_id"]]
            contract.status = "APPROVED"
            db_session.flush()

            class Result:
                status = "APPROVED"

            return Result()

    service = ContractApprovalService(db_session)
    service.engine = FakeApprovalEngine()

    results, errors = service.batch_approve_or_reject(
        task_ids=[task_a.id, task_b.id],
        approver_id=test_admin.id,
        action="approve",
        comment="合同批量审批通过",
    )

    assert len(results) == 2
    assert errors == []
    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.CONTRACT,
            SalesOperationLog.entity_id.in_([contract_a.id, contract_b.id]),
            SalesOperationLog.operation_type == SalesOperationType.APPROVE,
        )
        .order_by(SalesOperationLog.entity_id)
        .all()
    )

    assert len(logs) == 2
    assert {log.old_value["status"] for log in logs} == {"PENDING_APPROVAL"}
    assert {log.new_value["status"] for log in logs} == {"APPROVED"}
    assert all(log.remark == "合同批量审批通过" for log in logs)


def test_contract_withdraw_approval_writes_contract_status_change_log(
    db_session: Session, test_admin: User
):
    contract = _create_approved_contract(db_session, test_admin)
    contract.status = "PENDING_APPROVAL"
    task = _create_contract_approval_task(
        db_session, contract, test_admin, suffix_prefix="WITHDRAW"
    )
    instance_id = task.instance_id
    db_session.commit()

    class FakeApprovalEngine:
        def withdraw(self, **kwargs):
            assert kwargs["instance_id"] == instance_id
            contract.status = "DRAFT"
            instance = db_session.get(ApprovalInstance, instance_id)
            instance.status = "CANCELLED"
            db_session.flush()
            return instance

    service = ContractApprovalService(db_session)
    service.engine = FakeApprovalEngine()

    result = service.withdraw_approval(
        contract_id=contract.id,
        user_id=test_admin.id,
        reason="客户要求重提合同",
    )

    assert result["status"] == "withdrawn"
    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.CONTRACT,
            SalesOperationLog.entity_id == contract.id,
            SalesOperationLog.operation_type == SalesOperationType.STATUS_CHANGE,
        )
        .one()
    )

    assert log.old_value["status"] == "PENDING_APPROVAL"
    assert log.new_value["status"] == "DRAFT"
    assert "status" in log.changed_fields
    assert log.remark == "客户要求重提合同"


def test_quote_item_writes_sales_operation_logs(db_session: Session, test_admin: User):
    _quote, version, item = _create_quote_version_with_item(db_session, test_admin)

    create_response = create_quote_item(
        version.id,
        {
            "item_type": "MATERIAL",
            "item_name": "新增审计件",
            "qty": 2,
            "unit_price": 30,
            "cost": 12,
        },
        db=db_session,
        current_user=test_admin,
    )
    created_item_id = create_response.data["id"]

    update_quote_item(
        item.id,
        {"qty": 3, "unit_price": 50, "cost": 10},
        db=db_session,
        current_user=test_admin,
    )
    delete_quote_item(created_item_id, db=db_session, current_user=test_admin)

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE_VERSION,
            SalesOperationLog.entity_id == version.id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    operations = [log.operation_type for log in logs]
    assert operations.count(SalesOperationType.CREATE) == 1
    assert operations.count(SalesOperationType.UPDATE) == 1
    assert operations.count(SalesOperationType.DELETE) == 1

    update_log = next(log for log in logs if log.operation_type == SalesOperationType.UPDATE)
    assert update_log.old_value["item_id"] == item.id
    assert update_log.old_value["unit_price"] == "100.00"
    assert update_log.new_value["unit_price"] == "50"
    assert "unit_price" in update_log.changed_fields


def test_quote_cost_item_update_writes_quote_version_operation_log(
    db_session: Session, test_admin: User
):
    _quote, version, item = _create_quote_version_with_item(db_session, test_admin)
    item.cost = Decimal("12.00")
    item.cost_category = "材料"
    item.cost_source = "MANUAL"
    item.unit_price = Decimal("50.00")
    item.qty = Decimal("2")
    item.remark = "原始成本"
    db_session.commit()

    update_quote_cost_item(
        item_id=item.id,
        item_data={
            "cost": "88.00",
            "cost_category": "采购",
            "cost_source": "HISTORY",
            "unit_price": "120.00",
            "qty": "3",
            "remark": "按历史采购成本更新",
        },
        db=db_session,
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE_VERSION,
            SalesOperationLog.entity_id == version.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )

    assert log.old_value["item_id"] == item.id
    assert log.old_value["cost"] == "12.00"
    assert log.new_value["cost"] == "88.00"
    assert log.old_value["cost_category"] == "材料"
    assert log.new_value["cost_category"] == "采购"
    assert log.old_value["cost_source"] == "MANUAL"
    assert log.new_value["cost_source"] == "HISTORY"
    assert log.new_value["unit_price"] == "120.00"
    assert log.new_value["qty"] == "3"
    assert set(log.changed_fields) >= {
        "cost",
        "cost_category",
        "cost_source",
        "unit_price",
        "qty",
        "remark",
    }
    assert log.remark == f"quote_cost_item_id={item.id}"


def test_quote_cost_recalculate_writes_quote_version_operation_log(
    db_session: Session, test_admin: User
):
    quote, version, item = _create_quote_version_with_item(db_session, test_admin)
    item.qty = Decimal("2")
    item.unit_price = Decimal("100.00")
    item.cost = Decimal("30.00")
    second_item = QuoteItem(
        quote_version_id=version.id,
        item_type="SERVICE",
        item_name="调试服务",
        qty=Decimal("1"),
        unit_price=Decimal("50.00"),
        cost=Decimal("20.00"),
        unit="项",
    )
    db_session.add(second_item)
    version.cost_total = Decimal("20.00")
    version.total_price = Decimal("100.00")
    version.gross_margin = Decimal("80.00")
    db_session.commit()

    recalculate_cost(
        quote_id=quote.id,
        version_id=version.id,
        db=db_session,
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE_VERSION,
            SalesOperationLog.entity_id == version.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )

    assert log.old_value["cost_total"] == "20.00"
    assert log.new_value["cost_total"] == "80.00"
    assert log.old_value["total_price"] == "100.00"
    assert log.new_value["total_price"] == "250.00"
    assert log.old_value["gross_margin"] == "80.00"
    assert log.new_value["gross_margin"] == "68.00"
    assert set(log.changed_fields) >= {"cost_total", "total_price", "gross_margin"}
    assert log.remark == "quote_cost_recalculate"


def test_quote_cost_match_apply_writes_quote_version_operation_log(
    db_session: Session, test_admin: User
):
    quote, version, item = _create_quote_version_with_item(db_session, test_admin)
    item.qty = Decimal("1")
    item.unit_price = Decimal("100.00")
    item.cost = Decimal("20.00")
    item.cost_source = "MANUAL"
    second_item = QuoteItem(
        quote_version_id=version.id,
        item_type="MATERIAL",
        item_name="视觉模块",
        qty=Decimal("2"),
        unit_price=Decimal("80.00"),
        cost=Decimal("10.00"),
        cost_source="MANUAL",
        unit="件",
    )
    db_session.add(second_item)
    version.cost_total = Decimal("40.00")
    version.total_price = Decimal("260.00")
    version.gross_margin = Decimal("84.62")
    db_session.commit()

    apply_quote_cost_match_suggestions(
        quote_id=quote.id,
        version_id=version.id,
        apply_data=QuoteCostMatchApplyRequest(
            version_id=version.id,
            suggestions=[
                {
                    "item_id": item.id,
                    "cost": "40.00",
                    "specification": "STD-100",
                    "unit": "套",
                    "cost_category": "机械件",
                    "lead_time_days": 5,
                },
                {
                    "item_id": second_item.id,
                    "cost": "15.00",
                    "cost_category": "视觉件",
                    "lead_time_days": 12,
                },
            ],
        ),
        db=db_session,
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE_VERSION,
            SalesOperationLog.entity_id == version.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )

    assert log.old_value["cost_total"] == "40.00"
    assert log.new_value["cost_total"] == "70.00"
    assert log.old_value["gross_margin"] == "84.62"
    assert log.new_value["gross_margin"] == "73.08"
    assert log.new_value["updated_count"] == 2
    assert {item["item_id"] for item in log.new_value["items"]} == {
        item.id,
        second_item.id,
    }
    applied = {entry["item_id"]: entry for entry in log.new_value["items"]}
    assert applied[item.id]["cost"] == "40.00"
    assert applied[item.id]["cost_source"] == "HISTORY"
    assert applied[second_item.id]["cost"] == "15.00"
    assert set(log.changed_fields) >= {"cost_total", "gross_margin", "items"}
    assert log.remark == "quote_cost_match_apply"


def test_quote_cost_batch_update_prices_writes_quote_version_operation_log(
    db_session: Session, test_admin: User
):
    quote, version, item = _create_quote_version_with_item(db_session, test_admin)
    item.cost = Decimal("80.00")
    item.unit_price = Decimal("90.00")
    second_item = QuoteItem(
        quote_version_id=version.id,
        item_type="MATERIAL",
        item_name="软件授权",
        qty=Decimal("1"),
        unit_price=Decimal("45.00"),
        cost=Decimal("40.00"),
        unit="套",
    )
    db_session.add(second_item)
    db_session.commit()

    batch_update_prices(
        quote_id=quote.id,
        update_data=QuoteCostBatchUpdateRequest(
            version_id=version.id,
            mode="markup",
            rate=Decimal("25"),
        ),
        db=db_session,
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.QUOTE_VERSION,
            SalesOperationLog.entity_id == version.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )

    old_items = {entry["item_id"]: entry for entry in log.old_value["items"]}
    new_items = {entry["item_id"]: entry for entry in log.new_value["items"]}
    assert old_items[item.id]["unit_price"] == "90.00"
    assert new_items[item.id]["unit_price"] == "100.00"
    assert old_items[second_item.id]["unit_price"] == "45.00"
    assert new_items[second_item.id]["unit_price"] == "50.00"
    assert log.new_value["updated_count"] == 2
    assert log.new_value["mode"] == "markup"
    assert log.new_value["rate"] == "25"
    assert "items" in log.changed_fields
    assert log.remark == "quote_cost_batch_price_update"


def test_payment_record_writes_invoice_operation_logs(db_session: Session, test_admin: User):
    contract, invoice = _create_issued_invoice(db_session, test_admin)

    create_payment_record(
        db=db_session,
        record_data=PaymentRecordCreate(
            contract_id=contract.id,
            payment_date=date(2026, 7, 6),
            amount=Decimal("30.00"),
            payment_method="BANK",
            transaction_no="PAY-PERM07-001",
            remarks="首笔回款",
        ),
        current_user=test_admin,
    )
    update_payment_record(
        db=db_session,
        payment_id=invoice.id,
        record_data=PaymentRecordUpdate(
            amount=Decimal("40.00"),
            payment_date=date(2026, 7, 7),
            remarks="调整回款金额",
        ),
        current_user=test_admin,
    )
    delete_payment_record(db=db_session, payment_id=invoice.id, current_user=test_admin)

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.INVOICE,
            SalesOperationLog.entity_id == invoice.id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )
    operations = [log.operation_type for log in logs]

    assert operations == [
        SalesOperationType.CREATE,
        SalesOperationType.UPDATE,
        SalesOperationType.DELETE,
    ]
    assert logs[0].new_value["paid_amount"] == "30.00"
    assert logs[1].old_value["paid_amount"] == "30.00"
    assert logs[1].new_value["paid_amount"] == "40.00"
    assert "payment_status" in logs[2].changed_fields


def test_payment_match_writes_invoice_operation_log(db_session: Session, test_admin: User):
    _contract, invoice = _create_issued_invoice(db_session, test_admin)

    match_payment_to_invoice(
        db=db_session,
        payment_id=invoice.id,
        invoice_id=invoice.id,
        match_amount=Decimal("100.00"),
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.INVOICE,
            SalesOperationLog.entity_id == invoice.id,
            SalesOperationLog.operation_type == SalesOperationType.STATUS_CHANGE,
        )
        .one()
    )

    assert log.old_value["payment_status"] == "PENDING"
    assert log.new_value["payment_status"] == "PAID"
    assert log.new_value["paid_amount"] == "100.00"


def test_invoice_crud_writes_invoice_operation_logs(db_session: Session, test_admin: User):
    contract = _create_invoiceable_contract(db_session, test_admin)

    create_response = create_invoice(
        db=db_session,
        invoice_in=InvoiceCreate(
            contract_id=contract.id,
            invoice_type="SPECIAL",
            invoice_amount=Decimal("80.00"),
            tax_rate=Decimal("13.00"),
            tax_amount=Decimal("10.40"),
            total_amount=Decimal("90.40"),
            buyer_name="PERM07 原购买方",
            buyer_tax_no="91440300PERM07001",
        ),
        current_user=test_admin,
    )
    invoice_id = create_response.id

    update_invoice(
        db=db_session,
        invoice_id=invoice_id,
        invoice_in=InvoiceUpdate(
            invoice_amount=Decimal("90.00"),
            buyer_name="PERM07 更新购买方",
        ),
        current_user=test_admin,
    )
    delete_invoice(db=db_session, invoice_id=invoice_id, current_user=test_admin)

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.INVOICE,
            SalesOperationLog.entity_id == invoice_id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.UPDATE,
        SalesOperationType.DELETE,
    ]
    assert logs[0].new_value["amount"] == "80.00"
    assert logs[1].old_value["buyer_name"] == "PERM07 原购买方"
    assert logs[1].new_value["buyer_name"] == "PERM07 更新购买方"
    assert logs[1].new_value["amount"] == "90.00"
    assert set(logs[1].changed_fields) >= {"amount", "buyer_name"}
    assert logs[2].old_value["status"] == InvoiceStatusEnum.DRAFT.value


def test_invoice_issue_and_void_write_invoice_operation_logs(
    db_session: Session, test_admin: User
):
    invoice = _create_approved_invoice(db_session, test_admin)

    issue_invoice(
        db=db_session,
        invoice_id=invoice.id,
        issue_request=InvoiceIssueRequest(issue_date=date(2026, 7, 9)),
        current_user=test_admin,
    )
    void_invoice(
        db=db_session,
        invoice_id=invoice.id,
        reason="客户信息错误",
        current_user=test_admin,
    )

    original_logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.INVOICE,
            SalesOperationLog.entity_id == invoice.id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in original_logs] == [
        SalesOperationType.STATUS_CHANGE,
        SalesOperationType.STATUS_CHANGE,
    ]
    assert original_logs[0].old_value["status"] == InvoiceStatusEnum.APPROVED.value
    assert original_logs[0].new_value["status"] == InvoiceStatusEnum.ISSUED.value
    assert original_logs[0].new_value["payment_status"] == "PENDING"
    assert original_logs[1].old_value["status"] == InvoiceStatusEnum.ISSUED.value
    assert original_logs[1].new_value["status"] == InvoiceStatusEnum.CANCELLED.value
    assert "客户信息错误" in original_logs[1].remark

    red_invoice = (
        db_session.query(Invoice)
        .filter(
            Invoice.contract_id == invoice.contract_id,
            Invoice.invoice_type == "RED_CREDIT",
        )
        .one()
    )
    red_log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.INVOICE,
            SalesOperationLog.entity_id == red_invoice.id,
            SalesOperationLog.operation_type == SalesOperationType.CREATE,
        )
        .one()
    )
    assert red_log.new_value["amount"] == "-120.00"
    assert red_log.new_value["payment_status"] == "REVERSED"


def test_invoice_approval_start_writes_invoice_submit_log(
    db_session: Session, test_admin: User
):
    invoice, _task = _create_invoice_pending_approval_task(
        db_session,
        test_admin,
        suffix_prefix="START",
        invoice_status=InvoiceStatusEnum.DRAFT.value,
    )
    instance = db_session.get(ApprovalInstance, invoice.approval_instance_id)
    db_session.delete(_task)
    db_session.delete(instance)
    db_session.commit()

    start_invoice_approval(
        db=db_session,
        invoice_id=invoice.id,
        approval_request=ApprovalStartRequest(comment="提交开票审批"),
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.INVOICE,
            SalesOperationLog.entity_id == invoice.id,
            SalesOperationLog.operation_type == SalesOperationType.SUBMIT,
        )
        .one()
    )

    assert log.old_value["status"] == InvoiceStatusEnum.DRAFT.value
    assert log.new_value["status"] == "PENDING_APPROVAL"
    assert log.new_value["approval_instance_id"] is not None
    assert "status" in log.changed_fields
    assert log.remark == "提交开票审批"


def test_invoice_approval_action_writes_invoice_approve_log(
    db_session: Session, test_admin: User
):
    invoice, _task = _create_invoice_pending_approval_task(
        db_session, test_admin, suffix_prefix="APPROVE"
    )

    invoice_approval_action(
        db=db_session,
        invoice_id=invoice.id,
        action_request=ApprovalActionRequest(
            action="APPROVE",
            comment="同意开票",
        ),
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.INVOICE,
            SalesOperationLog.entity_id == invoice.id,
            SalesOperationLog.operation_type == SalesOperationType.APPROVE,
        )
        .one()
    )

    assert log.old_value["status"] == "PENDING_APPROVAL"
    assert log.new_value["status"] == InvoiceStatusEnum.APPROVED.value
    assert "status" in log.changed_fields
    assert log.remark == "同意开票"


def test_invoice_approval_action_writes_invoice_reject_log(
    db_session: Session, test_admin: User
):
    invoice, _task = _create_invoice_pending_approval_task(
        db_session, test_admin, suffix_prefix="REJECT"
    )

    invoice_approval_action(
        db=db_session,
        invoice_id=invoice.id,
        action_request=ApprovalActionRequest(
            action="REJECT",
            comment="信息需要重开",
        ),
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.INVOICE,
            SalesOperationLog.entity_id == invoice.id,
            SalesOperationLog.operation_type == SalesOperationType.REJECT,
        )
        .one()
    )

    assert log.old_value["status"] == "PENDING_APPROVAL"
    assert log.new_value["status"] == InvoiceStatusEnum.REJECTED.value
    assert "status" in log.changed_fields
    assert log.remark == "信息需要重开"


def test_contract_crud_writes_contract_operation_logs(
    db_session: Session, test_admin: User
):
    customer, opportunity = _create_contract_customer_and_opportunity(
        db_session, test_admin
    )

    create_response = create_contract(
        db=db_session,
        contract_in=ContractCreate(
            contract_name="PERM07 审计合同",
            customer_id=customer.id,
            opportunity_id=opportunity.id,
            contract_amount=Decimal("500.00"),
            payment_terms_summary="30%预付，70%验收",
        ),
        skip_g3_validation=True,
        current_user=test_admin,
    )
    contract_id = create_response.id

    update_contract(
        db=db_session,
        contract_id=contract_id,
        contract_in=ContractUpdate(
            contract_name="PERM07 审计合同-更新",
            contract_amount=Decimal("550.00"),
            payment_terms_summary="40%预付，60%验收",
        ),
        current_user=test_admin,
    )
    delete_contract(db=db_session, contract_id=contract_id, current_user=test_admin)

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.CONTRACT,
            SalesOperationLog.entity_id == contract_id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.UPDATE,
        SalesOperationType.DELETE,
    ]
    assert logs[0].new_value["contract_name"] == "PERM07 审计合同"
    assert logs[0].new_value["total_amount"] == "500.00"
    assert logs[1].old_value["contract_name"] == "PERM07 审计合同"
    assert logs[1].new_value["contract_name"] == "PERM07 审计合同-更新"
    assert logs[1].new_value["total_amount"] == "550.00"
    assert set(logs[1].changed_fields) >= {
        "contract_name",
        "total_amount",
        "payment_terms",
    }
    assert logs[2].old_value["status"] == "DRAFT"


def test_contract_from_quote_writes_contract_create_log(
    db_session: Session, test_admin: User
):
    quote, version, _item = _create_quote_version_with_item(db_session, test_admin)
    quote.status = "APPROVED"
    db_session.commit()

    response = create_contract_from_quote(
        db=db_session,
        request=ContractFromQuoteRequest(
            quote_id=quote.id,
            quote_version_id=version.id,
            contract_name="PERM07 报价转合同",
            payment_terms="50%预付，50%终验",
        ),
        skip_g3_validation=True,
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.CONTRACT,
            SalesOperationLog.entity_id == response.id,
            SalesOperationLog.operation_type == SalesOperationType.CREATE,
        )
        .one()
    )

    assert log.new_value["contract_name"] == "PERM07 报价转合同"
    assert log.new_value["quote_version_id"] == version.id
    assert log.new_value["total_amount"] == "100.00"
    assert log.new_value["payment_terms"] == "50%预付，50%终验"


def test_enhanced_contract_lifecycle_writes_operation_logs(
    db_session: Session, test_admin: User
):
    customer, opportunity = _create_contract_customer_and_opportunity(
        db_session, test_admin
    )

    contract = enhanced_contracts.create_contract(
        db=db_session,
        contract_data=EnhancedContractCreate(
            contract_name="PERM07 增强合同",
            contract_type="sales",
            customer_id=customer.id,
            opportunity_id=opportunity.id,
            total_amount=Decimal("900.00"),
            amount_with_tax=Decimal("900.00"),
            payment_terms="30%预付，70%终验",
            sales_owner_id=test_admin.id,
        ),
        current_user=test_admin,
    )

    enhanced_contracts.update_contract(
        db=db_session,
        contract_id=contract.id,
        contract_data=EnhancedContractUpdate(
            contract_name="PERM07 增强合同-更新",
            total_amount=Decimal("980.00"),
            payment_terms="40%预付，60%终验",
        ),
        current_user=test_admin,
    )

    term = enhanced_contracts.add_contract_term(
        db=db_session,
        contract_id=contract.id,
        term_data=EnhancedContractTermCreate(
            term_type="payment",
            term_content="按里程碑付款",
        ),
        current_user=test_admin,
    )
    enhanced_contracts.update_contract_term(
        db=db_session,
        term_id=term.id,
        term_data=EnhancedContractTermUpdate(term_content="按验收节点付款"),
        current_user=test_admin,
    )
    attachment = enhanced_contracts.upload_attachment(
        db=db_session,
        contract_id=contract.id,
        attachment_data=EnhancedContractAttachmentCreate(
            file_name="contract.pdf",
            file_path="/tmp/contract.pdf",
            file_type="application/pdf",
            file_size=1024,
        ),
        current_user=test_admin,
    )
    enhanced_contracts.delete_attachment(
        db=db_session, attachment_id=attachment.id, current_user=test_admin
    )
    enhanced_contracts.delete_contract_term(
        db=db_session, term_id=term.id, current_user=test_admin
    )
    enhanced_contracts.delete_contract(
        db=db_session, contract_id=contract.id, current_user=test_admin
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.CONTRACT,
            SalesOperationLog.entity_id == contract.id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.UPDATE,
        SalesOperationType.UPDATE,
        SalesOperationType.UPDATE,
        SalesOperationType.ATTACH,
        SalesOperationType.DELETE,
        SalesOperationType.UPDATE,
        SalesOperationType.DELETE,
    ]
    assert logs[0].new_value["contract_name"] == "PERM07 增强合同"
    assert logs[1].old_value["contract_name"] == "PERM07 增强合同"
    assert logs[1].new_value["contract_name"] == "PERM07 增强合同-更新"
    assert logs[2].new_value["term_content"] == "按里程碑付款"
    assert logs[3].old_value["term_content"] == "按里程碑付款"
    assert logs[3].new_value["term_content"] == "按验收节点付款"
    assert logs[4].new_value["file_name"] == "contract.pdf"
    assert logs[5].old_value["file_name"] == "contract.pdf"
    assert logs[6].old_value["term_content"] == "按验收节点付款"
    assert logs[7].old_value["contract_name"] == "PERM07 增强合同-更新"


def test_contract_sign_and_archive_write_status_change_logs(
    db_session: Session, test_admin: User
):
    contract = _create_approved_contract(db_session, test_admin)

    sign_contract(
        db=db_session,
        contract_id=contract.id,
        sign_request=ContractSignRequest(
            signed_date=date(2026, 7, 10),
            auto_create_project=False,
        ),
        auto_generate_payment_plans=False,
        current_user=test_admin,
    )
    archive_contract(db=db_session, contract_id=contract.id, current_user=test_admin)

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.CONTRACT,
            SalesOperationLog.entity_id == contract.id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.STATUS_CHANGE,
        SalesOperationType.STATUS_CHANGE,
    ]
    assert logs[0].old_value["status"] == "APPROVED"
    assert logs[0].new_value["status"] == "SIGNED"
    assert logs[0].new_value["signing_date"] == "2026-07-10"
    assert logs[1].old_value["status"] == "SIGNED"
    assert logs[1].new_value["status"] == "COMPLETED"


def test_contract_create_project_writes_contract_project_link_log(
    db_session: Session, test_admin: User
):
    customer, opportunity = _create_contract_customer_and_opportunity(
        db_session, test_admin
    )
    suffix = uuid.uuid4().hex[:8]
    contract = Contract(
        contract_code=f"CT-PROJ-PERM07-{suffix}",
        contract_name=f"PERM07 生成项目合同-{suffix}",
        contract_type="sales",
        customer_id=customer.id,
        opportunity_id=opportunity.id,
        total_amount=Decimal("1600.00"),
        amount_with_tax=Decimal("1600.00"),
        status="SIGNED",
        signing_date=date(2026, 7, 12),
        payment_terms="30%预付，70%终验",
        contract_subject="终验标准：设备联调通过",
        sales_owner_id=test_admin.id,
    )
    db_session.add(contract)
    db_session.flush()
    db_session.add(
        ContractDeliverable(
            contract_id=contract.id,
            deliverable_name="整机交付",
            deliverable_type="equipment",
            required_for_payment=True,
        )
    )
    db_session.commit()

    response = create_project_from_contract(
        contract_id=contract.id,
        db=db_session,
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.CONTRACT,
            SalesOperationLog.entity_id == contract.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )

    assert response["project_id"] == log.new_value["project_id"]
    assert log.old_value["project_id"] is None
    assert log.new_value["project_id"] is not None
    assert "project_id" in log.changed_fields
    assert response["project_code"] in log.remark


def test_payment_plan_create_writes_contract_update_log(
    db_session: Session, test_admin: User
):
    contract = _create_approved_contract(db_session, test_admin)

    create_payment_plans(
        db=db_session,
        payload=LegacyPaymentPlanCreateRequest(
            contract_id=contract.id,
            total_amount=Decimal("600.00"),
            payment_stages=[
                LegacyPaymentStageCreate(
                    stage="预付款",
                    percentage=Decimal("30.00"),
                    amount=Decimal("180.00"),
                ),
                LegacyPaymentStageCreate(
                    stage="尾款",
                    percentage=Decimal("70.00"),
                    amount=Decimal("420.00"),
                ),
            ],
        ),
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.CONTRACT,
            SalesOperationLog.entity_id == contract.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )

    assert log.old_value["payment_plans"] == []
    assert [plan["payment_name"] for plan in log.new_value["payment_plans"]] == [
        "预付款",
        "尾款",
    ]
    assert log.new_value["payment_plans"][0]["payment_ratio"] == "30.00"
    assert log.new_value["payment_plans"][0]["planned_amount"] == "180.00"
    assert log.new_value["payment_plans"][1]["payment_type"] == "WARRANTY"
    assert "payment_plans" in log.changed_fields


def test_contract_amendment_create_writes_contract_update_log(
    db_session: Session, test_admin: User
):
    contract = _create_approved_contract(db_session, test_admin)

    create_contract_amendment(
        db=db_session,
        contract_id=contract.id,
        amendment_in=ContractAmendmentCreate(
            contract_id=contract.id,
            amendment_type="AMOUNT",
            amendment_reason="客户增加视觉检测工位",
            amendment_content="合同金额增加 80 元，交付范围同步扩大",
            amendment_amount=Decimal("80.00"),
            effective_date=date(2026, 7, 20),
            remark="同步更新交付范围",
        ),
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.CONTRACT,
            SalesOperationLog.entity_id == contract.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )

    assert log.old_value["contract_amendments"] == []
    amendment = log.new_value["contract_amendments"][0]
    assert amendment["amendment_type"] == "AMOUNT"
    assert amendment["reason"] == "客户增加视觉检测工位"
    assert amendment["description"] == "合同金额增加 80 元，交付范围同步扩大"
    assert amendment["amount_change"] == "80.00"
    assert amendment["request_date"] == "2026-07-20"
    assert amendment["status"] == "PENDING"
    assert "contract_amendments" in log.changed_fields
    assert log.operation_desc == "创建合同变更记录"


def test_receivable_dispute_create_writes_operation_log(
    db_session: Session, test_admin: User
):
    contract = _create_approved_contract(db_session, test_admin)
    response = create_payment_plans(
        db=db_session,
        payload=LegacyPaymentPlanCreateRequest(
            contract_id=contract.id,
            total_amount=Decimal("300.00"),
            payment_stages=[
                LegacyPaymentStageCreate(
                    stage="验收款",
                    percentage=Decimal("100.00"),
                    amount=Decimal("300.00"),
                ),
            ],
        ),
        current_user=test_admin,
    )
    payment_id = response.data["items"][0]["id"]

    dispute = create_dispute(
        db=db_session,
        dispute_in=ReceivableDisputeCreate(
            payment_id=payment_id,
            reason_code="CUSTOMER_REJECT",
            description="客户对验收节点有异议",
            status="OPEN",
            responsible_dept="销售部",
            responsible_id=test_admin.id,
            expect_resolve_date=date(2026, 7, 20),
        ),
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "RECEIVABLE_DISPUTE",
            SalesOperationLog.entity_id == dispute.id,
            SalesOperationLog.operation_type == SalesOperationType.CREATE,
        )
        .one()
    )

    assert log.new_value["payment_id"] == payment_id
    assert log.new_value["reason_code"] == "CUSTOMER_REJECT"
    assert log.new_value["description"] == "客户对验收节点有异议"
    assert log.new_value["responsible_id"] == test_admin.id
    assert log.new_value["expect_resolve_date"] == "2026-07-20"
    assert log.changed_fields == []


def test_presale_expense_lost_projects_writes_operation_logs(
    db_session: Session, test_admin: User, monkeypatch
):
    def fake_expense_lost_projects(
        self,
        project_ids=None,
        start_date=None,
        end_date=None,
        created_by=None,
    ):
        return {
            "total_projects": 1,
            "total_expenses": 1,
            "total_amount": 288.0,
            "total_hours": 3.6,
            "expenses": [
                {
                    "project_id": 987,
                    "project_code": "P-LOST-001",
                    "project_name": "失单费用化项目",
                    "lead_id": 123,
                    "opportunity_id": 456,
                    "expense_type": "LABOR_COST",
                    "expense_category": "LOST_BID",
                    "amount": 288.0,
                    "labor_hours": 3.6,
                    "hourly_rate": 80.0,
                    "user_id": test_admin.id,
                    "user_name": test_admin.real_name,
                    "department_id": 8,
                    "department_name": "售前部",
                    "salesperson_id": test_admin.id,
                    "salesperson_name": test_admin.real_name,
                    "expense_date": date(2026, 7, 5),
                    "description": "未中标项目工时费用",
                    "loss_reason": "PRICE",
                    "created_by": created_by,
                }
            ],
        }

    monkeypatch.setattr(
        "app.services.cost.labor_cost_service.LaborCostExpenseService.expense_lost_projects",
        fake_expense_lost_projects,
    )

    response = expense_lost_projects(
        db=db_session,
        request=ExpenseLostProjectsRequest(project_ids=[987]),
        current_user=test_admin,
    )

    assert response.data["total_expenses"] == 1
    expense = db_session.query(PresaleExpense).one()
    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "PRESALE_EXPENSE",
            SalesOperationLog.entity_id == expense.id,
            SalesOperationLog.operation_type == SalesOperationType.CREATE,
        )
        .one()
    )

    assert log.entity_code == "P-LOST-001"
    assert log.new_value["project_id"] == 987
    assert log.new_value["expense_type"] == "LABOR_COST"
    assert log.new_value["amount"] == "288.00"
    assert log.new_value["labor_hours"] == "3.60"
    assert log.new_value["created_by"] == test_admin.id
    assert log.changed_fields == ["presale_expense"]


def test_scoring_rule_create_and_activate_write_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    version = f"PERM07-{suffix}"

    create_scoring_rule(
        db=db_session,
        request=ScoringRuleCreate(
            version=version,
            rules_json='{"thresholds": {"A": 85, "B": 70}}',
            description="PERM07 评分规则",
        ),
        current_user=test_admin,
    )
    rule = db_session.query(ScoringRule).filter(ScoringRule.version == version).one()

    activate_scoring_rule(
        db=db_session,
        rule_id=rule.id,
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "SCORING_RULE",
            SalesOperationLog.entity_id == rule.id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.STATUS_CHANGE,
    ]
    assert logs[0].new_value["version"] == version
    assert logs[0].new_value["rules_json"]["thresholds"]["A"] == 85
    assert logs[0].new_value["description"] == "PERM07 评分规则"
    assert logs[0].new_value["is_active"] is False
    assert logs[1].old_value["is_active"] is False
    assert logs[1].new_value["is_active"] is True
    assert logs[1].changed_fields == ["is_active"]


def test_scoring_rule_activate_logs_previous_active_rule_deactivation(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    old_rule = ScoringRule(
        version=f"PERM07-OLD-{suffix}",
        rules_json='{"thresholds": {"A": 90}}',
        description="原激活规则",
        is_active=True,
        created_by=test_admin.id,
    )
    new_rule = ScoringRule(
        version=f"PERM07-NEW-{suffix}",
        rules_json='{"thresholds": {"A": 85}}',
        description="新激活规则",
        is_active=False,
        created_by=test_admin.id,
    )
    db_session.add_all([old_rule, new_rule])
    db_session.commit()
    db_session.refresh(old_rule)
    db_session.refresh(new_rule)

    activate_scoring_rule(
        db=db_session,
        rule_id=new_rule.id,
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "SCORING_RULE",
            SalesOperationLog.entity_id.in_([old_rule.id, new_rule.id]),
            SalesOperationLog.operation_type == SalesOperationType.STATUS_CHANGE,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert len(logs) == 2
    logs_by_rule = {log.entity_id: log for log in logs}
    assert logs_by_rule[old_rule.id].old_value["is_active"] is True
    assert logs_by_rule[old_rule.id].new_value["is_active"] is False
    assert logs_by_rule[old_rule.id].changed_fields == ["is_active"]
    assert logs_by_rule[new_rule.id].old_value["is_active"] is False
    assert logs_by_rule[new_rule.id].new_value["is_active"] is True
    assert logs_by_rule[new_rule.id].changed_fields == ["is_active"]


def test_failure_case_create_and_update_write_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    response = create_failure_case(
        db=db_session,
        request=FailureCaseCreate(
            case_code=f"FC-PERM07-{suffix}",
            project_name="PERM07 失单案例",
            industry="3C电子",
            product_types='["FCT", "EOL"]',
            processes='["烧录", "视觉检测"]',
            takt_time_s=45,
            annual_volume=500000,
            budget_status="已批预算",
            customer_project_status="立项中",
            spec_status="SOW 不完整",
            price_sensitivity="HIGH",
            delivery_months=4,
            failure_tags='["报价偏高", "节拍风险"]',
            core_failure_reason="报价高于竞争对手且节拍方案未冻结",
            early_warning_signals='["客户压价", "样品未提供"]',
            final_result="LOST",
            lesson_learned="早期冻结节拍和样品边界",
            keywords='["节拍", "价格"]',
        ),
        current_user=test_admin,
    )

    update_failure_case(
        db=db_session,
        case_id=response.id,
        request=FailureCaseUpdate(
            project_name="PERM07 失单案例-复盘",
            failure_tags='["报价偏高", "需求冻结晚"]',
            core_failure_reason="需求冻结晚导致方案成本不可控",
            final_result="REVIEWED",
        ),
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "FAILURE_CASE",
            SalesOperationLog.entity_id == response.id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.UPDATE,
    ]
    assert logs[0].entity_code == f"FC-PERM07-{suffix}"
    assert logs[0].new_value["failure_tags"] == ["报价偏高", "节拍风险"]
    assert logs[0].new_value["early_warning_signals"] == ["客户压价", "样品未提供"]
    assert logs[1].old_value["project_name"] == "PERM07 失单案例"
    assert logs[1].new_value["project_name"] == "PERM07 失单案例-复盘"
    assert logs[1].old_value["failure_tags"] == ["报价偏高", "节拍风险"]
    assert logs[1].new_value["failure_tags"] == ["报价偏高", "需求冻结晚"]
    assert set(logs[1].changed_fields) >= {
        "project_name",
        "failure_tags",
        "core_failure_reason",
        "final_result",
    }


def test_assessment_template_and_items_write_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]

    created = create_assessment_template(
        db=db_session,
        request=TemplateCreateRequest(
            template_code=f"AT-PERM07-{suffix}",
            template_name="PERM07 技术评估模板",
            category="CUSTOM",
            description="非标设备技术评估",
            dimension_weights={"TECHNICAL": 60, "COMMERCIAL": 40},
        ),
        current_user=test_admin,
    )
    template_id = created.data["id"]

    update_assessment_template(
        db=db_session,
        template_id=template_id,
        request=TemplateUpdateRequest(
            template_name="PERM07 技术评估模板-更新",
            score_thresholds={"excellent": 95, "good": 80, "fair": 60, "poor": 0},
        ),
        current_user=test_admin,
    )
    set_default_template(
        db=db_session,
        template_id=template_id,
        category="CUSTOM",
        current_user=test_admin,
    )
    item = add_assessment_item(
        db=db_session,
        template_id=template_id,
        request=ItemCreateRequest(
            item_code=f"TECH-{suffix}",
            item_name="关键工艺成熟度",
            dimension="TECHNICAL",
            description="评估关键工艺是否成熟",
            weight=2.0,
            score_criteria={"levels": [{"score": 10, "description": "成熟"}]},
        ),
        current_user=test_admin,
    )
    batch_add_assessment_items(
        db=db_session,
        template_id=template_id,
        request=ItemBatchCreateRequest(
            items=[
                ItemCreateRequest(
                    item_code=f"COMM-{suffix}",
                    item_name="预算明确度",
                    dimension="COMMERCIAL",
                    weight=1.5,
                )
            ]
        ),
        current_user=test_admin,
    )

    template_logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "ASSESSMENT_TEMPLATE",
            SalesOperationLog.entity_id == template_id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in template_logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.UPDATE,
        SalesOperationType.STATUS_CHANGE,
    ]
    assert template_logs[0].entity_code == f"AT-PERM07-{suffix}"
    assert template_logs[0].new_value["template_name"] == "PERM07 技术评估模板"
    assert template_logs[1].old_value["template_name"] == "PERM07 技术评估模板"
    assert template_logs[1].new_value["template_name"] == "PERM07 技术评估模板-更新"
    assert "score_thresholds" in template_logs[1].changed_fields
    assert template_logs[2].old_value["is_default"] is False
    assert template_logs[2].new_value["is_default"] is True

    item_logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "ASSESSMENT_ITEM",
            SalesOperationLog.entity_id.in_([item.data["id"]]),
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in item_logs] == [SalesOperationType.CREATE]
    assert item_logs[0].new_value["item_code"] == f"TECH-{suffix}"
    assert item_logs[0].new_value["template_id"] == template_id

    batch_logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "ASSESSMENT_ITEM",
            SalesOperationLog.operation_type == SalesOperationType.CREATE,
            SalesOperationLog.new_value["item_code"].as_string() == f"COMM-{suffix}",
        )
        .all()
    )
    assert len(batch_logs) == 1
    assert batch_logs[0].new_value["template_id"] == template_id


def test_assessment_risk_and_version_write_operation_logs(
    db_session: Session, test_admin: User
):
    assessment = TechnicalAssessment(
        source_type=AssessmentSourceTypeEnum.LEAD.value,
        source_id=10001,
        evaluator_id=test_admin.id,
        status=AssessmentStatusEnum.COMPLETED.value,
        total_score=72,
        dimension_scores='{"TECHNICAL": 18, "COMMERCIAL": 16}',
        decision="有条件立项",
        risks="[]",
        conditions="[]",
    )
    db_session.add(assessment)
    db_session.commit()

    risk_response = create_assessment_risk(
        db=db_session,
        assessment_id=assessment.id,
        request=RiskCreateRequest(
            risk_type="TECHNICAL",
            risk_title="关键工艺验证风险",
            risk_description="核心测试工艺仍需样品验证",
            risk_level="HIGH",
            mitigation_plan="安排样品 DOE 验证",
        ),
        current_user=test_admin,
    )
    risk_id = risk_response.data["id"]

    update_risk_status(
        db=db_session,
        risk_id=risk_id,
        request=RiskStatusUpdateRequest(
            status="RESOLVED",
            note="样品验证通过",
        ),
        current_user=test_admin,
    )

    version_response = create_assessment_version(
        db=db_session,
        assessment_id=assessment.id,
        request=VersionCreateRequest(change_summary="初版技术评估归档"),
        change_summary=None,
        current_user=test_admin,
    )
    version_id = version_response.data["id"]

    risk_logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "ASSESSMENT_RISK",
            SalesOperationLog.entity_id == risk_id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in risk_logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.STATUS_CHANGE,
    ]
    assert risk_logs[0].entity_code == risk_response.data["risk_code"]
    assert risk_logs[0].new_value["risk_title"] == "关键工艺验证风险"
    assert risk_logs[0].new_value["assessment_id"] == assessment.id
    assert risk_logs[1].old_value["status"] == "OPEN"
    assert risk_logs[1].new_value["status"] == "RESOLVED"
    assert "status" in risk_logs[1].changed_fields
    assert risk_logs[1].new_value["resolution_notes"] == "样品验证通过"

    version_log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "ASSESSMENT_VERSION",
            SalesOperationLog.entity_id == version_id,
            SalesOperationLog.operation_type == SalesOperationType.CREATE,
        )
        .one()
    )
    assert version_log.new_value["assessment_id"] == assessment.id
    assert version_log.new_value["version_no"] == "V1.0"
    assert version_log.new_value["version_note"] == "初版技术评估归档"
    assert version_log.new_value["total_score"] == 72


def test_sales_target_create_and_update_write_target_operation_logs(
    db_session: Session, test_admin: User
):
    response = create_sales_target(
        db=db_session,
        target_data=SalesTargetCreate(
            target_scope="PERSONAL",
            user_id=test_admin.id,
            target_type="CONTRACT_AMOUNT",
            target_period="YEARLY",
            period_value="2026",
            target_value=Decimal("1200000.00"),
            description="2026 年个人合同额目标",
        ),
        current_user=test_admin,
    )

    update_sales_target(
        db=db_session,
        target_id=response.id,
        target_data=SalesTargetUpdate(
            target_value=Decimal("1500000.00"),
            description="2026 年个人合同额目标-调整",
            status="COMPLETED",
        ),
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "TARGET",
            SalesOperationLog.entity_id == response.id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.UPDATE,
    ]
    assert logs[0].new_value["target_scope"] == "PERSONAL"
    assert logs[0].new_value["user_id"] == test_admin.id
    assert logs[0].new_value["target_value"] == "1200000.00"
    assert logs[0].new_value["status"] == "ACTIVE"
    assert logs[1].old_value["target_value"] == "1200000.00"
    assert logs[1].new_value["target_value"] == "1500000.00"
    assert logs[1].old_value["status"] == "ACTIVE"
    assert logs[1].new_value["status"] == "COMPLETED"
    assert set(logs[1].changed_fields) >= {
        "target_value",
        "description",
        "status",
    }


def test_sales_team_crud_writes_team_operation_logs(db_session: Session, test_admin: User):
    suffix = uuid.uuid4().hex[:8]
    create_response = create_sales_team(
        db=db_session,
        request=SalesTeamCreate(
            team_code=f"TEAM-PERM07-{suffix}",
            team_name="PERM07 审计销售团队",
            description="华南区大客户销售团队",
            team_type="REGION",
            sort_order=10,
        ),
        current_user=test_admin,
    )
    team_id = create_response.data["id"]

    update_sales_team(
        db=db_session,
        team_id=team_id,
        request=SalesTeamUpdate(
            team_name="PERM07 审计销售团队-调整",
            description="华南区战略客户销售团队",
            team_type="SCALE",
            sort_order=20,
        ),
        current_user=test_admin,
    )
    delete_sales_team(db=db_session, team_id=team_id, current_user=test_admin)

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "TEAM",
            SalesOperationLog.entity_id == team_id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.UPDATE,
        SalesOperationType.DELETE,
    ]
    assert logs[0].new_value["team_code"] == f"TEAM-PERM07-{suffix}"
    assert logs[0].new_value["team_name"] == "PERM07 审计销售团队"
    assert logs[0].new_value["is_active"] is True
    assert logs[1].old_value["team_name"] == "PERM07 审计销售团队"
    assert logs[1].new_value["team_name"] == "PERM07 审计销售团队-调整"
    assert logs[1].old_value["team_type"] == "REGION"
    assert logs[1].new_value["team_type"] == "SCALE"
    assert set(logs[1].changed_fields) >= {"team_name", "description", "team_type", "sort_order"}
    assert logs[2].old_value["is_active"] is True
    assert logs[2].new_value["is_active"] is False


def test_sales_team_pk_lifecycle_writes_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    team_a = SalesTeam(
        team_code=f"TEAM-PK-A-{suffix}",
        team_name="PERM07 PK A 队",
        team_type="REGION",
        created_by=test_admin.id,
    )
    team_b = SalesTeam(
        team_code=f"TEAM-PK-B-{suffix}",
        team_name="PERM07 PK B 队",
        team_type="REGION",
        created_by=test_admin.id,
    )
    db_session.add_all([team_a, team_b])
    db_session.commit()

    create_response = create_team_pk(
        db=db_session,
        request=TeamPKCreateRequest(
            pk_name=f"PERM07 团队PK-{suffix}",
            pk_type="LEAD_COUNT",
            team_ids=[team_a.id, team_b.id],
            start_date=datetime(2099, 1, 1),
            end_date=datetime(2099, 2, 1),
            target_value=Decimal("10.00"),
            reward_description="初始奖励",
        ),
        current_user=test_admin,
    )
    pk_id = create_response.data["id"]

    update_team_pk(
        db=db_session,
        pk_id=pk_id,
        request=TeamPKUpdateRequest(
            pk_name=f"PERM07 团队PK-调整-{suffix}",
            target_value=Decimal("20.00"),
            reward_description="调整奖励",
        ),
        current_user=test_admin,
    )
    complete_team_pk(db=db_session, pk_id=pk_id, current_user=test_admin)

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "TEAM_PK",
            SalesOperationLog.entity_id == pk_id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.UPDATE,
        SalesOperationType.STATUS_CHANGE,
    ]
    assert logs[0].new_value["pk_name"] == f"PERM07 团队PK-{suffix}"
    assert logs[0].new_value["team_ids"] == [team_a.id, team_b.id]
    assert logs[0].new_value["status"] == "PENDING"
    assert logs[1].old_value["target_value"] == "10.00"
    assert logs[1].new_value["target_value"] == "20.00"
    assert logs[1].new_value["reward_description"] == "调整奖励"
    assert set(logs[1].changed_fields) >= {
        "pk_name",
        "target_value",
        "reward_description",
    }
    assert logs[2].old_value["status"] == "PENDING"
    assert logs[2].new_value["status"] == "COMPLETED"
    assert logs[2].new_value["winner_team_id"] in {team_a.id, team_b.id}
    assert "result_summary" in logs[2].changed_fields


def test_sales_team_member_changes_write_team_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    team = SalesTeam(
        team_code=f"TEAM-MEMBER-PERM07-{suffix}",
        team_name="PERM07 成员审计销售团队",
        team_type="REGION",
        created_by=test_admin.id,
    )
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)

    add_response = add_team_member(
        db=db_session,
        team_id=team.id,
        request=TeamMemberAddRequest(
            user_id=test_admin.id,
            role="MEMBER",
            is_primary=False,
            remark="初始加入",
        ),
        current_user=test_admin,
    )
    member_id = add_response.data["id"]

    update_team_member(
        db=db_session,
        team_id=team.id,
        member_id=member_id,
        request=TeamMemberUpdateRequest(
            role="DEPUTY",
            is_primary=False,
            remark="重点客户维护",
        ),
        current_user=test_admin,
    )
    remove_team_member(
        db=db_session,
        team_id=team.id,
        member_id=member_id,
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "TEAM",
            SalesOperationLog.entity_id == team.id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.UPDATE,
        SalesOperationType.UPDATE,
        SalesOperationType.UPDATE,
    ]
    assert logs[0].old_value["team_member"] is None
    assert logs[0].new_value["team_member"]["user_id"] == test_admin.id
    assert logs[0].new_value["team_member"]["role"] == "MEMBER"
    assert logs[0].new_value["team_member"]["is_active"] is True
    assert logs[1].old_value["team_member"]["role"] == "MEMBER"
    assert logs[1].new_value["team_member"]["role"] == "DEPUTY"
    assert logs[1].old_value["team_member"]["remark"] == "初始加入"
    assert logs[1].new_value["team_member"]["remark"] == "重点客户维护"
    assert "team_member" in logs[1].changed_fields
    assert logs[2].old_value["team_member"]["is_active"] is True
    assert logs[2].new_value["team_member"]["is_active"] is False


def test_sales_team_member_batch_add_writes_team_operation_log(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    team = SalesTeam(
        team_code=f"TEAM-MEMBER-BATCH-PERM07-{suffix}",
        team_name="PERM07 成员批量审计销售团队",
        team_type="REGION",
        created_by=test_admin.id,
    )
    new_member_user = User(
        username=f"perm07_team_member_{suffix}",
        password_hash="not-used",
        email=f"perm07_team_member_{suffix}@example.com",
        real_name="PERM07 团队成员",
        is_active=True,
    )
    db_session.add_all([team, new_member_user])
    db_session.commit()
    db_session.refresh(team)
    db_session.refresh(new_member_user)

    batch_add_team_members(
        db=db_session,
        team_id=team.id,
        request=TeamMemberBatchAddRequest(
            user_ids=[test_admin.id, new_member_user.id],
            role="MEMBER",
        ),
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "TEAM",
            SalesOperationLog.entity_id == team.id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [SalesOperationType.UPDATE]
    assert logs[0].old_value["team_members"] == []
    assert {member["user_id"] for member in logs[0].new_value["team_members"]} == {
        test_admin.id,
        new_member_user.id,
    }
    assert {member["role"] for member in logs[0].new_value["team_members"]} == {"MEMBER"}
    assert "team_members" in logs[0].changed_fields


def test_quote_cost_template_crud_writes_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    create_response = create_cost_template(
        db=db_session,
        template_in=QuoteCostTemplateCreate(
            name=f"PERM07 成本模板-{suffix}",
            category="STANDARD",
            description="标准成本结构",
            items=[
                {"name": "机械件", "amount": "80000.00"},
                {"name": "电气件", "amount": "50000.00"},
            ],
        ),
        current_user=test_admin,
    )
    template_id = create_response.id

    update_cost_template(
        db=db_session,
        template_id=template_id,
        template_in=QuoteCostTemplateUpdate(
            name=f"PERM07 成本模板-调整-{suffix}",
            category="CUSTOM",
            description="定制成本结构",
            items=[
                {"name": "机械件", "amount": "90000.00"},
                {"name": "视觉模块", "amount": "30000.00"},
            ],
        ),
        current_user=test_admin,
    )

    delete_cost_template(
        db=db_session,
        template_id=template_id,
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "QUOTE_COST_TEMPLATE",
            SalesOperationLog.entity_id == template_id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.UPDATE,
        SalesOperationType.DELETE,
    ]
    assert logs[0].new_value["template_name"] == f"PERM07 成本模板-{suffix}"
    assert logs[0].new_value["template_type"] == "STANDARD"
    assert logs[0].new_value["cost_structure"]["items"][0]["name"] == "机械件"
    assert logs[1].old_value["template_name"] == f"PERM07 成本模板-{suffix}"
    assert logs[1].new_value["template_name"] == f"PERM07 成本模板-调整-{suffix}"
    assert logs[1].old_value["cost_structure"]["items"][0]["amount"] == "80000.00"
    assert logs[1].new_value["cost_structure"]["items"][0]["amount"] == "90000.00"
    assert set(logs[1].changed_fields) >= {
        "template_name",
        "template_type",
        "description",
        "cost_structure",
    }
    assert logs[2].old_value["template_name"] == f"PERM07 成本模板-调整-{suffix}"
    assert logs[2].new_value == {}


def test_purchase_material_cost_crud_writes_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    create_response = create_purchase_material_cost(
        db=db_session,
        cost_in=PurchaseMaterialCostCreate(
            material_code=f"MAT-PERM07-{suffix}",
            material_name=f"PERM07 采购物料-{suffix}",
            specification="L300",
            brand="供应商品牌A",
            unit="件",
            material_type="机械件",
            is_standard_part=True,
            unit_cost=Decimal("12.3400"),
            currency="CNY",
            supplier_name="测试供应商A",
            purchase_date=date(2026, 7, 1),
            purchase_order_no=f"PO-PERM07-{suffix}",
            purchase_quantity=Decimal("20.0000"),
            lead_time_days=7,
            match_priority=5,
            match_keywords="机械件,L300",
            remark="初始采购成本",
        ),
        current_user=test_admin,
    )
    cost_id = create_response.id

    update_purchase_material_cost(
        db=db_session,
        cost_id=cost_id,
        cost_in=PurchaseMaterialCostUpdate(
            material_name=f"PERM07 采购物料-调整-{suffix}",
            unit_cost=Decimal("13.5000"),
            supplier_name="测试供应商B",
            purchase_date=date(2026, 7, 2),
            purchase_quantity=Decimal("25.0000"),
            lead_time_days=9,
            match_priority=8,
            match_keywords="机械件,L300,优先",
            remark="更新采购成本",
        ),
        current_user=test_admin,
    )

    delete_purchase_material_cost(
        db=db_session,
        cost_id=cost_id,
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "PURCHASE_MATERIAL_COST",
            SalesOperationLog.entity_id == cost_id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.UPDATE,
        SalesOperationType.DELETE,
    ]
    assert logs[0].new_value["material_code"] == f"MAT-PERM07-{suffix}"
    assert logs[0].new_value["material_name"] == f"PERM07 采购物料-{suffix}"
    assert logs[0].new_value["unit_cost"] == "12.3400"
    assert logs[0].new_value["purchase_date"] == "2026-07-01"
    assert logs[0].new_value["submitted_by"] == test_admin.id
    assert logs[1].old_value["material_name"] == f"PERM07 采购物料-{suffix}"
    assert logs[1].new_value["material_name"] == f"PERM07 采购物料-调整-{suffix}"
    assert logs[1].old_value["unit_cost"] == "12.3400"
    assert logs[1].new_value["unit_cost"] == "13.5000"
    assert logs[1].new_value["supplier_name"] == "测试供应商B"
    assert logs[1].new_value["match_priority"] == 8
    assert set(logs[1].changed_fields) >= {
        "material_name",
        "unit_cost",
        "supplier_name",
        "purchase_date",
        "purchase_quantity",
        "lead_time_days",
        "match_priority",
        "match_keywords",
        "remark",
    }
    assert logs[2].old_value["material_name"] == f"PERM07 采购物料-调整-{suffix}"
    assert logs[2].new_value == {}


def test_material_cost_reminder_update_acknowledge_writes_operation_logs(
    db_session: Session, test_admin: User
):
    reminder = MaterialCostUpdateReminder(
        reminder_type="PERIODIC",
        reminder_interval_days=30,
        next_reminder_date=date(2026, 7, 10),
        is_enabled=True,
        include_standard=True,
        include_non_standard=True,
        notify_roles=["procurement"],
        notify_users=[],
        reminder_count=0,
    )
    db_session.add(reminder)
    db_session.commit()

    update_cost_update_reminder(
        db=db_session,
        reminder_in=MaterialCostUpdateReminderUpdate(
            reminder_interval_days=45,
            next_reminder_date=date(2026, 8, 1),
            material_type_filter="机械件",
            include_non_standard=False,
            notify_roles=["procurement_manager"],
            notify_users=[test_admin.id],
        ),
        current_user=test_admin,
    )

    acknowledge_cost_update_reminder(db=db_session, current_user=test_admin)

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "MATERIAL_COST_REMINDER",
            SalesOperationLog.entity_id == reminder.id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.UPDATE,
        SalesOperationType.STATUS_CHANGE,
    ]
    assert logs[0].old_value["reminder_interval_days"] == 30
    assert logs[0].new_value["reminder_interval_days"] == 45
    assert logs[0].new_value["material_type_filter"] == "机械件"
    assert logs[0].new_value["notify_users"] == [test_admin.id]
    assert set(logs[0].changed_fields) >= {
        "reminder_interval_days",
        "next_reminder_date",
        "material_type_filter",
        "include_non_standard",
        "notify_roles",
        "notify_users",
        "last_updated_by",
    }
    assert logs[1].old_value["reminder_count"] == 0
    assert logs[1].new_value["reminder_count"] == 1
    assert logs[1].new_value["last_reminder_date"] is not None
    assert "next_reminder_date" in logs[1].changed_fields


def test_material_cost_match_updates_usage_with_operation_log(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    cost = PurchaseMaterialCost(
        material_code=f"MATCH-PERM07-{suffix}",
        material_name=f"PERM07 匹配物料-{suffix}",
        specification="L500",
        unit="件",
        material_type="机械件",
        is_standard_part=True,
        unit_cost=Decimal("88.0000"),
        currency="CNY",
        supplier_name="匹配供应商",
        purchase_date=date(2026, 7, 4),
        is_active=True,
        match_priority=9,
        usage_count=0,
        submitted_by=test_admin.id,
    )
    db_session.add(cost)
    db_session.commit()

    result = match_material_cost(
        db=db_session,
        match_request=MaterialCostMatchRequest(item_name=f"PERM07 匹配物料-{suffix}"),
        current_user=test_admin,
    )

    assert result.matched is True
    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "PURCHASE_MATERIAL_COST",
            SalesOperationLog.entity_id == cost.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )

    assert log.old_value["usage_count"] == 0
    assert log.new_value["usage_count"] == 1
    assert log.old_value["last_used_at"] is None
    assert log.new_value["last_used_at"] is not None
    assert set(log.changed_fields) >= {"usage_count", "last_used_at"}
    assert log.remark == "material_cost_match"


def test_quote_template_lifecycle_writes_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    create_response = create_quote_template(
        template_data={
            "template_name": f"PERM07 报价模板-{suffix}",
            "category": "ICT",
            "description": "标准 ICT 报价结构",
            "visibility_scope": "PRIVATE",
            "sections": {"items": [{"item_name": "ICT 测试工站", "qty": 1}]},
            "pricing_rules": {"total_price": "100000.00"},
            "release_notes": "初始模板",
        },
        db=db_session,
        current_user=test_admin,
    )
    template_id = create_response.data["id"]

    update_quote_template(
        template_id=template_id,
        template_data={
            "template_name": f"PERM07 报价模板-调整-{suffix}",
            "category": "FCT",
            "description": "标准 FCT 报价结构",
            "visibility_scope": "PUBLIC",
            "is_default": True,
            "status": "ACTIVE",
        },
        db=db_session,
        current_user=test_admin,
    )

    version_response = create_template_version(
        template_id=template_id,
        version_data={
            "version_no": "V2",
            "sections": {"items": [{"item_name": "FCT 测试工站", "qty": 2}]},
            "pricing_rules": {"total_price": "220000.00"},
            "release_notes": "增加双工位配置",
        },
        db=db_session,
        current_user=test_admin,
    )

    publish_template(template_id=template_id, db=db_session, current_user=test_admin)

    draft_response = create_quote_template(
        template_data={
            "template_name": f"PERM07 待删除报价模板-{suffix}",
            "category": "DRAFT",
        },
        db=db_session,
        current_user=test_admin,
    )
    draft_template_id = draft_response.data["id"]
    delete_quote_template(
        template_id=draft_template_id,
        db=db_session,
        current_user=test_admin,
    )

    template_logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "QUOTE_TEMPLATE",
            SalesOperationLog.entity_id == template_id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )
    version_logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "QUOTE_TEMPLATE_VERSION",
            SalesOperationLog.entity_id == version_response.data["id"],
        )
        .order_by(SalesOperationLog.id)
        .all()
    )
    deleted_template_log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "QUOTE_TEMPLATE",
            SalesOperationLog.entity_id == draft_template_id,
            SalesOperationLog.operation_type == SalesOperationType.DELETE,
        )
        .one()
    )

    assert [log.operation_type for log in template_logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.UPDATE,
        SalesOperationType.STATUS_CHANGE,
    ]
    assert template_logs[0].new_value["template_name"] == f"PERM07 报价模板-{suffix}"
    assert template_logs[0].new_value["current_version"]["version_no"] == "V1"
    assert template_logs[1].old_value["template_name"] == f"PERM07 报价模板-{suffix}"
    assert template_logs[1].new_value["template_name"] == f"PERM07 报价模板-调整-{suffix}"
    assert template_logs[1].old_value["visibility_scope"] == "PRIVATE"
    assert template_logs[1].new_value["visibility_scope"] == "PUBLIC"
    assert set(template_logs[1].changed_fields) >= {
        "template_name",
        "category",
        "description",
        "visibility_scope",
        "is_default",
        "status",
    }
    assert template_logs[2].old_value["status"] == "ACTIVE"
    assert template_logs[2].new_value["status"] == "PUBLISHED"
    assert template_logs[2].new_value["current_version_id"] == template_logs[0].new_value[
        "current_version_id"
    ]
    assert [log.operation_type for log in version_logs] == [
        SalesOperationType.CREATE,
    ]
    assert version_logs[0].new_value["version_no"] == "V2"
    assert version_logs[0].new_value["template_id"] == template_id
    assert version_logs[0].new_value["sections"]["items"][0]["item_name"] == "FCT 测试工站"
    assert version_logs[0].new_value["pricing_rules"]["total_price"] == "220000.00"
    assert deleted_template_log.old_value["template_name"] == f"PERM07 待删除报价模板-{suffix}"
    assert deleted_template_log.old_value["status"] == "DRAFT"


def test_structured_quote_template_lifecycle_writes_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    create_response = create_structured_quote_template(
        db=db_session,
        template_in=QuoteTemplateCreate(
            template_code=f"SQT-PERM07-{suffix}",
            template_name=f"PERM07 结构化报价模板-{suffix}",
            category="ATE",
            description="标准结构化报价模板",
            visibility_scope="TEAM",
            initial_version=QuoteTemplateVersionCreate(
                version_no="V1",
                sections={"items": [{"item_name": "ATE 测试工站", "qty": 1}]},
                pricing_rules={"total_price": "180000.00"},
                config_schema={"fields": ["station_count"]},
                discount_rules={"max_discount_pct": "5"},
                release_notes="初始结构化报价模板",
            ),
        ),
        current_user=test_admin,
    )
    template_id = create_response.id
    initial_version_id = create_response.current_version_id

    update_structured_quote_template(
        db=db_session,
        template_id=template_id,
        template_in=QuoteTemplateUpdate(
            template_name=f"PERM07 结构化报价模板-调整-{suffix}",
            category="FCT",
            description="FCT 结构化报价模板",
            visibility_scope="ALL",
            is_default=True,
            status="ACTIVE",
        ),
        current_user=test_admin,
    )

    version_response = create_structured_quote_template_version(
        db=db_session,
        template_id=template_id,
        version_in=QuoteTemplateVersionCreate(
            version_no="V2",
            sections={"items": [{"item_name": "FCT 测试工站", "qty": 2}]},
            pricing_rules={"total_price": "260000.00"},
            config_schema={"fields": ["station_count", "vision_module"]},
            discount_rules={"max_discount_pct": "8"},
            release_notes="增加视觉模块配置",
        ),
        current_user=test_admin,
    )

    publish_structured_quote_template_version(
        db=db_session,
        template_id=template_id,
        version_id=version_response.id,
        current_user=test_admin,
    )

    template_logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "QUOTE_TEMPLATE",
            SalesOperationLog.entity_id == template_id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )
    initial_version_log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "QUOTE_TEMPLATE_VERSION",
            SalesOperationLog.entity_id == initial_version_id,
            SalesOperationLog.operation_type == SalesOperationType.CREATE,
        )
        .one()
    )
    version_logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "QUOTE_TEMPLATE_VERSION",
            SalesOperationLog.entity_id == version_response.id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in template_logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.UPDATE,
        SalesOperationType.STATUS_CHANGE,
    ]
    assert template_logs[0].new_value["template_code"] == f"SQT-PERM07-{suffix}"
    assert template_logs[0].new_value["current_version"]["version_no"] == "V1"
    assert template_logs[1].old_value["template_name"] == f"PERM07 结构化报价模板-{suffix}"
    assert template_logs[1].new_value["template_name"] == f"PERM07 结构化报价模板-调整-{suffix}"
    assert template_logs[1].old_value["visibility_scope"] == "TEAM"
    assert template_logs[1].new_value["visibility_scope"] == "ALL"
    assert set(template_logs[1].changed_fields) >= {
        "template_name",
        "category",
        "description",
        "visibility_scope",
        "is_default",
        "status",
    }
    assert template_logs[2].old_value["current_version_id"] == initial_version_id
    assert template_logs[2].new_value["current_version_id"] == version_response.id
    assert initial_version_log.new_value["version_no"] == "V1"
    assert initial_version_log.new_value["pricing_rules"]["total_price"] == "180000.00"
    assert [log.operation_type for log in version_logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.STATUS_CHANGE,
    ]
    assert version_logs[0].new_value["version_no"] == "V2"
    assert version_logs[0].new_value["sections"]["items"][0]["item_name"] == "FCT 测试工站"
    assert version_logs[1].old_value["status"] == "DRAFT"
    assert version_logs[1].new_value["status"] == "PUBLISHED"
    assert version_logs[1].new_value["published_by"] == test_admin.id


def test_contract_template_lifecycle_writes_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    create_response = create_contract_template(
        db=db_session,
        template_in=ContractTemplateCreate(
            template_code=f"CT-PERM07-{suffix}",
            template_name=f"PERM07 合同模板-{suffix}",
            contract_type="SALES",
            description="标准销售合同模板",
            visibility_scope="TEAM",
            initial_version=ContractTemplateVersionCreate(
                version_no="V1",
                clause_sections={
                    "payment": {"title": "付款条款", "content": "30%预付款"},
                    "delivery": {"title": "交付条款", "content": "验收后交付"},
                },
                clause_library={"payment_terms": ["30%预付款"]},
                attachment_refs=["报价单"],
                approval_flow={"steps": ["法务复核"]},
                release_notes="初始合同模板",
            ),
        ),
        current_user=test_admin,
    )
    template_id = create_response.id
    initial_version_id = create_response.current_version_id

    update_contract_template(
        db=db_session,
        template_id=template_id,
        template_in=ContractTemplateUpdate(
            template_name=f"PERM07 合同模板-调整-{suffix}",
            contract_type="FRAMEWORK",
            description="框架销售合同模板",
            visibility_scope="ALL",
            is_default=True,
            status="ACTIVE",
        ),
        current_user=test_admin,
    )

    version_response = create_contract_template_version(
        db=db_session,
        template_id=template_id,
        version_in=ContractTemplateVersionCreate(
            version_no="V2",
            clause_sections={
                "payment": {"title": "付款条款", "content": "40%预付款"},
                "warranty": {"title": "质保条款", "content": "验收后12个月"},
            },
            clause_library={"payment_terms": ["40%预付款"], "warranty": ["12个月"]},
            attachment_refs=["报价单", "技术协议"],
            approval_flow={"steps": ["法务复核", "财务复核"]},
            release_notes="增加质保条款",
        ),
        current_user=test_admin,
    )

    publish_contract_template_version(
        db=db_session,
        template_id=template_id,
        version_id=version_response.id,
        current_user=test_admin,
    )

    template_logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "CONTRACT_TEMPLATE",
            SalesOperationLog.entity_id == template_id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )
    initial_version_log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "CONTRACT_TEMPLATE_VERSION",
            SalesOperationLog.entity_id == initial_version_id,
            SalesOperationLog.operation_type == SalesOperationType.CREATE,
        )
        .one()
    )
    version_logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "CONTRACT_TEMPLATE_VERSION",
            SalesOperationLog.entity_id == version_response.id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in template_logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.UPDATE,
        SalesOperationType.STATUS_CHANGE,
    ]
    assert template_logs[0].new_value["template_code"] == f"CT-PERM07-{suffix}"
    assert template_logs[0].new_value["current_version"]["version_no"] == "V1"
    assert template_logs[1].old_value["template_name"] == f"PERM07 合同模板-{suffix}"
    assert template_logs[1].new_value["template_name"] == f"PERM07 合同模板-调整-{suffix}"
    assert template_logs[1].old_value["contract_type"] == "SALES"
    assert template_logs[1].new_value["contract_type"] == "FRAMEWORK"
    assert set(template_logs[1].changed_fields) >= {
        "template_name",
        "contract_type",
        "description",
        "visibility_scope",
        "is_default",
        "status",
    }
    assert template_logs[2].old_value["current_version_id"] == initial_version_id
    assert template_logs[2].new_value["current_version_id"] == version_response.id
    assert initial_version_log.new_value["version_no"] == "V1"
    assert initial_version_log.new_value["clause_sections"]["payment"]["content"] == "30%预付款"
    assert [log.operation_type for log in version_logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.STATUS_CHANGE,
    ]
    assert version_logs[0].new_value["version_no"] == "V2"
    assert version_logs[0].new_value["clause_sections"]["warranty"]["content"] == "验收后12个月"
    assert version_logs[1].old_value["status"] == "DRAFT"
    assert version_logs[1].new_value["status"] == "PUBLISHED"
    assert version_logs[1].new_value["published_by"] == test_admin.id


def test_cpq_rule_set_create_update_writes_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    create_response = create_cpq_rule_set(
        db=db_session,
        rule_set_in=CpqRuleSetCreate(
            rule_code=f"CPQ-PERM07-{suffix}",
            rule_name=f"PERM07 CPQ 规则-{suffix}",
            description="标准 CPQ 规则",
            base_price=Decimal("120000.00"),
            currency="CNY",
            config_schema={
                "axes": [
                    {"key": "station_count", "label": "工站数"},
                    {"key": "vision_module", "label": "视觉模块"},
                ]
            },
            pricing_matrix={
                "station_count": {"1": "120000.00", "2": "180000.00"},
                "vision_module": {"enabled": "45000.00"},
            },
            approval_threshold={"discount_pct": "8", "amount": "200000.00"},
            visibility_scope="TEAM",
            is_default=True,
            owner_role="SALES_MANAGER",
        ),
        current_user=test_admin,
    )

    update_cpq_rule_set(
        db=db_session,
        rule_set_id=create_response.id,
        rule_set_in=CpqRuleSetUpdate(
            rule_name=f"PERM07 CPQ 规则-调整-{suffix}",
            description="框架 CPQ 规则",
            status="ACTIVE",
            base_price=Decimal("135000.00"),
            pricing_matrix={
                "station_count": {"1": "135000.00", "2": "195000.00"},
                "vision_module": {"enabled": "50000.00"},
            },
            approval_threshold={"discount_pct": "6", "amount": "220000.00"},
            visibility_scope="ALL",
            is_default=False,
            owner_role="SALES_DIRECTOR",
        ),
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "CPQ_RULE_SET",
            SalesOperationLog.entity_id == create_response.id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.UPDATE,
    ]
    assert logs[0].new_value["rule_code"] == f"CPQ-PERM07-{suffix}"
    assert logs[0].new_value["base_price"] == "120000.00"
    assert logs[0].new_value["pricing_matrix"]["vision_module"]["enabled"] == "45000.00"
    assert logs[0].new_value["approval_threshold"]["amount"] == "200000.00"
    assert logs[1].old_value["rule_name"] == f"PERM07 CPQ 规则-{suffix}"
    assert logs[1].new_value["rule_name"] == f"PERM07 CPQ 规则-调整-{suffix}"
    assert logs[1].old_value["base_price"] == "120000.00"
    assert logs[1].new_value["base_price"] == "135000.00"
    assert logs[1].old_value["approval_threshold"]["discount_pct"] == "8"
    assert logs[1].new_value["approval_threshold"]["discount_pct"] == "6"
    assert set(logs[1].changed_fields) >= {
        "rule_name",
        "description",
        "base_price",
        "pricing_matrix",
        "approval_threshold",
        "visibility_scope",
        "is_default",
        "owner_role",
    }


def test_sales_data_audit_submit_reject_cancel_writes_entity_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    reviewer = User(
        username=f"perm07_data_audit_reviewer_{suffix}",
        password_hash="not-used",
        email=f"perm07_data_audit_reviewer_{suffix}@example.com",
        real_name="PERM07 数据审核人",
        is_active=True,
    )
    customer = Customer(
        customer_code=f"CUST-PERM07-DATA-AUDIT-{suffix}",
        customer_name=f"PERM07 数据审核客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    opportunity = Opportunity(
        opp_code=f"OPP-PERM07-DATA-AUDIT-{suffix}",
        customer=customer,
        opp_name="PERM07 数据审核商机",
        stage="QUALIFICATION",
        est_amount=Decimal("100000.00"),
        owner_id=test_admin.id,
    )
    db_session.add_all([reviewer, customer, opportunity])
    db_session.commit()

    submit_response = submit_audit_request(
        db=db_session,
        request=SubmitAuditRequest(
            entity_type=SalesEntityType.OPPORTUNITY,
            entity_id=opportunity.id,
            entity_code=opportunity.opp_code,
            old_value={"est_amount": "100000.00"},
            new_value={"est_amount": "120000.00"},
            change_reason="客户追加测试工位",
            priority="HIGH",
        ),
        current_user=test_admin,
    )
    review_audit_request(
        request_id=submit_response.data["request_id"],
        db=db_session,
        request=ReviewActionRequest(
            action="reject",
            comment="预算依据不足",
            apply_immediately=False,
        ),
        current_user=reviewer,
    )
    cancel_response = submit_audit_request(
        db=db_session,
        request=SubmitAuditRequest(
            entity_type=SalesEntityType.OPPORTUNITY,
            entity_id=opportunity.id,
            entity_code=opportunity.opp_code,
            old_value={"expected_close_date": "2026-07-31"},
            new_value={"expected_close_date": "2026-08-15"},
            change_reason="客户验收窗口推迟",
        ),
        current_user=test_admin,
    )
    cancel_audit_request(
        request_id=cancel_response.data["request_id"],
        db=db_session,
        request=CancelAuditRequest(reason="改由销售例会确认"),
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id == opportunity.id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.SUBMIT,
        SalesOperationType.REJECT,
        SalesOperationType.SUBMIT,
        SalesOperationType.STATUS_CHANGE,
    ]
    assert logs[0].new_value["audit_status"] == "PENDING"
    assert logs[0].new_value["audit_request_id"] == submit_response.data["request_id"]
    assert logs[0].new_value["requested_change"]["est_amount"] == "120000.00"
    assert logs[0].changed_fields == ["est_amount"]
    assert logs[1].old_value["audit_status"] == "PENDING"
    assert logs[1].new_value["audit_status"] == "REJECTED"
    assert logs[1].new_value["review_comment"] == "预算依据不足"
    assert logs[1].operator_id == reviewer.id
    assert logs[2].new_value["requested_change"]["expected_close_date"] == "2026-08-15"
    assert logs[3].old_value["audit_status"] == "PENDING"
    assert logs[3].new_value["audit_status"] == "CANCELLED"
    assert logs[3].new_value["review_comment"] == "申请人撤销: 改由销售例会确认"
    assert logs[3].remark == "改由销售例会确认"


def test_customer_crud_writes_customer_operation_logs(
    db_session: Session, test_admin: User
):
    create_response = create_customer(
        db=db_session,
        customer_in=CustomerCreate(
            customer_name="PERM07 审计客户",
            short_name="审计客户",
            industry="自动化测试",
            status="potential",
            payment_terms="月结30天",
            annual_revenue=Decimal("100000.00"),
        ),
        current_user=test_admin,
    )
    customer_id = create_response.id

    update_customer(
        db=db_session,
        customer_id=customer_id,
        customer_in=CustomerUpdate(
            customer_name="PERM07 审计客户-更新",
            status="customer",
            payment_terms="月结45天",
            annual_revenue=Decimal("150000.00"),
        ),
        current_user=test_admin,
    )
    delete_customer(customer_id=customer_id, db=db_session, current_user=test_admin)

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.CUSTOMER,
            SalesOperationLog.entity_id == customer_id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.UPDATE,
        SalesOperationType.DELETE,
    ]
    assert logs[0].new_value["customer_name"] == "PERM07 审计客户"
    assert logs[0].new_value["annual_revenue"] == "100000.00"
    assert logs[1].old_value["customer_name"] == "PERM07 审计客户"
    assert logs[1].new_value["customer_name"] == "PERM07 审计客户-更新"
    assert logs[1].new_value["status"] == "customer"
    assert logs[1].new_value["payment_terms"] == "月结45天"
    assert set(logs[1].changed_fields) >= {
        "customer_name",
        "status",
        "payment_terms",
        "annual_revenue",
    }
    assert logs[2].old_value["status"] == "customer"


def test_customer_tag_create_writes_customer_update_operation_log(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-TAG-{suffix}",
        customer_name=f"PERM07 标签客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    db_session.add(customer)
    db_session.commit()

    create_customer_tag(
        db=db_session,
        customer_id=customer.id,
        tag_in=CustomerTagCreate(customer_id=customer.id, tag_name="重点客户"),
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.CUSTOMER,
            SalesOperationLog.entity_id == customer.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )

    assert log.old_value["tags"] == []
    assert log.new_value["tags"] == ["重点客户"]
    assert "tags" in log.changed_fields
    assert log.remark == "重点客户"


def test_customer_tag_batch_create_writes_customer_update_operation_log(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-TAG-BATCH-{suffix}",
        customer_name=f"PERM07 批量标签客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    existing_tag = CustomerTag(customer=customer, tag_name="既有标签")
    db_session.add_all([customer, existing_tag])
    db_session.commit()

    create_customer_tags_batch(
        db=db_session,
        customer_id=customer.id,
        tags_in=CustomerTagBatchCreate(
            customer_id=customer.id,
            tag_names=["高价值客户", "长期合作"],
        ),
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.CUSTOMER,
            SalesOperationLog.entity_id == customer.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )

    assert log.old_value["tags"] == ["既有标签"]
    assert set(log.new_value["tags"]) == {"既有标签", "高价值客户", "长期合作"}
    assert "tags" in log.changed_fields
    assert log.remark == "高价值客户,长期合作"


def test_customer_tag_delete_by_id_writes_customer_update_operation_log(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-TAG-DEL-ID-{suffix}",
        customer_name=f"PERM07 删除标签客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    tag = CustomerTag(customer=customer, tag_name="待删除标签")
    db_session.add_all([customer, tag])
    db_session.commit()

    delete_customer_tag(
        db=db_session,
        customer_id=customer.id,
        tag_id=tag.id,
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.CUSTOMER,
            SalesOperationLog.entity_id == customer.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )

    assert log.old_value["tags"] == ["待删除标签"]
    assert log.new_value["tags"] == []
    assert "tags" in log.changed_fields
    assert log.remark == "待删除标签"


def test_customer_tag_delete_by_name_writes_customer_update_operation_log(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-TAG-DEL-NAME-{suffix}",
        customer_name=f"PERM07 按名删标签客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    tag = CustomerTag(customer=customer, tag_name="按名称删除")
    db_session.add_all([customer, tag])
    db_session.commit()

    delete_customer_tags_by_name(
        db=db_session,
        customer_id=customer.id,
        tag_name="按名称删除",
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.CUSTOMER,
            SalesOperationLog.entity_id == customer.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )

    assert log.old_value["tags"] == ["按名称删除"]
    assert log.new_value["tags"] == []
    assert "tags" in log.changed_fields
    assert log.remark == "按名称删除"


def test_contact_crud_writes_contact_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-CONTACT-{suffix}",
        customer_name=f"PERM07 联系人客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    db_session.add(customer)
    db_session.commit()

    create_response = create_contact(
        db=db_session,
        customer_id=customer.id,
        contact_in=ContactCreate(
            name="张联系人",
            position="设备经理",
            mobile="13100000000",
            email="contact@example.com",
            is_primary=True,
        ),
        current_user=test_admin,
    )
    contact_id = create_response.id

    update_contact(
        db=db_session,
        contact_id=contact_id,
        contact_in=ContactUpdate(
            position="生产总监",
            mobile="13100000001",
            is_primary=False,
        ),
        current_user=test_admin,
    )
    delete_contact(contact_id=contact_id, db=db_session, current_user=test_admin)

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "CONTACT",
            SalesOperationLog.entity_id == contact_id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.UPDATE,
        SalesOperationType.DELETE,
    ]
    assert logs[0].new_value["customer_id"] == customer.id
    assert logs[0].new_value["name"] == "张联系人"
    assert logs[0].new_value["is_primary"] is True
    assert logs[1].old_value["position"] == "设备经理"
    assert logs[1].new_value["position"] == "生产总监"
    assert logs[1].new_value["mobile"] == "13100000001"
    assert set(logs[1].changed_fields) >= {"position", "mobile", "is_primary"}
    assert logs[2].old_value["name"] == "张联系人"
    assert logs[2].new_value == {}


def test_contact_set_primary_writes_status_change_operation_log(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-CONTACT-PRIMARY-{suffix}",
        customer_name=f"PERM07 主联系人客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    db_session.add(customer)
    db_session.flush()
    contact = create_contact(
        db=db_session,
        customer_id=customer.id,
        contact_in=ContactCreate(
            name="李联系人",
            position="项目经理",
            mobile="13000000000",
            is_primary=False,
        ),
        current_user=test_admin,
    )

    set_primary_contact(
        contact_id=contact.id,
        db=db_session,
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "CONTACT",
            SalesOperationLog.entity_id == contact.id,
            SalesOperationLog.operation_type == SalesOperationType.STATUS_CHANGE,
        )
        .one()
    )

    assert log.old_value["is_primary"] is False
    assert log.new_value["is_primary"] is True
    assert "is_primary" in log.changed_fields


def test_contact_set_primary_logs_previous_primary_demotion(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-CONTACT-PRIMARY-SWITCH-{suffix}",
        customer_name=f"PERM07 主联系人切换客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    db_session.add(customer)
    db_session.flush()
    old_primary = Contact(
        customer_id=customer.id,
        name="原主联系人",
        mobile="13000000001",
        is_primary=True,
    )
    new_primary = Contact(
        customer_id=customer.id,
        name="新主联系人",
        mobile="13000000002",
        is_primary=False,
    )
    db_session.add_all([old_primary, new_primary])
    db_session.commit()

    set_primary_contact(
        contact_id=new_primary.id,
        db=db_session,
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "CONTACT",
            SalesOperationLog.entity_id.in_([old_primary.id, new_primary.id]),
            SalesOperationLog.operation_type == SalesOperationType.STATUS_CHANGE,
        )
        .order_by(SalesOperationLog.entity_id)
        .all()
    )

    assert len(logs) == 2
    assert [log.entity_id for log in logs] == [old_primary.id, new_primary.id]
    assert [log.old_value["is_primary"] for log in logs] == [True, False]
    assert [log.new_value["is_primary"] for log in logs] == [False, True]
    assert all("is_primary" in log.changed_fields for log in logs)


def test_contact_create_primary_logs_previous_primary_demotion(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-CONTACT-CREATE-PRIMARY-{suffix}",
        customer_name=f"PERM07 新建主联系人客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    db_session.add(customer)
    db_session.flush()
    old_primary = Contact(
        customer_id=customer.id,
        name="原创建主联系人",
        mobile="13000000003",
        is_primary=True,
    )
    db_session.add(old_primary)
    db_session.commit()

    created = create_contact(
        db=db_session,
        customer_id=customer.id,
        contact_in=ContactCreate(
            name="新创建主联系人",
            mobile="13000000004",
            is_primary=True,
        ),
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "CONTACT",
            SalesOperationLog.entity_id.in_([old_primary.id, created.id]),
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert len(logs) == 2
    demotion_log = next(log for log in logs if log.entity_id == old_primary.id)
    creation_log = next(log for log in logs if log.entity_id == created.id)
    assert demotion_log.operation_type == SalesOperationType.STATUS_CHANGE
    assert demotion_log.old_value["is_primary"] is True
    assert demotion_log.new_value["is_primary"] is False
    assert "is_primary" in demotion_log.changed_fields
    assert creation_log.operation_type == SalesOperationType.CREATE
    assert creation_log.new_value["is_primary"] is True


def test_contact_update_primary_logs_previous_primary_demotion(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-CONTACT-UPDATE-PRIMARY-{suffix}",
        customer_name=f"PERM07 更新主联系人客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    db_session.add(customer)
    db_session.flush()
    old_primary = Contact(
        customer_id=customer.id,
        name="原更新主联系人",
        mobile="13000000005",
        is_primary=True,
    )
    new_primary = Contact(
        customer_id=customer.id,
        name="更新后主联系人",
        mobile="13000000006",
        is_primary=False,
    )
    db_session.add_all([old_primary, new_primary])
    db_session.commit()

    update_contact(
        db=db_session,
        contact_id=new_primary.id,
        contact_in=ContactUpdate(is_primary=True),
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == "CONTACT",
            SalesOperationLog.entity_id.in_([old_primary.id, new_primary.id]),
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert len(logs) == 2
    demotion_log = next(log for log in logs if log.entity_id == old_primary.id)
    promotion_log = next(log for log in logs if log.entity_id == new_primary.id)
    assert demotion_log.operation_type == SalesOperationType.STATUS_CHANGE
    assert demotion_log.old_value["is_primary"] is True
    assert demotion_log.new_value["is_primary"] is False
    assert "is_primary" in demotion_log.changed_fields
    assert promotion_log.operation_type == SalesOperationType.UPDATE
    assert promotion_log.old_value["is_primary"] is False
    assert promotion_log.new_value["is_primary"] is True


def test_quick_activity_writes_customer_and_opportunity_comment_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-ACT-{suffix}",
        customer_name=f"PERM07 活动客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    db_session.add(customer)
    db_session.flush()
    opportunity = Opportunity(
        opp_code=f"OPP-PERM07-ACT-{suffix}",
        opp_name=f"PERM07 活动商机-{suffix}",
        customer_id=customer.id,
        owner_id=test_admin.id,
        stage="DISCOVERY",
    )
    db_session.add(opportunity)
    db_session.commit()

    response = quick_activity(
        db=db_session,
        request=QuickActivityRequest(
            activity_type="VISIT",
            content="拜访客户，确认 FCT 测试节拍和夹具接口。",
            topic="客户拜访",
            customer_id=customer.id,
            opportunity_id=opportunity.id,
            follow_up_task="整理节拍参数并给售前",
        ),
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.operation_type == SalesOperationType.COMMENT,
            SalesOperationLog.entity_type.in_(
                [SalesEntityType.CUSTOMER, SalesEntityType.OPPORTUNITY]
            ),
            SalesOperationLog.entity_id.in_([customer.id, opportunity.id]),
        )
        .order_by(SalesOperationLog.entity_type)
        .all()
    )

    assert len(logs) == 2
    logs_by_type = {log.entity_type: log for log in logs}
    assert logs_by_type[SalesEntityType.CUSTOMER].entity_id == customer.id
    assert logs_by_type[SalesEntityType.OPPORTUNITY].entity_id == opportunity.id
    assert logs_by_type[SalesEntityType.OPPORTUNITY].new_value["activity_id"] == response["id"]
    assert logs_by_type[SalesEntityType.OPPORTUNITY].new_value["activity_no"] == response["activity_no"]
    assert logs_by_type[SalesEntityType.OPPORTUNITY].new_value["activity_type"] == "VISIT"
    assert logs_by_type[SalesEntityType.OPPORTUNITY].new_value["topic"] == "客户拜访"
    assert logs_by_type[SalesEntityType.OPPORTUNITY].new_value["follow_up_task"] == "整理节拍参数并给售前"
    assert logs_by_type[SalesEntityType.OPPORTUNITY].remark == "客户拜访"


def test_quick_activity_writes_lead_comment_log(db_session: Session, test_admin: User):
    lead = Lead(
        lead_code=f"LD-PERM07-ACT-{uuid.uuid4().hex[:8]}",
        source="展会",
        customer_name="PERM07 活动线索客户",
        contact_name="线索联系人",
        status="NEW",
        owner_id=test_admin.id,
    )
    db_session.add(lead)
    db_session.commit()

    response = quick_activity(
        db=db_session,
        request=QuickActivityRequest(
            activity_type="CALL",
            content="电话确认客户初步需求和预算。",
            topic="电话沟通",
            lead_id=lead.id,
            follow_up_task="补充客户产线信息",
        ),
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.LEAD,
            SalesOperationLog.entity_id == lead.id,
            SalesOperationLog.operation_type == SalesOperationType.COMMENT,
        )
        .one()
    )

    assert log.entity_code == lead.lead_code
    assert log.new_value["activity_id"] == response["id"]
    assert log.new_value["activity_type"] == "CALL"
    assert log.new_value["lead_id"] == lead.id
    assert log.new_value["follow_up_task"] == "补充客户产线信息"
    assert log.remark == "电话沟通"


def test_confirm_minutes_writes_customer_and_opportunity_comment_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-MIN-{suffix}",
        customer_name=f"PERM07 纪要客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    db_session.add(customer)
    db_session.flush()
    opportunity = Opportunity(
        opp_code=f"OPP-PERM07-MIN-{suffix}",
        opp_name=f"PERM07 纪要商机-{suffix}",
        customer_id=customer.id,
        owner_id=test_admin.id,
        stage="DISCOVERY",
    )
    db_session.add(opportunity)
    db_session.flush()
    job = AIGenerationJob(
        job_type="parse_meeting_minutes",
        status="SUCCESS",
        params={"minutes_text": "客户确认 FCT 节拍、夹具接口和交付排期。"},
        result={
            "structured": {
                "customer_name": customer.customer_name,
                "topic": "方案评审会",
                "summary": "客户确认 FCT 节拍、夹具接口和交付排期。",
                "key_demands": ["FCT 节拍 30 秒内", "夹具接口复核"],
                "competitors": ["竞品A"],
                "budget": "30万",
                "commitments": ["三天内提交方案"],
                "next_actions": ["整理节拍参数"],
                "next_meeting_checklist": {
                    "to_obtain": ["产线布局图"],
                    "to_confirm": ["验收口径"],
                    "technical_gaps": ["MES 接口协议"],
                },
                "importance": "high",
            },
            "candidates": {"customer": {"id": customer.id}},
        },
        progress=100,
        created_by=test_admin.id,
    )
    db_session.add(job)
    db_session.commit()

    response = confirm_minutes(
        db=db_session,
        request=ConfirmMinutesRequest(
            job_id=job.id,
            customer_id=customer.id,
            opportunity_id=opportunity.id,
        ),
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.operation_type == SalesOperationType.COMMENT,
            SalesOperationLog.entity_type.in_(
                [SalesEntityType.CUSTOMER, SalesEntityType.OPPORTUNITY]
            ),
            SalesOperationLog.entity_id.in_([customer.id, opportunity.id]),
        )
        .order_by(SalesOperationLog.entity_type)
        .all()
    )

    assert len(logs) == 2
    logs_by_type = {log.entity_type: log for log in logs}
    assert logs_by_type[SalesEntityType.CUSTOMER].entity_code == customer.customer_code
    assert logs_by_type[SalesEntityType.OPPORTUNITY].entity_code == opportunity.opp_code
    assert (
        logs_by_type[SalesEntityType.OPPORTUNITY].new_value["activity_id"]
        == response["communication_id"]
    )
    assert (
        logs_by_type[SalesEntityType.OPPORTUNITY].new_value["activity_no"]
        == response["communication_no"]
    )
    assert logs_by_type[SalesEntityType.OPPORTUNITY].new_value["activity_type"] == "MEETING"
    assert logs_by_type[SalesEntityType.OPPORTUNITY].new_value["topic"] == "方案评审会"
    assert "整理节拍参数" in logs_by_type[SalesEntityType.OPPORTUNITY].new_value[
        "follow_up_task"
    ]
    assert logs_by_type[SalesEntityType.OPPORTUNITY].remark == "方案评审会"


def test_confirm_minutes_backfill_writes_opportunity_update_log(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-MIN-UPD-{suffix}",
        customer_name=f"PERM07 纪要回填客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    db_session.add(customer)
    db_session.flush()
    opportunity = Opportunity(
        opp_code=f"OPP-PERM07-MIN-UPD-{suffix}",
        opp_name=f"PERM07 纪要回填商机-{suffix}",
        customer_id=customer.id,
        owner_id=test_admin.id,
        stage="DISCOVERY",
        requirement_maturity="HIGH",
        acceptance_basis="旧验收依据",
        budget_range="10万以内",
    )
    db_session.add(opportunity)
    db_session.flush()
    job = AIGenerationJob(
        job_type="parse_meeting_minutes",
        status="SUCCESS",
        params={"minutes_text": "客户补充 MES 接口和节拍要求。"},
        result={
            "structured": {
                "customer_name": customer.customer_name,
                "topic": "需求澄清会",
                "summary": "客户补充 MES 接口和节拍要求。",
                "key_demands": ["FCT 节拍 30 秒内", "MES 接口打通"],
                "competitors": [],
                "budget": "30万",
                "commitments": [],
                "next_actions": [],
                "next_meeting_checklist": {
                    "to_obtain": [],
                    "to_confirm": [],
                    "technical_gaps": ["MES 接口协议"],
                },
            },
            "candidates": {"customer": {"id": customer.id}},
        },
        progress=100,
        created_by=test_admin.id,
    )
    db_session.add(job)
    db_session.commit()

    confirm_minutes(
        db=db_session,
        request=ConfirmMinutesRequest(
            job_id=job.id,
            customer_id=customer.id,
            opportunity_id=opportunity.id,
        ),
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id == opportunity.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )

    assert log.old_value["requirement_maturity"] == "HIGH"
    assert log.new_value["requirement_maturity"] == "LOW"
    assert log.old_value["acceptance_basis"] == "旧验收依据"
    assert log.new_value["acceptance_basis"] == "FCT 节拍 30 秒内、MES 接口打通"
    assert log.old_value["budget_range"] == "10万以内"
    assert log.new_value["budget_range"] == "30万"
    assert set(log.changed_fields) >= {
        "requirement_maturity",
        "acceptance_basis",
        "budget_range",
    }
    assert log.remark == "需求澄清会"


def test_lead_crud_writes_lead_operation_logs(
    db_session: Session, test_admin: User
):
    create_response = create_lead(
        db=db_session,
        lead_in=LeadCreate(
            source="展会",
            customer_name="PERM07 审计线索客户",
            industry="自动化测试",
            contact_name="张三",
            contact_phone="13800000000",
            demand_summary="需要非标自动化产线",
            status="NEW",
        ),
        current_user=test_admin,
    )
    lead_id = create_response.id

    update_lead(
        db=db_session,
        lead_id=lead_id,
        lead_in=LeadUpdate(
            status="CONTACTED",
            contact_phone="13900000000",
            demand_summary="需要非标自动化产线，已电话沟通",
        ),
        current_user=test_admin,
    )
    delete_lead(db=db_session, lead_id=lead_id, current_user=test_admin)

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.LEAD,
            SalesOperationLog.entity_id == lead_id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.UPDATE,
        SalesOperationType.DELETE,
    ]
    assert logs[0].new_value["customer_name"] == "PERM07 审计线索客户"
    assert logs[0].new_value["status"] == "NEW"
    assert logs[1].old_value["status"] == "NEW"
    assert logs[1].old_value["contact_phone"] == "13800000000"
    assert logs[1].new_value["status"] == "CONTACTED"
    assert logs[1].new_value["contact_phone"] == "13900000000"
    assert logs[1].new_value["demand_summary"] == "需要非标自动化产线，已电话沟通"
    assert set(logs[1].changed_fields) >= {
        "status",
        "contact_phone",
        "demand_summary",
    }
    assert logs[2].old_value["status"] == "CONTACTED"


def test_lead_requirement_detail_create_and_update_write_lead_update_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    lead = Lead(
        lead_code=f"LEAD-PERM07-REQ-{suffix}",
        source="展会",
        customer_name="PERM07 需求详情线索",
        industry="自动化测试",
        contact_name="需求联系人",
        contact_phone="13600000001",
        demand_summary="需要 FCT 自动化测试方案",
        owner_id=test_admin.id,
        status="NEW",
    )
    db_session.add(lead)
    db_session.commit()

    create_lead_requirement_detail(
        db=db_session,
        lead_id=lead.id,
        detail_in=LeadRequirementDetailCreate(
            target_object_type="FCT",
            application_scenario="产线终测",
            requirement_maturity=2,
            has_sow=False,
            acceptance_basis="客户口头说明",
            cycle_time_seconds=45,
        ),
        current_user=test_admin,
    )
    update_lead_requirement_detail(
        db=db_session,
        lead_id=lead.id,
        detail_in=LeadRequirementDetailUpdate(
            requirement_maturity=4,
            has_sow=True,
            acceptance_basis="客户 SOW 与节拍表",
            cycle_time_seconds=30,
        ),
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.LEAD,
            SalesOperationLog.entity_id == lead.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert len(logs) == 2
    assert logs[0].old_value["requirement_detail"] is None
    assert logs[0].new_value["requirement_detail"]["requirement_maturity"] == 2
    assert logs[0].new_value["requirement_detail"]["acceptance_basis"] == "客户口头说明"
    assert logs[0].new_value["requirement_detail"]["cycle_time_seconds"] == "45.00"
    assert logs[1].old_value["requirement_detail"]["requirement_maturity"] == 2
    assert logs[1].new_value["requirement_detail"]["requirement_maturity"] == 4
    assert logs[1].old_value["requirement_detail"]["has_sow"] is False
    assert logs[1].new_value["requirement_detail"]["has_sow"] is True
    assert logs[1].new_value["requirement_detail"]["acceptance_basis"] == "客户 SOW 与节拍表"
    assert "requirement_detail" in logs[1].changed_fields


def test_requirement_freezes_write_lead_and_opportunity_status_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-FREEZE-{suffix}",
        customer_name=f"PERM07 需求冻结客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    lead = Lead(
        lead_code=f"LEAD-PERM07-FREEZE-{suffix}",
        source="展会",
        customer_name="PERM07 需求冻结线索",
        contact_name="冻结联系人",
        contact_phone="13600000002",
        demand_summary="冻结 FCT 需求包",
        owner_id=test_admin.id,
        status="NEW",
    )
    db_session.add_all([customer, lead])
    db_session.flush()
    detail = LeadRequirementDetail(
        lead_id=lead.id,
        target_object_type="FCT",
        requirement_maturity=3,
        has_sow=True,
        acceptance_basis="冻结前验收依据",
        requirement_version="DRAFT",
        is_frozen=False,
    )
    opportunity = Opportunity(
        opp_code=f"OPP-PERM07-FREEZE-{suffix}",
        opp_name=f"PERM07 需求冻结商机-{suffix}",
        customer_id=customer.id,
        owner_id=test_admin.id,
        stage="DISCOVERY",
    )
    db_session.add_all([detail, opportunity])
    db_session.commit()

    create_lead_requirement_freeze(
        db=db_session,
        lead_id=lead.id,
        freeze_in=RequirementFreezeCreate(
            source_type="LEAD",
            source_id=lead.id,
            freeze_type="SOLUTION",
            version_number="REQ-FREEZE-L-1",
            requires_ecr=True,
            description="方案范围冻结，后续变更走 ECR",
        ),
        current_user=test_admin,
    )
    create_opportunity_requirement_freeze(
        db=db_session,
        opp_id=opportunity.id,
        freeze_in=RequirementFreezeCreate(
            source_type="OPPORTUNITY",
            source_id=opportunity.id,
            freeze_type="QUOTE_BASELINE",
            version_number="REQ-FREEZE-O-1",
            requires_ecr=False,
            description="报价基线冻结",
        ),
        current_user=test_admin,
    )

    lead_log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.LEAD,
            SalesOperationLog.entity_id == lead.id,
            SalesOperationLog.operation_type == SalesOperationType.STATUS_CHANGE,
        )
        .one()
    )
    opp_log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id == opportunity.id,
            SalesOperationLog.operation_type == SalesOperationType.STATUS_CHANGE,
        )
        .one()
    )

    assert lead_log.old_value["requirement_detail"]["is_frozen"] is False
    assert lead_log.new_value["requirement_detail"]["is_frozen"] is True
    assert lead_log.new_value["requirement_detail"]["requirement_version"] == "REQ-FREEZE-L-1"
    assert lead_log.new_value["requirement_freeze"]["freeze_type"] == "SOLUTION"
    assert lead_log.new_value["requirement_freeze"]["version_number"] == "REQ-FREEZE-L-1"
    assert lead_log.new_value["requirement_freeze"]["requires_ecr"] is True
    assert "requirement_detail" in lead_log.changed_fields
    assert "requirement_freeze" in lead_log.changed_fields
    assert lead_log.remark == "方案范围冻结，后续变更走 ECR"

    assert opp_log.old_value["requirement_freeze"] is None
    assert opp_log.new_value["requirement_freeze"]["freeze_type"] == "QUOTE_BASELINE"
    assert opp_log.new_value["requirement_freeze"]["version_number"] == "REQ-FREEZE-O-1"
    assert opp_log.new_value["requirement_freeze"]["requires_ecr"] is False
    assert opp_log.remark == "报价基线冻结"


def test_open_items_write_lead_and_opportunity_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-OI-{suffix}",
        customer_name=f"PERM07 未决事项客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    lead = Lead(
        lead_code=f"LEAD-PERM07-OI-{suffix}",
        source="客户转介绍",
        customer_name="PERM07 未决事项线索",
        contact_name="未决事项联系人",
        contact_phone="13600000003",
        demand_summary="夹具验收标准待确认",
        owner_id=test_admin.id,
        status="NEW",
    )
    db_session.add_all([customer, lead])
    db_session.flush()
    opportunity = Opportunity(
        opp_code=f"OPP-PERM07-OI-{suffix}",
        opp_name=f"PERM07 未决事项商机-{suffix}",
        customer_id=customer.id,
        owner_id=test_admin.id,
        stage="DISCOVERY",
    )
    db_session.add(opportunity)
    db_session.commit()

    create_open_item(
        db=db_session,
        lead_id=lead.id,
        request=OpenItemCreate(
            item_type="TECHNICAL",
            description="客户需补充节拍验收标准",
            responsible_party="CUSTOMER",
            responsible_person_id=test_admin.id,
            blocks_quotation=True,
        ),
        current_user=test_admin,
    )
    opp_open_item = create_open_item_for_opportunity(
        db=db_session,
        opp_id=opportunity.id,
        request=OpenItemCreate(
            item_type="COMMERCIAL",
            description="价格有效期需确认",
            responsible_party="INTERNAL",
            responsible_person_id=test_admin.id,
            blocks_quotation=True,
        ),
        current_user=test_admin,
    )
    update_open_item(
        db=db_session,
        item_id=opp_open_item.id,
        request=OpenItemCreate(
            item_type="COMMERCIAL",
            description="价格有效期和付款条件需确认",
            responsible_party="INTERNAL",
            responsible_person_id=test_admin.id,
            blocks_quotation=False,
        ),
        current_user=test_admin,
    )
    close_open_item(
        db=db_session,
        item_id=opp_open_item.id,
        close_evidence="客户邮件已确认付款条件",
        current_user=test_admin,
    )

    lead_log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.LEAD,
            SalesOperationLog.entity_id == lead.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )
    opp_logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id == opportunity.id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert lead_log.old_value["open_item"] is None
    assert lead_log.new_value["open_item"]["item_type"] == "TECHNICAL"
    assert lead_log.new_value["open_item"]["description"] == "客户需补充节拍验收标准"
    assert lead_log.new_value["open_item"]["blocks_quotation"] is True
    assert "open_item" in lead_log.changed_fields

    assert [log.operation_type for log in opp_logs] == [
        SalesOperationType.UPDATE,
        SalesOperationType.UPDATE,
        SalesOperationType.STATUS_CHANGE,
    ]
    assert opp_logs[0].old_value["open_item"] is None
    assert opp_logs[0].new_value["open_item"]["item_type"] == "COMMERCIAL"
    assert opp_logs[0].new_value["open_item"]["blocks_quotation"] is True
    assert opp_logs[1].old_value["open_item"]["description"] == "价格有效期需确认"
    assert opp_logs[1].new_value["open_item"]["description"] == "价格有效期和付款条件需确认"
    assert opp_logs[1].old_value["open_item"]["blocks_quotation"] is True
    assert opp_logs[1].new_value["open_item"]["blocks_quotation"] is False
    assert opp_logs[2].old_value["open_item"]["status"] == "PENDING"
    assert opp_logs[2].new_value["open_item"]["status"] == "CLOSED"
    assert opp_logs[2].new_value["open_item"]["close_evidence"] == "客户邮件已确认付款条件"
    assert opp_logs[2].remark == "客户邮件已确认付款条件"


def test_ai_clarifications_write_lead_and_opportunity_update_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-AIC-{suffix}",
        customer_name=f"PERM07 AI澄清客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    lead = Lead(
        lead_code=f"LEAD-PERM07-AIC-{suffix}",
        source="官网",
        customer_name="PERM07 AI澄清线索",
        contact_name="澄清联系人",
        contact_phone="13600000004",
        demand_summary="缺少验收标准",
        owner_id=test_admin.id,
        status="NEW",
    )
    db_session.add_all([customer, lead])
    db_session.flush()
    opportunity = Opportunity(
        opp_code=f"OPP-PERM07-AIC-{suffix}",
        opp_name=f"PERM07 AI澄清商机-{suffix}",
        customer_id=customer.id,
        owner_id=test_admin.id,
        stage="DISCOVERY",
    )
    db_session.add(opportunity)
    db_session.commit()

    create_ai_clarification_for_lead(
        db=db_session,
        lead_id=lead.id,
        clarification_in=AIClarificationCreate(
            source_type="LEAD",
            source_id=lead.id,
            round=1,
            questions='["目标节拍是多少？"]',
        ),
        current_user=test_admin,
    )
    opp_clarification = create_ai_clarification_for_opportunity(
        db=db_session,
        opp_id=opportunity.id,
        clarification_in=AIClarificationCreate(
            source_type="OPPORTUNITY",
            source_id=opportunity.id,
            round=1,
            questions='["预算区间是否已确认？"]',
        ),
        current_user=test_admin,
    )
    update_ai_clarification(
        db=db_session,
        clarification_id=opp_clarification.id,
        clarification_in=AIClarificationUpdate(answers='["预算 80-120 万"]'),
        current_user=test_admin,
    )

    lead_log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.LEAD,
            SalesOperationLog.entity_id == lead.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )
    opp_logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id == opportunity.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert lead_log.old_value["ai_clarification"] is None
    assert lead_log.new_value["ai_clarification"]["source_type"] == "LEAD"
    assert lead_log.new_value["ai_clarification"]["round"] == 1
    assert lead_log.new_value["ai_clarification"]["questions"] == '["目标节拍是多少？"]'
    assert "ai_clarification" in lead_log.changed_fields

    assert len(opp_logs) == 2
    assert opp_logs[0].old_value["ai_clarification"] is None
    assert opp_logs[0].new_value["ai_clarification"]["questions"] == '["预算区间是否已确认？"]'
    assert opp_logs[0].new_value["ai_clarification"]["answers"] is None
    assert opp_logs[1].old_value["ai_clarification"]["answers"] is None
    assert opp_logs[1].new_value["ai_clarification"]["answers"] == '["预算 80-120 万"]'
    assert opp_logs[1].remark == '["预算 80-120 万"]'


def test_lead_convert_writes_lead_and_opportunity_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-LEAD-CONV-{suffix}",
        customer_name=f"PERM07 线索转商机客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    lead = Lead(
        lead_code=f"LEAD-PERM07-CONV-{suffix}",
        source="展会",
        customer_name="PERM07 待转商机线索",
        industry="自动化测试",
        contact_name="李四",
        contact_phone="13700000000",
        demand_summary="需要视觉检测工作站",
        owner_id=test_admin.id,
        status="NEW",
    )
    db_session.add_all([customer, lead])
    db_session.commit()

    response = convert_lead_to_opportunity(
        db=db_session,
        lead_id=lead.id,
        customer_id=customer.id,
        skip_validation=True,
        current_user=test_admin,
    )

    lead_log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.LEAD,
            SalesOperationLog.entity_id == lead.id,
            SalesOperationLog.operation_type == SalesOperationType.CONVERT,
        )
        .one()
    )
    opportunity_log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id == response.id,
            SalesOperationLog.operation_type == SalesOperationType.CREATE,
        )
        .one()
    )

    assert lead_log.old_value["status"] == "NEW"
    assert lead_log.new_value["status"] == "CONVERTED"
    assert "status" in lead_log.changed_fields
    assert opportunity_log.new_value["lead_id"] == lead.id
    assert opportunity_log.new_value["customer_id"] == customer.id
    assert opportunity_log.new_value["stage"] == "DISCOVERY"


def test_lead_follow_up_writes_comment_operation_log(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    lead = Lead(
        lead_code=f"LEAD-PERM07-FU-{suffix}",
        source="电话",
        customer_name="PERM07 跟进审计线索",
        industry="自动化测试",
        contact_name="王五",
        contact_phone="13600000000",
        demand_summary="需要自动上下料方案",
        owner_id=test_admin.id,
        status="CONTACTED",
    )
    db_session.add(lead)
    db_session.commit()

    next_action_at = datetime(2026, 8, 1, 9, 30)
    create_lead_follow_up(
        db=db_session,
        lead_id=lead.id,
        follow_up_in=LeadFollowUpCreate(
            follow_up_type="CALL",
            content="客户确认需要安排方案评审",
            next_action="安排方案评审会",
            next_action_at=next_action_at,
        ),
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.LEAD,
            SalesOperationLog.entity_id == lead.id,
            SalesOperationLog.operation_type == SalesOperationType.COMMENT,
        )
        .one()
    )

    assert log.old_value["next_action_at"] is None
    assert log.new_value["next_action_at"] == "2026-08-01T09:30:00"
    assert "next_action_at" in log.changed_fields
    assert log.remark == "客户确认需要安排方案评审"


def test_lead_mark_invalid_writes_status_change_operation_log(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    lead = Lead(
        lead_code=f"LEAD-PERM07-INVALID-{suffix}",
        source="网站",
        customer_name="PERM07 无效审计线索",
        industry="自动化测试",
        contact_name="赵六",
        contact_phone="13500000000",
        demand_summary="重复提交的线索",
        owner_id=test_admin.id,
        status="NEW",
    )
    db_session.add(lead)
    db_session.commit()

    mark_lead_invalid(
        db=db_session,
        lead_id=lead.id,
        reason="重复线索",
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.LEAD,
            SalesOperationLog.entity_id == lead.id,
            SalesOperationLog.operation_type == SalesOperationType.STATUS_CHANGE,
        )
        .one()
    )

    assert log.old_value["status"] == "NEW"
    assert log.new_value["status"] == "INVALID"
    assert "status" in log.changed_fields
    assert log.remark == "重复线索"


def test_lead_batch_update_status_writes_status_change_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    leads = [
        Lead(
            lead_code=f"LEAD-PERM07-BATCH-{suffix}-{index}",
            source="展会",
            customer_name=f"PERM07 批量状态线索-{index}",
            industry="自动化测试",
            contact_name=f"批量联系人{index}",
            contact_phone=f"1340000000{index}",
            demand_summary="批量清理测试线索",
            owner_id=test_admin.id,
            status="NEW",
        )
        for index in range(2)
    ]
    db_session.add_all(leads)
    db_session.commit()

    response = batch_update_status(
        db=db_session,
        request=BatchUpdateStatusRequest(
            lead_ids=[lead.id for lead in leads],
            status="INVALID",
            reason="批量清理",
        ),
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.LEAD,
            SalesOperationLog.entity_id.in_([lead.id for lead in leads]),
            SalesOperationLog.operation_type == SalesOperationType.STATUS_CHANGE,
        )
        .order_by(SalesOperationLog.entity_id)
        .all()
    )

    assert response.success_count == 2
    assert len(logs) == 2
    assert [log.old_value["status"] for log in logs] == ["NEW", "NEW"]
    assert [log.new_value["status"] for log in logs] == ["INVALID", "INVALID"]
    assert all("status" in log.changed_fields for log in logs)
    assert [log.remark for log in logs] == ["批量清理", "批量清理"]


def test_lead_batch_convert_writes_lead_and_opportunity_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-BATCH-CONV-{suffix}",
        customer_name=f"PERM07 批量转商机客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    leads = [
        Lead(
            lead_code=f"LEAD-PERM07-BATCH-CONV-{suffix}-{index}",
            source="展会",
            customer_name=f"PERM07 批量转商机线索-{index}",
            industry="自动化测试",
            contact_name=f"批量转化联系人{index}",
            contact_phone=f"1330000000{index}",
            demand_summary="批量转化测试线索",
            owner_id=test_admin.id,
            status="NEW",
        )
        for index in range(2)
    ]
    db_session.add(customer)
    db_session.add_all(leads)
    db_session.commit()

    response = batch_convert_leads(
        db=db_session,
        request=BatchConvertRequest(
            lead_ids=[lead.id for lead in leads],
            customer_id=customer.id,
            skip_validation=True,
        ),
        current_user=test_admin,
    )

    converted_opportunity_ids = [item.result_id for item in response.results if item.success]
    lead_logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.LEAD,
            SalesOperationLog.entity_id.in_([lead.id for lead in leads]),
            SalesOperationLog.operation_type == SalesOperationType.CONVERT,
        )
        .order_by(SalesOperationLog.entity_id)
        .all()
    )
    opportunity_logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id.in_(converted_opportunity_ids),
            SalesOperationLog.operation_type == SalesOperationType.CREATE,
        )
        .order_by(SalesOperationLog.entity_id)
        .all()
    )

    assert response.success_count == 2
    assert len(lead_logs) == 2
    assert len(opportunity_logs) == 2
    assert [log.old_value["status"] for log in lead_logs] == ["NEW", "NEW"]
    assert [log.new_value["status"] for log in lead_logs] == [
        "CONVERTED",
        "CONVERTED",
    ]
    assert all("status" in log.changed_fields for log in lead_logs)
    assert {log.new_value["lead_id"] for log in opportunity_logs} == {
        lead.id for lead in leads
    }
    assert {log.new_value["customer_id"] for log in opportunity_logs} == {customer.id}
    assert {log.new_value["stage"] for log in opportunity_logs} == {"DISCOVERY"}


def test_lead_batch_assign_owner_writes_assign_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    new_owner = User(
        username=f"perm07_owner_{suffix}",
        password_hash="not-used",
        email=f"perm07_owner_{suffix}@example.com",
        real_name="PERM07 新负责人",
        is_active=True,
    )
    leads = [
        Lead(
            lead_code=f"LEAD-PERM07-BATCH-ASSIGN-{suffix}-{index}",
            source="展会",
            customer_name=f"PERM07 批量分配线索-{index}",
            industry="自动化测试",
            contact_name=f"批量分配联系人{index}",
            contact_phone=f"1320000000{index}",
            demand_summary="批量分配测试线索",
            owner_id=test_admin.id,
            status="NEW",
        )
        for index in range(2)
    ]
    db_session.add(new_owner)
    db_session.add_all(leads)
    db_session.commit()

    response = batch_assign_owner(
        db=db_session,
        request=BatchAssignRequest(
            lead_ids=[lead.id for lead in leads],
            owner_id=new_owner.id,
        ),
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.LEAD,
            SalesOperationLog.entity_id.in_([lead.id for lead in leads]),
            SalesOperationLog.operation_type == SalesOperationType.ASSIGN,
        )
        .order_by(SalesOperationLog.entity_id)
        .all()
    )

    assert response.success_count == 2
    assert len(logs) == 2
    assert [log.old_value["owner_id"] for log in logs] == [test_admin.id, test_admin.id]
    assert [log.new_value["owner_id"] for log in logs] == [new_owner.id, new_owner.id]
    assert all("owner_id" in log.changed_fields for log in logs)
    assert [log.remark for log in logs] == ["PERM07 新负责人", "PERM07 新负责人"]


def test_priority_calculation_writes_lead_and_opportunity_update_logs(
    db_session: Session, test_admin: User, monkeypatch
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-PRIORITY-{suffix}",
        customer_name=f"PERM07 优先级客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    lead = Lead(
        lead_code=f"LEAD-PERM07-PRIORITY-{suffix}",
        source="展会",
        customer_name=customer.customer_name,
        contact_name="优先级联系人",
        owner_id=test_admin.id,
        status="NEW",
        priority_score=10,
    )
    db_session.add_all([customer, lead])
    db_session.flush()
    opportunity = Opportunity(
        opp_code=f"OPP-PERM07-PRIORITY-{suffix}",
        lead_id=lead.id,
        customer_id=customer.id,
        opp_name="PERM07 优先级商机",
        stage="DISCOVERY",
        owner_id=test_admin.id,
        priority_score=20,
    )
    db_session.add(opportunity)
    db_session.commit()

    def fake_lead_priority(self, lead_id: int):
        return {
            "lead_id": lead_id,
            "lead_code": lead.lead_code,
            "total_score": 86,
            "is_key_lead": True,
            "priority_level": "P1",
            "importance_level": "HIGH",
            "urgency_level": "HIGH",
        }

    def fake_opportunity_priority(self, opp_id: int):
        return {
            "opportunity_id": opp_id,
            "opp_code": opportunity.opp_code,
            "total_score": 76,
            "is_key_opportunity": True,
            "priority_level": "P2",
            "importance_level": "MEDIUM",
            "urgency_level": "MEDIUM",
        }

    monkeypatch.setattr(
        "app.services.lead_priority_scoring.LeadPriorityScoringService.calculate_lead_priority",
        fake_lead_priority,
    )
    monkeypatch.setattr(
        "app.services.lead_priority_scoring.LeadPriorityScoringService.calculate_opportunity_priority",
        fake_opportunity_priority,
    )

    calculate_lead_priority(
        lead_id=lead.id,
        db=db_session,
        current_user=test_admin,
    )
    calculate_opportunity_priority(
        opp_id=opportunity.id,
        db=db_session,
        current_user=test_admin,
    )

    lead_log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.LEAD,
            SalesOperationLog.entity_id == lead.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )
    opportunity_log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id == opportunity.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )

    assert lead_log.old_value["priority_score"] == 10
    assert lead_log.new_value["priority_score"] == 86
    assert lead_log.new_value["priority_level"] == "P1"
    assert lead_log.new_value["is_key_lead"] is True
    assert set(lead_log.changed_fields) >= {
        "priority_score",
        "priority_level",
        "is_key_lead",
    }
    assert opportunity_log.old_value["priority_score"] == 20
    assert opportunity_log.new_value["priority_score"] == 76
    assert opportunity_log.new_value["priority_level"] == "P2"
    assert opportunity_log.new_value["is_key_opportunity"] is True
    assert set(opportunity_log.changed_fields) >= {
        "priority_score",
        "priority_level",
        "is_key_opportunity",
    }


def test_technical_assessment_apply_writes_source_update_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-ASSESS-{suffix}",
        customer_name=f"PERM07 技术评估客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    lead = Lead(
        lead_code=f"LEAD-PERM07-ASSESS-{suffix}",
        source="官网",
        customer_name="PERM07 技术评估线索",
        industry="自动化测试",
        contact_name="评估联系人",
        contact_phone="13600000003",
        demand_summary="需要售前技术评估",
        owner_id=test_admin.id,
        status="NEW",
    )
    db_session.add_all([customer, lead])
    db_session.flush()
    opportunity = Opportunity(
        opp_code=f"OPP-PERM07-ASSESS-{suffix}",
        customer_id=customer.id,
        opp_name=f"PERM07 技术评估商机-{suffix}",
        stage="DISCOVERY",
        owner_id=test_admin.id,
    )
    db_session.add(opportunity)
    db_session.commit()

    apply_lead_assessment(
        db=db_session,
        lead_id=lead.id,
        request=TechnicalAssessmentApplyRequest(evaluator_id=test_admin.id),
        current_user=test_admin,
    )
    apply_opportunity_assessment(
        db=db_session,
        opp_id=opportunity.id,
        request=TechnicalAssessmentApplyRequest(evaluator_id=test_admin.id),
        current_user=test_admin,
    )

    lead_log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.LEAD,
            SalesOperationLog.entity_id == lead.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )
    opportunity_log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id == opportunity.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )

    assert lead_log.old_value["assessment_id"] is None
    assert lead_log.old_value["assessment_status"] is None
    assert lead_log.new_value["assessment_id"] == lead.assessment_id
    assert lead_log.new_value["assessment_status"] == "PENDING"
    assert set(lead_log.changed_fields) >= {"assessment_id", "assessment_status"}
    assert lead_log.operation_desc == "申请线索技术评估"

    assert opportunity_log.old_value["assessment_id"] is None
    assert opportunity_log.old_value["assessment_status"] is None
    assert opportunity_log.new_value["assessment_id"] == opportunity.assessment_id
    assert opportunity_log.new_value["assessment_status"] == "PENDING"
    assert set(opportunity_log.changed_fields) >= {"assessment_id", "assessment_status"}
    assert opportunity_log.operation_desc == "申请商机技术评估"


def test_technical_assessment_evaluate_writes_source_completion_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-ASSESS-EVAL-{suffix}",
        customer_name=f"PERM07 执行技术评估客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    lead = Lead(
        lead_code=f"LEAD-PERM07-ASSESS-EVAL-{suffix}",
        source="官网",
        customer_name="PERM07 执行技术评估线索",
        industry="自动化测试",
        contact_name="评估联系人",
        contact_phone="13600000004",
        demand_summary="需要执行售前技术评估",
        owner_id=test_admin.id,
        status="NEW",
    )
    db_session.add_all([customer, lead])
    db_session.flush()
    opportunity = Opportunity(
        opp_code=f"OPP-PERM07-ASSESS-EVAL-{suffix}",
        customer_id=customer.id,
        opp_name=f"PERM07 执行技术评估商机-{suffix}",
        stage="DISCOVERY",
        owner_id=test_admin.id,
    )
    db_session.add(opportunity)
    db_session.commit()

    apply_lead_assessment(
        db=db_session,
        lead_id=lead.id,
        request=TechnicalAssessmentApplyRequest(evaluator_id=test_admin.id),
        current_user=test_admin,
    )
    apply_opportunity_assessment(
        db=db_session,
        opp_id=opportunity.id,
        request=TechnicalAssessmentApplyRequest(evaluator_id=test_admin.id),
        current_user=test_admin,
    )

    evaluation_request = TechnicalAssessmentEvaluateRequest(
        enable_ai=False,
        requirement_data={
            "tech_maturity": "mature",
            "process_difficulty": "standard",
            "precision_requirement": "normal",
            "sample_support": "available",
            "budget_status": "confirmed",
            "price_sensitivity": "low",
            "gross_margin_safety": "safe",
            "payment_terms": "good",
            "resource_occupancy": "available",
            "delivery_feasibility": "feasible",
            "customer_nature": "strategic",
            "customer_potential": "high",
        },
    )
    asyncio.run(
        evaluate_assessment(
            db=db_session,
            assessment_id=lead.assessment_id,
            request=evaluation_request,
            current_user=test_admin,
        )
    )
    asyncio.run(
        evaluate_assessment(
            db=db_session,
            assessment_id=opportunity.assessment_id,
            request=evaluation_request,
            current_user=test_admin,
        )
    )

    lead_logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.LEAD,
            SalesOperationLog.entity_id == lead.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )
    opportunity_logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id == opportunity.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert len(lead_logs) == 2
    assert lead_logs[1].old_value["assessment_status"] == "PENDING"
    assert lead_logs[1].new_value["assessment_status"] == "COMPLETED"
    assert lead_logs[1].new_value["assessment_id"] == lead.assessment_id
    assert "assessment_status" in lead_logs[1].changed_fields
    assert lead_logs[1].operation_desc == "执行线索技术评估"

    assert len(opportunity_logs) == 2
    assert opportunity_logs[1].old_value["assessment_status"] == "PENDING"
    assert opportunity_logs[1].new_value["assessment_status"] == "COMPLETED"
    assert opportunity_logs[1].new_value["assessment_id"] == opportunity.assessment_id
    assert "assessment_status" in opportunity_logs[1].changed_fields
    assert opportunity_logs[1].operation_desc == "执行商机技术评估"


def test_opportunity_crud_writes_opportunity_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-OPP-{suffix}",
        customer_name=f"PERM07 商机客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    db_session.add(customer)
    db_session.commit()

    create_response = create_opportunity(
        db=db_session,
        opp_in=OpportunityCreate(
            customer_id=customer.id,
            opp_name="PERM07 审计商机",
            stage="DISCOVERY",
            probability=20,
            est_amount=Decimal("200000.00"),
            budget_range="20-30万",
        ),
        current_user=test_admin,
    )
    opportunity_id = create_response.id

    update_opportunity(
        db=db_session,
        opp_id=opportunity_id,
        opp_in=OpportunityUpdate(
            opp_name="PERM07 审计商机-更新",
            stage="QUALIFICATION",
            probability=55,
            est_amount=Decimal("260000.00"),
            budget_range="25-35万",
        ),
        current_user=test_admin,
    )
    delete_opportunity(db=db_session, opp_id=opportunity_id, current_user=test_admin)

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id == opportunity_id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.CREATE,
        SalesOperationType.UPDATE,
        SalesOperationType.DELETE,
    ]
    assert logs[0].new_value["opp_name"] == "PERM07 审计商机"
    assert logs[0].new_value["est_amount"] == "200000.00"
    assert logs[1].old_value["opp_name"] == "PERM07 审计商机"
    assert logs[1].new_value["opp_name"] == "PERM07 审计商机-更新"
    assert logs[1].new_value["stage"] == "QUALIFICATION"
    assert logs[1].new_value["probability"] == 55
    assert set(logs[1].changed_fields) >= {
        "opp_name",
        "stage",
        "probability",
        "est_amount",
        "budget_range",
    }
    assert logs[2].old_value["stage"] == "QUALIFICATION"


def test_opportunity_batch_stage_writes_status_change_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-OPP-BATCH-STAGE-{suffix}",
        customer_name=f"PERM07 商机批量阶段客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    db_session.add(customer)
    db_session.flush()
    opportunities = [
        Opportunity(
            opp_code=f"OPP-PERM07-BATCH-STAGE-{suffix}-{index}",
            customer_id=customer.id,
            opp_name=f"PERM07 批量阶段商机-{index}",
            stage="DISCOVERY",
            owner_id=test_admin.id,
            probability=20,
            est_amount=Decimal("100000.00"),
        )
        for index in range(2)
    ]
    db_session.add_all(opportunities)
    db_session.commit()

    response = batch_update_stage(
        db=db_session,
        request=BatchUpdateStageRequest(
            opportunity_ids=[opp.id for opp in opportunities],
            stage="QUALIFICATION",
            reason="批量推进到需求挖掘",
        ),
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id.in_([opp.id for opp in opportunities]),
            SalesOperationLog.operation_type == SalesOperationType.STATUS_CHANGE,
        )
        .order_by(SalesOperationLog.entity_id)
        .all()
    )

    assert response.success_count == 2
    assert len(logs) == 2
    assert [log.old_value["stage"] for log in logs] == ["DISCOVERY", "DISCOVERY"]
    assert [log.new_value["stage"] for log in logs] == [
        "QUALIFICATION",
        "QUALIFICATION",
    ]
    assert all("stage" in log.changed_fields for log in logs)
    assert [log.remark for log in logs] == [
        "批量推进到需求挖掘",
        "批量推进到需求挖掘",
    ]


def test_opportunity_batch_owner_writes_assign_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-OPP-BATCH-OWNER-{suffix}",
        customer_name=f"PERM07 商机批量负责人客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    new_owner = User(
        username=f"perm07_opp_owner_{suffix}",
        password_hash="not-used",
        email=f"perm07_opp_owner_{suffix}@example.com",
        real_name="PERM07 商机新负责人",
        is_active=True,
    )
    db_session.add_all([customer, new_owner])
    db_session.flush()
    opportunities = [
        Opportunity(
            opp_code=f"OPP-PERM07-BATCH-OWNER-{suffix}-{index}",
            customer_id=customer.id,
            opp_name=f"PERM07 批量负责人商机-{index}",
            stage="DISCOVERY",
            owner_id=test_admin.id,
            probability=20,
            est_amount=Decimal("100000.00"),
        )
        for index in range(2)
    ]
    db_session.add_all(opportunities)
    db_session.commit()

    response = batch_update_owner(
        db=db_session,
        request=BatchUpdateOwnerRequest(
            opportunity_ids=[opp.id for opp in opportunities],
            owner_id=new_owner.id,
        ),
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id.in_([opp.id for opp in opportunities]),
            SalesOperationLog.operation_type == SalesOperationType.ASSIGN,
        )
        .order_by(SalesOperationLog.entity_id)
        .all()
    )

    assert response.success_count == 2
    assert len(logs) == 2
    assert [log.old_value["owner_id"] for log in logs] == [test_admin.id, test_admin.id]
    assert [log.new_value["owner_id"] for log in logs] == [new_owner.id, new_owner.id]
    assert all("owner_id" in log.changed_fields for log in logs)
    assert [log.remark for log in logs] == [
        "PERM07 商机新负责人",
        "PERM07 商机新负责人",
    ]


def test_opportunity_batch_close_writes_status_change_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-OPP-BATCH-CLOSE-{suffix}",
        customer_name=f"PERM07 商机批量关闭客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    db_session.add(customer)
    db_session.flush()
    opportunities = [
        Opportunity(
            opp_code=f"OPP-PERM07-BATCH-CLOSE-{suffix}-{index}",
            customer_id=customer.id,
            opp_name=f"PERM07 批量关闭商机-{index}",
            stage="NEGOTIATION",
            owner_id=test_admin.id,
            probability=60,
            est_amount=Decimal("100000.00"),
        )
        for index in range(2)
    ]
    db_session.add_all(opportunities)
    db_session.commit()

    response = batch_close_opportunities(
        db=db_session,
        request=BatchWinLoseRequest(
            opportunity_ids=[opp.id for opp in opportunities],
            is_won=True,
            reason="批量成交",
        ),
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id.in_([opp.id for opp in opportunities]),
            SalesOperationLog.operation_type == SalesOperationType.STATUS_CHANGE,
        )
        .order_by(SalesOperationLog.entity_id)
        .all()
    )

    assert response.success_count == 2
    assert len(logs) == 2
    assert [log.old_value["stage"] for log in logs] == [
        "NEGOTIATION",
        "NEGOTIATION",
    ]
    assert [log.new_value["stage"] for log in logs] == ["WON", "WON"]
    assert [log.old_value["close_reason"] for log in logs] == [None, None]
    assert [log.new_value["close_reason"] for log in logs] == [
        "批量成交",
        "批量成交",
    ]
    assert all(log.new_value["closed_at"] for log in logs)
    assert all("stage" in log.changed_fields for log in logs)
    assert all("close_reason" in log.changed_fields for log in logs)
    assert all("closed_at" in log.changed_fields for log in logs)
    assert [log.remark for log in logs] == ["批量成交", "批量成交"]


def test_opportunity_stage_workflow_writes_status_change_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-OPP-WF-{suffix}",
        customer_name=f"PERM07 商机工作流客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    db_session.add(customer)
    db_session.flush()
    stage_opportunity = Opportunity(
        opp_code=f"OPP-PERM07-STAGE-{suffix}",
        customer_id=customer.id,
        opp_name="PERM07 阶段推进商机",
        stage="DISCOVERY",
        owner_id=test_admin.id,
    )
    win_opportunity_record = Opportunity(
        opp_code=f"OPP-PERM07-WIN-{suffix}",
        customer_id=customer.id,
        opp_name="PERM07 赢单商机",
        stage="CLOSING",
        owner_id=test_admin.id,
    )
    lose_opportunity_record = Opportunity(
        opp_code=f"OPP-PERM07-LOSE-{suffix}",
        customer_id=customer.id,
        opp_name="PERM07 输单商机",
        stage="CLOSING",
        owner_id=test_admin.id,
    )
    db_session.add_all([
        stage_opportunity,
        win_opportunity_record,
        lose_opportunity_record,
    ])
    db_session.commit()

    update_opportunity_stage(
        db=db_session,
        opp_id=stage_opportunity.id,
        stage="QUALIFICATION",
        current_user=test_admin,
    )
    win_opportunity(
        db=db_session,
        opp_id=win_opportunity_record.id,
        current_user=test_admin,
    )
    lose_opportunity(
        db=db_session,
        opp_id=lose_opportunity_record.id,
        lose_reason="预算取消",
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id.in_([
                stage_opportunity.id,
                win_opportunity_record.id,
                lose_opportunity_record.id,
            ]),
        )
        .order_by(SalesOperationLog.entity_id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.STATUS_CHANGE,
        SalesOperationType.STATUS_CHANGE,
        SalesOperationType.STATUS_CHANGE,
    ]
    assert [log.old_value["stage"] for log in logs] == [
        "DISCOVERY",
        "CLOSING",
        "CLOSING",
    ]
    assert [log.new_value["stage"] for log in logs] == [
        "QUALIFICATION",
        "WON",
        "LOST",
    ]
    assert all("stage" in log.changed_fields for log in logs)


def test_opportunity_post_workflow_writes_status_change_operation_logs(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-OPP-POST-{suffix}",
        customer_name=f"PERM07 商机 POST 客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    db_session.add(customer)
    db_session.flush()

    advance_record = Opportunity(
        opp_code=f"OPP-PERM07-ADV-{suffix}",
        customer_id=customer.id,
        opp_name="PERM07 POST 推进商机",
        stage="DISCOVERY",
        owner_id=test_admin.id,
    )
    win_record = Opportunity(
        opp_code=f"OPP-PERM07-POST-WIN-{suffix}",
        customer_id=customer.id,
        opp_name="PERM07 POST 赢单商机",
        stage="CLOSING",
        owner_id=test_admin.id,
    )
    lose_compat_record = Opportunity(
        opp_code=f"OPP-PERM07-POST-LOSE-{suffix}",
        customer_id=customer.id,
        opp_name="PERM07 POST 兼容输单商机",
        stage="CLOSING",
        owner_id=test_admin.id,
    )
    loss_record = Opportunity(
        opp_code=f"OPP-PERM07-POST-LOSS-{suffix}",
        customer_id=customer.id,
        opp_name="PERM07 POST 新输单商机",
        stage="CLOSING",
        owner_id=test_admin.id,
    )
    db_session.add_all([
        advance_record,
        win_record,
        lose_compat_record,
        loss_record,
    ])
    db_session.commit()

    advance_opportunity(
        db=db_session,
        opp_id=advance_record.id,
        request=OpportunityAdvanceRequest(),
        current_user=test_admin,
    )
    win_opportunity_post(
        db=db_session,
        opp_id=win_record.id,
        remark="客户确认签约",
        current_user=test_admin,
    )
    lose_opportunity_post_compat(
        db=db_session,
        opp_id=lose_compat_record.id,
        request={"loss_reason": "客户取消", "competitor": "竞品A"},
        current_user=test_admin,
    )
    loss_opportunity_post(
        db=db_session,
        opp_id=loss_record.id,
        request=OpportunityLossRequest(loss_reason="预算冻结", competitor="竞品B"),
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id.in_([
                advance_record.id,
                win_record.id,
                lose_compat_record.id,
                loss_record.id,
            ]),
        )
        .all()
    )
    logs_by_entity = {log.entity_id: log for log in logs}

    assert set(logs_by_entity) == {
        advance_record.id,
        win_record.id,
        lose_compat_record.id,
        loss_record.id,
    }
    assert all(
        log.operation_type == SalesOperationType.STATUS_CHANGE
        for log in logs_by_entity.values()
    )
    assert logs_by_entity[advance_record.id].old_value["stage"] == "DISCOVERY"
    assert logs_by_entity[advance_record.id].new_value["stage"] == "QUALIFICATION"
    assert logs_by_entity[win_record.id].old_value["stage"] == "CLOSING"
    assert logs_by_entity[win_record.id].new_value["stage"] == "WON"
    assert logs_by_entity[lose_compat_record.id].old_value["stage"] == "CLOSING"
    assert logs_by_entity[lose_compat_record.id].new_value["stage"] == "LOST"
    assert logs_by_entity[loss_record.id].old_value["stage"] == "CLOSING"
    assert logs_by_entity[loss_record.id].new_value["stage"] == "LOST"
    assert logs_by_entity[lose_compat_record.id].remark == "客户取消"
    assert logs_by_entity[loss_record.id].remark == "预算冻结"


def test_opportunity_score_writes_update_operation_log(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-OPP-SCORE-{suffix}",
        customer_name=f"PERM07 商机评分客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    opportunity = Opportunity(
        opp_code=f"OPP-PERM07-SCORE-{suffix}",
        customer=customer,
        opp_name="PERM07 评分商机",
        stage="QUALIFICATION",
        score=40,
        risk_level="HIGH",
        owner_id=test_admin.id,
    )
    db_session.add_all([customer, opportunity])
    db_session.commit()

    update_opportunity_score(
        db=db_session,
        opp_id=opportunity.id,
        score=85,
        score_remark="重点客户，需求清晰",
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id == opportunity.id,
        )
        .one()
    )

    assert log.operation_type == SalesOperationType.UPDATE
    assert log.old_value["score"] == 40
    assert log.old_value["risk_level"] == "HIGH"
    assert log.new_value["score"] == 85
    assert log.new_value["risk_level"] == "LOW"
    assert set(log.changed_fields) >= {"score", "risk_level", "updated_by"}
    assert log.remark == "重点客户，需求清晰"


def test_opportunity_gate_writes_status_change_operation_log(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-OPP-GATE-{suffix}",
        customer_name=f"PERM07 商机阶段门客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    opportunity = Opportunity(
        opp_code=f"OPP-PERM07-GATE-{suffix}",
        customer=customer,
        opp_name="PERM07 阶段门商机",
        stage="PROPOSAL",
        gate_status="PENDING",
        owner_id=test_admin.id,
    )
    db_session.add_all([customer, opportunity])
    db_session.commit()

    submit_opportunity_gate(
        db=db_session,
        opp_id=opportunity.id,
        gate_request=OpportunityGateSubmitRequest(gate_status="REJECT"),
        gate_type="G2",
        current_user=test_admin,
    )

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id == opportunity.id,
        )
        .one()
    )

    assert log.operation_type == SalesOperationType.STATUS_CHANGE
    assert log.old_value["gate_status"] == "PENDING"
    assert log.new_value["gate_status"] == "REJECT"
    assert set(log.changed_fields) >= {"gate_status", "updated_by"}
    assert log.remark == "G2"


def test_solution_review_persist_writes_opportunity_update_log(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-SOLREV-{suffix}",
        customer_name=f"PERM07 方案评审客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    opportunity = Opportunity(
        opp_code=f"OPP-PERM07-SOLREV-{suffix}",
        customer=customer,
        opp_name="PERM07 方案评审商机",
        stage="PROPOSAL",
        owner_id=test_admin.id,
    )
    db_session.add_all([customer, opportunity])
    db_session.commit()

    persist_solution_review(
        db_session,
        opportunity.id,
        [
            {
                "aspect": "节拍可达性",
                "risk_level": "HIGH",
                "finding": "测试节拍存在超时风险",
                "suggestion": "增加并行工位",
            }
        ],
        current_user=test_admin,
    )

    row = (
        db_session.query(OpportunityRequirement)
        .filter(OpportunityRequirement.opportunity_id == opportunity.id)
        .one()
    )
    assert "ai_solution_review" in (row.extra_json or "")

    log = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id == opportunity.id,
            SalesOperationLog.operation_type == SalesOperationType.UPDATE,
        )
        .one()
    )
    assert log.new_value["solution_review"]["high_risk"] == 1
    assert log.new_value["solution_review"]["resolved"] is False
    assert "solution_review" in log.changed_fields
    assert log.remark == "ai_solution_review"


def test_solution_review_resolution_writes_opportunity_status_change_log(
    db_session: Session, test_admin: User
):
    suffix = uuid.uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-PERM07-SOLRES-{suffix}",
        customer_name=f"PERM07 方案处置客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=test_admin.id,
    )
    opportunity = Opportunity(
        opp_code=f"OPP-PERM07-SOLRES-{suffix}",
        customer=customer,
        opp_name="PERM07 方案处置商机",
        stage="PROPOSAL",
        owner_id=test_admin.id,
    )
    db_session.add_all([customer, opportunity])
    db_session.commit()

    persist_solution_review(
        db_session,
        opportunity.id,
        [{"aspect": "接口兼容", "risk_level": "HIGH", "finding": "协议未确认"}],
        current_user=test_admin,
    )
    resolve_solution_review(
        db_session,
        opportunity.id,
        action="ACCEPT_RISK",
        note="客户确认可接受接口联调风险",
        user_id=test_admin.id,
        current_user=test_admin,
    )

    logs = (
        db_session.query(SalesOperationLog)
        .filter(
            SalesOperationLog.entity_type == SalesEntityType.OPPORTUNITY,
            SalesOperationLog.entity_id == opportunity.id,
        )
        .order_by(SalesOperationLog.id)
        .all()
    )

    assert [log.operation_type for log in logs] == [
        SalesOperationType.UPDATE,
        SalesOperationType.STATUS_CHANGE,
    ]
    assert logs[1].old_value["solution_review"]["resolved"] is False
    assert logs[1].new_value["solution_review"]["resolved"] is True
    assert logs[1].new_value["solution_review"]["resolution"]["action"] == "ACCEPT_RISK"
    assert "solution_review" in logs[1].changed_fields
    assert logs[1].remark == "ai_solution_review_resolution"
