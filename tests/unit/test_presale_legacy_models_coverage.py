# -*- coding: utf-8 -*-
"""Coverage for legacy app/models/presale.py module."""

from datetime import date, datetime
import importlib.util
from pathlib import Path
import sys
import types

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declarative_base


REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_MODULE_PATH = REPO_ROOT / "app/models/presale.py"


def _load_legacy_presale_module(monkeypatch):
    fake_base_module = types.ModuleType("app.models.base")
    base = declarative_base()

    class TimestampMixin:
        created_at = Column(DateTime, default=datetime.now)
        updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    fake_base_module.Base = base
    fake_base_module.TimestampMixin = TimestampMixin
    monkeypatch.setitem(sys.modules, "app.models.base", fake_base_module)

    spec = importlib.util.spec_from_file_location("legacy_presale_coverage", LEGACY_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_legacy_presale_models_define_expected_schema(monkeypatch):
    mod = _load_legacy_presale_module(monkeypatch)

    assert [item.value for item in mod.TicketTypeEnum] == [
        "CONSULT",
        "SURVEY",
        "SOLUTION",
        "QUOTATION",
        "TENDER",
        "MEETING",
        "SITE_VISIT",
    ]
    assert [item.value for item in mod.TicketUrgencyEnum] == ["NORMAL", "URGENT", "VERY_URGENT"]
    assert [item.value for item in mod.TicketStatusEnum] == [
        "PENDING",
        "ACCEPTED",
        "PROCESSING",
        "REVIEW",
        "COMPLETED",
        "CLOSED",
        "CANCELLED",
    ]
    assert [item.value for item in mod.DeliverableStatusEnum] == [
        "DRAFT",
        "SUBMITTED",
        "APPROVED",
        "REJECTED",
    ]
    assert [item.value for item in mod.SolutionStatusEnum] == [
        "DRAFT",
        "REVIEW",
        "APPROVED",
        "DELIVERED",
        "WON",
        "LOST",
    ]
    assert [item.value for item in mod.TenderResultEnum] == ["PENDING", "WON", "LOST", "CANCELLED"]

    assert mod.PresaleSupportTicket.__tablename__ == "presale_support_ticket"
    assert mod.PresaleSupportTicket.__table__.c.urgency.default.arg == "NORMAL"
    assert mod.PresaleSupportTicket.__table__.c.status.default.arg == "PENDING"
    assert mod.PresaleSupportTicket.__table__.c.pm_involvement_required.default.arg is False
    assert mod.PresaleSupportTicket.__table__.c.pm_assigned.default.arg is False
    assert {index.name for index in mod.PresaleSupportTicket.__table__.indexes} == {
        "idx_presale_ticket_no",
        "idx_presale_ticket_status",
        "idx_presale_ticket_applicant",
        "idx_presale_ticket_assignee",
        "idx_presale_ticket_customer",
    }

    assert mod.PresaleTicketDeliverable.__tablename__ == "presale_ticket_deliverable"
    assert mod.PresaleTicketDeliverable.__table__.c.version.default.arg == "V1.0"
    assert mod.PresaleTicketDeliverable.__table__.c.status.default.arg == "DRAFT"

    assert mod.PresaleTicketProgress.__tablename__ == "presale_ticket_progress"
    assert mod.PresaleSolution.__tablename__ == "presale_solution"
    assert mod.PresaleSolution.__table__.c.solution_type.default.arg == "CUSTOM"
    assert mod.PresaleSolution.__table__.c.status.default.arg == "DRAFT"
    assert mod.PresaleSolution.__table__.c.version.default.arg == "V1.0"
    assert {index.name for index in mod.PresaleSolution.__table__.indexes} == {
        "idx_solution_no",
        "idx_solution_ticket",
        "idx_solution_customer",
        "idx_solution_industry",
    }

    assert mod.PresaleSolutionCost.__tablename__ == "presale_solution_cost"
    assert mod.PresaleSolutionCost.__table__.c.sort_order.default.arg == 0

    assert mod.PresaleSolutionTemplate.__tablename__ == "presale_solution_template"
    assert mod.PresaleSolutionTemplate.__table__.c.use_count.default.arg == 0
    assert mod.PresaleSolutionTemplate.__table__.c.is_active.default.arg is True

    assert mod.PresaleWorkload.__tablename__ == "presale_workload"
    assert mod.PresaleWorkload.__table__.c.pending_tickets.default.arg == 0
    assert mod.PresaleWorkload.__table__.c.processing_tickets.default.arg == 0
    assert mod.PresaleWorkload.__table__.c.completed_tickets.default.arg == 0

    assert mod.PresaleCustomerTechProfile.__tablename__ == "presale_customer_tech_profile"
    assert mod.PresaleTenderRecord.__tablename__ == "presale_tender_record"
    assert mod.PresaleTenderRecord.__table__.c.result.default.arg == "PENDING"

    ticket = mod.PresaleSupportTicket(ticket_no="PS-001", title="测试工单", ticket_type="CONSULT", applicant_id=1)
    deliverable = mod.PresaleTicketDeliverable(ticket_id=1, name="方案文档")
    progress = mod.PresaleTicketProgress(ticket_id=1, progress_type="UPDATE", operator_id=1)
    solution = mod.PresaleSolution(solution_no="SOL-001", name="测试方案", author_id=1)
    cost = mod.PresaleSolutionCost(solution_id=1, category="设备", item_name="工装")
    template = mod.PresaleSolutionTemplate(template_no="TPL-001", name="标准模板")
    workload = mod.PresaleWorkload(user_id=1, stat_date=date(2026, 4, 1))
    profile = mod.PresaleCustomerTechProfile(customer_id=101)
    tender = mod.PresaleTenderRecord(tender_name="招标项目")

    assert ticket.ticket_no == "PS-001"
    assert deliverable.name == "方案文档"
    assert progress.progress_type == "UPDATE"
    assert solution.solution_no == "SOL-001"
    assert cost.item_name == "工装"
    assert template.template_no == "TPL-001"
    assert workload.stat_date == date(2026, 4, 1)
    assert profile.customer_id == 101
    assert tender.tender_name == "招标项目"
